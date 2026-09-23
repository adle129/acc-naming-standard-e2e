"""FR-01: remaining pages expose basic actions without opening ACC."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from components.file_list import GRIDCELL_ROLE, NAME_HEADER, SHOWING_ITEMS_PREFIX, TABLE_ROLE
from components.app_nav import FILES_NAV_NAME, NAV_LINK_ROLE, STEP_OPEN_FILES_NAV
from components.file_row import STEP_SELECT_FILE
from components.file_toolbar import (
    BUTTON_ROLE,
    DELETED_ITEMS_BUTTON_NAME,
    STEP_DELETED_ITEMS,
    STEP_UPLOAD,
    UPLOAD_BUTTON_NAME,
)
from components.toast import TOAST_UPLOADED
from pages.deleted_items_page import (
    COLUMN_ROLE,
    DELETED_BY_COLUMN_NAME,
    DELETED_VIEW_URL_HINT,
    DELETED_VIEW_URL_PATTERN,
    DeletedItemsPage,
)
from pages.login_page import (
    EMAIL_INPUT_SELECTOR,
    PASSWORD_INPUT_SELECTOR,
    STEP_LOGIN,
    SUBMIT_BUTTON_SELECTOR,
    WHAT_USERNAME_BOX,
    LoginPage,
)
from pages.project_page import ProjectPage
from dialogs.upload_validator import UPLOAD_FILES_HEADING, UploadValidator
from components.validator_item import (
    OPTION_ROLE,
    STEP_FILL_PROJECT,
    STEP_SELECT_ITEM,
    STEP_SELECT_STATUS,
    STEP_SELECT_VOLUME,
    value_has_code,
)
from dialogs.validator_dialog import (
    DIALOG_ROLE,
    FILE_NAME_HEADER,
    STEP_CANCEL_VALIDATOR,
    STEP_CHECK_ERRORS_ONLY,
    STEP_EDIT_ALL,
    STEP_REMOVE_ALL,
    STEP_UNCHECK_ERRORS_ONLY,
    STEP_VALIDATOR_RESTORE,
    STEP_VALIDATOR_UPLOAD,
)
from pages.restore_files_page import (
    RESTORE_FILES_HEADING,
    STEP_ACCEPT_PREVIOUS,
    RestoreFilesPage,
)
from pages.upload_files_page import STEP_ADD_FILES, UploadFilesPage
from pages.base_page import STEP_VERIFY_VISIBLE
from pages.files_page import FilesPage
from tests.framework.support import (
    SAMPLE_ACCEPTANCE_TEST_NAME,
    SAMPLE_CLASSIFICATION_VALUE,
    SAMPLE_CUSTOM_FIELDS_VALUE,
    SAMPLE_ENV_PASSWORD,
    SAMPLE_ENV_USERNAME,
    SAMPLE_FILE_NAME,
    SAMPLE_ITEM_COUNT,
    SAMPLE_LEVEL_VALUE,
    SAMPLE_SHOWING_TWO_ITEMS,
    SAMPLE_NUMBER_VALUE,
    SAMPLE_OPEN_URL,
    SAMPLE_PROJECT_VALUE,
    SAMPLE_REVISION_VALUE,
    SAMPLE_ROLE_VALUE,
    SAMPLE_STATUS_VALUE,
    SAMPLE_TYPE_VALUE,
    SAMPLE_VOLUME_VALUE,
    SAMPLE_ORIGINATOR_VALUE,
    SAMPLE_UPLOAD_FILE_NAME,
    read_text,
)
from utils.test_data import NamingAttributes
from utils.logger import (
    SECRET_MASK as LOGGER_SECRET_MASK,
    STEP_RESULT_OK,
    configure_logging,
    reset_logging,
    set_test_name,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


class FakeLocator:
    """Stand-in Playwright locator. Records click/fill and nested get_by_role."""

    def __init__(self) -> None:
        self.click_count = 0
        self.fill_values: list[str] = []
        self.child_roles: list[str] = []
        self.nth_indexes: list[int] = []
        self.press_keys: list[str] = []
        self.last_child: FakeLocator | None = None
        self.inner_text_value = ""
        self.input_value_text = ""
        self.page_fills: list[str] | None = None
        self.visible = False

    def click(self, **kwargs: object) -> None:
        """Record a click from a page-object action.

        Args:
            **kwargs: Ignored Playwright options such as timeout=.
        """
        self.click_count = self.click_count + 1

    @property
    def first(self) -> FakeLocator:
        """Playwright Locator.first. The fake has only one match.

        Returns:
            This locator.
        """
        return self

    @property
    def last(self) -> FakeLocator:
        """Playwright Locator.last. The fake has only one match.

        Returns:
            This locator.
        """
        return self

    def is_visible(self, **kwargs: object) -> bool:
        """Playwright Locator.is_visible(). Default hidden so dismiss is a no-op.

        Args:
            **kwargs: Ignored Playwright options such as timeout=.

        Returns:
            The visible flag set on this locator.
        """
        return self.visible

    def count(self) -> int:
        """Playwright Locator.count(). Zero so username_box falls back to textbox.

        Returns:
            Always 0 for the fake.
        """
        return 0

    def fill(self, value: str) -> None:
        """Record a fill from LoginPage.

        Args:
            value: Text typed into the field.
        """
        self.fill_values.append(value)
        if self.page_fills is not None:
            self.page_fills.append(value)

    def check(self) -> None:
        """Record a checkbox check, as errors-only does."""
        self.click_count = self.click_count + 1

    def uncheck(self) -> None:
        """Record a checkbox uncheck, as errors-only does."""
        self.click_count = self.click_count + 1

    def press_sequentially(self, text: str, **kwargs: object) -> None:
        """Record typed text on this locator, as Status/Classification do.

        Args:
            text: Characters sent to the focused control.
            **kwargs: Ignored Playwright options such as delay=.
        """
        self.fill_values.append(text)
        if self.page_fills is not None:
            self.page_fills.append(text)

    def press(self, key: str) -> None:
        """Record a key press on this locator.

        Args:
            key: Key name, for example Tab.
        """
        self.press_keys.append(key)

    def inner_text(self) -> str:
        """Return text configured by the fake page.

        Returns:
            The inner_text_value set on this locator.
        """
        return self.inner_text_value

    def input_value(self) -> str:
        """Return the input value configured by the fake page.

        Returns:
            The input_value_text set on this locator.
        """
        return self.input_value_text

    def _child(self) -> FakeLocator:
        """Build a nested locator that keeps the same configured text.

        Returns:
            A new fake locator.
        """
        child = FakeLocator()
        child.inner_text_value = self.inner_text_value
        child.input_value_text = self.input_value_text
        child.page_fills = self.page_fills
        child.visible = self.visible
        self.last_child = child
        return child

    def get_by_role(self, role: str, name: str | None = None, **kwargs: object) -> FakeLocator:
        """Return a nested locator, as FileRow.checkbox() does.

        Args:
            role: Accessible role requested under this locator.
            name: Optional accessible name.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A new fake locator.
        """
        self.child_roles.append(role)
        return self._child()

    def locator(self, selector: str) -> FakeLocator:
        """Return a nested CSS locator, as ValidatorDialog does for comboboxes.

        Args:
            selector: CSS selector under this locator.

        Returns:
            A new fake locator.
        """
        return self._child()

    def nth(self, index: int) -> FakeLocator:
        """Return a positional match, as ValidatorDialog does for comboboxes.

        Args:
            index: Zero-based index passed to Locator.nth().

        Returns:
            A new fake locator.
        """
        self.nth_indexes.append(index)
        return self._child()

    def filter(self, **kwargs: object) -> FakeLocator:
        """Playwright Locator.filter. The fake has one match, so return self.

        Args:
            **kwargs: Ignored Playwright filter options such as has=.

        Returns:
            This locator.
        """
        return self

    def or_(self, _other: FakeLocator) -> FakeLocator:
        """Playwright Locator.or_. The fake has one match, so return self.

        Args:
            _other: Unused alternate locator.

        Returns:
            This locator.
        """
        return self

    def evaluate(self, expression: str) -> int:
        """Playwright Locator.evaluate. Fake pages have one header cell.

        Args:
            expression: Ignored JS used live to read the column index.

        Returns:
            Always 0 for the fake.
        """
        return 0


class FakeKeyboard:
    """Stand-in Playwright keyboard for Tab / ArrowDown after a field fill."""

    def __init__(self) -> None:
        self.presses: list[str] = []

    def press(self, key: str) -> None:
        """Record a page-level key press.

        Args:
            key: Key name, for example Enter.
        """
        self.presses.append(key)

    def type(self, text: str) -> None:
        """Record typed text into the focused control.

        Args:
            text: Characters sent to the page.
        """
        self.presses.append(text)


class FakePage:
    """Stand-in Playwright page for every remaining page object."""

    def __init__(self) -> None:
        self.goto_urls: list[str] = []
        self.role_calls: list[tuple[str, str]] = []
        self.label_calls: list[str] = []
        self.text_calls: list[str] = []
        self.last_locator = FakeLocator()
        self.locator_calls: list[str] = []
        self.keyboard = FakeKeyboard()
        self.inner_text_value = ""
        self.input_value_text = ""
        self.fill_values: list[str] = []
        self.locator_visible = False
        self.timeout_ms = 0

    def set_default_timeout(self, timeout: float) -> None:
        """Record the page timeout the live fixture applies.

        Args:
            timeout: Milliseconds passed to page.set_default_timeout().
        """
        self.timeout_ms = timeout

    def wait_for_url(self, url: object, **kwargs: object) -> None:
        """No-op stand-in for Playwright wait_for_url after login.

        Args:
            url: Pattern or predicate LoginPage waits on.
            **kwargs: Ignored extra Playwright options.
        """
        return None

    def locator(self, selector: str) -> FakeLocator:
        """Record a CSS locator used by LoginPage.

        Args:
            selector: CSS selector string.

        Returns:
            A fake locator.
        """
        self.locator_calls.append(selector)
        locator = FakeLocator()
        locator.inner_text_value = self.inner_text_value
        locator.input_value_text = self.input_value_text
        locator.page_fills = self.fill_values
        locator.visible = self.locator_visible
        self.last_locator = locator
        return locator

    def goto(self, url: str | None = None, **kwargs: object) -> None:
        """Record navigation.

        Args:
            url: Absolute URL passed as url=.
            **kwargs: Ignored extra Playwright options.
        """
        self.goto_urls.append(url or "")

    def get_by_role(self, role: str, name: str | None = None, **kwargs: object) -> FakeLocator:
        """Record a role locator.

        Args:
            role: Accessible role.
            name: Accessible name.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A fake locator.
        """
        self.role_calls.append((role, name or ""))
        locator = FakeLocator()
        locator.inner_text_value = self.inner_text_value
        locator.input_value_text = self.input_value_text
        locator.page_fills = self.fill_values
        locator.visible = self.locator_visible
        self.last_locator = locator
        return locator

    def get_by_label(self, label: str, **kwargs: object) -> FakeLocator:
        """Record a labelled field.

        Args:
            label: Accessible label.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A fake locator.
        """
        self.label_calls.append(label)
        locator = FakeLocator()
        locator.inner_text_value = self.inner_text_value
        locator.input_value_text = self.input_value_text
        locator.page_fills = self.fill_values
        locator.visible = self.locator_visible
        self.last_locator = locator
        return locator

    def get_by_text(self, text: str, **kwargs: object) -> FakeLocator:
        """Record a text locator used by Toast.

        Args:
            text: Visible toast text.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A fake locator.
        """
        self.text_calls.append(text)
        locator = FakeLocator()
        locator.inner_text_value = self.inner_text_value
        locator.input_value_text = self.input_value_text
        locator.page_fills = self.fill_values
        locator.visible = self.locator_visible
        self.last_locator = locator
        return locator


def _silence_combobox_expect(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace validator expect() so dropdown set_* tests stay off-browser.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """

    class FakeAssertion:
        """Stand-in for Playwright LocatorAssertions.to_have_text."""

        def to_have_text(self, value: object) -> None:
            """Ignore the written-back combobox text on a FakeLocator."""
            return None

        def to_have_count(self, value: object) -> None:
            """Ignore the closed-listbox wait on a FakeLocator."""
            return None

    def fake_expect(_locator: object) -> FakeAssertion:
        """Return the fake assertion.

        Args:
            _locator: Combobox handed to expect() after a select.

        Returns:
            A recorder that accepts to_have_text.
        """
        return FakeAssertion()

    # set_* waits for the box text; FakeLocator is not a real Playwright node.
    monkeypatch.setattr("components.validator_item.expect", fake_expect)


