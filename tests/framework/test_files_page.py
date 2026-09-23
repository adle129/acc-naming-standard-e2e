"""FR-01: FilesPage opens the Files tool and enters a folder without opening ACC."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from components.folder_list import (
    FOLDER_ROLE,
    STEP_OPEN_FOLDER,
    TREE_GRID_NAME,
    TREE_GRID_ROLE,
)
from pages.files_page import (
    FILES_VIEW_URL_HINT,
    FILES_VIEW_URL_PATTERN,
    FOLDERS_TAB_NAME,
    TAB_ROLE,
    FilesPage,
)
from tests.framework.support import (
    FILES_PAGE_REL,
    FOLDER_LIST_REL,
    FORBIDDEN_SLEEP,
    FORBIDDEN_WAIT,
    REPO_ROOT,
    SAMPLE_ACCEPTANCE_TEST_NAME,
    SAMPLE_FOLDER_NAME,
    expected_files_url,
    read_text,
)
from utils.logger import STEP_RESULT_OK, configure_logging, reset_logging, set_test_name

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


class FakeLocator:
    """Stand-in Playwright locator. Records click() and nested get_by_role."""

    def __init__(self) -> None:
        self.click_count = 0
        self.role_calls: list[tuple[str, str]] = []
        self.last_child: FakeLocator | None = None

    def click(self) -> None:
        """Record that open_folder asked Playwright to click."""
        self.click_count = self.click_count + 1

    def get_by_role(self, role: str, name: str | None = None, **kwargs: object) -> FakeLocator:
        """Record a nested role, as FolderList does under the tree grid.

        Args:
            role: Accessible role requested under this locator.
            name: Visible name, for example the folder name.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A child fake locator.
        """
        self.role_calls.append((role, name or ""))
        child = FakeLocator()
        self.last_child = child
        return child


class FakePage:
    """Stand-in Playwright page for FilesPage and FolderList."""

    def __init__(self) -> None:
        self.goto_urls: list[str] = []
        self.role_calls: list[tuple[str, str]] = []
        self.last_locator = FakeLocator()

    def goto(self, url: str | None = None, **kwargs: object) -> None:
        """Record navigation the way BasePage.navigate_to calls it.

        Args:
            url: Absolute URL passed as the url= keyword.
            **kwargs: Ignored extra Playwright options.
        """
        self.goto_urls.append(url or "")

    def get_by_role(self, role: str, name: str | None = None, **kwargs: object) -> FakeLocator:
        """Record a role locator so tests can prove the folder name was used.

        Args:
            role: Accessible role requested by FolderList.
            name: Visible folder name.
            **kwargs: Ignored extra Playwright options.

        Returns:
            A fake locator that records click().
        """
        self.role_calls.append((role, name or ""))
        locator = FakeLocator()
        self.last_locator = locator
        return locator


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


def test_open_files_navigates_to_the_files_url(tmp_path: Path) -> None:
    """Prove open_files uses Settings.files_url() and does not hardcode a project.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    # The URL comes from config, the same helper the acceptance fixture will use.
    files_url = expected_files_url()
    files.open_files(files_url)
    assert page.goto_urls == [files_url]


def test_validate_uses_the_folders_url_hint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove FilesPage.validate checks the folders URL and the Folders tab.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        monkeypatch: Replaces expect so this test never launches a browser.
    """
    seen = {}

    class FakeAssertion:
        """Stand-in for Playwright assertions used by validate()."""

        def to_have_url(self, url: object) -> None:
            """Record the URL pattern FilesPage asked to verify.

            Args:
                url: The url= argument, expected to be FILES_VIEW_URL_PATTERN.
            """
            seen["url"] = url

        def to_be_visible(self) -> None:
            """Record that validate also waited for the Folders tab."""
            seen["visible"] = True

    def fake_expect(_target: object) -> FakeAssertion:
        """Return the fake assertion instead of a real Playwright expect.

        Args:
            _target: Page or locator handed to expect().

        Returns:
            A recorder for to_have_url and to_be_visible.
        """
        return FakeAssertion()

    monkeypatch.setattr("pages.base_page.expect", fake_expect)
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    # URL alone is not enough; the Folders tab must be on screen too.
    files.validate_files_page()
    assert seen["url"] == FILES_VIEW_URL_PATTERN
    assert FILES_VIEW_URL_HINT in FILES_VIEW_URL_PATTERN.pattern
    assert seen["visible"] is True
    assert (TAB_ROLE, FOLDERS_TAB_NAME) in page.role_calls


def test_open_folder_clicks_the_named_folder(tmp_path: Path, _isolated_logger: Path) -> None:
    """Prove open_folder clicks the locator built from the folder's visible name.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
        _isolated_logger: Run log path created by the autouse fixture.
    """
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    # SAMPLE_FOLDER_NAME matches ACC_FOLDER_NAME / Name-standard in the sample case.
    files.folder_list.open_folder(SAMPLE_FOLDER_NAME)
    # The tree is a grid; the folder name is a cell under that grid.
    assert page.role_calls == [(TREE_GRID_ROLE, TREE_GRID_NAME)]
    assert page.last_locator.role_calls == [(FOLDER_ROLE, SAMPLE_FOLDER_NAME)]
    assert page.last_locator.last_child is not None
    assert page.last_locator.last_child.click_count == 1
    text = read_text(_isolated_logger)
    assert STEP_OPEN_FOLDER.format(name=SAMPLE_FOLDER_NAME) in text
    assert STEP_RESULT_OK in text


def test_folder_locator_is_exposed_for_expect(tmp_path: Path) -> None:
    """Prove tests can expect() the folder locator without a raw page selector.

    Args:
        tmp_path: Isolated root forwarded to BasePage.
    """
    page = FakePage()
    files = FilesPage(page, root=tmp_path)
    # Product tests will write expect(files.folder_list.folder(name)).to_be_visible().
    locator = files.folder_list.folder(SAMPLE_FOLDER_NAME)
    assert locator is page.last_locator.last_child
    assert page.role_calls == [(TREE_GRID_ROLE, TREE_GRID_NAME)]
    assert page.last_locator.role_calls == [(FOLDER_ROLE, SAMPLE_FOLDER_NAME)]


def test_files_modules_have_no_sleeps() -> None:
    """Prove FilesPage and FolderList never use time.sleep or wait_for_timeout."""
    files_source = read_text(REPO_ROOT / FILES_PAGE_REL)
    folder_source = read_text(REPO_ROOT / FOLDER_LIST_REL)
    assert FORBIDDEN_SLEEP not in files_source
    assert FORBIDDEN_WAIT not in files_source
    assert FORBIDDEN_SLEEP not in folder_source
    assert FORBIDDEN_WAIT not in folder_source
