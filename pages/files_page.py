"""Files tool: folder list, file list, toolbar, and toast."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from components.app_nav import AppNav
from components.file_list import FileList
from components.file_row import FileRow
from components.file_toolbar import FileToolbar
from components.folder_list import FolderList
from components.toast import Toast
from pages.base_page import BasePage

# Query flag that distinguishes the live Files list from Deleted items.
FILES_VIEW_URL_HINT = "moduleId=folders"
FILES_VIEW_URL_PATTERN = re.compile(FILES_VIEW_URL_HINT)
# Folders tab is visible on the Files list before a folder is opened.
TAB_ROLE = "tab"
FOLDERS_TAB_NAME = "Folders"


class FilesPage(BasePage):
    """ACC Files tool used by upload, delete, and the return from Deleted items."""

    def __init__(self, page: Any, *, root: Path | None = None) -> None:
        """Attach the Playwright page and the Files components.

        Args:
            page: Playwright Page, or a test double.
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.folder_list = FolderList(page, root=root)
        self.file_list = FileList(page, root=root)
        self.toolbar = FileToolbar(page, root=root)
        self.toast = Toast(page, root=root)
        self.app_nav = AppNav(page, root=root)

    def open_files(self, files_url: str) -> None:
        """Open the project's Files tool URL.

        Args:
            files_url: Absolute URL from Settings.files_url().
        """
        self.navigate_to(files_url)

    def folder(self, name: str) -> Any:
        """Return the folder cell in the left tree.

        Args:
            name: Visible folder name.

        Returns:
            Playwright locator.
        """
        return self.folder_list.folder(name)

    def upload_button(self) -> Any:
        """Return the Upload control on the Files action bar.

        Returns:
            Playwright locator.
        """
        return self.toolbar.upload_button()

    def deleted_items_button(self) -> Any:
        """Return the Deleted items control on the Files action bar.

        Returns:
            Playwright locator.
        """
        return self.toolbar.deleted_items_button()

    def delete_button(self) -> Any:
        """Return the Delete control on the Files action bar.

        Returns:
            Playwright locator.
        """
        return self.toolbar.delete_button()

    def folders_tab(self) -> Any:
        """Return the Folders tab that marks the Files list.

        Returns:
            Playwright locator for the Folders tab.
        """
        return self.page.get_by_role(TAB_ROLE, name=FOLDERS_TAB_NAME)

    def validate_files_page(self) -> None:
        """Prove this is the Files UI: folders URL plus the Folders tab."""
        self.verify_url(FILES_VIEW_URL_PATTERN)
        self.verify_visible(self.folders_tab())

    def verify_folder_visible(self, name: str) -> None:
        """Prove the named folder is shown. Shared by every Files test.

        Args:
            name: Visible folder name, for example ACC_FOLDER_NAME.
        """
        self.folder_list.verify_folder_visible(name)

    def verify_file_visible(self, name: str) -> None:
        """Prove a file row is shown after upload or restore.

        Args:
            name: Visible file name from expected_file_name().
        """
        self.verify_visible(self.row(name).name_cell())

    def verify_file_hidden(self, name: str) -> None:
        """Prove a file row is gone after delete.

        Args:
            name: Visible file name from expected_file_name().
        """
        self.verify_hidden(self.row(name).name_cell())

    def click_folder(self, name: str) -> None:
        """Open a folder and wait until its file list (and Upload) are ready.

        Args:
            name: Visible folder name, for example ACC_FOLDER_NAME.
        """
        self.folder_list.open_folder(name)
        # Upload is not on the project-root bar; it appears after this folder's files load.
        self.verify_visible(self.toolbar.upload_button())

    def click_upload_button(self) -> None:
        """Click Upload on the action bar."""
        self.toolbar.upload()

    def click_delete_button(self) -> None:
        """Click Delete on the action bar."""
        self.toolbar.delete()

    def click_deleted_items_button(self) -> None:
        """Click Deleted items on the action bar."""
        self.toolbar.open_deleted_items()

    def select_file(self, name: str) -> None:
        """Tick the row checkbox.

        Args:
            name: Visible file name.
        """
        self.row(name).select()

    def get_items_count(self) -> int:
        """Return how many files are in the current folder list.

        Returns:
            The number shown by Showing N items.
        """
        return self.file_list.get_items_count()

    def get_item_list(self) -> list[str]:
        """Return the file names in the current folder list.

        Returns:
            Visible file names in list order.
        """
        return self.file_list.get_item_list()

    def verify_toast(self, text: str) -> None:
        """Prove a success toast is shown.

        Args:
            text: Toast constant from components.toast.
        """
        self.toast.verify(text)

    def row(self, name: str) -> FileRow:
        """Return the files-list row for one file name.

        Args:
            name: Visible file name, usually from expected_file_name().

        Returns:
            FileRow bound to that name.
        """
        return FileRow(self.page, name, root=self.root)
