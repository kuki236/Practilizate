import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from practilizate import __version__
from practilizate.config import Settings, load_settings
from practilizate.logging import configure_logging, get_logger

LOGGER = get_logger("practilizate.cli")


def default_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="practilizate",
        description=(
            "Ingest, validate, load, and export public pre-professional internship "
            "offers from practicas.pe."
        ),
    )
    parser.add_argument("--version", action="version", version=f"practilizate {__version__}")
    parser.add_argument("--log-level", default=None, help="Log level (default: INFO).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser(
        "ingest",
        help="Fetch listings and details into the local cache.",
        description="Fetch public listings and detail pages, respecting rate limits.",
    )
    _add_source_options(ingest)
    ingest.add_argument("--run-id", default=None, help="Run identifier (default: timestamp).")
    ingest.add_argument(
        "--artifacts-dir",
        type=Path,
        default=None,
        help="Directory for the ingest report (default: artifacts/runs/<run-id>).",
    )
    ingest.add_argument("--max-pages", type=int, default=None, help="Page cap per career.")

    run = subparsers.add_parser(
        "run",
        help="Run the full pipeline: ingest, normalize, quality, load, export.",
        description="Run every pipeline stage and write reproducible artifacts.",
    )
    _add_source_options(run)
    run.add_argument("--run-id", default=None, help="Run identifier (default: timestamp).")
    run.add_argument(
        "--artifacts-dir",
        type=Path,
        default=None,
        help="Directory for run artifacts (default: artifacts/runs/<run-id>).",
    )
    run.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for the CSV and Excel deliverables (default: data/processed).",
    )
    run.add_argument("--max-pages", type=int, default=None, help="Page cap per career.")
    run.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip the PostgreSQL load (demo only; the E2E suite never uses this).",
    )
    run.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any quality rule fails, not only critical rules.",
    )
    run.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL for this run.",
    )

    quality = subparsers.add_parser(
        "quality",
        help="Print the quality report for a run.",
        description="Read and summarize the quality report written by a previous run.",
    )
    _add_run_reference_options(quality)

    load = subparsers.add_parser(
        "load",
        help="Load a completed run into PostgreSQL.",
        description="Create the star schema and load the normalized offers of a run.",
    )
    _add_run_reference_options(load)
    load.add_argument("--database-url", default=None, help="Override DATABASE_URL.")

    export = subparsers.add_parser(
        "export",
        help="Export a completed run to Excel and CSV.",
        description="Rebuild the dashboard CSV and the Spanish Excel workbook from a run.",
    )
    _add_run_reference_options(export)
    export.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Destination directory (default: data/processed).",
    )
    export.add_argument(
        "--format",
        default="excel,csv",
        help="Comma-separated formats: excel,csv (default: excel,csv).",
    )

    return parser


def _add_source_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        choices=["fixtures", "live"],
        default=None,
        help="Data source (default: PRACTILIZATE_SOURCE or fixtures).",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Reference date in YYYY-MM-DD for deterministic deadline calculations.",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=None,
        help="Fixture directory (default: data/fixtures).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Raw cache directory (default: data/raw/cache).",
    )


def _add_run_reference_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-id", default=None, help="Run identifier (default: latest).")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=None,
        help="Directory that contains the run artifacts.",
    )


def _settings_from_args(args: argparse.Namespace) -> Settings:
    overrides: dict[str, object] = {}
    for field in ("source", "as_of", "fixtures_dir", "cache_dir", "output_dir", "artifacts_dir"):
        value = getattr(args, field, None)
        if value is not None:
            overrides[field] = value
    if getattr(args, "database_url", None):
        overrides["database_url"] = args.database_url
    return load_settings(**overrides)


def _artifact_dir(settings: Settings, args: argparse.Namespace, run_id: str) -> Path:
    if args.artifacts_dir is not None:
        return args.artifacts_dir
    return settings.artifacts_dir / "runs" / run_id


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = _settings_from_args(args)
    configure_logging(args.log_level or settings.log_level)
    run_id = getattr(args, "run_id", None) or default_run_id()

    try:
        if args.command == "ingest":
            from practilizate.pipeline import ingest_command

            return ingest_command(settings, args, _artifact_dir(settings, args, run_id))
        if args.command == "run":
            from practilizate.pipeline import run_command

            return run_command(settings, args, _artifact_dir(settings, args, run_id))
        if args.command == "quality":
            from practilizate.pipeline import quality_command

            return quality_command(settings, args)
        if args.command == "load":
            from practilizate.pipeline import load_command

            return load_command(settings, args)
        if args.command == "export":
            from practilizate.pipeline import export_command

            return export_command(settings, args)
    except KeyboardInterrupt:
        LOGGER.warning("interrupted")
        return 130
    except Exception:
        LOGGER.exception("command failed", extra={"command": args.command})
        return 1

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
