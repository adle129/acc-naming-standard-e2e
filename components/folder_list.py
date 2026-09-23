"""Folder list: open a naming-standard folder by its visible name."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

# Live Files tree is a grid, not a list of links.
TREE_GRID_ROLE = "grid"
TREE_GRID_NAME = "tree-list"
FOLDER_ROLE = "gridcell"

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
        tree = self.page.get_by_role(TREE_GRID_ROLE, name=TREE_GRID_NAME)
        return tree.get_by_role(FOLDER_ROLE, name=name)

    def verify_folder_visible(self, name: str) -> None:
        """Prove a folder name is on screen. Tests call this instead of expect().

        Args:
            name: Visible folder name, for example ACC_FOLDER_NAME.
        """
        self.verify_visible(self.folder(name))

    @step(STEP_OPEN_FOLDER)
    def open_folder(self, name: str) -> None:
        """Click the folder so the Files list shows that folder's contents.

        Args:
            name: Visible folder name.
        """
        self.folder(name).click()
