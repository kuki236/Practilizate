import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from practilizate.config import Settings
from practilizate.fetch import FetchError, LiveSource
from practilizate.ingest import ingest_offers
from practilizate.logging import get_logger
from practilizate.models import IngestResult
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


def _write_normalized(path: Path, result: IngestResult) -> None:
    write_json(
        path,
        {
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


def run_command(settings: Settings, args, run_dir: Path) -> int:
    run_id = validate_run_id(args.run_id or run_dir.name)
    run_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    started_at = datetime.now(UTC)
    result = _ingest(settings, args)
    _write_ingest_report(run_dir / "ingest_report.json", run_id, result)
    _write_normalized(run_dir / "normalized_offers.json", result)
    runtime = round(time.perf_counter() - started, 3)
    manifest = {
        "run_id": run_id,
        "source": result.source,
        "as_of": result.as_of,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime_seconds": runtime,
        "status": "ingested",
        "counts": {
            "offers": result.stats.unique_offers,
            "careers": result.stats.careers,
            "pages": result.stats.pages,
            "listing_refs": result.stats.listing_refs,
            "duplicates": result.stats.duplicate_refs,
            "detail_failures": len(result.stats.detail_failures),
        },
        "stages": {"ingest": result.stats.model_dump(mode="json")},
        "artifacts": {
            "normalized": "normalized_offers.json",
            "ingest_report": "ingest_report.json",
        },
    }
    write_json(run_dir / "run_manifest.json", manifest)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    write_json(settings.artifacts_dir / "latest.json", {"run_id": run_id, "path": str(run_dir)})
    LOGGER.info(
        "run command ingested offers",
        extra={
            "run_id": run_id,
            "offers": result.stats.unique_offers,
            "duplicates": result.stats.duplicate_refs,
            "runtime_seconds": runtime,
            "artifacts": str(run_dir),
        },
    )
    return 0


def quality_command(settings: Settings, args) -> int:
    run_dir = resolve_run_dir(settings, args)
    report = read_json(run_dir / "quality_report.json")
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0


def load_command(settings: Settings, args) -> int:
    raise PipelineError("load is available after the star-schema checkpoint")


def export_command(settings: Settings, args) -> int:
    raise PipelineError("export is available after the workbook checkpoint")
