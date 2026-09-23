"""Shared File Validator chrome. Field get/set live on ValidatorItem."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, expect

from components.validator_item import ValidatorItem
from dialogs.upload_dialog import CLOSE_IMAGE_NAME, IMAGE_ROLE
from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
DIALOG_ROLE = "dialog"
TABLE_ROLE = "table"
ROW_ROLE = "row"
GRIDCELL_ROLE = "gridcell"
CHECKBOX_ROLE = "checkbox"
SWITCH_ROLE = "switch"
FILE_NAME_HEADER = "File name"
EMPTY_CELL = ""

UPLOAD_BUTTON_NAME = "Upload"
RESTORE_BUTTON_NAME = "Restore"
CANCEL_BUTTON_NAME = "Cancel"
# After a row is ticked the product switches Edit all / Remove all to Edit (1).
EDIT_ALL_BUTTON_NAME = re.compile(r"^Edit( all| \(\d+\))$")
REMOVE_ALL_BUTTON_NAME = re.compile(r"^Remove( all| \(\d+\))$")
ERRORS_ONLY_CHECKBOX_NAME = "Only show files with errors"
PREVIOUS_VERSION_LABEL = "Show attribute values from previous version"
ERROR_BANNER_HINT = "doesn't comply"
# Live restore banners name the delimiter as "special characters".
SPECIAL_CHARACTERS_HINT = "special characters"
WHAT_ERROR_TEXT = "error text {text}"
WHAT_ERROR_BANNER = "delimiter error banner"
WHAT_SPECIAL_CHARACTERS = SPECIAL_CHARACTERS_HINT
WHAT_EDIT_ALL = "Edit all"
WHAT_REMOVE_ALL = "Remove all"
WHAT_ADD_FILES = "Add files"
WHAT_ERRORS_ONLY = ERRORS_ONLY_CHECKBOX_NAME
WHAT_PREVIOUS_VERSION_LABEL = PREVIOUS_VERSION_LABEL
WHAT_PREVIOUS_VERSION_SWITCH = "previous-version switch"
WHAT_CLOSE_VALIDATOR = "validator close"
WHAT_CANCEL_VALIDATOR = CANCEL_BUTTON_NAME
WHAT_UPLOAD_BUTTON = UPLOAD_BUTTON_NAME

STEP_VALIDATOR_UPLOAD = "click Upload button"
STEP_VALIDATOR_RESTORE = "click Restore button"
STEP_CANCEL_VALIDATOR = "click Cancel button"
STEP_EDIT_ALL = "click Edit all"
STEP_REMOVE_ALL = "click Remove all"
STEP_CLOSE_VALIDATOR = "close validator"
STEP_CHECK_ERRORS_ONLY = "check Only show files with errors"
STEP_UNCHECK_ERRORS_ONLY = "uncheck Only show files with errors"


class ValidatorDialog(BasePage):
    """Upload and restore validators share the file table and chrome."""

    def heading(self) -> Locator:
        """Return the validator title. UploadFilesPage / RestoreFilesPage set the text.

        Returns:
            Playwright locator.
        """
        raise NotImplementedError

    def dialog(self) -> Locator:
        """Return this validator overlay, not the picker or confirm dialogs.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).filter(has=self.heading())

    def edit_all_button(self) -> Locator:
        """Return Edit all on the attribute table.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=EDIT_ALL_BUTTON_NAME)

    def remove_all_button(self) -> Locator:
        """Return Remove all on the file list.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=REMOVE_ALL_BUTTON_NAME)

    def errors_only_checkbox(self) -> Locator:
        """Return the Only show files with errors filter.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(CHECKBOX_ROLE, name=ERRORS_ONLY_CHECKBOX_NAME)

    def close_button(self) -> Locator:
        """Return the x control on this validator overlay.

        Returns:
            Playwright locator.
        """
        return self.dialog().get_by_role(IMAGE_ROLE, name=CLOSE_IMAGE_NAME)

    def previous_version_label(self) -> Locator:
        """Return the Show attribute values from previous version text.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(PREVIOUS_VERSION_LABEL, exact=True)

    def previous_version_switch(self) -> Locator:
        """Return Show attribute values from previous version.

        Returns:
            Playwright locator for the one switch on this overlay.
        """
        return self.dialog().get_by_role(SWITCH_ROLE)

    def error_banner(self) -> Locator:
        """Return the compliance-error banner above the file list.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(ERROR_BANNER_HINT)

    def error_text(self, text: str) -> Locator:
        """Return the exact validator error string from the rules file.

        Args:
            text: Exact UI error, for example naming_rules delimiter_error_text.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(text, exact=True)

    def verify_error_text(self, text: str) -> None:
        """Prove the exact validator error is shown.

        Args:
            text: Exact UI error, for example naming_rules delimiter_error_text.
        """
        self.verify_visible(self.error_text(text), WHAT_ERROR_TEXT.format(text=text))

    def verify_error_text_hidden(self, text: str) -> None:
        """Prove the exact validator error is gone.

        Args:
            text: Exact UI error, for example naming_rules delimiter_error_text.
        """
        self.verify_hidden(self.error_text(text), WHAT_ERROR_TEXT.format(text=text))

    def verify_delimiter_error_visible(self) -> None:
        """Prove the restore banner reports a special-character / delimiter error."""
        self.verify_visible(self.error_banner(), WHAT_ERROR_BANNER)
        self.verify_visible(
            self.page.get_by_text(SPECIAL_CHARACTERS_HINT),
            WHAT_SPECIAL_CHARACTERS,
        )

    def verify_delimiter_error_hidden(self) -> None:
        """Prove the compliance banner is gone after the delimiter is removed."""
        self.verify_hidden(self.error_banner(), WHAT_ERROR_BANNER)

    def item(self, name: str) -> ValidatorItem:
        """Return the table row for one listed file.

        Args:
            name: Local file name, for example a.txt.

        Returns:
            ValidatorItem bound to that row.
        """
        return ValidatorItem(self.page, name, root=self.root)

    def get_items_count(self) -> int:
        """Return how many files are listed on the validator table.

        Returns:
            Visible data-row count, not the header row.
        """
        return self._item_rows().count()

    def get_item_list(self) -> list[str]:
        """Return the local file names listed on the validator table.

        Returns:
            Local names (for example a.txt) in list order, for item(name).
        """
        rows = self._item_rows()
        names = []
        total = rows.count()
        for index in range(total):
            names.append(self._local_file_name_from_row(rows.nth(index)))
        return names

    def _file_name_table(self) -> Locator:
        """Return the table that has the File name column header.

        Returns:
            Playwright locator for that table.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=FILE_NAME_HEADER, exact=True)
        return self.page.get_by_role(TABLE_ROLE).filter(has=header)

    def _item_rows(self) -> Locator:
        """Return data rows in the File name table, not the header row.

        Returns:
            Playwright locator for those rows.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=FILE_NAME_HEADER, exact=True)
        return self._file_name_table().get_by_role(ROW_ROLE).filter(has_not=header)

    def _local_file_name_from_row(self, row: Locator) -> str:
        """Read the local file name from the first non-empty cell in a row.

        Args:
            row: One File-name data row.

        Returns:
            The last line of that cell (the original local name).
        """
        cells = row.get_by_role(GRIDCELL_ROLE)
        total = cells.count()
        for index in range(total):
            text = cells.nth(index).inner_text().strip()
            if text == EMPTY_CELL:
                continue
            # First line is the composed preview; the last line is a.txt.
            lines = text.splitlines()
            return lines[-1].strip()
        return EMPTY_CELL

    def upload_button(self) -> Locator:
        """Return Upload on the validator footer, not the Files toolbar.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).get_by_role(BUTTON_ROLE, name=UPLOAD_BUTTON_NAME)

    def restore_button(self) -> Locator:
        """Return Restore on the validator footer, not the Deleted items toolbar.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).get_by_role(BUTTON_ROLE, name=RESTORE_BUTTON_NAME)

    def cancel_button(self) -> Locator:
        """Return Cancel so a run can leave without uploading or restoring.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).get_by_role(BUTTON_ROLE, name=CANCEL_BUTTON_NAME)

    @step(STEP_EDIT_ALL)
    def click_edit_all_button(self) -> None:
        """Click Edit all (or Edit (N) when rows are selected)."""
        self.edit_all_button().click()

    @step(STEP_REMOVE_ALL)
    def click_remove_all_button(self) -> None:
        """Click Remove all (or Remove (N) when rows are selected)."""
        self.remove_all_button().click()

    @step(STEP_CLOSE_VALIDATOR)
    def click_close_button(self) -> None:
        """Click x on the validator overlay."""
        self.close_button().click()

    @step(STEP_CHECK_ERRORS_ONLY)
    def check_errors_only(self) -> None:
        """Tick Only show files with errors."""
        self.errors_only_checkbox().check()

    @step(STEP_UNCHECK_ERRORS_ONLY)
    def uncheck_errors_only(self) -> None:
        """Clear Only show files with errors."""
        self.errors_only_checkbox().uncheck()

    def verify_errors_only_checked(self) -> None:
        """Prove Only show files with errors is ticked."""
        expect(self.errors_only_checkbox()).to_be_checked()

    def verify_errors_only_unchecked(self) -> None:
        """Prove Only show files with errors is cleared."""
        expect(self.errors_only_checkbox()).not_to_be_checked()

    @step(STEP_VALIDATOR_UPLOAD)
    def click_upload_button(self) -> None:
        """Click Upload on the File Validator."""
        self.upload_button().click()

    @step(STEP_VALIDATOR_RESTORE)
    def click_restore_button(self) -> None:
        """Click Restore on the File Validator."""
        self.restore_button().click()

    @step(STEP_CANCEL_VALIDATOR)
    def click_cancel_button(self) -> None:
        """Leave the validator without uploading or restoring."""
        self.cancel_button().click()
