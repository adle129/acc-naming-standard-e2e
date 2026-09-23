"""FR-15: pytest.assume records a failure and lets later steps run."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.framework.support import (
    ASSUME_ADDOPTS_EMPTY,
    ASSUME_PROBE_FILE_NAME,
    ASSUME_PROBE_SOURCE,
    REPO_ROOT,
    SAMPLE_ASSUME_CONTINUED,
    SAMPLE_ASSUME_FAIL_MESSAGE,
    SAMPLE_ASSUME_PASS_MESSAGE,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Probe must fail; 0 would mean pytest-assume swallowed the failed assume.
PROBE_FAILED_EXIT = 0
PYTHONPATH_ENV = "PYTHONPATH"


def test_pytest_assume_is_available() -> None:
    """Prove pytest-assume registered pytest.assume for product tests."""
    # The plugin attaches assume on the pytest namespace during configure.
    assert hasattr(pytest, "assume")
    # A passing check must not fail this framework test.
    passed = pytest.assume(True, SAMPLE_ASSUME_PASS_MESSAGE)
    # pytest.assume returns the condition so a later step can still branch.
    assert passed is True


def test_failed_assume_fails_the_test_after_later_steps(tmp_path: Path) -> None:
    """Prove pytest.assume still fails the test after the body prints a later step.

    Args:
        tmp_path: Isolated directory for a one-off probe test file.
    """
    # A nested pytest run is the only way to see pytest-assume mark a test failed.
    probe = tmp_path / ASSUME_PROBE_FILE_NAME
    # The probe calls pytest.assume(False) and then prints.
    probe.write_text(ASSUME_PROBE_SOURCE, encoding="utf-8")
    env = os.environ.copy()
    # Keep the same interpreter env; pytest-assume is already installed.
    env[PYTHONPATH_ENV] = str(REPO_ROOT)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe),
            "-o",
            ASSUME_ADDOPTS_EMPTY,
            "-q",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    output = result.stdout + result.stderr
    # Non-zero means pytest-assume failed the test after the body finished.
    assert result.returncode != PROBE_FAILED_EXIT, output
    # The first assume message must appear in the report.
    assert SAMPLE_ASSUME_FAIL_MESSAGE in output
    # The print after pytest.assume(False) proves the flow was not stopped mid-test.
    assert SAMPLE_ASSUME_CONTINUED in output
