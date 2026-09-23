"""Top action bar: Upload, Delete, Restore, Deleted items."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, expect

from pages.base_page import BasePage
from utils.logger import step

# Accessible names from the English product UI.
BUTTON_ROLE = "button"
UPLOAD_BUTTON_NAME = "Upload"
MOVE_BUTTON_NAME = "Move"
DELETE_BUTTON_NAME = "Delete"
RESTORE_BUTTON_NAME = "Restore"
# After a row is ticked the product shows Restore (1), same as Edit (1).
RESTORE_BUTTON_PATTERN = re.compile(r"^Restore( \(\d+\))?$")
DELETED_ITEMS_BUTTON_NAME = "Deleted items"
LISTITEM_ROLE = "listitem"
MENUITEM_ROLE = "menuitem"
# Delete is a prefix of Deleted items; require an exact accessible name.
EXACT_BUTTON_NAME = True

# After a row is selected, ACC accepts the keyboard Delete key.
DELETE_KEY = "Delete"
ESCAPE_KEY = "Escape"
# Confirm can take a moment after the key press.
DELETE_CONFIRM_WAIT_MS = 3000
# Move's next sibling is the unnamed overflow that holds Copy / Delete.
MOVE_OVERFLOW_XPATH = "xpath=following-sibling::button[1]"

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

    def move_button(self) -> Locator:
        """Return Move, which appears after a Files-list row is selected.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(
            BUTTON_ROLE, name=MOVE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def more_button(self) -> Locator:
        """Return the unnamed overflow immediately after Move.

        Returns:
            Playwright locator.
        """
        # This icon has no accessible name; Move is the stable neighbor.
        return self.move_button().locator(MOVE_OVERFLOW_XPATH)

    def delete_button(self) -> Locator:
        """Return Delete on the action bar when the product paints a named button.

        Returns:
            Playwright locator.
        """
        return self.page.get_by_role(
            BUTTON_ROLE, name=DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )

    def delete_menu_item(self) -> Locator:
        """Return Delete in the overflow menu opened from moreVertical.

        Returns:
            Playwright locator.
        """
        listed = self.page.get_by_role(
            LISTITEM_ROLE, name=DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )
        menu = self.page.get_by_role(
            MENUITEM_ROLE, name=DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME
        )
        return listed.or_(menu)

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
        """Open the delete confirmation for the selected file."""
        # A leftover upload summary or drawer steals the Delete key.
        self.page.keyboard.press(ESCAPE_KEY)
        self.page.keyboard.press(DELETE_KEY)
        # Confirm uses a Delete button too; stop here so the dialog can click it.
        if self.delete_button().is_visible(timeout=DELETE_CONFIRM_WAIT_MS):
            return
        self.more_button().click()
        item = self.delete_menu_item()
        if item.is_visible(timeout=DELETE_CONFIRM_WAIT_MS):
            item.click()
            return
        labeled = self.page.get_by_text(DELETE_BUTTON_NAME, exact=EXACT_BUTTON_NAME)
        expect(labeled).to_be_visible()
        labeled.click()

    @step(STEP_RESTORE)
    def restore(self) -> None:
        """Open the restore confirmation from the action bar."""
        self.restore_button().click()

    @step(STEP_DELETED_ITEMS)
    def open_deleted_items(self) -> None:
        """Switch to the Deleted items view."""
        self.deleted_items_button().click()
