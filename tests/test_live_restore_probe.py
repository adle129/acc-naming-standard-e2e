"""Live probe: open Restore files and dump the title / Accept controls.

This is not an assertion of product behavior. It writes the overlay text so
RESTORE_FILES_HEADING and Accept can be locked without a 60s timeout.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from components.toast import TOAST_DELETED, TOAST_UPLOADED
from components.file_toolbar import BUTTON_ROLE
from dialogs.delete_dialog import DeleteDialog
from dialogs.restore_confirm_dialog import RestoreConfirmDialog
from dialogs.restore_items_dialog import RestoreItemsDialog
from dialogs.upload_dialog import UploadDialog
from dialogs.upload_progress_dialog import UploadProgressDialog
from pages.deleted_items_page import DeletedItemsPage
from pages.files_page import FilesPage
from pages.restore_files_page import ACCEPT_BUTTON_NAME, RESTORE_FILES_HEADING, RestoreFilesPage
from pages.upload_files_page import UploadFilesPage
from tests.live_support import LiveAcc
from tests.framework.support import (
    ACCEPT_TEXT_HINT,
    LIST_SETTLE_MS,
    MSG_UPLOADED_NAME_MISSING,
    SHOWING_NONEMPTY_PATTERN,
    PROBE_RESTORE_NOT_OPENED,
    PROBE_RESTORE_NOT_VISIBLE,
    PROBE_SEEDED_DELETED,
    PROBE_TEXT_LIMIT,
    RESTORE_PROBE_PATH,
    RESTORE_TEXT_HINT,
    SAMPLE_UPLOAD_FILE_NAME,
)
from utils.test_data import (
    FILES_DIR,
    ROW_UPLOAD_DELETE_RESTORE,
    SUITE_ACCEPTANCE,
    load_row,
)

# Real ACC. Not a framework self-check.
pytestmark = pytest.mark.smoke


def test_live_restore_files_structure(live_acc: LiveAcc) -> None:
    """Open Restore files when a deleted row exists and dump title / Accept.

    Args:
        live_acc: Function fixture that opens the naming folder and cleans up.
    """
    # The fixture already opened Files and the naming-standard folder.
    files = live_acc.files
    page = live_acc.page
    files.click_deleted_items_button()
    deleted = DeletedItemsPage(page)
    deleted.validate_deleted_items_page()
    # Deleted items rows can arrive after the Deleted by column.
    try:
        expect(deleted.file_list.showing_label()).to_have_text(
            SHOWING_NONEMPTY_PATTERN,
            timeout=LIST_SETTLE_MS,
        )
    except AssertionError:
        pass

    lines = []
    names = deleted.get_item_list()
    lines.append(f"deleted names={names!r}")
    if not names:
        # Restore files needs a selected deleted row; seed one then reopen.
        names = _seed_deleted_file(live_acc, deleted, lines)
    if not names:
        lines.append(PROBE_RESTORE_NOT_OPENED)
        _write_probe(RESTORE_PROBE_PATH, lines)
        assert RESTORE_PROBE_PATH.is_file()
        return

    # First deleted row is enough to reach the attribute table.
    deleted.select_file(names[0])
    restore_count = deleted.restore_button().count()
    lines.append(f"Restore button count after select={restore_count}")
    _append_button_texts(page, lines)
    if restore_count == 0:
        # The Name row click selects some ACC grids when the split checkbox does not.
        deleted.row(names[0]).row().click()
        restore_count = deleted.restore_button().count()
        lines.append(f"Restore button count after row click={restore_count}")
        _append_button_texts(page, lines)
    if restore_count == 0:
        lines.append(PROBE_RESTORE_NOT_VISIBLE)
        try:
            lines.append(page.locator("body").aria_snapshot())
        except Exception as error:
            lines.append(f"body aria_snapshot failed: {error}")
        _write_probe(RESTORE_PROBE_PATH, lines)
        assert RESTORE_PROBE_PATH.is_file()
        return
    deleted.click_restore_button()
    confirm = RestoreConfirmDialog(page)
    confirm.validate_restore_confirm_dialog()
    confirm.click_restore_button()
    items = RestoreItemsDialog(page)
    items.validate_restore_items_dialog()
    items.click_continue_button()

    restore = RestoreFilesPage(page)
    heading_count = restore.heading().count()
    lines.append(f"heading {RESTORE_FILES_HEADING!r} count={heading_count}")
    restore_texts = page.get_by_text(RESTORE_TEXT_HINT).all_inner_texts()
    for text in restore_texts[:PROBE_TEXT_LIMIT]:
        lines.append(f"restore text: {text!r}")
    accept_count = restore.accept_buttons().count()
    lines.append(f"{ACCEPT_BUTTON_NAME} count={accept_count}")
    accept_texts = page.get_by_text(ACCEPT_TEXT_HINT).all_inner_texts()
    for text in accept_texts[:PROBE_TEXT_LIMIT]:
        lines.append(f"accept text: {text!r}")
    try:
        snap = restore.dialog().aria_snapshot()
        lines.append("dialog aria_snapshot:")
        lines.append(snap)
    except Exception as error:
        lines.append(f"dialog aria_snapshot failed: {error}")
        snap = page.locator("body").aria_snapshot()
        lines.append("body aria_snapshot:")
        lines.append(snap)

    # Leave without restoring so the deleted row stays for later runs.
    restore.click_cancel_button()
    _write_probe(RESTORE_PROBE_PATH, lines)
    assert RESTORE_PROBE_PATH.is_file()


def _seed_deleted_file(
    live_acc: LiveAcc,
    deleted: DeletedItemsPage,
    lines: list[str],
) -> list[str]:
    """Upload a unique file then delete it so Restore files can open.

    Args:
        live_acc: Function fixture that tracks the composed name for cleanup.
        deleted: Deleted items page currently on screen.
        lines: Probe lines to append.

    Returns:
        Deleted-item names after the seed, or empty if upload did not list.
    """
    files = live_acc.files
    page = live_acc.page
    # Files nav lands on project root; the validator only opens in this folder.
    deleted.click_files()
    files.validate_files_page()
    files.click_folder(live_acc.settings.folder_name)
    files.click_upload_button()
    upload = UploadDialog(page)
    upload.validate_upload_dialog()
    upload.select_files(FILES_DIR / SAMPLE_UPLOAD_FILE_NAME)
    upload_files = UploadFilesPage(page)
    upload_files.validate_upload_files_page()
    # Unique project makes this row easy to find after upload.
    case = load_row(SUITE_ACCEPTANCE, ROW_UPLOAD_DELETE_RESTORE)
    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    item.set_attributes(case.attributes)
    upload_files.click_upload_button()
    # Done is visible during upload; wait for the toast before leaving the dialog.
    files.verify_toast(TOAST_UPLOADED)
    progress = UploadProgressDialog(page)
    progress.click_done_button()
    files.validate_files_page()
    # The composed name starts with the unique project; wait for that row.
    expect(files.page.get_by_text(case.attributes.project)).to_be_visible()
    listed = files.get_item_list()
    lines.append(f"files list after upload={listed!r}")
    uploaded_name = ""
    for name in listed:
        if case.attributes.project in name:
            uploaded_name = name
            break
    if uploaded_name == "":
        lines.append(MSG_UPLOADED_NAME_MISSING.format(project=case.attributes.project))
        return []
    # Cleanup deletes this name only if it is still on the Files list.
    live_acc.remember_upload(uploaded_name)
    return _delete_and_reopen_deleted(files, deleted, uploaded_name, lines)


def _delete_and_reopen_deleted(
    files: FilesPage,
    deleted: DeletedItemsPage,
    name: str,
    lines: list[str],
) -> list[str]:
    """Delete one Files-list row and return the Deleted items names.

    Args:
        files: Files page on the naming folder.
        deleted: Deleted items page to reopen after delete.
        name: Visible file name to delete.
        lines: Probe lines to append.

    Returns:
        Deleted-item names after the delete.
    """
    files.select_file(name)
    files.click_delete_button()
    delete = DeleteDialog(files.page)
    delete.validate_delete_dialog()
    delete.click_delete_button()
    files.verify_toast(TOAST_DELETED)
    files.click_deleted_items_button()
    deleted.validate_deleted_items_page()
    lines.append(PROBE_SEEDED_DELETED)
    lines.append(f"seeded name={name!r}")
    return deleted.get_item_list()


def _append_button_texts(page: Page, lines: list[str]) -> None:
    """Record visible button names so Restore wording can be locked.

    Args:
        page: Playwright page launched by pytest-playwright.
        lines: Probe lines to append.
    """
    buttons = page.get_by_role(BUTTON_ROLE)
    total = buttons.count()
    lines.append(f"button count={total}")
    limit = total
    if limit > PROBE_TEXT_LIMIT:
        limit = PROBE_TEXT_LIMIT
    for index in range(limit):
        text = buttons.nth(index).inner_text().replace("\n", " ").strip()
        lines.append(f"button: {text!r}")


def _write_probe(path: Path, lines: list[str]) -> None:
    """Write the Restore dump so pytest output is not the only copy.

    Args:
        path: Destination under reports/.
        lines: One diagnostic line each.
    """
    # reports/ may be empty except .gitkeep.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
