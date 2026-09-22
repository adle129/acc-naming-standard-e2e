"""Secrets and generated artifacts must stay out of git."""

import subprocess
from pathlib import Path

import pytest

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Repository root: tests/framework -> tests -> repo.
ROOT = Path(__file__).resolve().parents[2]

# Patterns that must appear as text in .gitignore.
REQUIRED_PATTERNS = (
    ".env",
    "auth_state.json",
    "config/fernet.key",
    "reports/**",
    "logs/**",
)

# Concrete paths git check-ignore must report as ignored.
IGNORED_PATHS = (
    ".env",
    "auth_state.json",
    "config/fernet.key",
    "reports/report.html",
    "logs/run_example.log",
)


def test_gitignore_lists_sensitive_patterns() -> None:
    """Prove .gitignore text includes every required secret/artifact pattern."""
    # Read the committed ignore file, not git's computed exclude set.
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    # Keep the missing names for a precise assertion message.
    missing = []
    for pattern in REQUIRED_PATTERNS:
        if pattern not in text:
            missing.append(pattern)
    # An empty list means a reviewer cannot accidentally commit these paths.
    assert missing == [], f".gitignore missing patterns: {missing}"


def test_git_ignores_secret_and_artifact_paths() -> None:
    """Prove git itself treats the secret and artifact paths as ignored."""
    # Ask git, not just the text file, so a broken pattern is caught.
    result = subprocess.run(
        ["git", "check-ignore", "-v", *IGNORED_PATHS],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    # check-ignore returns 0 only when every given path is ignored.
    assert result.returncode == 0, result.stderr
    # The last tab-separated field is the path git matched.
    ignored = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line.split("\t", 1)[-1].strip()
        ignored.add(path)
    # Compare the requested paths against what git actually reported.
    missing = []
    for path in IGNORED_PATHS:
        if path not in ignored:
            missing.append(path)
    # Any leftover path would be committable and fail FR-12.
    assert missing == [], f"git does not ignore: {missing}\n{result.stdout}"
