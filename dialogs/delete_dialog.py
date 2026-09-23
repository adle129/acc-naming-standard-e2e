"""Delete confirmation dialog."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
DELETE_BUTTON_NAME = "Delete"
CANCEL_BUTTON_NAME = "Cancel"
EXACT_BUTTON_NAME = True
STEP_CONFIRM_DELETE = "click Delete in dialog"
STEP_CANCEL_DELETE = "click Cancel in delete dialog"


class DeleteDialog(BasePage):
    """Confirm delete after the action-bar Delete click."""

    def delete_button(self) -> Locator:
        """Return the Delete confirm control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(
            BUTTON_ROLE, name=DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def cancel_button(self) -> Locator:
        """Return Cancel so a smoke run can leave without deleting.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=CANCEL_BUTTON_NAME)

    def validate_delete_dialog(self) -> None:
        """Prove the delete confirmation is open."""
        self.verify_visible(self.delete_button())

    @step(STEP_CONFIRM_DELETE)
    def click_delete_button(self) -> None:
        """Click Delete in the confirmation dialog."""
        self.delete_button().click()

    @step(STEP_CANCEL_DELETE)
    def click_cancel_button(self) -> None:
        """Leave the delete confirmation without deleting."""
        self.cancel_button().click()
