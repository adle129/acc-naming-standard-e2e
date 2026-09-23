"""File names and counts on the Files list and Deleted items list."""

from __future__ import annotations

import re

from playwright.sync_api import Locator

from pages.base_page import BasePage

TABLE_ROLE = "table"
ROW_ROLE = "row"
GRIDCELL_ROLE = "gridcell"
NAME_HEADER = "Name"
SHOWING_ITEMS_PREFIX = "Showing "
SHOWING_ITEMS_PATTERN = re.compile(r"Showing (\d+) items?")
COUNT_GROUP = 1
EMPTY_CELL = ""


class FileList(BasePage):
    """The file-name column shared by Files and Deleted items."""

    def showing_label(self) -> Locator:
        """Return the Showing N items label above the list.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(SHOWING_ITEMS_PREFIX)

    def get_items_count(self) -> int:
        """Return how many files the current list reports.

        Returns:
            The number from Showing N items, or 0 when that label is missing.
        """
        text = self.showing_label().inner_text()
        match = SHOWING_ITEMS_PATTERN.search(text)
        if match is None:
            return 0
        return int(match.group(COUNT_GROUP))

    def get_item_list(self) -> list[str]:
        """Return the visible file names in list order.

        Returns:
            File names from the Name column, one string per row.
        """
        rows = self._item_rows()
        names = []
        total = rows.count()
        for index in range(total):
            names.append(self._file_name_from_row(rows.nth(index)))
        return names

    def _name_table(self) -> Locator:
        """Return the table that has the Name column header.

        Returns:
            Playwright locator for that table.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=NAME_HEADER, exact=True)
        return self.page.get_by_role(TABLE_ROLE).filter(has=header)

    def _item_rows(self) -> Locator:
        """Return data rows in the Name table, not the header row.

        Returns:
            Playwright locator for those rows.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=NAME_HEADER, exact=True)
        return self._name_table().get_by_role(ROW_ROLE).filter(has_not=header)

    def _file_name_from_row(self, row: Locator) -> str:
        """Read the file name from the first non-empty cell in a row.

        Args:
            row: One Name-column data row.

        Returns:
            Visible file name.
        """
        cells = row.get_by_role(GRIDCELL_ROLE)
        total = cells.count()
        for index in range(total):
            text = cells.nth(index).inner_text().strip()
            if text != EMPTY_CELL:
                # A name cell can include a second line (original name on Deleted items).
                lines = text.splitlines()
                return lines[0].strip()
        return EMPTY_CELL
