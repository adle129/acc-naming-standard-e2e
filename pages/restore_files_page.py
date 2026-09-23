"""Restore files page: file rows and footer actions on the Deleted items URL."""

from __future__ import annotations

from playwright.sync_api import Locator

from dialogs.validator_dialog import (
    BUTTON_ROLE,
    STEP_CANCEL_VALIDATOR,
    STEP_VALIDATOR_RESTORE,
    ValidatorDialog,
)
from pages.deleted_items_page import DELETED_VIEW_URL_PATTERN
from utils.logger import step

# Live ACC does not paint "Restore files"; this subtitle is unique to the overlay.
RESTORE_FILES_HEADING = "awaiting validation before it is restored"
FILE_NAME_EXACT = False
ACCEPT_BUTTON_NAME = "Accept"
STEP_ACCEPT_PREVIOUS = "accept previous-version values"


class RestoreFilesPage(ValidatorDialog):
    """Restore files screen opened from Deleted items after Continue.

    Shared chrome lives on ValidatorDialog. Accept is restore-only.
    Per-file get/set live on ValidatorItem from item(name).
    """

    def heading(self) -> Locator:
        """Return the Restore files title text.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(RESTORE_FILES_HEADING)

    def file_name(self, name: str) -> Locator:
        """Return the listed file name on the restore table.

        Args:
            name: Visible or local file name.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_text(name, exact=FILE_NAME_EXACT)

    def accept_buttons(self) -> Locator:
        """Return Accept controls on previous-version (yellow) values.

        Returns:
            Playwright locator; may match more than one button.
        """
        return self.dialog().get_by_role(BUTTON_ROLE, name=ACCEPT_BUTTON_NAME)

    def validate_restore_files_page(self) -> None:
        """Prove Restore files is open on the Deleted items URL."""
        self.verify_url(DELETED_VIEW_URL_PATTERN)
        self.verify_visible(self.heading())

    def get_items_count(self) -> int:
        """Return how many files are awaiting restore.

        Returns:
            Visible data-row count on the File name table.
        """
        return super().get_items_count()

    def get_item_list(self) -> list[str]:
        """Return the local file names awaiting restore.

        Returns:
            Local names in list order, for example a.txt.
        """
        return super().get_item_list()

    def verify_file_visible(self, name: str) -> None:
        """Prove the file is listed as awaiting restore.

        Args:
            name: Visible or local file name.
        """
        self.verify_visible(self.file_name(name))

    def select_item(self, name: str) -> None:
        """Tick the file-row checkbox.

        Args:
            name: Visible or local file name.
        """
        self.item(name).select()

    def verify_item_selected(self, name: str) -> None:
        """Prove the file-row checkbox is checked.

        Args:
            name: Visible or local file name.
        """
        self.item(name).verify_selected()

    @step(STEP_ACCEPT_PREVIOUS)
    def accept_previous_version(self) -> None:
        """Click each visible Accept on previous-version values.

        No-op when the product did not show Accept.
        """
        buttons = self.accept_buttons()
        total = buttons.count()
        for index in range(total):
            buttons.nth(index).click()

    @step(STEP_VALIDATOR_RESTORE)
    def click_restore_button(self) -> None:
        """Click Restore on the Restore files page."""
        self.restore_button().click()

    @step(STEP_CANCEL_VALIDATOR)
    def click_cancel_button(self) -> None:
        """Click Cancel on the Restore files page."""
        self.cancel_button().click()
