"""Live probe: open Status and write the dropdown structure to reports/.

This is not an assertion of product behavior. It dumps combobox names and
option roles so Status can be wired without a 60s timeout.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import expect

from components.validator_item import (
    ENABLED_COMBOBOX_SELECTOR,
    LISTBOX_ROLE,
    OPTION_ROLE,
)
from dialogs.upload_dialog import UploadDialog
from pages.upload_files_page import UploadFilesPage
from tests.live_support import LiveAcc
from tests.framework.support import (
    LISTITEM_ROLE,
    PROBE_LIST_TIMEOUT_MS,
    PROBE_OPTION_LIMIT,
    SAMPLE_UPLOAD_FILE_NAME,
    STATUS_PROBE_PATH,
)
from utils.test_data import FILES_DIR

# Real ACC. Not a framework self-check.
pytestmark = pytest.mark.smoke


def test_live_status_dropdown_structure(live_acc: LiveAcc) -> None:
    """Open Status once and write combobox / option structure to reports/.

    Args:
        live_acc: Function fixture that opens the naming folder and cleans up.
    """
    # The fixture already opened Files and the naming-standard folder.
    files = live_acc.files
    page = live_acc.page
    files.click_upload_button()
    upload = UploadDialog(page)
    upload.validate_upload_dialog()
    upload.select_files(FILES_DIR / SAMPLE_UPLOAD_FILE_NAME)
    upload_files = UploadFilesPage(page)
    upload_files.validate_upload_files_page()
    upload_files.verify_file_visible(SAMPLE_UPLOAD_FILE_NAME)

    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    lines = []
    # Enabled combobox names show whether nth(5) is actually Status.
    boxes = item.attribute_row().locator(ENABLED_COMBOBOX_SELECTOR)
    total = boxes.count()
    lines.append(f"enabled combobox count={total}")
    for index in range(total):
        box = boxes.nth(index)
        label = box.get_attribute("aria-label") or ""
        text = box.inner_text().replace("\n", " ").strip()
        lines.append(f"combo[{index}] aria-label={label!r} text={text!r}")

    # Open Status only; do not wait 60s for S0.
    item.status_box().click()
    page.set_default_timeout(PROBE_LIST_TIMEOUT_MS)
    expect.set_options(timeout=PROBE_LIST_TIMEOUT_MS)
    try:
        expect(page.get_by_role(LISTBOX_ROLE).last).to_be_visible()
        lines.append("listbox last: visible")
    except AssertionError:
        lines.append("listbox last: not visible")

    listboxes = page.get_by_role(LISTBOX_ROLE)
    lines.append(f"listbox count={listboxes.count()}")
    options = page.get_by_role(OPTION_ROLE)
    lines.append(f"option count={options.count()}")
    option_texts = options.all_inner_texts()
    for text in option_texts[:PROBE_OPTION_LIMIT]:
        lines.append(f"option: {text!r}")
    listitems = page.get_by_role(LISTITEM_ROLE)
    lines.append(f"listitem count={listitems.count()}")
    item_texts = listitems.all_inner_texts()
    for text in item_texts[:PROBE_OPTION_LIMIT]:
        lines.append(f"listitem: {text!r}")

    try:
        snap = page.get_by_role(LISTBOX_ROLE).last.aria_snapshot()
        lines.append("listbox aria_snapshot:")
        lines.append(snap)
    except Exception as error:
        lines.append(f"listbox aria_snapshot failed: {error}")
        snap = page.locator("body").aria_snapshot()
        lines.append("body aria_snapshot:")
        lines.append(snap)

    # reports/ is gitignored; the dump is for this run only.
    _write_probe(STATUS_PROBE_PATH, lines)
    # The file must exist so the reviewer can open it after the headed run.
    assert STATUS_PROBE_PATH.is_file()


def _write_probe(path: Path, lines: list[str]) -> None:
    """Write the Status dump so pytest output is not the only copy.

    Args:
        path: Destination under reports/.
        lines: One diagnostic line each.
    """
    # reports/ may be empty except .gitkeep.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
