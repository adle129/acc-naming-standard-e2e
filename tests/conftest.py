"""Session login plus one function-scoped live ACC fixture.

Framework tests do not request page or live_acc, so they never open a browser.
"""

from __future__ import annotations

from collections.abc import Generator, Iterator

import pytest
from playwright.sync_api import Browser, Page

from tests.live_support import LiveAcc
from utils.auth import (
    AUTH_STATE_FILE_NAME,
    ensure_storage_state,
    read_storage_state,
    with_storage_state,
)
from utils.config import get_settings, safe_settings_summary
from utils.logger import (
    PHASE_CLEANUP,
    PHASE_CLEANUP_NAMES,
    PHASE_CLEANUP_NONE,
    PHASE_CONFIG,
    PHASE_PREPARE,
    PHASE_PYTEST,
    PHASE_SESSION_AUTH_LOGIN,
    PHASE_SESSION_AUTH_REUSE,
    PHASE_TEST_END,
    PHASE_TEST_NAME,
    PHASE_TEST_START,
    STEP_RESULT_FAIL,
    STEP_RESULT_OK,
    STEP_RESULT_START,
    log_phase,
    phase_scope,
    short_test_name,
)

# pytest-playwright / pytest-rerunfailures option dest names.
OPTION_HEADED = "headed"
OPTION_SLOWMO = "slowmo"
OPTION_RERUNS = "reruns"
OPTION_DEFAULT_FALSE = False
OPTION_DEFAULT_ZERO = 0


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[None],
) -> Generator[None, None, None]:
    """Store setup/call/teardown reports on the item for live_acc TEST END.

    Args:
        item: The pytest item being run.
        call: The current setup, call, or teardown phase.

    Yields:
        Control to other hookimpls, then attaches the finished report.
    """
    # Other plugins (reruns) must finish so we log the final OK or FAIL.
    outcome = yield
    # live_acc reads rep_call after the test body.
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


def _pytest_option(pytestconfig: pytest.Config, name: str, default: object) -> object:
    """Read a CLI option, or default when the plugin is not registered.

    Args:
        pytestconfig: Pytest config for this session.
        name: Option dest, for example headed.
        default: Value used when getoption raises.

    Returns:
        The option value or default.
    """
    try:
        return pytestconfig.getoption(name)
    except ValueError:
        return default


def _call_result(request: pytest.FixtureRequest) -> str:
    """Return OK or FAIL from the test-body report when it exists.

    Args:
        request: The live_acc fixture request.

    Returns:
        STEP_RESULT_OK, STEP_RESULT_FAIL, or START when the body never ran.
    """
    report = getattr(request.node, "rep_call", None)
    if report is None:
        # prepare failed; the test body did not start.
        return STEP_RESULT_START
    if report.failed:
        return STEP_RESULT_FAIL
    return STEP_RESULT_OK


def _cleanup_names_text(acc: LiveAcc) -> str:
    """Return the remembered Files-list names for the cleanup log line.

    Args:
        acc: The live helper after the test body, before cleanup.

    Returns:
        Comma-separated names, or PHASE_CLEANUP_NONE.
    """
    if not acc.uploaded_names:
        return PHASE_CLEANUP_NONE
    return ", ".join(acc.uploaded_names)


@pytest.fixture(scope="session")
def storage_state(browser: Browser) -> str:
    """Log in once per pytest session and return the auth_state.json path.

    Reuses a valid cache so later upload tests skip Autodesk ID (and Arkose).
    Tests do not call LoginPage; this fixture is the only login entry.

    Args:
        browser: Session-scoped Playwright browser from pytest-playwright.

    Returns:
        Path string passed to browser_context_args as storage_state.
    """
    # Settings come from .env + credentials.json; never hardcode the password.
    settings = get_settings()
    # Read the cache first so the log can say reuse versus a fresh login.
    cached = read_storage_state()
    will_reuse = cached is not None and not settings.show_login
    path = ensure_storage_state(browser, settings)
    if will_reuse:
        # Cached cookies; Autodesk ID and Arkose are not shown.
        log_phase(
            PHASE_SESSION_AUTH_REUSE.format(file=AUTH_STATE_FILE_NAME),
            result=STEP_RESULT_OK,
        )
    else:
        # LoginPage ran (missing cache or ACC_SHOW_LOGIN=true).
        log_phase(
            PHASE_SESSION_AUTH_LOGIN.format(file=AUTH_STATE_FILE_NAME),
            result=STEP_RESULT_OK,
        )
    return str(path)


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict,
    storage_state: str,
) -> dict:
    """Give every product page the session cookies and an English locale.

    Args:
        browser_context_args: Default context args from pytest-playwright.
        storage_state: Path returned by the storage_state fixture.

    Returns:
        Context args with storage_state set. Framework tests never request page.
    """
    # Copy then assign so a reviewer can see the one key this fixture adds.
    return with_storage_state(browser_context_args, storage_state)


@pytest.fixture
def live_acc(page: Page, request: pytest.FixtureRequest) -> Iterator[LiveAcc]:
    """Open the naming folder for one live test, then delete leftovers from Files.

    Not autouse: framework tests must not request page. Each live test asks for
    live_acc. Session login stays in storage_state.

    Args:
        page: Function-scoped Playwright page (new context per test).
        request: Used to read pytest CLI options and the call report.

    Yields:
        LiveAcc bound to that page, already on the naming-standard folder.
    """
    settings = get_settings()
    # Strip [chromium] so the log shows the pytest function name as the case name.
    test_name = short_test_name()
    # TEST START includes the name so it is not only in the third column.
    log_phase(PHASE_TEST_START.format(name=test_name), result=STEP_RESULT_START)
    # A dedicated TEST NAME line is easy to search for in a long run log.
    log_phase(PHASE_TEST_NAME.format(name=test_name))
    # Config never includes the password; see safe_settings_summary.
    log_phase(PHASE_CONFIG.format(details=safe_settings_summary(settings)))
    # headed / slowmo / reruns come from this pytest process, not from .env.
    log_phase(
        PHASE_PYTEST.format(
            headed=_pytest_option(request.config, OPTION_HEADED, OPTION_DEFAULT_FALSE),
            slowmo=_pytest_option(request.config, OPTION_SLOWMO, OPTION_DEFAULT_ZERO),
            reruns=_pytest_option(request.config, OPTION_RERUNS, OPTION_DEFAULT_ZERO),
        )
    )
    acc = LiveAcc(page, settings)
    with phase_scope(PHASE_PREPARE):
        # Open Files, open the naming folder, delete leftover generated uploads.
        acc.prepare()
    try:
        yield acc
    finally:
        # Remembered names are the files this test created, not demo rows.
        log_phase(PHASE_CLEANUP_NAMES.format(names=_cleanup_names_text(acc)))
        with phase_scope(PHASE_CLEANUP):
            acc.cleanup()
        # OK or FAIL from the test body; START if prepare never reached yield.
        log_phase(PHASE_TEST_END.format(name=test_name), result=_call_result(request))
