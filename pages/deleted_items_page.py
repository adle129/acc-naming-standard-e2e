"""Deleted items view (moduleId=deleted)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator

from components.app_nav import AppNav
from components.file_list import FileList
from components.file_row import FileRow
from components.file_toolbar import FileToolbar
from components.toast import Toast
from pages.base_page import BasePage

# Deleted by is unique to this view; the Files list does not show it.
DELETED_BY_COLUMN_NAME = "Deleted by"
DELETED_DATE_COLUMN_NAME = "Deleted date"
COLUMN_ROLE = "gridcell"
BUTTON_ROLE = "button"
FILTER_BUTTON_NAME = "Filter"

# Query flag that distinguishes Deleted items from the live Files list.
DELETED_VIEW_URL_HINT = "moduleId=deleted"
DELETED_VIEW_URL_PATTERN = re.compile(DELETED_VIEW_URL_HINT)
WHAT_DELETED_BY = DELETED_BY_COLUMN_NAME
WHAT_DELETED_FILE = "deleted file {name}"
WHAT_RESTORE_BUTTON = "Restore button"


class DeletedItemsPage(BasePage):
    """Deleted items list. Opened from the Files toolbar, not by a raw URL."""

    def __init__(self, page: Any, *, root: Path | None = None) -> None:
        """Attach the Playwright page and the shared list components.

        Args:
            page: Playwright Page, or a test double.
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.file_list = FileList(page, root=root)
        self.toolbar = FileToolbar(page, root=root)
        self.toast = Toast(page, root=root)
        self.app_nav = AppNav(page, root=root)

    def restore_button(self) -> Locator:
        """Return the Restore control (visible after a row is selected).

        Returns:
            Playwright locator.
        """
        return self.toolbar.restore_button()

    def files_link(self) -> Locator:
        """Return the Files nav link used to leave Deleted items.

        Returns:
            Playwright locator.
        """
        return self.app_nav.files_link()

    def heading(self) -> Locator:
        """Return the Deleted by column, the marker unique to this view.

        Returns:
            Playwright locator used by validate_deleted_items_page().
        """
        return self.deleted_by_column()

    def deleted_by_column(self) -> Locator:
        """Return the Deleted by column header on this view.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(COLUMN_ROLE, name=DELETED_BY_COLUMN_NAME)

    def deleted_date_column(self) -> Locator:
        """Return the Deleted date column header on this view.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(COLUMN_ROLE, name=DELETED_DATE_COLUMN_NAME)

    def filter_button(self) -> Locator:
        """Return Filter on the Deleted items action bar.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=FILTER_BUTTON_NAME)

    def validate_deleted_items_page(self) -> None:
        """Prove this is the Deleted items UI: deleted URL plus the heading."""
        self.verify_url(DELETED_VIEW_URL_PATTERN)
        self.verify_visible(self.heading(), WHAT_DELETED_BY)

    def verify_file_visible(self, name: str) -> None:
        """Prove a deleted file row is shown.

        Args:
            name: Visible file name.
        """
        self.verify_visible(self.row(name).name_cell(), WHAT_DELETED_FILE.format(name=name))

    def verify_file_hidden(self, name: str) -> None:
        """Prove a file row is gone after restore.

        Args:
            name: Visible file name.
        """
        self.verify_hidden(self.row(name).name_cell(), WHAT_DELETED_FILE.format(name=name))

    def verify_toast(self, text: str) -> None:
        """Prove a success toast is shown.

        Args:
            text: Toast constant from components.toast.
        """
        self.toast.verify(text)

    def row(self, name: str) -> FileRow:
        """Return the deleted-items row for one file name.

        Args:
            name: Visible file name.

        Returns:
            FileRow bound to that name.
        """
        return FileRow(self.page, name, root=self.root)

    def select_file(self, name: str) -> None:
        """Tick the deleted-items row. Tests call verify_file_selected() after this.

        Args:
            name: Visible file name.
        """
        self.row(name).select()

    def verify_file_selected(self) -> None:
        """Prove a Deleted-items row is selected (Restore is on the action bar)."""
        self.verify_visible(self.restore_button(), WHAT_RESTORE_BUTTON)

    def get_items_count(self) -> int:
        """Return how many files are in the Deleted items list.

        Returns:
            The number shown by Showing N items.
        """
        return self.file_list.get_items_count()

    def verify_items_count(self, expected: int) -> None:
        """Prove the Deleted items count matches this test's file only.

        Args:
            expected: Showing N items after delete or restore of this file.
        """
        self.file_list.verify_items_count(expected)

    def get_item_list(self) -> list[str]:
        """Return the file names in the Deleted items list.

        Returns:
            Visible file names in list order.
        """
        return self.file_list.get_item_list()

    def file_name_containing(self, token: str) -> str:
        """Return the Deleted-items name that contains token after delete.

        Args:
            token: Unique Project from the case row.

        Returns:
            Visible composed file name.
        """
        return self.file_list.name_containing(token)

    def click_restore_button(self) -> None:
        """Click Restore on the action bar."""
        self.toolbar.restore()

    def click_files(self) -> None:
        """Click Files in the nav to return to the live list."""
        self.app_nav.open_files()

    def return_to_files(self) -> None:
        """Go back to the live Files list."""
        self.click_files()
