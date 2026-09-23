"""Upload progress dialog."""

from __future__ import annotations

from playwright.sync_api import Locator, expect

from components.toast import TOAST_UPLOADED
from dialogs.upload_dialog import CLOSE_IMAGE_NAME, IMAGE_ROLE
from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
DONE_BUTTON_NAME = "Done"
UPLOAD_SUMMARY_TEXT = "Total 1 file."
ICON_BUTTON_TEST_ID = "icon-button"
STEP_DONE = "click Done"
WHAT_DONE = DONE_BUTTON_NAME


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
        self.verify_visible(self.done_button(), WHAT_DONE)

    @step(STEP_DONE)
    def click_done_button(self) -> None:
        """Click Done so the Files list is usable again."""
        self.done_button().click()
        expect(self.done_button()).to_be_hidden()
        # The toast intercepts the summary X until it disappears.
        expect(self.page.get_by_text(TOAST_UPLOADED)).to_be_hidden()
        summary = self.page.get_by_text(UPLOAD_SUMMARY_TEXT)
        if summary.is_visible():
            # icon-button is the summary X; drawer-close-btn is a different control.
            closer = self.page.get_by_test_id(ICON_BUTTON_TEST_ID).filter(
                has=self.page.get_by_role(IMAGE_ROLE, name=CLOSE_IMAGE_NAME)
            )
            closer.first.click()
            expect(summary).to_be_hidden()
