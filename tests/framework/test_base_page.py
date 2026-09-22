"""FR-01 / FR-10: BasePage opens URLs and writes screenshots without opening ACC."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from pages.base_page import (
    FULL_PAGE_SCREENSHOT,
    NAME_STAMP_SEPARATOR,
    REPORTS_DIR_NAME,
    SCREENSHOT_EXT,
    SCREENSHOTS_DIR_NAME,
    STEP_NAVIGATE,
    STEP_SCREENSHOT,
    STEP_VERIFY_URL,
    BasePage,
    screenshot_dir,
    screenshot_file_name,
)
from tests.framework.support import (
    BASE_PAGE_REL,
    FORBIDDEN_SLEEP,
    FORBIDDEN_WAIT,
    REPO_ROOT,
    SAMPLE_ACCEPTANCE_TEST_NAME,
    SAMPLE_OPEN_URL,
    SAMPLE_SCREENSHOT_BYTES,
    SAMPLE_SCREENSHOT_STAMP,
    read_text,
)
from utils.logger import (
    STEP_RESULT_OK,
    configure_logging,
    current_test_name,
    reset_logging,
    set_test_name,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


class FakePage:
    """Stand-in Playwright page. Records calls; never talks to ACC."""

    def __init__(self) -> None:
        self.goto_urls: list[str] = []
        self.screenshot_calls: list[tuple[str, bool]] = []

    def goto(self, url: str) -> None:
        """Record navigation the way Playwright Page.goto does.

        Args:
            url: Absolute URL BasePage asked to open.
        """
        self.goto_urls.append(url)

    def screenshot(self, path: str, full_page: bool = False) -> bytes:
        """Write fake PNG bytes to path so tests can assert the file exists.

        Args:
            path: Destination path BasePage computed.
            full_page: Must be True; FR-10 requires a full-page capture.

        Returns:
            The fake PNG bytes that were written.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(SAMPLE_SCREENSHOT_BYTES)
        self.screenshot_calls.append((path, full_page))
        return SAMPLE_SCREENSHOT_BYTES


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path) -> Iterator[Path]:
    """Give each test a fresh logger under tmp_path.

    Args:
        tmp_path: Pytest temp directory used as the log directory.

    Yields:
        Path of the run log file created for this test.
    """
    reset_logging()
    log_path = configure_logging(log_dir=tmp_path)
    set_test_name(SAMPLE_ACCEPTANCE_TEST_NAME)
    yield log_path
    reset_logging()


def test_navigate_to_goes_to_the_given_url(tmp_path: Path, _isolated_logger: Path) -> None:
    """Prove navigate_to calls page.goto and logs the URL as a step.

    Args:
        tmp_path: Isolated root so screenshots would not hit the real reports/.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    base = BasePage(page, root=tmp_path)
    # Later pages call this instead of page.goto so the step log stays consistent.
    base.navigate_to(SAMPLE_OPEN_URL)
    # The fake records the URL so we know ACC was never contacted.
    assert page.goto_urls == [SAMPLE_OPEN_URL]
    text = read_text(_isolated_logger)
    assert STEP_NAVIGATE.format(url=SAMPLE_OPEN_URL) in text
    assert STEP_RESULT_OK in text


def test_verify_url_uses_playwright_expect(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove verify_url is the single wrapper around expect().to_have_url.

    Args:
        tmp_path: Isolated root passed into BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so this test never launches a browser.
    """
    seen_page = {}
    seen_url = {}

    class FakeAssertion:
        """Stand-in for Playwright's PageAssertions."""

        def to_have_url(self, url: str) -> None:
            """Record the pattern BasePage asked Playwright to check.

            Args:
                url: The url= argument passed to to_have_url.
            """
            seen_url["value"] = url

    def fake_expect(page: FakePage) -> FakeAssertion:
        """Return the fake assertion instead of a real Playwright expect.

        Args:
            page: The page object BasePage handed to expect().

        Returns:
            A recorder that captures to_have_url.
        """
        seen_page["value"] = page
        return FakeAssertion()

    # Patch the name BasePage imported, not playwright.sync_api itself.
    monkeypatch.setattr("pages.base_page.expect", fake_expect)
    page = FakePage()
    base = BasePage(page, root=tmp_path)
    # Product tests will call this after navigate_to; the expect stays in BasePage.
    base.verify_url(SAMPLE_OPEN_URL)
    assert seen_page["value"] is page
    assert seen_url["value"] == SAMPLE_OPEN_URL
    text = read_text(_isolated_logger)
    assert STEP_VERIFY_URL.format(url_pattern=SAMPLE_OPEN_URL) in text


