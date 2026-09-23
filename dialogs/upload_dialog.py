"""Upload picker: Select files, then the OS file chooser."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

BUTTON_ROLE = "button"
BANNER_ROLE = "banner"
DIALOG_ROLE = "dialog"
IMAGE_ROLE = "img"
SELECT_FILES_BUTTON_NAME = "Select files"
UPLOAD_BANNER_NAME = "Upload"
DONE_BUTTON_NAME = "Done"
CLOSE_IMAGE_NAME = "x"
STEP_SELECT_FILES = "click Select files"
STEP_CLOSE_UPLOAD = "close Upload picker"


class UploadDialog(BasePage):
    """First upload dialog that opens the native file picker."""

    def validate_upload_dialog(self) -> None:
        """Prove the upload picker is open (Select files is visible)."""
        self.verify_visible(self.select_files_button())

    def heading(self) -> Locator:
        """Return the Upload banner on the picker dialog.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BANNER_ROLE, name=UPLOAD_BANNER_NAME, exact=True)

    def select_files_button(self) -> Locator:
        """Return the Select files control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=SELECT_FILES_BUTTON_NAME)

    def done_button(self) -> Locator:
        """Return Done on the picker (enabled after a finished upload).

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=DONE_BUTTON_NAME)

    def dialog(self) -> Locator:
        """Return the picker dialog (the one that has Select files).

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(DIALOG_ROLE).filter(has=self.select_files_button())

    def close_button(self) -> Locator:
        """Return the picker close control (the x image on this dialog).

        Returns:
            Playwright locator.
        """
        return self.dialog().get_by_role(IMAGE_ROLE, name=CLOSE_IMAGE_NAME)

    @step(STEP_SELECT_FILES)
    def click_select_files_button(self) -> None:
        """Click Select files."""
        self.select_files_button().click()

    @step(STEP_CLOSE_UPLOAD)
    def click_close(self) -> None:
        """Dismiss the picker after Cancel so Files actions are clickable."""
        self.close_button().click()

    def select_files(self, file_path: Path) -> None:
        """Click Select files and attach one local file.

        Args:
            file_path: File to upload, for example data/files/a.txt.
        """
        # expect_file_chooser covers the OS picker so we do not click OK ourselves.
        with self.page.expect_file_chooser() as chooser_info:
            self.click_select_files_button()
        chooser_info.value.set_files(str(file_path))
