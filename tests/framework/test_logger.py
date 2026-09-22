"""FR-11: step-level logging can diagnose a failure without a rerun."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from utils.logger import (
    configure_logging,
    reset_logging,
    set_screenshot_path,
    set_test_name,
    step,
    step_scope,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Repository root: tests/framework -> tests -> repo.
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path) -> Iterator[Path]:
    """Give each test a fresh logger that writes into tmp_path.

    Args:
        tmp_path: Pytest temp directory used as the log directory.

    Yields:
        Path of the run log file created for this test.
    """
    # Drop handlers left over from a previous test in this process.
    reset_logging()
    # Point the file handler at tmp_path so we never touch repo logs/.
    log_path = configure_logging(log_dir=tmp_path)
    # Use the acceptance-test name so log lines match the PRD example shape.
    set_test_name("test_upload_delete_restore")
    # Hand the log path to the test so it can read what @step wrote.
    yield log_path
    # Always close handlers so Windows can delete the temp directory.
    reset_logging()


def _read(log_path: Path) -> str:
    """Return the full text of a run log.

    Args:
        log_path: Log file created by configure_logging.

    Returns:
        UTF-8 contents of the log file.
    """
    # Tests assert on substrings; keep the helper to one read.
    return log_path.read_text(encoding="utf-8")


def test_successful_step_writes_pipe_line(_isolated_logger: Path) -> None:
    """Prove a passing @step line has test name, action, OK, and duration.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step("fill Project = {value}")
    def fill_project(value: str) -> str:
        """Stand-in page-object action that echoes the formatted value.

        Args:
            value: Project attribute written into the step description.

        Returns:
            The same value, proving the wrapper still returns the result.
        """
        # No UI here; the decorator only needs a successful return.
        return value

    # Call the wrapped action the way a later Page Object method will.
    assert fill_project("hw472") == "hw472"
    # Read the file handler output, not stdout, so DEBUG lines are included.
    text = _read(_isolated_logger)
    # Passing steps are INFO, matching console-visible output.
    assert "INFO" in text
    # The fixture-set test name must appear in the pipe line.
    assert "test_upload_delete_restore" in text
    # First action in this test is numbered STEP 1.
    assert "STEP 1" in text
    # {value} is interpolated from the function argument.
    assert "fill Project = hw472" in text
    # Result column for a clean return is OK.
    assert "OK" in text
    # Duration is always recorded so waits are visible without sleeps.
    assert "ms" in text


def test_failed_step_is_diagnosable_from_the_log(_isolated_logger: Path) -> None:
    """Prove a failing @step records FAIL, the exception, and a screenshot path.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # T10 will set this from the screenshot hook; here we inject the path.
    set_screenshot_path("reports/screenshots/test_upload_delete_restore.png")

    @step("expect banner hidden")
    def expect_banner_hidden() -> None:
        """Stand-in assertion that always fails like a web-first expect.

        Raises:
            AssertionError: Always, so the decorator takes the FAIL path.
        """
        # The message must show up in the log so a rerun is unnecessary.
        raise AssertionError("banner still visible")

    # The decorator must re-raise; logging is extra, not a swallow.
    with pytest.raises(AssertionError, match="banner still visible"):
        expect_banner_hidden()

    # Inspect the file after the exception has been logged.
    text = _read(_isolated_logger)
    # Failures use ERROR so they stand out in the file and on the console.
    assert "ERROR" in text
    # The failing action is still the first step in this isolated test.
    assert "STEP 1" in text
    # Action text is the decorator description, not the Python traceback only.
    assert "expect banner hidden" in text
    # Result column is FAIL, matching the PRD example.
    assert "FAIL" in text
    # Exception type + message make the log enough to diagnose the failure.
    assert "AssertionError: banner still visible" in text
    # Screenshot path is appended so the reviewer can open the PNG next.
    assert "screenshot: reports/screenshots/test_upload_delete_restore.png" in text


def test_step_redacts_password_arguments(_isolated_logger: Path) -> None:
    """Prove password-like arguments are replaced with *** in the log.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step("login as {username} password={password}")
    def login(username: str, password: str) -> None:
        """Stand-in login action that would otherwise leak the password.

        Args:
            username: Account name that is safe to log.
            password: Secret that must be redacted in the formatted action.
        """
        # No work needed; we only care how the decorator formats arguments.
        return None

    # Pass a realistic secret; it must never appear in the log file.
    login("reviewer@example.com", "super-secret")
    # Read after the step so the redacted line is on disk.
    text = _read(_isolated_logger)
    # Non-secret fields stay readable for diagnosis.
    assert "reviewer@example.com" in text
    # The raw password must be absent from every log line.
    assert "super-secret" not in text
    # The placeholder proves the field was present and intentionally masked.
    assert "password=***" in text


def test_step_scope_logs_ok_and_fail(_isolated_logger: Path) -> None:
    """Prove the context-manager form logs both OK and FAIL paths.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # Ad-hoc block used when a page object is not worth extracting yet.
    with step_scope("open files page"):
        # Empty body is enough to exercise the OK path.
        pass
    # The inner error must surface to the test runner after it is logged.
    with pytest.raises(RuntimeError, match="boom"):
        with step_scope("click Upload"):
            # Fail after the scope has started so FAIL + exception are written.
            raise RuntimeError("boom")

    # Both scopes share one log file from the fixture.
    text = _read(_isolated_logger)
    # First scope description is present on an OK line.
    assert "open files page" in text
    # Second scope description is present on a FAIL line.
    assert "click Upload" in text
    # Exception text is required so the log replaces a rerun.
    assert "RuntimeError: boom" in text


def test_file_handler_keeps_debug_start_lines(_isolated_logger: Path) -> None:
    """Prove the file handler records DEBUG START lines the console omits.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step("pick Type = {value}")
    def pick_type(value: str) -> None:
        """Stand-in dropdown action used only to emit START + OK lines.

        Args:
            value: Type code interpolated into the step description.
        """
        # Successful no-op is enough to emit START then OK.
        return None

    # Trigger both the DEBUG start line and the INFO OK line.
    pick_type("CA")
    # File level is DEBUG, so START must be in the file even if console is INFO.
    text = _read(_isolated_logger)
    # START is the file-only breadcrumb that a step began.
    assert "DEBUG" in text
    assert "START" in text
    # Argument formatting still applies on the start/OK action text.
    assert "pick Type = CA" in text


def test_logger_module_has_no_sleeps() -> None:
    """Prove logger.py never uses time.sleep or Playwright wait_for_timeout."""
    # Read source so a future sleep cannot hide behind a helper name.
    source = (ROOT / "utils" / "logger.py").read_text(encoding="utf-8")
    # NFR-01: hard sleeps are forbidden in production framework code.
    assert "time.sleep" not in source
    # Raw Playwright timeouts are also forbidden; @step uses perf_counter instead.
    assert "wait_for_timeout" not in source
