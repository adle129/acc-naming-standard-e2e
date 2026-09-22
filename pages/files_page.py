"""Files tool: folder list and the files view (moduleId=folders)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from components.folder_list import FolderList
from pages.base_page import BasePage

# Query flag that distinguishes the live Files list from Deleted items.
FILES_VIEW_URL_HINT = "moduleId=folders"
FILES_VIEW_URL_PATTERN = re.compile(FILES_VIEW_URL_HINT)


class FilesPage(BasePage):
    """ACC Files tool. Toolbar, rows, and toast arrive in the next task."""

    def __init__(self, page: Any, *, root: Path | None = None) -> None:
        """Attach the Playwright page and the folder list component.

        Args:
            page: Playwright Page, or a test double.
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.folder_list = FolderList(page, root=root)

    def open_files(self, files_url: str) -> None:
        """Open the project's Files tool URL.

        Args:
            files_url: Absolute URL from Settings.files_url().
        """
        self.navigate_to(files_url)

    def verify_files_view(self) -> None:
        """Prove the browser is on the Files list, not Deleted items."""
        self.verify_url(FILES_VIEW_URL_PATTERN)
