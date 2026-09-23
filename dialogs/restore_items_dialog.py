"""Restore items dialog."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
CONTINUE_BUTTON_NAME = "Continue"
STEP_CONTINUE = "click Continue"


class RestoreItemsDialog(BasePage):
    """Second restore dialog with Continue."""

    def continue_button(self) -> Locator:
        """Return the Continue control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=CONTINUE_BUTTON_NAME)

    def validate_restore_items_dialog(self) -> None:
        """Prove the Restore items dialog is open."""
        self.verify_visible(self.continue_button())

    @step(STEP_CONTINUE)
    def click_continue_button(self) -> None:
        """Click Continue."""
        self.continue_button().click()
