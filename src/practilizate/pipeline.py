import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from practilizate.config import Settings
from practilizate.db import load_offers
from practilizate.export import ExportContext, write_dashboard_csv, write_excel
from practilizate.fetch import FetchError, LiveSource
from practilizate.ingest import ingest_offers
from practilizate.logging import get_logger
from practilizate.models import IngestResult, Offer, QualityReport
from practilizate.quality import evaluate_quality
from practilizate.sources import FixtureSource, OfferSource, SourceError

LOGGER = get_logger("practilizate.pipeline")

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class PipelineError(RuntimeError):
    pass


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.match(run_id):
        raise PipelineError(
            "invalid run id: use letters, digits, dashes, or underscores (max 64 characters)"
        )
    return run_id


def make_source(settings: Settings, max_pages: int | None = None) -> OfferSource:
    pages = max_pages or settings.max_pages_per_career
    if settings.source == "fixtures":
        return FixtureSource(settings.fixtures_dir, settings.as_of, max_pages=pages)
    if settings.source == "live":
        return LiveSource(
            cache_dir=settings.cache_dir,
            user_agent=settings.user_agent,
            rate_limit_seconds=settings.rate_limit_seconds,
            timeout_seconds=settings.request_timeout_seconds,
            max_pages=pages,
        )
    raise PipelineError(f"unknown source: {settings.source}")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    tmp = path.with_suffix(f"{path.suffix}.tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
        newline="\n",
    )
    tmp.replace(path)


