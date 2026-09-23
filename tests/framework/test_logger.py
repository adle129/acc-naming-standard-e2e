"""FR-11: step-level logging can diagnose a failure without a rerun."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.framework.support import (
    FIRST_STEP_LABEL,
    FORBIDDEN_SLEEP,
    FORBIDDEN_WAIT,
    LOGGER_REL_PATH,
    REPO_ROOT,
    SAMPLE_ACCEPTANCE_NODE_CHROMIUM,
    SAMPLE_ACCEPTANCE_TEST_NAME,
    SAMPLE_BANNER_ERROR,
    SAMPLE_LOGIN_PASSWORD,
    SAMPLE_LOGIN_USERNAME,
    SAMPLE_PROJECT_VALUE,
    SAMPLE_SCOPE_ERROR,
    SAMPLE_SCREENSHOT_REL,
    SAMPLE_TYPE_VALUE,
    STEP_CLICK_UPLOAD,
    STEP_EXPECT_BANNER,
    STEP_FILL_PROJECT,
    STEP_LOGIN,
    STEP_OPEN_FILES,
    STEP_PICK_TYPE,
    read_text,
)
from utils.test_data import ROW_UPLOAD_DELETE_RESTORE, SUITE_ACCEPTANCE
from utils.logger import (
    CASE_STEP,
    CASE_STEP_COLUMN,
    DURATION_SUFFIX,
    PHASE_CASE,
    PHASE_COLUMN,
    PHASE_TEST_END,
    PHASE_TEST_START,
    SECRET_MASK,
    STEP_RESULT_FAIL,
    STEP_RESULT_OK,
    STEP_RESULT_START,
    configure_logging,
    log_case,
    log_case_step,
    log_phase,
    phase_scope,
    reset_logging,
    set_screenshot_path,
    set_test_name,
    short_test_name,
    step,
    step_scope,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


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
    set_test_name(SAMPLE_ACCEPTANCE_TEST_NAME)
    # Hand the log path to the test so it can read what @step wrote.
    yield log_path
    # Always close handlers so Windows can delete the temp directory.
    reset_logging()


def test_successful_step_writes_pipe_line(_isolated_logger: Path) -> None:
    """Prove a passing @step line has test name, action, OK, and duration.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step(STEP_FILL_PROJECT)
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
    assert fill_project(SAMPLE_PROJECT_VALUE) == SAMPLE_PROJECT_VALUE
    # Read the file handler output, not stdout, so DEBUG lines are included.
    text = read_text(_isolated_logger)
    # Passing steps are INFO, matching console-visible output.
    assert "INFO" in text
    # The fixture-set test name must appear in the pipe line.
    assert SAMPLE_ACCEPTANCE_TEST_NAME in text
    # First action in this test is numbered STEP 1.
    assert FIRST_STEP_LABEL in text
    # {value} is interpolated from the function argument.
    assert STEP_FILL_PROJECT.format(value=SAMPLE_PROJECT_VALUE) in text
    # Result column for a clean return is OK.
    assert STEP_RESULT_OK in text
    # Duration is always recorded so waits are visible without sleeps.
    assert DURATION_SUFFIX in text


