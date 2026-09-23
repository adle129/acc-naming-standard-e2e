"""Session login plus one function-scoped live ACC fixture.

Framework tests do not request page or live_acc, so they never open a browser.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page

from tests.live_support import LiveAcc
from utils.auth import ensure_storage_state, with_storage_state
from utils.config import get_settings


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
    path = ensure_storage_state(browser, settings)
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
def live_acc(page: Page) -> Iterator[LiveAcc]:
    """Open the naming folder for one live test, then clean this test's leftovers.

    Not autouse: framework tests must not request page. Each live test asks for
    live_acc. Session login stays in storage_state.

    Args:
        page: Function-scoped Playwright page (new context per test).

    Yields:
        LiveAcc bound to that page, already on the naming-standard folder.
    """
    settings = get_settings()
    acc = LiveAcc(page, settings)
    acc.prepare()
    try:
        yield acc
    finally:
        acc.cleanup()