def read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise PipelineError(f"artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def run_dir_for(settings: Settings, args, run_id: str) -> Path:
    if getattr(args, "artifacts_dir", None) is not None:
        return Path(args.artifacts_dir)
    return settings.artifacts_dir / "runs" / run_id


def resolve_run_dir(settings: Settings, args) -> Path:
    if getattr(args, "artifacts_dir", None) is not None:
        return Path(args.artifacts_dir)
    run_id = getattr(args, "run_id", None)
    if run_id:
        return settings.artifacts_dir / "runs" / validate_run_id(run_id)
    latest = settings.artifacts_dir / "latest.json"
    if latest.is_file():
        payload = read_json(latest)
        return settings.artifacts_dir / "runs" / str(payload["run_id"])
    raise PipelineError("no run specified and no artifacts/latest.json found")


def _max_pages(args) -> int | None:
    value = getattr(args, "max_pages", None)
    if value is None:
        return None
    if value < 1:
        raise PipelineError("--max-pages must be at least 1")
    return value


def _ingest(settings: Settings, args) -> IngestResult:
    source = make_source(settings, _max_pages(args))
    try:
        return ingest_offers(source, as_of=settings.as_of)
    except (FetchError, SourceError) as error:
        raise PipelineError(f"ingestion failed: {error}") from error
    finally:
        close = getattr(source, "close", None)
        if callable(close):
            close()


def _write_ingest_report(path: Path, run_id: str, result: IngestResult) -> None:
    write_json(
        path,
        {
            "run_id": run_id,
            "source": result.source,
            "as_of": result.as_of,
            "stats": result.stats.model_dump(mode="json"),
        },
    )


def _write_normalized(path: Path, result: IngestResult, run_id: str) -> None:
    write_json(
        path,
        {
            "run_id": run_id,
            "source": result.source,
            "as_of": result.as_of,
            "offers": [offer.model_dump(mode="json") for offer in result.offers],
        },
    )


def ingest_command(settings: Settings, args, run_dir: Path) -> int:
    run_id = validate_run_id(args.run_id or run_dir.name)
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = _ingest(settings, args)
    _write_ingest_report(run_dir / "ingest_report.json", run_id, result)
    LOGGER.info(
        "ingest command finished",
        extra={
            "run_id": run_id,
            "offers": result.stats.unique_offers,
            "runtime_seconds": round(time.perf_counter() - started, 3),
            "artifacts": str(run_dir),
        },
    )
    return 0


def _load_into_db(
    settings: Settings, run_id: str, run_dir: Path, offers: list[Offer]
) -> dict[str, int]:
    result = load_offers(offers, settings.database_url, settings.sql_dir)
    write_json(
        run_dir / "database_load.json",
        {"run_id": run_id, "counts": result.counts},
    )
    return result.counts


def run_command(settings: Settings, args, run_dir: Path) -> int:
    run_id = validate_run_id(args.run_id or run_dir.name)
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    started_at = datetime.now(UTC)
    result = _ingest(settings, args)
    evaluation = evaluate_quality(
        result.offers,
        run_id=run_id,
        source=result.source,
        as_of=result.as_of,
        salary_min=settings.salary_min,
        salary_max=settings.salary_max,
    )
    for offer in result.offers:
        offer.quality_score = evaluation.scores.get(offer.offer_id, 1.0)

    _write_ingest_report(run_dir / "ingest_report.json", run_id, result)
    write_json(run_dir / "quality_report.json", evaluation.report)
    _write_normalized(run_dir / "normalized_offers.json", result, run_id)

    strict_failure = bool(getattr(args, "strict", False)) and any(
        rule.failed > 0 for rule in evaluation.report.rules
    )
    status = "failed_quality" if not evaluation.report.passed or strict_failure else "qualified"
    stages: dict[str, object] = {"ingest": result.stats.model_dump(mode="json")}
    artifacts = {
        "normalized": "normalized_offers.json",
        "ingest_report": "ingest_report.json",
        "quality_report": "quality_report.json",
    }

    if status == "qualified":
        if getattr(args, "skip_db", False):
            status = "qualified_no_db"
        else:
            try:
                stages["load"] = _load_into_db(settings, run_id, run_dir, result.offers)
                artifacts["database_load"] = "database_load.json"
                status = "completed"
            except Exception as error:
                LOGGER.exception("database load failed", extra={"run_id": run_id})
                stages["load"] = {"status": "failed", "error_type": type(error).__name__}
                status = "failed_load"

    outputs: dict[str, str] = {}
    if status in {"completed", "qualified_no_db", "failed_load"}:
        try:
            output_dir = Path(getattr(args, "output_dir", None) or settings.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            csv_path = output_dir / "dashboard_dataset.csv"
            excel_path = output_dir / "practilizate.xlsx"
            context = ExportContext(
                run_id=run_id,
                source=result.source,
                as_of=result.as_of,
                generated_at=datetime.now(UTC).replace(tzinfo=None),
                runtime_seconds=round(time.perf_counter() - started, 3),
                quality=evaluation.report,
                salary_max=settings.salary_max,
            )
            csv_rows = write_dashboard_csv(result.offers, csv_path, result.as_of)
            excel_sheets = write_excel(result.offers, context, excel_path)
            write_json(
                run_dir / "export_report.json",
                {
                    "run_id": run_id,
                    "csv": {"path": str(csv_path), "rows": csv_rows},
                    "excel": {"path": str(excel_path), "sheets": excel_sheets},
                },
            )
            stages["export"] = {"csv_rows": csv_rows, "excel_sheets": excel_sheets}
            artifacts["dashboard_csv"] = "dashboard_dataset.csv"
            artifacts["excel"] = "practilizate.xlsx"
            artifacts["export_report"] = "export_report.json"
            outputs = {"dashboard_csv": str(csv_path), "excel": str(excel_path)}
        except Exception as error:
            LOGGER.exception("export failed", extra={"run_id": run_id})
            stages["export"] = {"status": "failed", "error_type": type(error).__name__}
            status = "failed_export"
    runtime = round(time.perf_counter() - started, 3)
    manifest = {
        "run_id": run_id,
        "source": result.source,
        "as_of": result.as_of,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime_seconds": runtime,
        "status": status,
        "quality": {
            "overall_score": evaluation.report.overall_score,
            "passed": evaluation.report.passed,
            "strict": bool(getattr(args, "strict", False)),
            "critical_failures": evaluation.report.critical_failures,
            "failed_rules": [rule.rule_id for rule in evaluation.report.rules if rule.failed > 0],
        },
        "counts": {
            "offers": result.stats.unique_offers,
            "careers": result.stats.careers,
            "pages": result.stats.pages,
            "listing_refs": result.stats.listing_refs,
            "duplicates": result.stats.duplicate_refs,
            "detail_failures": len(result.stats.detail_failures),
        },
        "stages": stages,
        "artifacts": artifacts,
        "outputs": outputs,
    }
    write_json(run_dir / "run_manifest.json", manifest)
    if getattr(args, "artifacts_dir", None) is None:
        settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
        write_json(settings.artifacts_dir / "latest.json", {"run_id": run_id, "path": str(run_dir)})
    LOGGER.info(
        "run command finished",
        extra={
            "run_id": run_id,
            "offers": result.stats.unique_offers,
            "duplicates": result.stats.duplicate_refs,
            "quality_score": evaluation.report.overall_score,
            "critical_failures": evaluation.report.critical_failures,
            "status": status,
            "runtime_seconds": runtime,
            "artifacts": str(run_dir),
        },
    )
    return 0 if status in {"completed", "qualified_no_db"} else 1


def quality_command(settings: Settings, args) -> int:
    run_dir = resolve_run_dir(settings, args)
    report = read_json(run_dir / "quality_report.json")
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


def load_command(settings: Settings, args) -> int:
    run_dir = resolve_run_dir(settings, args)
    payload = read_json(run_dir / "normalized_offers.json")
    offers = [Offer.model_validate(item) for item in payload["offers"]]
    run_id = validate_run_id(str(payload.get("run_id") or run_dir.name))
    counts = _load_into_db(settings, run_id, run_dir, offers)
    sys.stdout.write(json.dumps(counts, ensure_ascii=False, indent=2) + "\n")
    return 0


def export_command(settings: Settings, args) -> int:
    run_dir = resolve_run_dir(settings, args)
    payload = read_json(run_dir / "normalized_offers.json")
    offers = [Offer.model_validate(item) for item in payload["offers"]]
    run_id = validate_run_id(str(payload.get("run_id") or run_dir.name))
    quality_payload = read_json(run_dir / "quality_report.json")
    quality = QualityReport.model_validate(quality_payload)
    manifest = read_json(run_dir / "run_manifest.json")
    output_dir = Path(getattr(args, "output_dir", None) or settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    formats = {part.strip().lower() for part in str(args.format).split(",") if part.strip()}
    unknown = formats - {"excel", "csv"}
    if unknown:
        raise PipelineError(f"unknown export format: {', '.join(sorted(unknown))}")
    context = ExportContext(
        run_id=run_id,
        source=str(manifest.get("source", payload.get("source", settings.source))),
        as_of=settings.as_of,
        generated_at=datetime.now(UTC).replace(tzinfo=None),
        runtime_seconds=float(manifest.get("runtime_seconds", 0.0)),
        quality=quality,
        salary_max=settings.salary_max,
    )
    result: dict[str, object] = {}
    if "csv" in formats:
        rows = write_dashboard_csv(offers, output_dir / "dashboard_dataset.csv", settings.as_of)
        result["csv"] = {"rows": rows}
    if "excel" in formats:
        sheets = write_excel(offers, context, output_dir / "practilizate.xlsx")
        result["excel"] = {"sheets": sheets}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return 0
