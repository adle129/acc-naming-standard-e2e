"""Folder list: open a naming-standard folder by its visible name."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

# Accessible role for a folder name in the Files tree. First live run may change only this.
FOLDER_ROLE = "link"

# Step text. Tests import this so they do not copy action wording.
STEP_OPEN_FOLDER = "open folder {name}"


class FolderList(BasePage):
    """Left-hand folder list used to enter the enforced folder."""

    def folder(self, name: str) -> Locator:
        """Return the locator for one folder row.

        Args:
            name: Visible folder name, for example the configured ACC_FOLDER_NAME.

        Returns:
            Playwright locator. Tests call expect() on this; this method does not.
        """
        return self.page.get_by_role(FOLDER_ROLE, name=name)

    @step(STEP_OPEN_FOLDER)
    def open_folder(self, name: str) -> None:
        """Click the folder so the Files list shows that folder's contents.

        Args:
            name: Visible folder name.
        """
        self.folder(name).click()
