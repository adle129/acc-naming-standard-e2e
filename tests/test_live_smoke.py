"""Live ACC smoke: open real pages and click sample-case buttons.

This is not the M5 acceptance test. It proves Files, Upload picker, Upload
validator, and Deleted items against the real product. Login is the session
fixture. Framework tests still use FakePage and do not import this.
"""

from __future__ import annotations

import pytest

from dialogs.upload_dialog import UploadDialog
from dialogs.validator_dialog import (
    WHAT_ADD_FILES,
    WHAT_CANCEL_VALIDATOR,
    WHAT_CLOSE_VALIDATOR,
    WHAT_EDIT_ALL,
    WHAT_ERROR_BANNER,
    WHAT_ERRORS_ONLY,
    WHAT_PREVIOUS_VERSION_LABEL,
    WHAT_PREVIOUS_VERSION_SWITCH,
    WHAT_REMOVE_ALL,
    WHAT_UPLOAD_BUTTON,
)
from components.validator_item import (
    FIELD_CLASSIFICATION,
    FIELD_CUSTOM_FIELDS,
    FIELD_LEVEL,
    FIELD_NUMBER,
    FIELD_ORIGINATOR,
    FIELD_PROJECT,
    FIELD_REVISION,
    FIELD_ROLE,
    FIELD_STATUS,
    FIELD_TYPE,
    FIELD_VOLUME,
    value_has_code,
)
from pages.deleted_items_page import WHAT_DELETED_BY, DeletedItemsPage
from pages.upload_files_page import UploadFilesPage
from tests.live_support import LiveAcc
from tests.framework.support import (
    MSG_ATTRIBUTE_VALUE,
    MSG_COUNT_EQUALS_LIST,
    MSG_ITEM_IN_LIST,
    SAMPLE_ORIGINATOR_VALUE,
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


def test_live_open_files_and_click_upload(live_acc: LiveAcc) -> None:
    """Prove Files, Upload, validator, and Deleted items page methods work live.

    Args:
        live_acc: Function fixture that opens the naming folder and cleans up.
    """
    # The fixture already opened Files and the naming-standard folder.
    files = live_acc.files
    page = live_acc.page
    # Soft check: a count mismatch must not skip Upload or Deleted items.
    file_count = files.get_items_count()
    # Names are read separately so the message can show both sides.
    file_names = files.get_item_list()
    pytest.assume(
        file_count == len(file_names),
        MSG_COUNT_EQUALS_LIST.format(count=file_count, length=len(file_names)),
    )
    # Sample step 3: Upload on the action bar opens the picker dialog.
    files.click_upload_button()

    upload = UploadDialog(page)
    # The picker must be on screen before the OS file chooser.
    upload.validate_upload_dialog()
    # Sample steps 4–5: Select files + OS picker. a.txt is the committed sample.
    upload.select_files(FILES_DIR / SAMPLE_UPLOAD_FILE_NAME)

    upload_files = UploadFilesPage(page)
    # Sample step 6: the Upload files banner on the Files folder URL.
    upload_files.validate_upload_files_page()
    # The listed name includes the composed preview; match the local file name.
    upload_files.verify_file_visible(SAMPLE_UPLOAD_FILE_NAME)
    listed = upload_files.get_item_list()
    listed_count = upload_files.get_items_count()
    pytest.assume(
        listed_count == len(listed),
        MSG_COUNT_EQUALS_LIST.format(count=listed_count, length=len(listed)),
    )
    pytest.assume(
        SAMPLE_UPLOAD_FILE_NAME in listed,
        MSG_ITEM_IN_LIST.format(name=SAMPLE_UPLOAD_FILE_NAME),
    )
    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    # Page chrome: do not click Remove / Upload / Add files (those change the run).
    upload_files.verify_visible(upload_files.edit_all_button(), WHAT_EDIT_ALL)
    upload_files.verify_visible(upload_files.remove_all_button(), WHAT_REMOVE_ALL)
    upload_files.verify_visible(upload_files.add_files_button(), WHAT_ADD_FILES)
    upload_files.verify_visible(upload_files.errors_only_checkbox(), WHAT_ERRORS_ONLY)
    upload_files.verify_visible(upload_files.error_banner(), WHAT_ERROR_BANNER)
    upload_files.verify_visible(
        upload_files.previous_version_label(),
        WHAT_PREVIOUS_VERSION_LABEL,
    )
    upload_files.verify_visible(
        upload_files.previous_version_switch(),
        WHAT_PREVIOUS_VERSION_SWITCH,
    )
    upload_files.verify_visible(upload_files.close_button(), WHAT_CLOSE_VALIDATOR)
    upload_files.verify_visible(upload_files.cancel_button(), WHAT_CANCEL_VALIDATOR)
    upload_files.verify_visible(upload_files.upload_button(), WHAT_UPLOAD_BUTTON)
    # a.txt has errors, so the filter keeps it listed.
    upload_files.check_errors_only()
    upload_files.verify_errors_only_checked()
    upload_files.uncheck_errors_only()
    upload_files.verify_errors_only_unchecked()
    # Tick the row so later attribute get/set apply to this item.
    item.select()
    item.verify_selected()
    # Sample steps 7a–7k: values come from the acceptance JSON row.
    case = load_row(SUITE_ACCEPTANCE, ROW_UPLOAD_DELETE_RESTORE)
    attrs = case.attributes
    item.set_attributes(attrs)
    # Soft checks: read the same row back; a mismatch must not skip later pages.
    actual = item.get_attributes()
    exact_fields = (
        (FIELD_PROJECT, actual.project, attrs.project),
        (FIELD_NUMBER, actual.number, attrs.number),
        (FIELD_REVISION, actual.revision, attrs.revision),
        (FIELD_CUSTOM_FIELDS, actual.custom_fields, attrs.custom_fields),
    )
    for field, got, expected in exact_fields:
        pytest.assume(
            got == expected,
            MSG_ATTRIBUTE_VALUE.format(field=field, expected=expected, actual=got),
        )
    prefix_fields = (
        (FIELD_VOLUME, actual.volume, attrs.volume),
        (FIELD_LEVEL, actual.level, attrs.level),
        (FIELD_TYPE, actual.type, attrs.type),
        (FIELD_ROLE, actual.role, attrs.role),
        (FIELD_STATUS, actual.status, attrs.status),
        (FIELD_CLASSIFICATION, actual.classification, attrs.classification),
    )
    for field, got, expected in prefix_fields:
        pytest.assume(
            value_has_code(got, expected),
            MSG_ATTRIBUTE_VALUE.format(field=field, expected=expected, actual=got),
        )
    originator = item.get_originator()
    pytest.assume(
        value_has_code(originator, SAMPLE_ORIGINATOR_VALUE),
        MSG_ATTRIBUTE_VALUE.format(
            field=FIELD_ORIGINATOR,
            expected=SAMPLE_ORIGINATOR_VALUE,
            actual=originator,
        ),
    )
    # Leave without uploading so later pages can still be opened.
    upload_files.click_cancel_button()
    # Cancel leaves the picker open; close it so Deleted items is clickable.
    upload.click_close()

    files.validate_files_page()
    # Sample step 13 navigation, without requiring a deleted row first.
    files.click_deleted_items_button()
    deleted = DeletedItemsPage(page)
    deleted.validate_deleted_items_page()
    # Deleted by is unique to this view; Files list does not show it.
    deleted.verify_visible(deleted.deleted_by_column(), WHAT_DELETED_BY)
    # Soft check: Deleted items count/list can fail without skipping the return to Files.
    deleted_count = deleted.get_items_count()
    # Names are read separately so the message can show both sides.
    deleted_names = deleted.get_item_list()
    pytest.assume(
        deleted_count == len(deleted_names),
        MSG_COUNT_EQUALS_LIST.format(count=deleted_count, length=len(deleted_names)),
    )
    # Sample step 21: Files nav returns to the live list.
    deleted.click_files()
    files.validate_files_page()
