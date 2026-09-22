"""Secrets and generated artifacts must stay out of git."""

import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.framework

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATTERNS = (
    ".env",
    "auth_state.json",
    "reports/**",
    "logs/**",
)

IGNORED_PATHS = (
    ".env",
    "auth_state.json",
    "reports/report.html",
    "logs/run_example.log",
)


def test_gitignore_lists_sensitive_patterns() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    missing = [pattern for pattern in REQUIRED_PATTERNS if pattern not in text]
    assert missing == [], f".gitignore missing patterns: {missing}"


def test_git_ignores_secret_and_artifact_paths() -> None:
    result = subprocess.run(
        ["git", "check-ignore", "-v", *IGNORED_PATHS],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    ignored = {line.split("\t", 1)[-1].strip() for line in result.stdout.splitlines() if line.strip()}
    missing = [path for path in IGNORED_PATHS if path not in ignored]
    assert missing == [], f"git does not ignore: {missing}\n{result.stdout}"
