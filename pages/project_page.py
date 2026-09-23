"""Project landing page after login, before the Files tool URL is opened."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from components.app_nav import FILES_NAV_NAME, AppNav
from pages.base_page import BasePage

WHAT_FILES_NAV = FILES_NAV_NAME


class ProjectPage(BasePage):
    """Project hub. Open the project, then jump to Files via the nav."""

    def __init__(self, page: Any, *, root: Path | None = None) -> None:
        """Attach the Playwright page and the left nav.

        Args:
            page: Playwright Page, or a test double.
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.app_nav = AppNav(page, root=root)

    def open_project(self, url: str) -> None:
        """Open a project landing URL.

        Args:
            url: Absolute project URL supplied by the caller.
        """
        self.navigate_to(url)

    def validate_project_page(self) -> None:
        """Prove the current page is the project hub (Files nav is present)."""
        self.verify_visible(self.app_nav.files_link(), WHAT_FILES_NAV)

    def click_files(self) -> None:
        """Click Files in the project nav."""
        self.app_nav.open_files()

    def open_files_tool(self) -> None:
        """Enter the Files tool from the project nav."""
        self.click_files()
