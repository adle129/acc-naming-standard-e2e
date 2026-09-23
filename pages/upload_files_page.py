"""Upload files page: file rows and footer actions on the Files folder URL."""

from __future__ import annotations

from playwright.sync_api import Locator

from dialogs.validator_dialog import (
    STEP_CANCEL_VALIDATOR,
    STEP_VALIDATOR_UPLOAD,
    ValidatorDialog,
)
from pages.files_page import FILES_VIEW_URL_PATTERN
from utils.logger import step

# Live ACC paints "Upload files" as banner text, not a heading role name.
UPLOAD_FILES_HEADING = "Upload files"
# The listed name includes the composed preview, so match a.txt as a substring.
FILE_NAME_EXACT = False
ADD_FILES_BUTTON_NAME = "Add files"
STEP_ADD_FILES = "click Add files"
WHAT_UPLOAD_FILES_HEADING = UPLOAD_FILES_HEADING
WHAT_AWAITING_FILE = "awaiting file {name}"


class UploadFilesPage(ValidatorDialog):
    """Upload files screen opened from the Files folder URL after Select files.

    Shared chrome lives on ValidatorDialog. Add files is upload-only.
    Per-file get/set live on ValidatorItem from item(name).
    """

    def heading(self) -> Locator:
        """Return the Upload files title text.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(UPLOAD_FILES_HEADING, exact=True)

    def file_name(self, name: str) -> Locator:
        """Return the awaiting file name on the list.

        Args:
            name: Local file name, for example a.txt.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(name, exact=FILE_NAME_EXACT)

    def add_files_button(self) -> Locator:
        """Return Add files on the footer (text, not a button role).

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(ADD_FILES_BUTTON_NAME, exact=True)

    def validate_upload_files_page(self) -> None:
        """Prove Upload files is open on the Files folder URL."""
        self.verify_url(FILES_VIEW_URL_PATTERN)
        self.verify_visible(self.heading(), WHAT_UPLOAD_FILES_HEADING)

    def validate_upload_validator(self) -> None:
        """Same as validate_upload_files_page(); kept for existing tests."""
        self.validate_upload_files_page()

    def get_items_count(self) -> int:
        """Return how many files are awaiting upload.

        Returns:
            Visible data-row count on the File name table.
        """
        return super().get_items_count()

    def get_item_list(self) -> list[str]:
        """Return the local file names awaiting upload.

        Returns:
            Local names in list order, for example a.txt.
        """
        return super().get_item_list()

    def verify_file_visible(self, name: str) -> None:
        """Prove the selected file is listed as awaiting upload.

        Args:
            name: Local file name, for example a.txt.
        """
        self.verify_visible(self.file_name(name), WHAT_AWAITING_FILE.format(name=name))

    def item_row(self, name: str) -> Locator:
        """Return the list row that contains this file name.

        Args:
            name: Local file name, for example a.txt.

        Returns:
            Playwright locator for that row.
        """
        return self.item(name).row()

    def item_checkbox(self, name: str) -> Locator:
        """Return the checkbox on that file row.

        Args:
            name: Local file name, for example a.txt.

        Returns:
            Playwright locator scoped to the row, not the errors-only filter.
        """
        return self.item(name).checkbox()

    def select_item(self, name: str) -> None:
        """Tick the file-row checkbox so that item becomes the active row.

        Args:
            name: Local file name, for example a.txt.
        """
        self.item(name).select()

    def verify_item_selected(self, name: str) -> None:
        """Prove the file-row checkbox is checked.

        Args:
            name: Local file name, for example a.txt.
        """
        self.item(name).verify_selected()

    @step(STEP_ADD_FILES)
    def click_add_files_button(self) -> None:
        """Click Add files on the footer."""
        self.add_files_button().click()

    @step(STEP_VALIDATOR_UPLOAD)
    def click_upload_button(self) -> None:
        """Click Upload on the Upload files page."""
        self.upload_button().click()

    @step(STEP_CANCEL_VALIDATOR)
    def click_cancel_button(self) -> None:
        """Click Cancel on the Upload files page."""
        self.cancel_button().click()


