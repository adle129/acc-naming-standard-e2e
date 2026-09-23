"""Acceptance path: login, upload, delete, restore on live ACC.

Page-state gates stay on POM (validate_* / verify_*): a missing control
must stop the next click. Business rules use pytest.assume so one mismatch
is recorded and later sibling checks still run. Action methods do not assert.
"""

from __future__ import annotations

import pytest

from components.file_list import ITEM_COUNT_DELTA_ONE, MSG_ITEMS_COUNT
from components.toast import TOAST_DELETED, TOAST_RESTORED, TOAST_UPLOADED
from components.validator_item import (
    FIELD_CLASSIFICATION,
    FIELD_CUSTOM_FIELDS,
    FIELD_LEVEL,
    FIELD_NUMBER,
    FIELD_PROJECT,
    FIELD_REVISION,
    FIELD_ROLE,
    FIELD_STATUS,
    FIELD_TYPE,
    FIELD_VOLUME,
    value_has_code,
)
from dialogs.delete_dialog import DeleteDialog
from dialogs.restore_confirm_dialog import RestoreConfirmDialog
from dialogs.restore_items_dialog import RestoreItemsDialog
from dialogs.upload_dialog import UploadDialog
from dialogs.upload_progress_dialog import UploadProgressDialog
from dialogs.validator_dialog import ERROR_BANNER_HINT, SPECIAL_CHARACTERS_HINT
from pages.deleted_items_page import DeletedItemsPage
from pages.restore_files_page import RestoreFilesPage
from pages.upload_files_page import UploadFilesPage
from tests.framework.support import (
    MSG_ATTRIBUTE_VALUE,
    MSG_BANNER_MUST_BE_HIDDEN,
    MSG_BANNER_MUST_CONTAIN,
    MSG_ITEM_IN_LIST,
    MSG_ITEM_NOT_IN_LIST,
    SAMPLE_UPLOAD_FILE_NAME,
)
from tests.acceptance_steps import (
    CASE_STEP_1,
    CASE_STEP_2,
    CASE_STEP_3,
    CASE_STEP_4,
    CASE_STEP_5,
    CASE_STEP_6,
    CASE_STEP_7,
    CASE_STEP_7_DELIMITER,
    CASE_STEP_8,
    CASE_STEP_9,
    CASE_STEP_10,
    CASE_STEP_11,
    CASE_STEP_12,
    CASE_STEP_13,
    CASE_STEP_14,
    CASE_STEP_15,
    CASE_STEP_16,
    CASE_STEP_17,
    CASE_STEP_18,
    CASE_STEP_19,
    CASE_STEP_20,
    CASE_STEP_21,
)
from tests.live_support import LiveAcc
from utils.logger import log_case, log_case_step
from utils.test_data import (
    FILES_DIR,
    ROW_UPLOAD_DELETE_RESTORE,
    SUITE_ACCEPTANCE,
    case_attribute_summary,
    delimiter_invalid_project,
    load_row,
)

# Real ACC. The reviewer runs this marker.
pytestmark = pytest.mark.acceptance


def _assume_text_equals(field: str, actual: str, expected: str) -> None:
    """Record a typed-field mismatch without stopping later field checks.

    Args:
        field: FIELD_* name used in the assumption message.
        actual: Value read back from the control.
        expected: Value from the acceptance JSON row.
    """
    # Business: typed Project / Number / Revision / custom fields stay as entered.
    pytest.assume(
        actual == expected,
        MSG_ATTRIBUTE_VALUE.format(
            field=field,
            expected=expected,
            actual=actual,
        ),
    )


def _assume_dropdown_equals(field: str, actual: str, expected: str) -> None:
    """Record a dropdown mismatch without stopping later field checks.

    Args:
        field: FIELD_* name used in the assumption message.
        actual: Visible dropdown text after the select.
        expected: Code from the acceptance JSON row.
    """
    # Business: ACC may append the option title after the selected code.
    pytest.assume(
        value_has_code(actual, expected),
        MSG_ATTRIBUTE_VALUE.format(
            field=field,
            expected=expected,
            actual=actual,
        ),
    )


def _assume_delimiter_banner(banner_text: str) -> None:
    """Record each missing delimiter hint so both phrases are reported.

    Args:
        banner_text: Inner text of the painted compliance banner.
    """
    # Business: live ACC names a delimiter as a special-character compliance error.
    pytest.assume(
        ERROR_BANNER_HINT in banner_text,
        MSG_BANNER_MUST_CONTAIN.format(
            hint=ERROR_BANNER_HINT,
            actual=banner_text,
        ),
    )
    # Business: the same banner must name special characters, not a generic toast.
    pytest.assume(
        SPECIAL_CHARACTERS_HINT in banner_text,
        MSG_BANNER_MUST_CONTAIN.format(
            hint=SPECIAL_CHARACTERS_HINT,
            actual=banner_text,
        ),
    )


