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
from utils.test_data import naming_rules

# Overlay checks must not wait the full ACC timeout when nothing is open.
DISMISS_TIMEOUT_MS = 2000
# Playwright's expect() default; live tests must put this back after they finish.
DEFAULT_EXPECT_TIMEOUT_MS = 5000
# Generated uploads look like AB12-XXX-ZZ-ZZ-CA-D-3402.txt (unique Project + case row).
GENERATED_NAME_MARKER = "-XXX-ZZ-ZZ-CA-D-"
GENERATED_PROJECT_LENGTH = 4
GENERATED_NAME_SUFFIX = ".txt"
# Leftover deletes must not sit on the full ACC timeout per file.
CLEANUP_TIMEOUT_MS = 10000


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
    """One live test: open the naming folder, then clean this test's Files rows.

    Delete only moves a file to Deleted items. This account cannot purge that
    view, so cleanup never opens Deleted items or tries a permanent delete.
    """

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
        self.uploaded_projects: list[str] = []

    def remember_project(self, project: str) -> None:
        """Record the unique Project so cleanup can find the composed name.

        Args:
            project: NamingAttributes.project from this test's case row.
        """
        if project not in self.uploaded_projects:
            self.uploaded_projects.append(project)

    def remember_upload(self, name: str) -> None:
        """Record a Files-list name this test created, so cleanup can delete it.

        Args:
            name: Visible composed name after upload.
        """
        if name not in self.uploaded_names:
            self.uploaded_names.append(name)

    def prepare(self) -> None:
        """Open the naming-standard folder and apply the ACC timeout."""
        self.page.set_default_timeout(self.settings.timeout_ms)
        expect.set_options(timeout=self.settings.timeout_ms)
        self.files.open_files(self.settings.files_url())
        self.files.validate_files_page()
        self.files.verify_folder_visible(self.settings.folder_name)
        self.files.click_folder(self.settings.folder_name)
        self.files.verify_folder_opened()
        dismiss_open_overlays(self.page)
        # Previous failed runs leave unique-Project files in this shared folder.
        self._delete_generated_leftovers()

    def cleanup(self) -> None:
        """Move this test's leftover Files-list rows to Deleted items."""
        try:
            dismiss_open_overlays(self.page)
            self._delete_remembered_uploads()
        finally:
            expect.set_options(timeout=DEFAULT_EXPECT_TIMEOUT_MS)

    def _delete_remembered_uploads(self) -> None:
        """Delete Files-list rows this test created, plus leftover generated names."""
        if not self.uploaded_names and not self.uploaded_projects:
            return
        self.files.open_files(self.settings.files_url())
        self.files.validate_files_page()
        self.files.click_folder(self.settings.folder_name)
        self.files.verify_folder_opened()
        dismiss_open_overlays(self.page)
        listed = self.files.get_item_list()
        to_delete = []
        for name in listed:
            if self._should_delete_name(name):
                to_delete.append(name)
        self._delete_names(to_delete)

    def _delete_generated_leftovers(self) -> None:
        """Delete leftover generated uploads already shown on this folder list."""
        listed = self.files.get_item_list()
        to_delete = []
        for name in listed:
            if self._is_generated_upload(name):
                to_delete.append(name)
        self._delete_names(to_delete)

    def _delete_names(self, names: list[str]) -> None:
        """Delete each listed name, continuing when one row fails.

        Args:
            names: Visible composed names still on the Files list.
        """
        previous = self.settings.timeout_ms
        self.page.set_default_timeout(CLEANUP_TIMEOUT_MS)
        expect.set_options(timeout=CLEANUP_TIMEOUT_MS)
        try:
            for name in names:
                try:
                    self._delete_one_listed_file(name)
                except Exception:
                    # Keep deleting the rest; one stale row must not block the others.
                    continue
        finally:
            self.page.set_default_timeout(previous)
            expect.set_options(timeout=previous)

    def _should_delete_name(self, name: str) -> bool:
        """Return True when this Files-list name is leftover test data.

        Args:
            name: Visible composed file name.

        Returns:
            True when the name was recorded or matches this suite's generated shape.
        """
        if name in self.uploaded_names:
            return True
        for project in self.uploaded_projects:
            if project in name:
                return True
        return self._is_generated_upload(name)

    def _is_generated_upload(self, name: str) -> bool:
        """Return True for unique-Project files created by this suite.

        Args:
            name: Visible composed file name.

        Returns:
            False for demo names such as res1-... that must stay in the folder.
        """
        if GENERATED_NAME_MARKER not in name:
            return False
        if not name.endswith(GENERATED_NAME_SUFFIX):
            return False
        project = name.split("-")[0]
        if len(project) != GENERATED_PROJECT_LENGTH:
            return False
        rules = naming_rules()
        for demo in rules["forbidden_demo_values"]:
            if project.lower() == demo.lower():
                return False
        return True

    def _delete_one_listed_file(self, name: str) -> None:
        """Select one leftover file and confirm Delete.

        Args:
            name: Visible composed name still on the Files list.
        """
        dismiss_open_overlays(self.page)
        self.files.select_file(name)
        self.files.verify_file_selected()
        self.files.click_delete_button()
        confirm = DeleteDialog(self.page)
        confirm.click_delete_button()
        dismiss_open_overlays(self.page)