def test_failed_step_is_diagnosable_from_the_log(_isolated_logger: Path) -> None:
    """Prove a failing @step records FAIL, the exception, and a screenshot path.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # T10 will set this from the screenshot hook; here we inject the path.
    set_screenshot_path(SAMPLE_SCREENSHOT_REL)

    @step(STEP_EXPECT_BANNER)
    def expect_banner_hidden() -> None:
        """Stand-in assertion that always fails like a web-first expect.

        Raises:
            AssertionError: Always, so the decorator takes the FAIL path.
        """
        # The message must show up in the log so a rerun is unnecessary.
        raise AssertionError(SAMPLE_BANNER_ERROR)

    # The decorator must re-raise; logging is extra, not a swallow.
    with pytest.raises(AssertionError, match=SAMPLE_BANNER_ERROR):
        expect_banner_hidden()

    # Inspect the file after the exception has been logged.
    text = read_text(_isolated_logger)
    # Failures use ERROR so they stand out in the file and on the console.
    assert "ERROR" in text
    # The failing action is still the first step in this isolated test.
    assert FIRST_STEP_LABEL in text
    # Action text is the decorator description, not the Python traceback only.
    assert STEP_EXPECT_BANNER in text
    # Result column is FAIL, matching the PRD example.
    assert STEP_RESULT_FAIL in text
    # Exception type + message make the log enough to diagnose the failure.
    assert f"AssertionError: {SAMPLE_BANNER_ERROR}" in text
    # Screenshot path is appended so the reviewer can open the PNG next.
    assert SAMPLE_SCREENSHOT_REL in text


def test_step_redacts_password_arguments(_isolated_logger: Path) -> None:
    """Prove password-like arguments are replaced with the secret mask in the log.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step(STEP_LOGIN)
    def login(username: str, password: str) -> None:
        """Stand-in login action that would otherwise leak the password.

        Args:
            username: Account name that is safe to log.
            password: Secret that must be redacted in the formatted action.
        """
        # No work needed; we only care how the decorator formats arguments.
        return None

    # Pass a realistic secret; it must never appear in the log file.
    login(SAMPLE_LOGIN_USERNAME, SAMPLE_LOGIN_PASSWORD)
    # Read after the step so the redacted line is on disk.
    text = read_text(_isolated_logger)
    # Non-secret fields stay readable for diagnosis.
    assert SAMPLE_LOGIN_USERNAME in text
    # The raw password must be absent from every log line.
    assert SAMPLE_LOGIN_PASSWORD not in text
    # The placeholder proves the field was present and intentionally masked.
    assert f"password={SECRET_MASK}" in text


def test_step_scope_logs_ok_and_fail(_isolated_logger: Path) -> None:
    """Prove the context-manager form logs both OK and FAIL paths.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # Ad-hoc block used when a page object is not worth extracting yet.
    with step_scope(STEP_OPEN_FILES):
        # Empty body is enough to exercise the OK path.
        pass
    # The inner error must surface to the test runner after it is logged.
    with pytest.raises(RuntimeError, match=SAMPLE_SCOPE_ERROR):
        with step_scope(STEP_CLICK_UPLOAD):
            # Fail after the scope has started so FAIL + exception are written.
            raise RuntimeError(SAMPLE_SCOPE_ERROR)

    # Both scopes share one log file from the fixture.
    text = read_text(_isolated_logger)
    # First scope description is present on an OK line.
    assert STEP_OPEN_FILES in text
    # Second scope description is present on a FAIL line.
    assert STEP_CLICK_UPLOAD in text
    # Exception text is required so the log replaces a rerun.
    assert f"RuntimeError: {SAMPLE_SCOPE_ERROR}" in text


def test_file_handler_keeps_debug_start_lines(_isolated_logger: Path) -> None:
    """Prove the file handler records DEBUG START lines the console omits.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """

    @step(STEP_PICK_TYPE)
    def pick_type(value: str) -> None:
        """Stand-in dropdown action used only to emit START + OK lines.

        Args:
            value: Type code interpolated into the step description.
        """
        # Successful no-op is enough to emit START then OK.
        return None

    # Trigger both the DEBUG start line and the INFO OK line.
    pick_type(SAMPLE_TYPE_VALUE)
    # File level is DEBUG, so START must be in the file even if console is INFO.
    text = read_text(_isolated_logger)
    # START is the file-only breadcrumb that a step began.
    assert "DEBUG" in text
    assert STEP_RESULT_START in text
    # Argument formatting still applies on the start/OK action text.
    assert STEP_PICK_TYPE.format(value=SAMPLE_TYPE_VALUE) in text


def test_log_phase_writes_run_column_without_a_step_number(
    _isolated_logger: Path,
) -> None:
    """Prove TEST START / TEST END use RUN, not STEP 1.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # START marks the beginning of the product test body and names the function.
    start_line = PHASE_TEST_START.format(name=SAMPLE_ACCEPTANCE_TEST_NAME)
    log_phase(start_line, result=STEP_RESULT_START)
    # END is written from the live_acc fixture after cleanup.
    end_line = PHASE_TEST_END.format(name=SAMPLE_ACCEPTANCE_TEST_NAME)
    log_phase(end_line, result=STEP_RESULT_OK)
    # File handler includes both lines for the reviewer.
    text = read_text(_isolated_logger)
    # Lifecycle lines stay in the RUN column so UI steps keep STEP n.
    assert PHASE_COLUMN in text
    # The start label must include the pytest test name.
    assert start_line in text
    # The end label must include the same name with OK.
    assert end_line in text
    # A phase line must not consume the first UI step number.
    assert FIRST_STEP_LABEL not in text


