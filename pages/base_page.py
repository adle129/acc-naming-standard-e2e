"""Common navigation, screenshot, and @step-wrapped actions for every page object."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from re import Pattern
from typing import Any

from playwright.sync_api import expect

from utils.config import REPO_ROOT
from utils.logger import current_test_name, set_screenshot_path, step

# Screenshot layout from FR-10: reports/screenshots/<test_name>_<timestamp>.png
REPORTS_DIR_NAME = "reports"
SCREENSHOTS_DIR_NAME = "screenshots"
SCREENSHOT_EXT = ".png"
SCREENSHOT_STAMP_FORMAT = "%Y%m%d_%H%M%S_%f"
NAME_STAMP_SEPARATOR = "_"

# Playwright screenshot flag. Full page so a failure is diagnosable without scrolling.
FULL_PAGE_SCREENSHOT = True

# Step text. Tests import these so they do not copy action wording.
STEP_NAVIGATE = "navigate to {url}"
STEP_VERIFY_URL = "verify url {url_pattern}"
STEP_SCREENSHOT = "screenshot {name}"


def screenshot_dir(root: Path | None = None) -> Path:
    """Return reports/screenshots under the given (or repo) root.

    Args:
        root: Project root. Defaults to this repository.

    Returns:
        Directory where failure screenshots are written.
    """
    # Tests pass a temp root so CI never writes into the real reports/ tree.
    return (REPO_ROOT if root is None else Path(root)) / REPORTS_DIR_NAME / SCREENSHOTS_DIR_NAME


def screenshot_file_name(test_name: str, stamp: str) -> str:
    """Build the FR-10 screenshot file name.

    Args:
        test_name: Pytest node name, for example test_upload_delete_restore.
        stamp: Timestamp fragment already formatted.

    Returns:
        File name only, including the .png suffix.
    """
    return test_name + NAME_STAMP_SEPARATOR + stamp + SCREENSHOT_EXT


class BasePage:
    """Shared page-object base. Waits come from Playwright auto-wait, not sleep."""

    def __init__(self, page: Any, *, root: Path | None = None) -> None:
        """Attach a Playwright page (or a test double) and an optional repo root.

        Args:
            page: Playwright Page, or a fake with goto() and screenshot().
            root: Project root used for screenshot paths. Defaults to this repo.
        """
        self.page = page
        self.root = REPO_ROOT if root is None else Path(root)

    @step(STEP_NAVIGATE)
    def navigate_to(self, url: str) -> None:
        """Go to a URL. Playwright waits for load; this method does not sleep.

        Args:
            url: Absolute URL to open.
        """
        self.page.goto(url=url)

    @step(STEP_VERIFY_URL)
    def verify_url(self, url_pattern: str | Pattern[str]) -> None:
        """Check the current URL. All pages use this so the expect call stays in one place.

        Args:
            url_pattern: Exact URL string, or a compiled regex for query-string pages.
        """
        expect(self.page).to_have_url(url=url_pattern)

    @step(STEP_SCREENSHOT)
    def take_screenshot(self, name: str | None = None, stamp: str | None = None) -> Path:
        """Capture a full-page screenshot and record its path for the logger.

        Args:
            name: File-name prefix. Defaults to the current pytest test name.
            stamp: Timestamp fragment. Defaults to now. Tests pass a fixed value.

        Returns:
            Absolute path of the PNG that was written.
        """
        if name is None:
            name = current_test_name()
        if stamp is None:
            stamp = datetime.now().strftime(SCREENSHOT_STAMP_FORMAT)
        directory = screenshot_dir(self.root)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / screenshot_file_name(name, stamp)
        # full_page so the log + PNG pair is enough to diagnose without a rerun.
        self.page.screenshot(path=str(path), full_page=FULL_PAGE_SCREENSHOT)
        set_screenshot_path(path)
        return path