@pytest.fixture(autouse=True)
def _isolated_logger(tmp_path: Path) -> Iterator[Path]:
    """Give each test a fresh logger under tmp_path.

    Args:
        tmp_path: Pytest temp directory used as the log directory.

    Yields:
        Path of the run log file created for this test.
    """
    reset_logging()
    log_path = configure_logging(log_dir=tmp_path)
    set_test_name(SAMPLE_ACCEPTANCE_TEST_NAME)
    yield log_path
    reset_logging()


def test_login_fills_username_and_password_without_logging_the_secret(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove LoginPage.login types both fields and redacts the password in the log.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    login = LoginPage(page, root=tmp_path)
    login.login(SAMPLE_ENV_USERNAME, SAMPLE_ENV_PASSWORD)
    # Email, password, and the form submit use input/button types, not English labels.
    assert EMAIL_INPUT_SELECTOR in page.locator_calls
    assert PASSWORD_INPUT_SELECTOR in page.locator_calls
    assert SUBMIT_BUTTON_SELECTOR in page.locator_calls
    text = read_text(_isolated_logger)
    assert STEP_LOGIN.format(username=SAMPLE_ENV_USERNAME, password=LOGGER_SECRET_MASK) in text
    # The plaintext password must not appear in the step log.
    assert SAMPLE_ENV_PASSWORD not in text
    assert STEP_RESULT_OK in text


def test_login_validate_checks_the_email_field(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove LoginPage.validate waits for the email field, not a URL.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so this test never launches a browser.
    """
    seen = {}

    class FakeAssertion:
        """Stand-in for Playwright LocatorAssertions."""

        def to_be_visible(self) -> None:
            """Record that validate asked Playwright to wait for visibility."""
            seen["visible"] = True

    def fake_expect(locator: FakeLocator) -> FakeAssertion:
        """Return the fake assertion.

        Args:
            locator: The email field LoginPage handed to expect().

        Returns:
            A recorder for to_be_visible.
        """
        seen["locator"] = locator
        return FakeAssertion()

    monkeypatch.setattr("pages.base_page.expect", fake_expect)
    page = FakePage()
    login = LoginPage(page, root=tmp_path)
    login.validate_login_page()
    assert page.locator_calls == [EMAIL_INPUT_SELECTOR]
    assert seen["visible"] is True
    text = read_text(_isolated_logger)
    assert STEP_VERIFY_VISIBLE.format(what=WHAT_USERNAME_BOX) in text


def test_project_page_opens_files_from_nav(tmp_path: Path, _isolated_logger: Path) -> None:
    """Prove ProjectPage jumps to Files through AppNav.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    project = ProjectPage(page, root=tmp_path)
    project.open_project(SAMPLE_OPEN_URL)
    assert page.goto_urls == [SAMPLE_OPEN_URL]
    project.open_files_tool()
    assert page.role_calls == [(NAV_LINK_ROLE, FILES_NAV_NAME)]
    assert page.last_locator.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_OPEN_FILES_NAV in text


def test_project_validate_checks_files_nav(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove ProjectPage.validate uses the Files nav link as the page marker.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        monkeypatch: Replaces expect so this test never launches a browser.
    """
    seen = {}

    class FakeAssertion:
        """Stand-in for Playwright LocatorAssertions."""

        def to_be_visible(self) -> None:
            """Record that validate asked Playwright to wait for visibility."""
            seen["visible"] = True

    def fake_expect(_locator: FakeLocator) -> FakeAssertion:
        """Return the fake assertion.

        Args:
            _locator: Unused Files-nav locator.

        Returns:
            A recorder for to_be_visible.
        """
        return FakeAssertion()

    monkeypatch.setattr("pages.base_page.expect", fake_expect)
    page = FakePage()
    project = ProjectPage(page, root=tmp_path)
    project.validate_project_page()
    assert page.role_calls == [(NAV_LINK_ROLE, FILES_NAV_NAME)]
    assert seen["visible"] is True


def test_files_toolbar_and_row_and_toast(tmp_path: Path, _isolated_logger: Path) -> None:
    """Prove FilesPage composes toolbar, row, and toast.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    files.toolbar.upload()
    assert page.role_calls[-1] == (BUTTON_ROLE, UPLOAD_BUTTON_NAME)
    row = files.row(SAMPLE_FILE_NAME)
    row.select()
    # select() finds the row by the visible file name on the Name table.
    assert SAMPLE_FILE_NAME in page.text_calls
    toast = files.toast.message(TOAST_UPLOADED)
    assert TOAST_UPLOADED in page.text_calls
    assert toast is page.last_locator
    text = read_text(_isolated_logger)
    assert STEP_UPLOAD in text
    assert STEP_SELECT_FILE in text


def test_deleted_items_view_and_return_to_files(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove DeletedItemsPage checks moduleId=deleted and can return to Files.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so verify_url does not launch a browser.
    """
    seen = {}

    class FakeAssertion:
        """Stand-in for Playwright PageAssertions."""

        def to_have_url(self, url: object) -> None:
            """Record the deleted-view pattern.

            Args:
                url: The url= argument from verify_url.
            """
            seen["url"] = url

        def to_be_visible(self) -> None:
            """Record that validate also waited for the Deleted by column."""
            seen["visible"] = True

    def fake_expect(_page: FakePage) -> FakeAssertion:
        """Return the fake assertion.

        Args:
            _page: Unused page object.

        Returns:
            A recorder for to_have_url.
        """
        return FakeAssertion()

    monkeypatch.setattr("pages.base_page.expect", fake_expect)
    page = FakePage()
    deleted = DeletedItemsPage(page, root=tmp_path)
    deleted.validate_deleted_items_page()
    assert seen["url"] == DELETED_VIEW_URL_PATTERN
    assert DELETED_VIEW_URL_HINT in DELETED_VIEW_URL_PATTERN.pattern
    assert seen["visible"] is True
    assert (COLUMN_ROLE, DELETED_BY_COLUMN_NAME) in page.role_calls
    deleted.toolbar.open_deleted_items()
    assert page.role_calls[-1] == (BUTTON_ROLE, DELETED_ITEMS_BUTTON_NAME)
    deleted.return_to_files()
    assert page.role_calls[-1] == (NAV_LINK_ROLE, FILES_NAV_NAME)
    text = read_text(_isolated_logger)
    assert STEP_DELETED_ITEMS in text
    assert STEP_OPEN_FILES_NAV in text


def test_upload_validator_heading_is_visible_text(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove the validator finds Upload files by text and can Cancel.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    validator = UploadValidator(page, root=tmp_path)
    # Live ACC does not expose a heading role for this title.
    heading = validator.heading()
    assert heading is page.last_locator
    assert page.text_calls[-1] == UPLOAD_FILES_HEADING
    validator.click_cancel_button()
    # Cancel is scoped to the dialog so it does not hit another page Cancel.
    assert page.role_calls[-1] == (DIALOG_ROLE, "")
    assert BUTTON_ROLE in page.last_locator.child_roles
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_CANCEL_VALIDATOR in text


def test_upload_files_item_sets_project(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove item.set_project types into the Project textbox on that row.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    # Values come from support; the method must not hardcode hw472.
    item.set_project(SAMPLE_PROJECT_VALUE)
    # Fields live on the attribute table; the fill is recorded on the page.
    assert SAMPLE_PROJECT_VALUE in page.fill_values
    text = read_text(_isolated_logger)
    assert STEP_FILL_PROJECT.format(value=SAMPLE_PROJECT_VALUE) in text


def test_upload_files_item_sets_volume(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove item.set_volume clicks the option inside the open listbox.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so to_have_text does not launch a browser.
    """
    # set_volume waits for the combobox text after the option click.
    _silence_combobox_expect(monkeypatch)
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    item = upload_files.item(SAMPLE_UPLOAD_FILE_NAME)
    volume = item.volume_box()
    assert volume is not None
    item.set_volume(SAMPLE_VOLUME_VALUE)
    # Options are clicked by accessible name so a leftover listbox is not used.
    option_roles = []
    for role, _name in page.role_calls:
        if role == OPTION_ROLE:
            option_roles.append(role)
    assert option_roles
    text = read_text(_isolated_logger)
    assert STEP_SELECT_VOLUME.format(value=SAMPLE_VOLUME_VALUE) in text


def test_upload_files_item_sets_status(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove item.set_status clicks the option inside the open listbox.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so to_have_text does not launch a browser.
    """
    # set_status waits for the combobox text after the option click.
    _silence_combobox_expect(monkeypatch)
    page = FakePage()
    item = UploadFilesPage(page, root=tmp_path).item(SAMPLE_UPLOAD_FILE_NAME)
    item.set_status(SAMPLE_STATUS_VALUE)
    # Status options use the accessible name S0 Initial status.
    assert page.role_calls[-1][0] == OPTION_ROLE
    text = read_text(_isolated_logger)
    assert STEP_SELECT_STATUS.format(value=SAMPLE_STATUS_VALUE) in text


def test_upload_files_item_set_attributes_uses_each_field(
    tmp_path: Path,
    _isolated_logger: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove set_attributes walks the 10 NamingAttributes fields on one row.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
        monkeypatch: Replaces expect so dropdown to_have_text stays off-browser.
    """
    # Dropdown fields wait for the written-back text after each option click.
    _silence_combobox_expect(monkeypatch)
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    attributes = NamingAttributes(
        project=SAMPLE_PROJECT_VALUE,
        volume=SAMPLE_VOLUME_VALUE,
        level=SAMPLE_LEVEL_VALUE,
        type=SAMPLE_TYPE_VALUE,
        role=SAMPLE_ROLE_VALUE,
        number=SAMPLE_NUMBER_VALUE,
        status=SAMPLE_STATUS_VALUE,
        revision=SAMPLE_REVISION_VALUE,
        classification=SAMPLE_CLASSIFICATION_VALUE,
        custom_fields=SAMPLE_CUSTOM_FIELDS_VALUE,
    )
    upload_files.item(SAMPLE_UPLOAD_FILE_NAME).set_attributes(attributes)
    # Project, Classification filter, and custom fields fill; custom fields is last.
    assert SAMPLE_PROJECT_VALUE in page.fill_values
    assert SAMPLE_CLASSIFICATION_VALUE in page.fill_values
    assert page.fill_values[-1] == SAMPLE_CUSTOM_FIELDS_VALUE
    text = read_text(_isolated_logger)
    assert STEP_FILL_PROJECT.format(value=SAMPLE_PROJECT_VALUE) in text
    assert STEP_SELECT_VOLUME.format(value=SAMPLE_VOLUME_VALUE) in text


def test_files_page_reads_item_count(tmp_path: Path) -> None:
    """Prove FilesPage.get_items_count parses the Showing N items label.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    # The fake locator returns this text from inner_text().
    page.inner_text_value = SAMPLE_SHOWING_TWO_ITEMS
    files = FilesPage(page, root=tmp_path)
    assert files.get_items_count() == SAMPLE_ITEM_COUNT
    # Acceptance uses the same label to prove one upload changed Showing N.
    files.verify_items_count(SAMPLE_ITEM_COUNT)
    assert page.text_calls[-1] == SHOWING_ITEMS_PREFIX


def test_deleted_items_page_reads_item_count(tmp_path: Path) -> None:
    """Prove DeletedItemsPage.get_items_count uses the same Showing label.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    page.inner_text_value = SAMPLE_SHOWING_TWO_ITEMS
    deleted = DeletedItemsPage(page, root=tmp_path)
    assert deleted.get_items_count() == SAMPLE_ITEM_COUNT
    # Restore checks this count dropped by one for this test's file only.
    deleted.verify_items_count(SAMPLE_ITEM_COUNT)
    assert page.text_calls[-1] == SHOWING_ITEMS_PREFIX


def test_files_page_item_list_uses_the_name_table(tmp_path: Path) -> None:
    """Prove get_item_list looks up the Name column table.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    # FakeLocator.count() is 0, so the list is empty; the lookup still runs.
    names = files.get_item_list()
    assert names == []
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, NAME_HEADER) in page.role_calls


def test_deleted_items_page_item_list_uses_the_name_table(tmp_path: Path) -> None:
    """Prove Deleted items get_item_list uses the same Name column table.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    deleted = DeletedItemsPage(page, root=tmp_path)
    names = deleted.get_item_list()
    assert names == []
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, NAME_HEADER) in page.role_calls


def test_upload_files_page_reads_item_count(tmp_path: Path) -> None:
    """Prove UploadFilesPage.get_items_count reads the File name table rows.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    # FakeLocator.count() is 0, so the count is empty; the lookup still runs.
    assert upload_files.get_items_count() == 0
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, FILE_NAME_HEADER) in page.role_calls


def test_upload_files_page_item_list_uses_the_file_name_table(tmp_path: Path) -> None:
    """Prove get_item_list looks up the File name column table.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    names = upload_files.get_item_list()
    assert names == []
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, FILE_NAME_HEADER) in page.role_calls


def test_upload_files_item_get_project_reads_the_textbox(tmp_path: Path) -> None:
    """Prove item.get_project reads input_value() on that row.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    # The fake textbox returns this from input_value().
    page.input_value_text = SAMPLE_PROJECT_VALUE
    item = UploadFilesPage(page, root=tmp_path).item(SAMPLE_UPLOAD_FILE_NAME)
    assert item.get_project() == SAMPLE_PROJECT_VALUE


def test_upload_files_item_get_volume_reads_the_combobox(tmp_path: Path) -> None:
    """Prove item.get_volume reads the dropdown text on that row.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    # The fake combobox returns this from inner_text().
    page.inner_text_value = SAMPLE_VOLUME_VALUE
    item = UploadFilesPage(page, root=tmp_path).item(SAMPLE_UPLOAD_FILE_NAME)
    assert item.get_volume() == SAMPLE_VOLUME_VALUE


def test_upload_files_item_get_originator_reads_the_combobox(tmp_path: Path) -> None:
    """Prove get_originator is available even though it is not in NamingAttributes.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    page.inner_text_value = SAMPLE_ORIGINATOR_VALUE
    item = UploadFilesPage(page, root=tmp_path).item(SAMPLE_UPLOAD_FILE_NAME)
    assert item.get_originator() == SAMPLE_ORIGINATOR_VALUE


def test_upload_files_item_get_attributes_reads_text_and_dropdowns(
    tmp_path: Path,
) -> None:
    """Prove get_attributes fills NamingAttributes from this row's fields.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    # Text boxes share one fake input value; dropdowns share one fake inner text.
    page.input_value_text = SAMPLE_PROJECT_VALUE
    page.inner_text_value = SAMPLE_VOLUME_VALUE
    item = UploadFilesPage(page, root=tmp_path).item(SAMPLE_UPLOAD_FILE_NAME)
    attributes = item.get_attributes()
    assert attributes.project == SAMPLE_PROJECT_VALUE
    assert attributes.number == SAMPLE_PROJECT_VALUE
    assert attributes.volume == SAMPLE_VOLUME_VALUE
    assert attributes.status == SAMPLE_VOLUME_VALUE


def test_value_has_code_accepts_a_title_suffix() -> None:
    """Prove a dropdown that appends a title still matches the code."""
    # Live ACC may concatenate the code and the option title.
    displayed = SAMPLE_STATUS_VALUE + SAMPLE_TYPE_VALUE
    assert value_has_code(displayed, SAMPLE_STATUS_VALUE) is True
    # An empty control must not match a real code.
    assert value_has_code("", SAMPLE_VOLUME_VALUE) is False


def test_upload_files_page_select_item_ticks_the_row_checkbox(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove select_item finds the file row and clicks its checkbox.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    upload_files.select_item(SAMPLE_UPLOAD_FILE_NAME)
    # The checkbox is on the File name table inside the validator dialog.
    assert (DIALOG_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, FILE_NAME_HEADER) in page.role_calls
    assert SAMPLE_UPLOAD_FILE_NAME in page.text_calls
    text = read_text(_isolated_logger)
    assert STEP_SELECT_ITEM in text


def test_upload_files_page_clicks_upload_and_cancel(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove UploadFilesPage click_upload_button and click_cancel_button hit the footer.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    upload_files.click_upload_button()
    # Upload is scoped to the dialog so it does not hit the Files toolbar Upload.
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    upload_files.click_cancel_button()
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_VALIDATOR_UPLOAD in text
    assert STEP_CANCEL_VALIDATOR in text


def test_upload_files_page_clicks_remaining_chrome(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove Edit all, Remove all, Add files, and errors-only are wired.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    upload_files = UploadFilesPage(page, root=tmp_path)
    # These clicks must not be inlined in product tests.
    upload_files.click_edit_all_button()
    upload_files.click_remove_all_button()
    upload_files.click_add_files_button()
    upload_files.check_errors_only()
    upload_files.uncheck_errors_only()
    text = read_text(_isolated_logger)
    assert STEP_EDIT_ALL in text
    assert STEP_REMOVE_ALL in text
    assert STEP_ADD_FILES in text
    assert STEP_CHECK_ERRORS_ONLY in text
    assert STEP_UNCHECK_ERRORS_ONLY in text


def test_restore_files_heading_is_visible_text(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove RestoreFilesPage finds Restore files by text and can Cancel.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    restore = RestoreFilesPage(page, root=tmp_path)
    # Live ACC does not expose a Restore files title; the awaiting line is unique.
    heading = restore.heading()
    assert heading is page.last_locator
    assert page.text_calls[-1] == RESTORE_FILES_HEADING
    restore.click_cancel_button()
    # Cancel is scoped to the dialog so it does not hit Deleted items Cancel.
    assert page.role_calls[-1] == (DIALOG_ROLE, "")
    assert BUTTON_ROLE in page.last_locator.child_roles
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_CANCEL_VALIDATOR in text


def test_restore_files_page_reads_item_count(tmp_path: Path) -> None:
    """Prove RestoreFilesPage.get_items_count reads the File name table rows.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    restore = RestoreFilesPage(page, root=tmp_path)
    # FakeLocator.count() is 0, so the count is empty; the lookup still runs.
    assert restore.get_items_count() == 0
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, FILE_NAME_HEADER) in page.role_calls


def test_restore_files_page_item_list_uses_the_file_name_table(tmp_path: Path) -> None:
    """Prove Restore get_item_list looks up the File name column table.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    restore = RestoreFilesPage(page, root=tmp_path)
    names = restore.get_item_list()
    assert names == []
    assert (TABLE_ROLE, "") in page.role_calls
    assert (GRIDCELL_ROLE, FILE_NAME_HEADER) in page.role_calls


def test_restore_files_page_clicks_restore_and_accept(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove RestoreFilesPage clicks Restore and Accept on the shared chrome.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    restore = RestoreFilesPage(page, root=tmp_path)
    # Accept is restore-only; count is 0 on the fake so the loop is a no-op.
    restore.accept_previous_version()
    restore.click_restore_button()
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_ACCEPT_PREVIOUS in text
    assert STEP_VALIDATOR_RESTORE in text


def test_restore_files_page_clicks_shared_chrome(
    tmp_path: Path,
    _isolated_logger: Path,
) -> None:
    """Prove RestoreFilesPage inherits Edit all, Remove all, and errors-only.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    restore = RestoreFilesPage(page, root=tmp_path)
    # These locators live on ValidatorDialog so Upload and Restore share them.
    restore.click_edit_all_button()
    restore.click_remove_all_button()
    restore.check_errors_only()
    restore.uncheck_errors_only()
    text = read_text(_isolated_logger)
    assert STEP_EDIT_ALL in text
    assert STEP_REMOVE_ALL in text
    assert STEP_CHECK_ERRORS_ONLY in text
    assert STEP_UNCHECK_ERRORS_ONLY in text

