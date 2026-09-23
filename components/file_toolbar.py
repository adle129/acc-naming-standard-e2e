"""Top action bar: Upload, Delete, Restore, Deleted items."""

from __future__ import annotations

import re

from playwright.sync_api import Locator

from pages.base_page import BasePage
from utils.logger import step

# Accessible names from the English product UI.
BUTTON_ROLE = "button"
UPLOAD_BUTTON_NAME = "Upload"
DELETE_BUTTON_NAME = "Delete"
RESTORE_BUTTON_NAME = "Restore"
# After a row is ticked the product shows Restore (1), same as Edit (1).
RESTORE_BUTTON_PATTERN = re.compile(r"^Restore( \(\d+\))?$")
DELETED_ITEMS_BUTTON_NAME = "Deleted items"
# Delete is a prefix of Deleted items; require an exact accessible name.
EXACT_BUTTON_NAME = True

STEP_UPLOAD = "click Upload"
STEP_DELETE = "click Delete"
STEP_RESTORE = "click Restore"
STEP_DELETED_ITEMS = "click Deleted items"


class FileToolbar(BasePage):
    """Files / Deleted items action bar. Restore is shown only after a row is selected."""

    def upload_button(self) -> Locator:
        """Return the Upload control.

        Returns:
            Playwright locator. Tests call expect() on this.
        """
        return self.page.get_by_role(
            BUTTON_ROLE, name=UPLOAD_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def delete_button(self) -> Locator:
        """Return the contextual Delete control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(
            BUTTON_ROLE, name=DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def restore_button(self) -> Locator:
        """Return the contextual Restore control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=RESTORE_BUTTON_PATTERN)

    def deleted_items_button(self) -> Locator:
        """Return the Deleted items control.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(BUTTON_ROLE, name=DELETED_ITEMS_BUTTON_NAME)

    @step(STEP_UPLOAD)
    def upload(self) -> None:
        """Open the upload picker from the action bar."""
        self.upload_button().click()

    @step(STEP_DELETE)
    def delete(self) -> None:
        """Open the delete confirmation from the action bar."""
        self.delete_button().click()

    @step(STEP_RESTORE)
    def restore(self) -> None:
        """Open the restore confirmation from the action bar."""
        self.restore_button().click()

    @step(STEP_DELETED_ITEMS)
    def open_deleted_items(self) -> None:
        """Switch to the Deleted items view."""
        self.deleted_items_button().click()