def test_screenshot_path_matches_fr10_layout() -> None:
    """Prove screenshot names are reports/screenshots/<test>_<stamp>.png."""
    # Directory helper must stay under reports/screenshots, not logs/.
    directory = screenshot_dir(REPO_ROOT)
    assert directory.name == SCREENSHOTS_DIR_NAME
    assert directory.parent.name == REPORTS_DIR_NAME
    # File name is test name, underscore, stamp, extension — no extra folders.
    name = screenshot_file_name(SAMPLE_ACCEPTANCE_TEST_NAME, SAMPLE_SCREENSHOT_STAMP)
    assert name.startswith(SAMPLE_ACCEPTANCE_TEST_NAME + NAME_STAMP_SEPARATOR)
    assert name.endswith(SCREENSHOT_EXT)
    assert SAMPLE_SCREENSHOT_STAMP in name


def test_take_screenshot_writes_full_page_file(tmp_path: Path, _isolated_logger: Path) -> None:
    """Prove take_screenshot writes a PNG under the isolated reports tree.

    Args:
        tmp_path: Isolated project root for the screenshot file.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    base = BasePage(page, root=tmp_path)
    # Fixed stamp so the assertion does not depend on the clock.
    path = base.take_screenshot(name=SAMPLE_ACCEPTANCE_TEST_NAME, stamp=SAMPLE_SCREENSHOT_STAMP)
    expected = screenshot_dir(tmp_path) / screenshot_file_name(
        SAMPLE_ACCEPTANCE_TEST_NAME,
        SAMPLE_SCREENSHOT_STAMP,
    )
    assert path == expected
    # The file must exist so a reviewer can open it after a failure.
    assert path.exists()
    assert path.read_bytes() == SAMPLE_SCREENSHOT_BYTES
    # FR-10 requires a full-page capture, not the visible viewport only.
    assert page.screenshot_calls == [(str(path), FULL_PAGE_SCREENSHOT)]
    # The step log names the screenshot so the PNG and the log line match.
    text = read_text(_isolated_logger)
    assert STEP_SCREENSHOT.format(name=SAMPLE_ACCEPTANCE_TEST_NAME) in text


def test_take_screenshot_defaults_to_the_current_test_name(tmp_path: Path) -> None:
    """Prove a caller can omit name and still get a test-named PNG.

    Args:
        tmp_path: Isolated project root for the screenshot file.
    """
    page = FakePage()
    base = BasePage(page, root=tmp_path)
    # T10's failure hook will call take_screenshot() with no name argument.
    path = base.take_screenshot(stamp=SAMPLE_SCREENSHOT_STAMP)
    # The logger already knows the pytest node name from set_test_name().
    assert path.name.startswith(current_test_name() + NAME_STAMP_SEPARATOR)


def test_base_page_has_no_sleeps() -> None:
    """Prove BasePage never uses time.sleep or wait_for_timeout."""
    source = read_text(REPO_ROOT / BASE_PAGE_REL)
    # NFR-01: waits are Playwright auto-wait on goto/screenshot, not sleeps.
    assert FORBIDDEN_SLEEP not in source
    assert FORBIDDEN_WAIT not in source
