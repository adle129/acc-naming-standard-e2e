"""Left navigation rail. Files is the entry used to leave Deleted items."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

# Visible name of the Files tool in the project nav.
NAV_LINK_ROLE = "link"
FILES_NAV_NAME = "Files"

STEP_OPEN_FILES_NAV = "open Files from nav"


class AppNav(BasePage):
    """Project-level navigation used to return to the Files list."""

    def files_link(self) -> Locator:
        """Return the Files entry in the left rail.

        Returns:
            Playwright locator. Tests call expect() on this.
        """
        return self.page.get_by_role(NAV_LINK_ROLE, name=FILES_NAV_NAME)

    @step(STEP_OPEN_FILES_NAV)
    def open_files(self) -> None:
        """Click Files so the browser returns to the live folder list."""
        self.files_link().click()