def test_short_test_name_strips_browser_parameter() -> None:
    """Prove TEST NAME drops the Playwright [chromium] suffix."""
    # Pytest-playwright appends the browser to PYTEST_CURRENT_TEST.
    set_test_name(SAMPLE_ACCEPTANCE_NODE_CHROMIUM)
    # Reviewers search for the function name, not the node id.
    assert short_test_name() == SAMPLE_ACCEPTANCE_TEST_NAME


def test_log_case_step_writes_sample_step_number(_isolated_logger: Path) -> None:
    """Prove a business step line uses CASE and Step N - action.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # Sample step 3 is the first action the reviewer looks for after prepare.
    log_case_step(3, STEP_CLICK_UPLOAD)
    # Read the file so we assert the formatted line, not stdout.
    text = read_text(_isolated_logger)
    # CASE keeps this line apart from POM STEP 3 click Upload.
    assert CASE_STEP_COLUMN in text
    # The reviewer searches for this exact Step N wording.
    assert CASE_STEP.format(number=3, action=STEP_CLICK_UPLOAD) in text


def test_log_case_writes_suite_row_and_fields(_isolated_logger: Path) -> None:
    """Prove the case line names the JSON row and the filled attributes.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # Description text comes from the JSON row; keep it in one constant here.
    description = STEP_OPEN_FILES
    # Field summary is built by case_attribute_summary in product tests.
    attributes = STEP_FILL_PROJECT.format(value=SAMPLE_PROJECT_VALUE)
    # Same helper the acceptance test calls after load_row.
    log_case(
        suite=SUITE_ACCEPTANCE,
        row_id=ROW_UPLOAD_DELETE_RESTORE,
        description=description,
        attributes=attributes,
    )
    # Read the file so we assert the formatted action, not stdout.
    text = read_text(_isolated_logger)
    # Suite and row id must appear so the reviewer knows which JSON case ran.
    expected = PHASE_CASE.format(
        suite=SUITE_ACCEPTANCE,
        row_id=ROW_UPLOAD_DELETE_RESTORE,
        description=description,
    )
    assert expected in text
    # Attribute values stay on the extra column of the same line.
    assert attributes in text


def test_phase_scope_logs_ok_and_fail(_isolated_logger: Path) -> None:
    """Prove prepare/cleanup timing writes START then OK, or FAIL.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    # Empty prepare is enough to emit START and OK.
    with phase_scope(STEP_OPEN_FILES):
        pass
    # A failing cleanup must still surface after it is logged.
    with pytest.raises(RuntimeError, match=SAMPLE_SCOPE_ERROR):
        with phase_scope(STEP_CLICK_UPLOAD):
            raise RuntimeError(SAMPLE_SCOPE_ERROR)
    # Both scopes share the isolated log file.
    text = read_text(_isolated_logger)
    # Successful prepare uses the RUN column.
    assert PHASE_COLUMN in text
    # START is INFO for lifecycle so the console shows prepare beginning.
    assert STEP_RESULT_START in text
    # The failing action text is required for diagnosis.
    assert STEP_CLICK_UPLOAD in text
    # Exception text is required so the log replaces a rerun.
    assert f"RuntimeError: {SAMPLE_SCOPE_ERROR}" in text


def test_logger_module_has_no_sleeps() -> None:
    """Prove logger.py never uses time.sleep or Playwright wait_for_timeout."""
    # Read source so a future sleep cannot hide behind a helper name.
    source = read_text(REPO_ROOT / LOGGER_REL_PATH)
    # NFR-01: hard sleeps are forbidden in production framework code.
    assert FORBIDDEN_SLEEP not in source
    # Raw Playwright timeouts are also forbidden; @step uses perf_counter instead.
    assert FORBIDDEN_WAIT not in source
