"""Playwright storage_state save, load, and one-time programmatic login."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from utils.config import REPO_ROOT, Settings

# Repo-root file. Git-ignored; never committed.
AUTH_STATE_FILE_NAME = "auth_state.json"

# pytest-playwright new_context() keyword that injects the saved cookies.
STORAGE_STATE_ARG = "storage_state"
# ACC follows the browser locale. Pin English so locators stay on English names.
LOCALE_ARG = "locale"
BROWSER_LOCALE = "en-US"
# Default Playwright 1280 hides the Upload label; ACC shows it at desktop width.
VIEWPORT_ARG = "viewport"
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080
BROWSER_VIEWPORT = {"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}

# Fail-fast messages. Tests match these constants so wording stays in one place.
MSG_AUTH_STATE_INVALID = "auth_state.json is not valid JSON."
MSG_AUTH_STATE_NOT_OBJECT = "auth_state.json must be a JSON object."
MSG_LOGIN_FAILED = "Automated login failed. Run: python utils/setup_auth.py --headed"

# Injected by framework tests so ensure_storage_state never opens ACC.
LoginFn = Callable[[Any, Settings], None]


class AuthError(RuntimeError):
    """Broken auth_state.json. Messages must never include secrets."""


def auth_state_path(root: Path | None = None) -> Path:
    """Return auth_state.json under the given (or repo) root.

    Args:
        root: Project root. Defaults to this repository.

    Returns:
        Absolute path to the git-ignored storage_state file.
    """
    # Tests pass a temp root so the real auth_state.json is never overwritten.
    return (REPO_ROOT if root is None else Path(root)) / AUTH_STATE_FILE_NAME


def write_storage_state(payload: dict, *, root: Path | None = None) -> Path:
    """Write a Playwright storage_state object to disk.

    Args:
        payload: Object returned by BrowserContext.storage_state().
        root: Project root. Defaults to this repository.

    Returns:
        Path that was written.
    """
    path = auth_state_path(root)
    # Playwright's payload is JSON: cookies plus origins. Do not log it.
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def read_storage_state(*, root: Path | None = None) -> dict | None:
    """Read a saved storage_state file.

    Args:
        root: Project root. Defaults to this repository.

    Returns:
        The parsed object, or None when the file is absent.
        Missing is normal: the T10 fixture then logs in programmatically.

    Raises:
        AuthError: The file exists but is not a JSON object.
    """
    path = auth_state_path(root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthError(MSG_AUTH_STATE_INVALID) from exc
    if not isinstance(payload, dict):
        raise AuthError(MSG_AUTH_STATE_NOT_OBJECT)
    return payload


def with_storage_state(browser_context_args: dict, storage_state: str) -> dict:
    """Copy Playwright context args and attach the saved login file.

    Args:
        browser_context_args: Args from pytest-playwright's fixture.
        storage_state: Path to auth_state.json.

    Returns:
        A new dict Playwright can pass to browser.new_context().
    """
    args = dict(browser_context_args)
    args[STORAGE_STATE_ARG] = storage_state
    # Locale is independent of cookies; a Chinese Windows host must still see Upload.
    args[LOCALE_ARG] = BROWSER_LOCALE
    args[VIEWPORT_ARG] = BROWSER_VIEWPORT
    return args


def ensure_storage_state(
    browser: Any,
    settings: Settings,
    *,
    root: Path | None = None,
    login: LoginFn | None = None,
) -> Path:
    """Reuse auth_state.json, or log in with LoginPage and write the file.

    When settings.show_login is False and a valid cache exists, LoginPage is skipped.
    When settings.show_login is True, LoginPage always runs so the sign-in UI is shown.

    Args:
        browser: Playwright browser, or a test double with new_context().
        settings: Resolved ACC settings, including show_login.
        root: Project root. Defaults to this repository.
        login: Optional login callback. Tests inject a fake; production uses LoginPage.

    Returns:
        Path of the storage_state file.

    Raises:
        AuthError: Programmatic login did not finish (SSO, MFA, or Arkose).
    """
    path = auth_state_path(root)
    cached = read_storage_state(root=root)
    # show_login=False keeps the cached session (no Autodesk ID page).
    if cached is not None and not settings.show_login:
        return path
    if login is None:
        login = _login_with_page
    context = browser.new_context(locale=BROWSER_LOCALE, viewport=BROWSER_VIEWPORT)
    page = context.new_page()
    try:
        page.set_default_timeout(settings.timeout_ms)
        login(page, settings)
        payload = context.storage_state()
    except Exception as exc:
        raise AuthError(MSG_LOGIN_FAILED) from exc
    finally:
        context.close()
    write_storage_state(payload, root=root)
    return path


def _login_with_page(page: Any, settings: Settings) -> None:
    """Open Autodesk ID and submit the saved credentials.

    Args:
        page: Playwright page on a fresh context (no storage_state yet).
        settings: Username, password, and ACC base URL.
    """
    # Imported here so framework tests that inject login= never load LoginPage.
    from pages.login_page import LoginPage

    login_page = LoginPage(page)
    login_page.navigate_to(settings.base_url)
    login_page.validate_login_page()
    login_page.login(settings.username, settings.password)
