"""Upload progress dialog."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
DONE_BUTTON_NAME = "Done"
STEP_DONE = "click Done"


class UploadProgressDialog(BasePage):
    """Progress dialog after the validator Upload click."""

    def done_button(self) -> Locator:
        """Return the Done control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=DONE_BUTTON_NAME)

    def validate_upload_progress_dialog(self) -> None:
        """Prove the upload progress dialog is open."""
        self.verify_visible(self.done_button())

    @step(STEP_DONE)
    def click_done_button(self) -> None:
        """Click Done to return to the Files list."""
        self.done_button().click()
