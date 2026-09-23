"""One file row: checkbox and visible name."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError

from components.file_list import FileList, GRIDCELL_ROLE, NAME_HEADER, TABLE_ROLE
from pages.base_page import BasePage
from utils.logger import step

# Table row + checkbox. First live run may change only these roles.
FILE_ROW_ROLE = "row"
CHECKBOX_ROLE = "checkbox"
# In-row checkbox is missing on Deleted items; fail fast and use the split column.
SPLIT_CHECKBOX_TIMEOUT_MS = 3000

STEP_SELECT_FILE = "select file"


class FileRow(BasePage):
    """One files-list or deleted-items row, found by the visible file name."""

    def __init__(self, page: Any, name: str, *, root: Path | None = None) -> None:
        """Bind the Playwright page and the file name used to find the row.

        Args:
            page: Playwright Page, or a test double.
            name: Visible file name, usually expected_file_name(preview, ext).
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.name = name

    def row(self) -> Locator:
        """Return the row that shows this file name.

        Returns:
            Playwright locator for the whole row.
        """
        return self.page.get_by_role(FILE_ROW_ROLE, name=self.name)

    def checkbox(self) -> Locator:
        """Return the row checkbox used by the toolbar path.

        Returns:
            Playwright locator. Scoped to the row, not the page.
        """
        return self.row().get_by_role(CHECKBOX_ROLE)

    def name_cell(self) -> Locator:
        """Return the name cell so tests can expect the file to appear or disappear.

        Returns:
            Playwright locator for the visible file name.
        """
        return self.row()

    def _split_checkbox(self) -> Locator:
        """Return the Deleted-items checkbox that lines up with this file name.

        Returns:
            Playwright locator for that checkbox in the split column.
        """
        names = FileList(self.page, root=self.root).get_item_list()
        index = names.index(self.name)
        name_header = self.page.get_by_role(GRIDCELL_ROLE, name=NAME_HEADER, exact=True)
        # The checkbox column is its own table; the Name table has no boxes.
        table = self.page.get_by_role(TABLE_ROLE).filter(
            has=self.page.get_by_role(CHECKBOX_ROLE)
        ).filter(has_not=name_header)
        return table.get_by_role(CHECKBOX_ROLE).nth(index)

    @step(STEP_SELECT_FILE)
    def select(self) -> None:
        """Tick the row checkbox so Delete or Restore appears on the toolbar."""
        try:
            self.checkbox().click(timeout=SPLIT_CHECKBOX_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # Deleted items keeps checkboxes in a separate table from the Name column.
            self._split_checkbox().click()
