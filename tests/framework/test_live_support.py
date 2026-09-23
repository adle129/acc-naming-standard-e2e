"""Function-level live helpers dismiss overlays and track uploads without ACC."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from dialogs.upload_dialog import STEP_CLOSE_UPLOAD
from dialogs.validator_dialog import STEP_CANCEL_VALIDATOR
from tests.framework.support import (
    SAMPLE_ACCEPTANCE_TEST_NAME,
    SAMPLE_COMPOSED_FILE_NAME,
    SAMPLE_DEMO_RES1_FILE_NAME,
    SAMPLE_GENERATED_PROJECT,
    SAMPLE_KEEP_MANUAL_FILE_NAME,
    SAMPLE_SETTINGS,
    read_text,
)
from tests.framework.test_pages import FakePage
from tests.live_support import (
    DEFAULT_EXPECT_TIMEOUT_MS,
    DISMISS_TIMEOUT_MS,
    LiveAcc,
    dismiss_open_overlays,
)
from utils.logger import configure_logging, reset_logging, set_test_name

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path) -> Iterator[Path]:
    """Give dismiss-click tests a logger so @step can write.

    Args:
        tmp_path: Isolated log directory.

    Yields:
        Path of the run log file created for this test.
    """
    reset_logging()
    log_path = configure_logging(log_dir=tmp_path)
    set_test_name(SAMPLE_ACCEPTANCE_TEST_NAME)
    yield log_path
    reset_logging()


def test_dismiss_open_overlays_is_quiet_when_nothing_is_visible() -> None:
    """Prove dismiss does not click when every overlay control is hidden.

    Args:
        None.
    """
    page = FakePage()
    # Default FakeLocator.is_visible() is False, so no Cancel / close runs.
    dismiss_open_overlays(page, timeout_ms=DISMISS_TIMEOUT_MS)
    assert page.last_locator.click_count == 0


def test_dismiss_open_overlays_clicks_cancel_when_visible(
    _isolated_logger: Path,
) -> None:
    """Prove a visible validator Cancel is clicked so the next test starts clean.

    Args:
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    # Overlay checks use is_visible(); the fake then allows the Cancel click.
    page.locator_visible = True
    dismiss_open_overlays(page, timeout_ms=DISMISS_TIMEOUT_MS)
    # @step lines prove Cancel and picker close ran, not just that a locator exists.
    text = read_text(_isolated_logger)
    assert STEP_CANCEL_VALIDATOR in text
    assert STEP_CLOSE_UPLOAD in text


def test_live_acc_remembers_only_this_test_upload() -> None:
    """Prove remember_upload stores the composed name for later delete.

    Args:
        None.
    """
    page = FakePage()
    acc = LiveAcc(page, SAMPLE_SETTINGS)
    # Cleanup deletes only names this test recorded, not names[0] on the folder.
    acc.remember_upload(SAMPLE_COMPOSED_FILE_NAME)
    assert acc.uploaded_names == [SAMPLE_COMPOSED_FILE_NAME]


def test_live_acc_remembers_project_before_composed_name() -> None:
    """Prove remember_project is enough for cleanup when name capture fails.

    Args:
        None.
    """
    page = FakePage()
    acc = LiveAcc(page, SAMPLE_SETTINGS)
    # Acceptance records Project as soon as the case row is loaded.
    acc.remember_project(SAMPLE_GENERATED_PROJECT)
    assert acc.uploaded_projects == [SAMPLE_GENERATED_PROJECT]
    # The composed name contains that Project, so cleanup can still select it.
    assert acc._should_delete_name(SAMPLE_COMPOSED_FILE_NAME) is True


def test_generated_leftover_is_deleted_demo_file_is_kept() -> None:
    """Prove leftover unique-Project files are cleaned; demo rows stay.

    Args:
        None.
    """
    page = FakePage()
    acc = LiveAcc(page, SAMPLE_SETTINGS)
    # Failed runs leave AB12-XXX-ZZ-ZZ-CA-D-3402.txt on the shared folder.
    assert acc._is_generated_upload(SAMPLE_COMPOSED_FILE_NAME) is True
    # res1 is a forbidden demo Project and must not be swept.
    assert acc._is_generated_upload(SAMPLE_DEMO_RES1_FILE_NAME) is False
    # Manual test-... names do not use this suite's composed marker.
    assert acc._is_generated_upload(SAMPLE_KEEP_MANUAL_FILE_NAME) is False


def test_cleanup_skips_delete_when_no_upload_was_recorded() -> None:
    """Prove cleanup does not open Files again when this test created nothing.

    Args:
        None.
    """
    page = FakePage()
    acc = LiveAcc(page, SAMPLE_SETTINGS)
    # uploaded_names is empty, so _delete_remembered_uploads returns immediately.
    acc.cleanup()
    assert page.goto_urls == []


def test_default_expect_timeout_is_playwright_default() -> None:
    """Prove cleanup restores the Playwright expect timeout, not ACC_TIMEOUT_MS."""
    # Cleanup must put back a timeout shorter than ACC_TIMEOUT_MS.
    assert DEFAULT_EXPECT_TIMEOUT_MS < SAMPLE_SETTINGS.timeout_ms
