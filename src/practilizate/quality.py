import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from urllib.parse import urlparse

from practilizate.logging import get_logger
from practilizate.models import Offer, QualityReport, QualityRuleResult
from practilizate.text import normalize_key

LOGGER = get_logger("practilizate.quality")

ALLOWED_MODALITIES = {"Preprofesional", "Profesional"}
ALLOWED_ATTENDANCE = {"Presencial", "Híbrido", "Virtual"}
CRITICAL_RULES = {"R02", "R03", "R13", "R16", "R17"}
SAMPLE_SIZE = 5
DETAILED_REQUIREMENTS_LENGTH = 80
MOJIBAKE_MARKERS = ("Ã", "Â", "\ufffd")


@dataclass
class _Rule:
    rule_id: str
    description: str
    checked: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)

    def result(self) -> QualityRuleResult:
        checked = len(self.checked)
        failed = len(self.failed)
        pass_rate = round((checked - failed) / checked, 4) if checked else 1.0
        return QualityRuleResult(
            rule_id=self.rule_id,
            description=self.description,
            severity="critical" if self.rule_id in CRITICAL_RULES else "warning",
            checked=checked,
            failed=failed,
            pass_rate=pass_rate,
            sample_failed_offer_ids=sorted(self.failed)[:SAMPLE_SIZE],
        )


@dataclass
class QualityEvaluation:
    report: QualityReport
    scores: dict[str, float]


def _check(rule: _Rule, offer: Offer, condition: bool) -> None:
    rule.checked.add(offer.offer_id)
    if not condition:
        rule.failed.add(offer.offer_id)


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _text_is_normalized(value: str) -> bool:
    if value != value.strip() or "  " in value:
        return False
    if any(marker in value for marker in MOJIBAKE_MARKERS):
        return False
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", value):
        return False
    try:
        value.encode("utf-8").decode("utf-8")
    except UnicodeError:
        return False
    return True


def evaluate_quality(
    offers: list[Offer],
    *,
    run_id: str,
    source: str,
    as_of: date,
    salary_min: float,
    salary_max: float,
) -> QualityEvaluation:
    rules = {
        "R01": _Rule("R01", "Required fields: title, company, URL"),
        "R02": _Rule("R02", "Unique offer URL"),
        "R03": _Rule("R03", "Valid absolute URL"),
        "R04": _Rule("R04", "Valid published date"),
        "R05": _Rule("R05", "Valid deadline date"),
        "R06": _Rule("R06", "Deadline is not earlier than published date"),
        "R07": _Rule("R07", "Salary is numeric or explicitly null"),
        "R08": _Rule("R08", "Salary within configured bounds"),
        "R09": _Rule("R09", "Company name is not empty after normalization"),
        "R10": _Rule("R10", "Location is present"),
        "R11": _Rule("R11", "Modality is in the allowed set"),
        "R12": _Rule("R12", "Attendance is in the allowed set"),
        "R13": _Rule("R13", "At least one career is associated"),
        "R14": _Rule("R14", "Duplicate title + company + deadline"),
        "R15": _Rule("R15", "Skills are present when requirements are detailed"),
        "R16": _Rule("R16", "Source fetch timestamp exists"),
        "R17": _Rule("R17", "Text is valid UTF-8 and normalized"),
    }

    url_counts: dict[str, list[str]] = defaultdict(list)
    content_groups: dict[tuple[str, str, date], list[str]] = defaultdict(list)

    for offer in offers:
        title_present = bool(offer.title) and offer.title != "Sin título"
        _check(rules["R01"], offer, title_present and bool(offer.company) and bool(offer.url))
        url_counts[offer.url].append(offer.offer_id)
        _check(rules["R03"], offer, _valid_url(offer.url))
        _check(rules["R04"], offer, offer.published_at is not None)
        _check(rules["R05"], offer, offer.deadline_at is not None)
        if offer.published_at is not None and offer.deadline_at is not None:
            _check(rules["R06"], offer, offer.deadline_at >= offer.published_at)
        salary_consistent = (offer.salary_amount is None) or (offer.salary_text is not None)
        _check(rules["R07"], offer, salary_consistent)
        if offer.salary_amount is not None:
            _check(
                rules["R08"],
                offer,
                salary_min <= offer.salary_amount <= salary_max,
            )
        _check(rules["R09"], offer, offer.company_normalized is not None)
        _check(rules["R10"], offer, bool(offer.location))
        _check(rules["R11"], offer, offer.modality in ALLOWED_MODALITIES)
        _check(rules["R12"], offer, offer.attendance in ALLOWED_ATTENDANCE)
        _check(rules["R13"], offer, bool(offer.careers))
        if offer.company_normalized and offer.deadline_at is not None:
            key = (
                normalize_key(offer.title),
                offer.company_normalized,
                offer.deadline_at,
            )
            content_groups[key].append(offer.offer_id)
            _check(rules["R14"], offer, True)
        if len(offer.requirements_text) >= DETAILED_REQUIREMENTS_LENGTH:
            _check(rules["R15"], offer, bool(offer.skills))
        _check(rules["R16"], offer, offer.source_fetched_at is not None)
        _check(
            rules["R17"],
            offer,
            all(
                _text_is_normalized(value)
                for value in (offer.title, offer.company or "", offer.requirements_text)
            ),
        )

    for offer_ids in url_counts.values():
        if len(offer_ids) > 1:
            for offer_id in offer_ids:
                rules["R02"].checked.add(offer_id)
                rules["R02"].failed.add(offer_id)
        else:
            rules["R02"].checked.add(offer_ids[0])

    for offer_ids in content_groups.values():
        if len(offer_ids) > 1:
            for offer_id in offer_ids:
                rules["R14"].failed.add(offer_id)

    ordered_rules = [rules[f"R{index:02d}"].result() for index in range(1, 18)]
    overall_score = round(sum(result.pass_rate for result in ordered_rules) / len(ordered_rules), 4)
    critical_failures = [
        result.rule_id
        for result in ordered_rules
        if result.severity == "critical" and result.failed > 0
    ]
    report = QualityReport(
        run_id=run_id,
        source=source,
        as_of=as_of,
        generated_at=datetime.now(UTC),
        offers_checked=len(offers),
        rules=ordered_rules,
        overall_score=overall_score,
        critical_failures=critical_failures,
        passed=not critical_failures,
    )

    scores = _offer_scores(offers, rules)
    LOGGER.info(
        "quality evaluation finished",
        extra={
            "offers": len(offers),
            "overall_score": overall_score,
            "critical_failures": critical_failures,
        },
    )
    return QualityEvaluation(report=report, scores=scores)


def _offer_scores(offers: list[Offer], rules: dict[str, _Rule]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for offer in offers:
        applicable = 0
        failed = 0
        for rule in rules.values():
            if offer.offer_id in rule.checked:
                applicable += 1
                if offer.offer_id in rule.failed:
                    failed += 1
        scores[offer.offer_id] = round(1 - (failed / applicable), 4) if applicable else 1.0
    return scores
