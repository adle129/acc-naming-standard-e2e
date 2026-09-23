"""One file row on the Upload files / Restore validator table."""

from __future__ import annotations

import re
from pathlib import Path
from re import Pattern
from typing import Any

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError, expect

from pages.base_page import BasePage
from utils.logger import step
from utils.test_data import NamingAttributes

TEXTBOX_ROLE = "textbox"
ROW_ROLE = "row"
CHECKBOX_ROLE = "checkbox"
OPTION_ROLE = "option"
LISTBOX_ROLE = "listbox"
DIALOG_ROLE = "dialog"
TABLE_ROLE = "table"
GRIDCELL_ROLE = "gridcell"
FILE_NAME_HEADER = "File name"
PROJECT_HEADER = "Project *"
ORIGINATOR_HEADER = "Originator *"
VOLUME_HEADER = "Volume/System *"
LEVEL_HEADER = "Level/Location *"
TYPE_HEADER = "Type *"
ROLE_HEADER = "Role *"
STATUS_HEADER = "Status *"
CLASSIFICATION_HEADER = "Classification *"
# The listed name includes the composed preview, so match a.txt as a substring.
FILE_NAME_EXACT = False
FIRST_ROW_INDEX = 0

# Live ACC exposes text fields by their format-mask accessible names.
PROJECT_BOX_NAME = "XXXXXX"
NUMBER_BOX_NAME = "######"
REVISION_BOX_NAME = "XXXXXXXX"
CUSTOM_FIELDS_BOX_NAME = "#####"

DISABLED_COMBO_CLASS = "SelectBox--disabled"
ENABLED_COMBOBOX_SELECTOR = f'[role="combobox"]:not(.{DISABLED_COMBO_CLASS})'
VISIBLE_LISTBOX_SELECTOR = '[role="listbox"]:visible'
# First click after Role may only dismiss the leftover list; retry once.
LIST_REOPEN_TIMEOUT_MS = 3000
CLOSED_LISTBOX_COUNT = 0
# ACC header cells expose Volume/System * as the accessible name, not inner_text.
HEADER_INDEX_SCRIPT = """(el) => {
    const row = el.closest('[role="row"]');
    if (!row) {
        return 0;
    }
    const cells = row.querySelectorAll('[role="gridcell"]');
    return Array.prototype.indexOf.call(cells, el);
}"""

STEP_SELECT_ITEM = "select upload item"
STEP_FILL_PROJECT = "fill Project = {value}"
STEP_SELECT_ORIGINATOR = "select Originator = {value}"
STEP_SELECT_VOLUME = "select Volume/System = {value}"
STEP_SELECT_LEVEL = "select Level/Location = {value}"
STEP_SELECT_TYPE = "select Type = {value}"
STEP_SELECT_ROLE = "select Role = {value}"
STEP_FILL_NUMBER = "fill Number = {value}"
STEP_SELECT_STATUS = "select Status = {value}"
STEP_FILL_REVISION = "fill Revision = {value}"
STEP_SELECT_CLASSIFICATION = "select Classification = {value}"
STEP_FILL_CUSTOM_FIELDS = "fill custom fields = {value}"

FIELD_PROJECT = "project"
FIELD_ORIGINATOR = "originator"
FIELD_VOLUME = "volume"
FIELD_LEVEL = "level"
FIELD_TYPE = "type"
FIELD_ROLE = "role"
FIELD_NUMBER = "number"
FIELD_STATUS = "status"
FIELD_REVISION = "revision"
FIELD_CLASSIFICATION = "classification"
FIELD_CUSTOM_FIELDS = "custom_fields"


