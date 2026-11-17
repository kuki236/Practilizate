import subprocess
import sys

import practilizate


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "practilizate", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_exposes_help_and_version() -> None:
    help_result = run_cli("--help")
    assert help_result.returncode == 0
    for command in ("ingest", "run", "quality", "load", "export"):
        assert command in help_result.stdout

    version_result = run_cli("--version")
    assert version_result.returncode == 0
    assert f"practilizate {practilizate.__version__}" in version_result.stdout