def test_upload_delete_restore(live_acc: LiveAcc) -> None:
    """Prove the demo path: upload with attributes, delete, then restore.

    Args:
        live_acc: Function fixture that opens the naming folder and cleans up.
    """
    # The fixture already opened Files and the naming-standard folder.
    files = live_acc.files
    # One Playwright page is shared by every page object in this run.
    page = live_acc.page
    # Unique Project/Number come from the JSON row, not from demo values.
    case = load_row(SUITE_ACCEPTANCE, ROW_UPLOAD_DELETE_RESTORE)
    # RUN/case line tells the reviewer which JSON row this body is executing.
    log_case(
        suite=case.suite,
        row_id=case.row_id,
        description=case.description,
        attributes=case_attribute_summary(case.attributes),
    )
    # Attributes are the 10 naming-standard fields filled on Upload files.
    attrs = case.attributes
    # Remember Project now so cleanup can find the file if name capture fails.
    live_acc.remember_project(attrs.project)
    # Baseline Files count; later asserts only care about this test's one .txt.
    files_before = files.get_items_count()
    # Sample steps 1–2 already ran in live_acc.prepare(); log them for the reviewer.
    log_case_step(1, CASE_STEP_1)
    log_case_step(2, CASE_STEP_2)

    # Sample step 3: Upload on the action bar opens the picker dialog.
    log_case_step(3, CASE_STEP_3)
    files.click_upload_button()
    # The picker must be on screen before the OS file chooser.
    upload = UploadDialog(page)
    # Page state: Select files is showing.
    upload.validate_upload_dialog()
    # Sample steps 4–5: attach the committed sample file, not a generated one.
    log_case_step(4, CASE_STEP_4)
    log_case_step(5, CASE_STEP_5)
    upload.select_files(FILES_DIR / SAMPLE_UPLOAD_FILE_NAME)

    # Sample step 6: the Upload files overlay lists the awaiting file.
    log_case_step(6, CASE_STEP_6)
    upload_files = UploadFilesPage(page)
    # Page state: URL stays on the Files folder while the validator is open.
    upload_files.validate_upload_files_page()
    # Page state: the local a.txt row is painted on the validator table.
    upload_files.verify_file_visible(SAMPLE_UPLOAD_FILE_NAME)
    # Tick the row so attribute set/get apply to this file.
    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    # Sample step 7: fill the ten fields, then read each one back.
    log_case_step(7, CASE_STEP_7)
    # Sample step 7a: Project is typed; get after fill must match the case.
    item.set_project(attrs.project)
    _assume_text_equals(FIELD_PROJECT, item.get_project(), attrs.project)
    # Sample step 7b: Volume is a dropdown; get after select must show the code.
    item.set_volume(attrs.volume)
    _assume_dropdown_equals(FIELD_VOLUME, item.get_volume(), attrs.volume)
    # Sample step 7c: Level is a dropdown; get after select must show the code.
    item.set_level(attrs.level)
    _assume_dropdown_equals(FIELD_LEVEL, item.get_level(), attrs.level)
    # Sample step 7d: Type is a dropdown; get after select must show the code.
    item.set_type(attrs.type)
    _assume_dropdown_equals(FIELD_TYPE, item.get_type(), attrs.type)
    # Sample step 7e: Role is a dropdown; get after select must show the code.
    item.set_role(attrs.role)
    _assume_dropdown_equals(FIELD_ROLE, item.get_role(), attrs.role)
    # Sample step 7f: Number is typed digits; get after fill must match the case.
    item.set_number(attrs.number)
    _assume_text_equals(FIELD_NUMBER, item.get_number(), attrs.number)
    # Sample step 7g: Status is a dropdown; get after select must show the code.
    item.set_status(attrs.status)
    _assume_dropdown_equals(FIELD_STATUS, item.get_status(), attrs.status)
    # Sample step 7h: Revision is typed; get after fill must match the case.
    item.set_revision(attrs.revision)
    _assume_text_equals(FIELD_REVISION, item.get_revision(), attrs.revision)
    # Sample step 7i: Classification is a dropdown; get after select must show the code.
    item.set_classification(attrs.classification)
    _assume_dropdown_equals(
        FIELD_CLASSIFICATION,
        item.get_classification(),
        attrs.classification,
    )
    # Sample step 7k: custom fields is typed digits; get after fill must match.
    item.set_custom_fields(attrs.custom_fields)
    _assume_text_equals(
        FIELD_CUSTOM_FIELDS,
        item.get_custom_fields(),
        attrs.custom_fields,
    )
    # Invalid Project uses the naming delimiter + suffix, not a hardcoded res-1.
    log_case_step(7, CASE_STEP_7_DELIMITER)
    item.set_project(delimiter_invalid_project(attrs.project))
    # Page state: the validator paints the compliance banner after Tab.
    upload_files.verify_delimiter_error_visible()
    # Business: the hint must name the delimiter as a special-character error.
    _assume_delimiter_banner(upload_files.error_banner().inner_text())
    # Put the unique Project back so the composed name and cleanup stay ours.
    item.set_project(attrs.project)
    # Page state: a valid Project clears the compliance banner.
    upload_files.verify_delimiter_error_hidden()
    # Business: the typed Project is again the unique case value.
    _assume_text_equals(FIELD_PROJECT, item.get_project(), attrs.project)
    # Sample step 8: Upload for real; do not Cancel.
    log_case_step(8, CASE_STEP_8)
    upload_files.click_upload_button()
    # Page state: the upload toast widget is showing.
    files.verify_toast(TOAST_UPLOADED)
    # Sample step 9: Done returns to the Files list.
    log_case_step(9, CASE_STEP_9)
    progress = UploadProgressDialog(page)
    # Done is enabled after Uploaded to the folder name.
    progress.click_done_button()
    # Page state: this is the Files list, not Deleted items.
    files.validate_files_page()
    # The composed name starts with the unique Project from this run.
    uploaded_name = files.file_name_containing(attrs.project)
    # Cleanup deletes this row if a later step fails after upload.
    live_acc.remember_upload(uploaded_name)
    # Page state: the Name-table row for this file is painted.
    files.verify_file_visible(uploaded_name)
    # Business: this composed .txt is now in the folder inventory.
    listed_after_upload = files.get_item_list()
    # Soft: a list miss must not skip the count check at this same checkpoint.
    pytest.assume(
        uploaded_name in listed_after_upload,
        MSG_ITEM_IN_LIST.format(name=uploaded_name),
    )
    # Business: upload added exactly one item; assume so a list miss still checks count.
    count_after_upload = files.get_items_count()
    pytest.assume(
        count_after_upload == files_before + ITEM_COUNT_DELTA_ONE,
        MSG_ITEMS_COUNT.format(
            expected=files_before + ITEM_COUNT_DELTA_ONE,
            actual=count_after_upload,
        ),
    )

    # Sample step 10: checkbox + action-bar Delete, not the row menu.
    log_case_step(10, CASE_STEP_10)
    files.select_file(uploaded_name)
    # Page state: Move appears only after this row is selected.
    files.verify_file_selected()
    # Delete opens the confirmation dialog.
    files.click_delete_button()
    # Sample step 11: confirm in the dialog.
    log_case_step(11, CASE_STEP_11)
    delete = DeleteDialog(page)
    # Page state: the confirm control is on screen.
    delete.validate_delete_dialog()
    # Confirming removes the file from the live list.
    delete.click_delete_button()
    # Sample step 12: the toast and the missing row prove delete finished.
    log_case_step(12, CASE_STEP_12)
    # Page state: the deleted toast widget is showing.
    files.verify_toast(TOAST_DELETED)
    # Page state: the Name-table row is gone.
    files.verify_file_hidden(uploaded_name)
    # Business: this composed .txt left the folder inventory.
    listed_after_delete = files.get_item_list()
    # Soft: a list miss must not skip the count check at this same checkpoint.
    pytest.assume(
        uploaded_name not in listed_after_delete,
        MSG_ITEM_NOT_IN_LIST.format(name=uploaded_name),
    )
    # Business: delete removed exactly one item; assume so a list miss still checks count.
    count_after_delete = files.get_items_count()
    pytest.assume(
        count_after_delete == files_before,
        MSG_ITEMS_COUNT.format(
            expected=files_before,
            actual=count_after_delete,
        ),
    )

    # Sample step 13: Deleted items is a page, opened from the toolbar.
    log_case_step(13, CASE_STEP_13)
    files.click_deleted_items_button()
    # The deleted view has its own URL and Deleted by column.
    deleted = DeletedItemsPage(page)
    # Page state: this is Deleted items, not the live Files list.
    deleted.validate_deleted_items_page()
    # Page state: this same composed .txt is painted on Deleted items.
    deleted.verify_file_visible(uploaded_name)
    # Business: the file we deleted is the one sitting in Deleted items.
    deleted_listed = deleted.get_item_list()
    # Soft: keep going to the restore path even if the inventory string missed.
    pytest.assume(
        uploaded_name in deleted_listed,
        MSG_ITEM_IN_LIST.format(name=uploaded_name),
    )
    # Count here is only used to prove this one file left after restore.
    deleted_after_delete = deleted.get_items_count()

    # Sample step 14: select the row so Restore appears on the toolbar.
    log_case_step(14, CASE_STEP_14)
    deleted.select_file(uploaded_name)
    # Page state: Restore appears only after this row is selected.
    deleted.verify_file_selected()
    # Restore on the action bar opens the first confirm dialog.
    deleted.click_restore_button()
    # Sample step 15: confirm Restore.
    log_case_step(15, CASE_STEP_15)
    confirm = RestoreConfirmDialog(page)
    # Page state: the first restore dialog is open.
    confirm.validate_restore_confirm_dialog()
    # Confirming opens Restore items (Continue).
    confirm.click_restore_button()
    # Sample step 16: Continue reaches the Restore files validator.
    log_case_step(16, CASE_STEP_16)
    items = RestoreItemsDialog(page)
    # Page state: Continue is on screen.
    items.validate_restore_items_dialog()
    # Continue opens Restore files on the Deleted items URL.
    items.click_continue_button()

    # Sample step 17: Restore files lets the user edit attributes.
    log_case_step(17, CASE_STEP_17)
    restore = RestoreFilesPage(page)
    # Page state: the restore validator overlay is open.
    restore.validate_restore_files_page()
    # Yellow previous-version values, if shown, must be accepted before Restore.
    restore.accept_previous_version()
    # Restore edits the same local a.txt row the upload used.
    restore_item = restore.item(SAMPLE_UPLOAD_FILE_NAME)
    # Sample step 18: Project plus "-" must show the delimiter error.
    log_case_step(18, CASE_STEP_18)
    restore_item.set_project(delimiter_invalid_project(attrs.project))
    # Page state: the compliance banner is painted.
    restore.verify_delimiter_error_visible()
    # Business: ACC classifies a delimiter in Project as a special-character error.
    _assume_delimiter_banner(restore.error_banner().inner_text())
    # Sample step 19: put the unique Project back so the composed name stays ours.
    log_case_step(19, CASE_STEP_19)
    restore_item.set_project(attrs.project)
    # Page state: the compliance banner is gone.
    restore.verify_delimiter_error_hidden()
    # Business: a valid Project clears the delimiter rule; assume so Restore still runs.
    pytest.assume(
        restore.error_banner().is_visible() is False,
        MSG_BANNER_MUST_BE_HIDDEN,
    )
    # Restore for real; do not Cancel.
    restore.click_restore_button()
    # Sample step 20: the toast and the Deleted-items count prove restore finished.
    log_case_step(20, CASE_STEP_20)
    # Page state: the restore toast widget is showing.
    deleted.verify_toast(TOAST_RESTORED)
    # Business: restore removed exactly this one file from Deleted items.
    deleted_after_restore = deleted.get_items_count()
    # Soft: a count miss must not skip returning to Files to check the restored row.
    pytest.assume(
        deleted_after_restore == deleted_after_delete - ITEM_COUNT_DELTA_ONE,
        MSG_ITEMS_COUNT.format(
            expected=deleted_after_delete - ITEM_COUNT_DELTA_ONE,
            actual=deleted_after_restore,
        ),
    )

    # Sample step 21: Files nav returns to the live list.
    log_case_step(21, CASE_STEP_21)
    deleted.click_files()
    # Files nav lands on Project Files; reopen the naming folder.
    files.validate_files_page()
    files.click_folder(live_acc.settings.folder_name)
    # Page state: Upload is back after the folder files load.
    files.verify_folder_opened()
    # Page state: the restored row is painted on Files.
    files.verify_file_visible(uploaded_name)
    # Business: the unique Project still maps to the same composed .txt.
    restored_name = files.file_name_containing(attrs.project)
    # Soft: a name miss must not skip the final count check.
    pytest.assume(
        restored_name == uploaded_name,
        MSG_ITEM_IN_LIST.format(name=uploaded_name),
    )
    # Business: the folder count is again baseline plus this one restored file.
    count_after_restore = files.get_items_count()
    pytest.assume(
        count_after_restore == files_before + ITEM_COUNT_DELTA_ONE,
        MSG_ITEMS_COUNT.format(
            expected=files_before + ITEM_COUNT_DELTA_ONE,
            actual=count_after_restore,
        ),
    )