class ValidatorItem(BasePage):
    """Checkbox and naming-standard fields for one listed file."""

    def __init__(self, page: Any, name: str, *, root: Path | None = None) -> None:
        """Bind the Playwright page and the file name used to find the row.

        Args:
            page: Playwright Page, or a test double.
            name: Local file name, for example a.txt.
            root: Optional project root forwarded to BasePage.
        """
        super().__init__(page, root=root)
        self.name = name

    def row(self) -> Locator:
        """Return the File name row (checkbox), not the attribute-field row.

        Returns:
            Playwright locator for that row.
        """
        # The row name includes the composed preview, so match the local name inside it.
        name_cell = self.page.get_by_text(self.name, exact=FILE_NAME_EXACT)
        return self._file_name_rows().filter(has=name_cell)

    def attribute_row(self) -> Locator:
        """Return the naming-standard field row aligned with this file.

        Returns:
            Playwright locator for the Project / dropdown row.
        """
        return self._attribute_rows().nth(self._name_row_index())

    def checkbox(self) -> Locator:
        """Return the checkbox on this row.

        Returns:
            Playwright locator scoped to the row.
        """
        return self.row().get_by_role(CHECKBOX_ROLE)

    @step(STEP_SELECT_ITEM)
    def select(self) -> None:
        """Tick this row's checkbox so the item becomes the active row."""
        self.checkbox().click()

    def verify_selected(self) -> None:
        """Prove this row's checkbox is checked."""
        expect(self.checkbox()).to_be_checked()

    def project_box(self) -> Locator:
        """Return the Project text field on this row.

        Returns:
            Playwright locator.
        """
        return self.attribute_row().get_by_role(TEXTBOX_ROLE, name=PROJECT_BOX_NAME, exact=True)

    def originator_box(self) -> Locator:
        """Return the Originator dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(ORIGINATOR_HEADER)

    def volume_box(self) -> Locator:
        """Return the Volume/System dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(VOLUME_HEADER)

    def level_box(self) -> Locator:
        """Return the Level/Location dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(LEVEL_HEADER)

    def type_box(self) -> Locator:
        """Return the Type dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(TYPE_HEADER)

    def role_box(self) -> Locator:
        """Return the Role dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(ROLE_HEADER)

    def number_box(self) -> Locator:
        """Return the Number text field on this row.

        Returns:
            Playwright locator.
        """
        return self.attribute_row().get_by_role(TEXTBOX_ROLE, name=NUMBER_BOX_NAME, exact=True)

    def status_box(self) -> Locator:
        """Return the Status dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(STATUS_HEADER)

    def revision_box(self) -> Locator:
        """Return the Revision text field on this row.

        Returns:
            Playwright locator.
        """
        return self.attribute_row().get_by_role(TEXTBOX_ROLE, name=REVISION_BOX_NAME, exact=True)

    def classification_box(self) -> Locator:
        """Return the Classification dropdown on this row.

        Returns:
            Playwright locator.
        """
        return self._combobox_in_column(CLASSIFICATION_HEADER)

    def custom_fields_box(self) -> Locator:
        """Return the custom fields text field on this row.

        Returns:
            Playwright locator.
        """
        return self.attribute_row().get_by_role(TEXTBOX_ROLE, name=CUSTOM_FIELDS_BOX_NAME, exact=True)

    @step(STEP_FILL_PROJECT)
    def set_project(self, value: str) -> None:
        """Set Project on this row.

        Args:
            value: Project attribute, usually from NamingAttributes.project.
        """
        self.project_box().fill(value)

    @step(STEP_SELECT_ORIGINATOR)
    def set_originator(self, value: str) -> None:
        """Set Originator on this row.

        Args:
            value: Originator code shown in the option list.
        """
        self._select_dropdown(self.originator_box(), value)

    @step(STEP_SELECT_VOLUME)
    def set_volume(self, value: str) -> None:
        """Set Volume/System on this row.

        Args:
            value: Volume code, for example ZZ.
        """
        self._select_dropdown(self.volume_box(), value)

    @step(STEP_SELECT_LEVEL)
    def set_level(self, value: str) -> None:
        """Set Level/Location on this row.

        Args:
            value: Level code, for example ZZ.
        """
        self._select_dropdown(self.level_box(), value)

    @step(STEP_SELECT_TYPE)
    def set_type(self, value: str) -> None:
        """Set Type on this row.

        Args:
            value: Type code, for example CA.
        """
        self._select_dropdown(self.type_box(), value)

    @step(STEP_SELECT_ROLE)
    def set_role(self, value: str) -> None:
        """Set Role on this row.

        Args:
            value: Role code, for example D.
        """
        self._select_dropdown(self.role_box(), value)

    @step(STEP_FILL_NUMBER)
    def set_number(self, value: str) -> None:
        """Set Number on this row.

        Args:
            value: Number attribute, usually from NamingAttributes.number.
        """
        self.number_box().fill(value)

    @step(STEP_SELECT_STATUS)
    def set_status(self, value: str) -> None:
        """Set Status on this row.

        Args:
            value: Status code, for example S0.
        """
        self._select_dropdown(self.status_box(), value)

    @step(STEP_FILL_REVISION)
    def set_revision(self, value: str) -> None:
        """Set Revision on this row.

        Args:
            value: Revision text, for example dff.
        """
        self.revision_box().fill(value)

    @step(STEP_SELECT_CLASSIFICATION)
    def set_classification(self, value: str) -> None:
        """Set Classification on this row.

        Args:
            value: Classification code, for example Ac_05.
        """
        self._select_searchable_dropdown(self.classification_box(), value)

    @step(STEP_FILL_CUSTOM_FIELDS)
    def set_custom_fields(self, value: str) -> None:
        """Set custom fields on this row.

        Args:
            value: Custom-fields text, for example 222.
        """
        self.custom_fields_box().fill(value)

    def set_attributes(self, attributes: NamingAttributes) -> None:
        """Set the 10 naming-standard fields on this row.

        Originator is left as the product default.

        Args:
            attributes: Values from load_row(...).attributes.
        """
        self.set_project(attributes.project)
        self.set_volume(attributes.volume)
        self.set_level(attributes.level)
        self.set_type(attributes.type)
        self.set_role(attributes.role)
        self.set_number(attributes.number)
        self.set_status(attributes.status)
        self.set_revision(attributes.revision)
        self.set_classification(attributes.classification)
        self.set_custom_fields(attributes.custom_fields)

    def get_project(self) -> str:
        """Return Project on this row.

        Returns:
            Text in the Project box.
        """
        return self._textbox_value(self.project_box())

    def get_originator(self) -> str:
        """Return Originator on this row.

        Returns:
            Visible Originator text.
        """
        return self._combobox_value(self.originator_box())

    def get_volume(self) -> str:
        """Return Volume/System on this row.

        Returns:
            Visible Volume/System text.
        """
        return self._combobox_value(self.volume_box())

    def get_level(self) -> str:
        """Return Level/Location on this row.

        Returns:
            Visible Level/Location text.
        """
        return self._combobox_value(self.level_box())

    def get_type(self) -> str:
        """Return Type on this row.

        Returns:
            Visible Type text.
        """
        return self._combobox_value(self.type_box())

    def get_role(self) -> str:
        """Return Role on this row.

        Returns:
            Visible Role text.
        """
        return self._combobox_value(self.role_box())

    def get_number(self) -> str:
        """Return Number on this row.

        Returns:
            Text in the Number box.
        """
        return self._textbox_value(self.number_box())

    def get_status(self) -> str:
        """Return Status on this row.

        Returns:
            Visible Status text.
        """
        return self._combobox_value(self.status_box())

    def get_revision(self) -> str:
        """Return Revision on this row.

        Returns:
            Text in the Revision box.
        """
        return self._textbox_value(self.revision_box())

    def get_classification(self) -> str:
        """Return Classification on this row.

        Returns:
            Visible Classification text.
        """
        return self._combobox_value(self.classification_box())

    def get_custom_fields(self) -> str:
        """Return custom fields on this row.

        Returns:
            Text in the custom fields box.
        """
        return self._textbox_value(self.custom_fields_box())

    def get_attributes(self) -> NamingAttributes:
        """Return the 10 naming-standard fields on this row.

        Originator is read with get_originator(); it is not in NamingAttributes.

        Returns:
            Current field values on this row.
        """
        return NamingAttributes(
            project=self.get_project(),
            volume=self.get_volume(),
            level=self.get_level(),
            type=self.get_type(),
            role=self.get_role(),
            number=self.get_number(),
            status=self.get_status(),
            revision=self.get_revision(),
            classification=self.get_classification(),
            custom_fields=self.get_custom_fields(),
        )

    def _textbox_value(self, box: Locator) -> str:
        """Read a text field through input_value().

        Args:
            box: Project, Number, Revision, or custom fields.

        Returns:
            Current input value.
        """
        return box.input_value()

    def _combobox_value(self, box: Locator) -> str:
        """Read a dropdown's visible text.

        Args:
            box: One attribute combobox on this row.

        Returns:
            First non-empty line, or input_value() when the box has no text.
        """
        text = box.inner_text().strip()
        if text:
            # Some boxes keep a second line from a leftover SelectBox clone.
            lines = text.splitlines()
            return lines[0].strip()
        return box.input_value()

    def _combobox_in_column(self, header: str) -> Locator:
        """Return the enabled dropdown in the column with this header.

        Args:
            header: Column header, for example Status *.

        Returns:
            Playwright locator for that combobox.
        """
        return self._cell_by_header(header).locator(ENABLED_COMBOBOX_SELECTOR)

    def _cell_by_header(self, header: str) -> Locator:
        """Return this file's attribute cell under the named column.

        Args:
            header: Column header, for example Status *.

        Returns:
            Playwright locator for that gridcell.
        """
        return self.attribute_row().get_by_role(GRIDCELL_ROLE).nth(self._header_index(header))

    def _header_index(self, header: str) -> int:
        """Return the column index of a header in the attribute table.

        Args:
            header: Column header, for example Status *.

        Returns:
            Zero-based index, or 0 when the fake page has no header cells.
        """
        header_cell = self._attribute_header_row().get_by_role(
            GRIDCELL_ROLE,
            name=header,
            exact=True,
        )
        # inner_text is not always "Status *"; the role name is.
        index = header_cell.evaluate(HEADER_INDEX_SCRIPT)
        return int(index)

    def _attribute_header_row(self) -> Locator:
        """Return the header row that lists Project * / Status *.

        Returns:
            Playwright locator for that row.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=PROJECT_HEADER, exact=True)
        table = self._validator_dialog().get_by_role(TABLE_ROLE).filter(has=header)
        return table.get_by_role(ROW_ROLE).filter(has=header)

    def _validator_dialog(self) -> Locator:
        """Return the Upload files / Restore dialog that holds both tables.

        Returns:
            Playwright locator scoped to that dialog.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=FILE_NAME_HEADER, exact=True)
        return self.page.get_by_role(DIALOG_ROLE).filter(has=header)

    def _file_name_rows(self) -> Locator:
        """Return data rows in the File name table.

        Returns:
            Playwright locator for those rows.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=FILE_NAME_HEADER, exact=True)
        table = self._validator_dialog().get_by_role(TABLE_ROLE).filter(has=header)
        return table.get_by_role(ROW_ROLE).filter(has_not=header)

    def _attribute_rows(self) -> Locator:
        """Return data rows in the Project / attribute table.

        Returns:
            Playwright locator for those rows.
        """
        header = self.page.get_by_role(GRIDCELL_ROLE, name=PROJECT_HEADER, exact=True)
        table = self._validator_dialog().get_by_role(TABLE_ROLE).filter(has=header)
        return table.get_by_role(ROW_ROLE).filter(has_not=header)

    def _name_row_index(self) -> int:
        """Return this file's index in the File name table.

        Returns:
            Zero-based row index, or 0 when the fake page has no rows.
        """
        rows = self._file_name_rows()
        total = rows.count()
        if total == 0:
            # FakePage.count() is 0; live callers already saw the file name.
            return FIRST_ROW_INDEX
        for index in range(total):
            text = rows.nth(index).inner_text()
            if self.name in text:
                return index
        return FIRST_ROW_INDEX

    def _select_dropdown(self, box: Locator, value: str) -> None:
        """Open a portal dropdown and click the matching option.

        Args:
            box: The combobox to open.
            value: Option code. Matched at the start of the option name.
        """
        self._wait_listbox_closed()
        box.click()
        option = self.page.get_by_role(OPTION_ROLE, name=_option_name_pattern(value))
        try:
            option.click(timeout=LIST_REOPEN_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # The first click dismissed a leftover list; open Status/Volume again.
            box.click()
            option.click()
        self._wait_combobox_shows(box, value)
        self._wait_listbox_closed()

    def _select_searchable_dropdown(self, box: Locator, value: str) -> None:
        """Filter the open listbox and click the matching option.

        Args:
            box: The combobox to open.
            value: Option code, for example S0 or Ac_05.
        """
        self._wait_listbox_closed()
        box.click()
        listbox = self._open_listbox()
        # Classification is virtualized; type into the open combobox to narrow it.
        box.press_sequentially(value)
        self._option(listbox, value).click()
        self._wait_combobox_shows(box, value)
        self._wait_listbox_closed()

    def _open_listbox(self) -> Locator:
        """Return the open option list (portal), not leftover closed lists.

        Returns:
            Playwright locator for the listbox.
        """
        # The newest portal is last; earlier columns can leave a closed listbox in the DOM.
        return self.page.get_by_role(LISTBOX_ROLE).last

    def _option(self, listbox: Locator, value: str) -> Locator:
        """Return the option in this listbox whose name starts with the code.

        Args:
            listbox: The open option list.
            value: Option code, for example ZZ. Must not match zz inside mezzanine.

        Returns:
            Playwright locator for one option.
        """
        # Accessible name is "S0 Initial status"; inner_text is "S0\\nInitial status".
        return listbox.get_by_role(OPTION_ROLE, name=_option_name_pattern(value))

    def _wait_combobox_shows(self, box: Locator, value: str) -> None:
        """Wait until the combobox text starts with the selected code.

        Args:
            box: The combobox that was just set.
            value: Option code that must appear as a prefix.
        """
        expect(box).to_have_text(_option_text_pattern(value))

    def _wait_listbox_closed(self) -> None:
        """Wait until no option list is visible, so the next column can open."""
        expect(self.page.locator(VISIBLE_LISTBOX_SELECTOR)).to_have_count(
            CLOSED_LISTBOX_COUNT
        )


def _option_name_pattern(value: str) -> Pattern[str]:
    """Build a name pattern for the option accessible name.

    Args:
        value: Option code, for example ZZ or S0.

    Returns:
        Compiled pattern used by get_by_role(name=).
    """
    # Live name is "S0 Initial status", not "S0\\nInitial status".
    return re.compile(r"^" + re.escape(value) + r"\b", re.IGNORECASE)


def _option_text_pattern(value: str) -> Pattern[str]:
    """Build a text pattern that matches the code at the start of the option.

    Args:
        value: Option code, for example ZZ or S0.

    Returns:
        Compiled pattern used by expect().to_have_text().
    """
    return re.compile(r"^\s*" + re.escape(value), re.IGNORECASE)


def value_has_code(displayed: str, code: str) -> bool:
    """True when the control shows the code as a prefix.

    ACC may append the option title, for example S0Initial status.

    Args:
        displayed: Text read from the control.
        code: Expected attribute code, for example S0.

    Returns:
        True when displayed starts with the code, ignoring case.
    """
    if not displayed:
        return False
    return displayed.strip().upper().startswith(code.strip().upper())
