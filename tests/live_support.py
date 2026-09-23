"""Function-level live ACC helpers. Session login stays in conftest."""

from __future__ import annotations

from typing import Any

from playwright.sync_api import expect

from dialogs.delete_dialog import DeleteDialog
from dialogs.restore_confirm_dialog import RestoreConfirmDialog
from dialogs.upload_dialog import UploadDialog
from pages.files_page import FilesPage
from pages.restore_files_page import RestoreFilesPage
from pages.upload_files_page import UploadFilesPage
from utils.config import Settings

# Overlay checks must not wait the full ACC timeout when nothing is open.
DISMISS_TIMEOUT_MS = 2000
# Playwright's expect() default; live tests must put this back after they finish.
DEFAULT_EXPECT_TIMEOUT_MS = 5000


def locator_is_visible(locator: Any, timeout_ms: int) -> bool:
    """Return whether a control is showing, without failing the test.

    Args:
        locator: Playwright locator, or a test double with is_visible().
        timeout_ms: How long to wait before treating it as hidden.

    Returns:
        True when the locator is visible.
    """
    return locator.is_visible(timeout=timeout_ms)


def dismiss_open_overlays(page: Any, timeout_ms: int = DISMISS_TIMEOUT_MS) -> None:
    """Close Upload / Restore / picker / confirm dialogs if they are on screen.

    Args:
        page: Playwright page, or a test double.
        timeout_ms: Per-control wait used when looking for an overlay.
    """
    upload_files = UploadFilesPage(page)
    if locator_is_visible(upload_files.cancel_button(), timeout_ms):
        upload_files.click_cancel_button()
    restore = RestoreFilesPage(page)
    if locator_is_visible(restore.cancel_button(), timeout_ms):
        restore.click_cancel_button()
    confirm = RestoreConfirmDialog(page)
    if locator_is_visible(confirm.cancel_button(), timeout_ms):
        confirm.click_cancel_button()
    delete = DeleteDialog(page)
    if locator_is_visible(delete.cancel_button(), timeout_ms):
        delete.click_cancel_button()
    upload = UploadDialog(page)
    if locator_is_visible(upload.select_files_button(), timeout_ms):
        upload.click_close()


class LiveAcc:
    """One live test: open the naming folder, then clean up this test's files."""

    def __init__(self, page: Any, settings: Settings) -> None:
        """Bind the function-scoped page and the shared ACC settings.

        Args:
            page: Playwright page from pytest-playwright (new context per test).
            settings: Resolved .env settings for URL, folder, and timeouts.
        """
        self.page = page
        self.settings = settings
        self.files = FilesPage(page)
        self.uploaded_names: list[str] = []

    def remember_upload(self, name: str) -> None:
        """Record a Files-list name this test created, so cleanup can delete it.

        Args:
            name: Visible composed name after upload.
        """
        self.uploaded_names.append(name)

    def prepare(self) -> None:
        """Open the naming-standard folder and apply the ACC timeout."""
        self.page.set_default_timeout(self.settings.timeout_ms)
        expect.set_options(timeout=self.settings.timeout_ms)
        self.files.open_files(self.settings.files_url())
        self.files.validate_files_page()
        self.files.verify_folder_visible(self.settings.folder_name)
        self.files.click_folder(self.settings.folder_name)
        dismiss_open_overlays(self.page)

    def cleanup(self) -> None:
        """Dismiss overlays, delete this test's uploads, restore expect timeout."""
        try:
            dismiss_open_overlays(self.page)
            self._delete_remembered_uploads()
        finally:
            expect.set_options(timeout=DEFAULT_EXPECT_TIMEOUT_MS)

    def _delete_remembered_uploads(self) -> None:
        """Delete Files-list rows this test uploaded, if they are still there."""
        if not self.uploaded_names:
            return
        self.files.open_files(self.settings.files_url())
        self.files.validate_files_page()
        self.files.click_folder(self.settings.folder_name)
        for name in self.uploaded_names:
            listed = self.files.get_item_list()
            if name not in listed:
                continue
            self.files.select_file(name)
            self.files.click_delete_button()
            DeleteDialog(self.page).click_delete_button()
