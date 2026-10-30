import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def offers_by_suffix(e2e_run: Path) -> dict[str, dict]:
    payload = load_json(e2e_run / "normalized_offers.json")
    return {
        offer["url"].rsplit("-", 1)[-1].removesuffix(".html"): offer for offer in payload["offers"]
    }


def test_fixture_run_normalizes_offers_and_preserves_multi_career(e2e_run: Path) -> None:
    payload = load_json(e2e_run / "normalized_offers.json")
    offers = payload["offers"]
    assert len(offers) == 12
    assert len({offer["url"] for offer in offers}) == 12

    by_id = offers_by_suffix(e2e_run)
    multi = by_id["90001"]
    assert [career["id"] for career in multi["careers"]] == ["1", "10"]
    assert [career["id"] for career in by_id["90007"]["careers"]] == ["10"]

    report = load_json(e2e_run / "ingest_report.json")
    assert report["stats"]["listing_refs"] == 13
    assert report["stats"]["duplicate_refs"] == 1
    assert report["stats"]["detail_failures"] == []
    assert report["stats"]["careers"] == 3


def test_fixture_run_surfaces_medium_hard_cases(e2e_run: Path) -> None:
    by_id = offers_by_suffix(e2e_run)

    assert by_id["90002"]["salary_amount"] is None
    assert by_id["90002"]["status"] == "expiring_soon"
    assert by_id["90003"]["deadline_at"] is None
    assert by_id["90003"]["status"] == "unknown"
    assert by_id["90004"]["published_at"] is None
    assert by_id["90005"]["salary_amount"] == 95000.0
    assert by_id["90006"]["company"] is None
    assert by_id["90006"]["company_normalized"] is None
    assert by_id["90008"]["status"] == "expired"
    assert by_id["90009"]["location"] is None
    assert by_id["90010"]["attendance"] == "Rotativo"
    assert by_id["90011"]["skills"] == []
    assert len(by_id["90012"]["skills"]) >= 2

    support = by_id["90003"]
    assert "reclutamiento@example.com" not in support["requirements_text"]
    assert "999 111 222" not in support["requirements_text"]
    assert "[contacto eliminado]" in support["requirements_text"]


def test_quality_report_flags_expected_failures(e2e_run: Path) -> None:
    report = load_json(e2e_run / "quality_report.json")
    assert report["offers_checked"] == 12
    assert report["passed"] is True
    assert report["critical_failures"] == []
    assert report["overall_score"] == 0.9427

    rules = {rule["rule_id"]: rule for rule in report["rules"]}
    expected = {
        "R01": ["90006"],
        "R04": ["90004"],
        "R05": ["90003"],
        "R06": ["90008"],
        "R08": ["90005"],
        "R09": ["90006"],
        "R10": ["90009"],
        "R12": ["90010"],
        "R14": ["90001", "90007"],
        "R15": ["90011"],
    }
    for rule_id, samples in expected.items():
        assert rules[rule_id]["failed"] == len(samples), rule_id
        assert rules[rule_id]["sample_failed_offer_ids"] == samples, rule_id

    for rule_id in ("R02", "R03", "R07", "R11", "R13", "R16", "R17"):
        assert rules[rule_id]["failed"] == 0, rule_id

    scores = {
        offer["offer_id"]: offer["quality_score"]
        for offer in load_json(e2e_run / "normalized_offers.json")["offers"]
    }
    assert scores["90002"] == 1.0
    assert scores["90012"] == 1.0
    assert scores["90006"] < 0.9
    assert scores["90001"] < 1.0


def test_strict_mode_blocks_warning_only_runs(e2e_strict_run: Path) -> None:
    manifest = load_json(e2e_strict_run / "run_manifest.json")
    assert manifest["status"] == "failed_quality"
    assert manifest["quality"]["passed"] is True
    assert manifest["quality"]["strict"] is True
    assert manifest["quality"]["failed_rules"]
    report = load_json(e2e_strict_run / "quality_report.json")
    assert report["passed"] is True
