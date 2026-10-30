import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_DIR = REPO_ROOT / "artifacts" / "e2e"
E2E_DATABASE_URL = (
    os.environ.get("E2E_DATABASE_URL")
    or "postgresql+psycopg://practilizate:practilizate@localhost:5433/practilizate_e2e"
)


def _ensure_database(database_url: str) -> None:
    url = make_url(database_url)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        exists = connection.execute(
            text("select 1 from pg_database where datname = :name"), {"name": url.database}
        ).scalar()
        if not exists:
            connection.execute(text(f'create database "{url.database}"'))
    admin.dispose()


def _reset_public_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("drop schema if exists public cascade"))
        connection.execute(text("create schema public"))
    engine.dispose()


def run_cli(*args: str, database_url: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url or E2E_DATABASE_URL
    return subprocess.run(
        [sys.executable, "-m", "practilizate", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def e2e_run() -> Path:
    _ensure_database(E2E_DATABASE_URL)
    _reset_public_schema(E2E_DATABASE_URL)
    E2E_DIR.mkdir(parents=True, exist_ok=True)
    for entry in E2E_DIR.iterdir():
        if entry.name == ".gitkeep":
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()

    result = run_cli(
        "run",
        "--source",
        "fixtures",
        "--as-of",
        "2026-10-29",
        "--run-id",
        "e2e",
        "--artifacts-dir",
        str(E2E_DIR),
        "--output-dir",
        str(E2E_DIR),
        database_url=E2E_DATABASE_URL,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"pipeline failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return E2E_DIR


@pytest.fixture(scope="session")
def e2e_database_url() -> str:
    return E2E_DATABASE_URL


@pytest.fixture(scope="session")
def e2e_strict_run(e2e_run: Path) -> Path:
    strict_dir = e2e_run / "strict"
    strict_dir.mkdir(parents=True, exist_ok=True)
    result = run_cli(
        "run",
        "--source",
        "fixtures",
        "--as-of",
        "2026-10-29",
        "--run-id",
        "e2e-strict",
        "--artifacts-dir",
        str(strict_dir),
        "--output-dir",
        str(strict_dir),
        "--strict",
        database_url=E2E_DATABASE_URL,
    )
    assert result.returncode == 1, (
        f"strict run should fail on warnings:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return strict_dir


@pytest.fixture(scope="session")
def e2e_db(e2e_run: Path, e2e_database_url: str):
    engine = create_engine(e2e_database_url)
    yield engine
    engine.dispose()
