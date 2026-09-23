"""Restore confirmation dialog."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
DIALOG_ROLE = "dialog"
RESTORE_BUTTON_NAME = "Restore"
CANCEL_BUTTON_NAME = "Cancel"
EXACT_BUTTON_NAME = True
STEP_CONFIRM_RESTORE = "click Restore in dialog"
STEP_CANCEL_RESTORE = "click Cancel in restore dialog"


class RestoreConfirmDialog(BasePage):
    """First restore confirm after the action-bar Restore click."""

    def restore_button(self) -> Locator:
        """Return the Restore confirm control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).get_by_role(
            BUTTON_ROLE, name=RESTORE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def cancel_button(self) -> Locator:
        """Return Cancel so a smoke run can leave without restoring.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).get_by_role(
            BUTTON_ROLE, name=CANCEL_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def validate_restore_confirm_dialog(self) -> None:
        """Prove the first restore confirmation is open."""
        self.verify_visible(self.restore_button())

    @step(STEP_CONFIRM_RESTORE)
    def click_restore_button(self) -> None:
        """Click Restore in the confirmation dialog."""
        self.restore_button().click()

    @step(STEP_CANCEL_RESTORE)
    def click_cancel_button(self) -> None:
        """Leave the restore confirmation without restoring."""
        self.cancel_button().click()
