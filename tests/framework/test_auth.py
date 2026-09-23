"""FR-12: storage_state is saved and loaded without opening ACC."""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from tests.framework.support import (
    AUTH_STATE_REL,
    BASE_ENV,
    SAMPLE_AUTH_ARRAY_TEXT,
    SAMPLE_CONTEXT_ARGS,
    SAMPLE_CONTEXT_IGNORE_HTTPS,
    SAMPLE_ENV_PASSWORD,
    SAMPLE_INVALID_AUTH_TEXT,
    SAMPLE_SETTINGS,
    SAMPLE_STORAGE_COOKIES_KEY,
    SAMPLE_STORAGE_STATE,
    write_credentials,
)
from utils.auth import (
    AUTH_STATE_FILE_NAME,
    MSG_AUTH_STATE_INVALID,
    MSG_AUTH_STATE_NOT_OBJECT,
    MSG_LOGIN_FAILED,
    BROWSER_LOCALE,
    BROWSER_VIEWPORT,
    LOCALE_ARG,
    STORAGE_STATE_ARG,
    VIEWPORT_ARG,
    AuthError,
    auth_state_path,
    ensure_storage_state,
    read_storage_state,
    with_storage_state,
    write_storage_state,
)
from utils.config import Settings
from utils.setup_auth import (
    EXIT_OK,
    EXIT_USAGE,
    FLAG_HEADED,
    MSG_NEED_HEADED,
    MSG_SAVED,
    main as setup_auth_main,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework


def _fake_capture(_settings: Settings, wait_for_enter) -> dict:
    """Return a canned storage_state so tests never launch a browser.

    Args:
        _settings: Resolved settings. Unused; the fake does not open ACC.
        wait_for_enter: Prompt hook. Called so the CLI still waits once.

    Returns:
        The sample Playwright storage_state object.
    """
    # The real CLI waits after the browser opens; keep that order here.
    wait_for_enter()
    # Cookies and origins are empty because no Autodesk session exists in CI.
    return SAMPLE_STORAGE_STATE


def test_auth_state_path_uses_the_committed_file_name(tmp_path: Path) -> None:
    """Prove auth_state.json lives at the project root, not under config/.

    Args:
        tmp_path: Isolated project root so the real auth file is not touched.
    """
    # The gitignore pattern is this exact file name at the repo root.
    path = auth_state_path(tmp_path)
    assert path.parent == tmp_path
    assert path.name == AUTH_STATE_FILE_NAME
    assert path.name == AUTH_STATE_REL


def test_write_and_read_storage_state_roundtrip(tmp_path: Path) -> None:
    """Prove a storage_state object written to disk can be read back.

    Args:
        tmp_path: Isolated project root for the temporary auth file.
    """
    # Write the same shape Playwright's context.storage_state() returns.
    written = write_storage_state(SAMPLE_STORAGE_STATE, root=tmp_path)
    # The helper must create the git-ignored file name, not a new layout.
    assert written == auth_state_path(tmp_path)
    # T10 will pass this object to new_context(storage_state=...).
    loaded = read_storage_state(root=tmp_path)
    assert loaded == SAMPLE_STORAGE_STATE
    assert SAMPLE_STORAGE_COOKIES_KEY in loaded


def test_read_storage_state_returns_none_when_file_is_missing(tmp_path: Path) -> None:
    """Prove a missing auth file is normal, not a hard failure.

    Args:
        tmp_path: Empty project root with no auth_state.json.
    """
    # Phase-1 default is programmatic login when no cache exists.
    loaded = read_storage_state(root=tmp_path)
    assert loaded is None


def test_read_storage_state_rejects_invalid_json(tmp_path: Path) -> None:
    """Prove a corrupt auth file fails fast without leaking secrets.

    Args:
        tmp_path: Isolated project root that receives a broken auth file.
    """
    # Write text that is not JSON so the loader cannot parse it.
    auth_state_path(tmp_path).write_text(SAMPLE_INVALID_AUTH_TEXT, encoding="utf-8")
    # The message is a constant so tests do not copy the wording.
    with pytest.raises(AuthError, match=re.escape(MSG_AUTH_STATE_INVALID)):
        read_storage_state(root=tmp_path)


def test_read_storage_state_rejects_a_json_array(tmp_path: Path) -> None:
    """Prove storage_state must be a JSON object, not a list.

    Args:
        tmp_path: Isolated project root that receives a JSON array.
    """
    # Playwright writes an object with cookies and origins, never a top-level list.
    auth_state_path(tmp_path).write_text(SAMPLE_AUTH_ARRAY_TEXT, encoding="utf-8")
    with pytest.raises(AuthError, match=re.escape(MSG_AUTH_STATE_NOT_OBJECT)):
        read_storage_state(root=tmp_path)


def test_login_failed_message_points_at_the_fallback_script() -> None:
    """Prove the T10 fail-fast text tells the reviewer to run setup_auth.py."""
    # Automated login is primary; this string is what the fixture will raise.
    assert "setup_auth.py" in MSG_LOGIN_FAILED
    assert FLAG_HEADED.strip("-") in MSG_LOGIN_FAILED


def test_setup_auth_requires_headed_flag() -> None:
    """Prove the CLI refuses to run without --headed."""
    # A headless run cannot complete SSO or MFA, so the script must stop.
    code = setup_auth_main([])
    assert code == EXIT_USAGE


def test_setup_auth_headed_writes_auth_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Prove --headed saves storage_state through the injected collector.

    Args:
        tmp_path: Isolated project root where the CLI writes auth_state.json.
        capsys: Captures stdout/stderr so we can assert no password leak.
    """
    # load_settings needs a credentials file even when the password comes from env.
    write_credentials(tmp_path)
    # argv uses the same --headed switch a reviewer would type.
    argv = [FLAG_HEADED, "--root", str(tmp_path)]
    # The fake collector returns canned cookies so Playwright is never started.
    code = setup_auth_main(
        argv,
        environ=BASE_ENV,
        capture=_fake_capture,
        wait_for_enter=lambda: None,
    )
    assert code == EXIT_OK
    # The saved file must be the Playwright-shaped object, not a password dump.
    saved = json.loads(auth_state_path(tmp_path).read_text(encoding="utf-8"))
    assert saved == SAMPLE_STORAGE_STATE
    # stdout tells the reviewer the file name, not the absolute path with secrets.
    output = capsys.readouterr()
    assert MSG_SAVED.format(path=AUTH_STATE_FILE_NAME) in output.out
    # The env password must never appear in CLI output.
    assert SAMPLE_ENV_PASSWORD not in output.out
    assert SAMPLE_ENV_PASSWORD not in output.err


def test_setup_auth_without_headed_prints_usage(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Prove the missing-flag path prints the usage constant, not a traceback.

    Args:
        capsys: Captures stderr where the usage message is written.
    """
    # No --headed and no settings: the CLI must not try to log in.
    setup_auth_main([])
    output = capsys.readouterr()
    assert MSG_NEED_HEADED in output.err
    # A usage error must not mention the password field.
    assert SAMPLE_ENV_PASSWORD not in output.err


class FakePage:
    """Stand-in Playwright page. Records the timeout the login helper sets."""

    def __init__(self) -> None:
        self.timeout_ms: int | None = None

    def set_default_timeout(self, timeout_ms: int) -> None:
        """Record ACC_TIMEOUT_MS so tests can prove it was applied.

        Args:
            timeout_ms: Value from Settings.timeout_ms.
        """
        self.timeout_ms = timeout_ms


class FakeContext:
    """Stand-in browser context that returns a canned storage_state."""

    def __init__(self) -> None:
        self.page = FakePage()
        self.closed = False

    def new_page(self) -> FakePage:
        """Return the one fake page.

        Returns:
            The page created with this context.
        """
        return self.page

    def storage_state(self) -> dict:
        """Return the sample cookies object Playwright would write.

        Returns:
            SAMPLE_STORAGE_STATE.
        """
        return SAMPLE_STORAGE_STATE

    def close(self) -> None:
        """Mark the context closed after login or failure."""
        self.closed = True


class FakeBrowser:
    """Stand-in browser. Records whether login opened a context."""

    def __init__(self) -> None:
        self.context = FakeContext()
        self.new_context_calls = 0

    def new_context(self, **kwargs: object) -> FakeContext:
        """Open one fake context the way the session fixture does.

        Args:
            **kwargs: Playwright options such as locale=. Ignored by the fake.

        Returns:
            The recorded fake context.
        """
        self.new_context_calls = self.new_context_calls + 1
        return self.context


class ForbiddenBrowser:
    """Browser that must not be used when auth_state.json already exists."""

    def new_context(self, **kwargs: object) -> FakeContext:
        """Fail if a cache hit still tries to open Autodesk.

        Returns:
            Never returns; the cache path must skip this.

        Raises:
            AssertionError: Always, because a cache hit must not log in.
        """
        raise AssertionError("cache hit must not open a browser context")


def test_with_storage_state_adds_the_auth_file_path() -> None:
    """Prove browser_context_args gets storage_state without dropping other keys."""
    # Start from the same shape pytest-playwright already built.
    merged = with_storage_state(SAMPLE_CONTEXT_ARGS, AUTH_STATE_REL)
    # Other context keys stay; locale and viewport are added on top.
    assert merged["ignore_https_errors"] is SAMPLE_CONTEXT_IGNORE_HTTPS
    # The Playwright keyword must be storage_state, not a new name.
    assert merged[STORAGE_STATE_ARG] == AUTH_STATE_REL
    # English locale so ACC does not follow a Chinese Windows language pack.
    assert merged[LOCALE_ARG] == BROWSER_LOCALE
    # Desktop width so the Upload label is not collapsed to an icon.
    assert merged[VIEWPORT_ARG] == BROWSER_VIEWPORT


def test_ensure_storage_state_reuses_an_existing_file(tmp_path: Path) -> None:
    """Prove a valid cache skips LoginPage and does not open a context.

    Args:
        tmp_path: Isolated root that already has auth_state.json.
    """
    # Write a valid Playwright object so read_storage_state accepts it.
    write_storage_state(SAMPLE_STORAGE_STATE, root=tmp_path)
    login_calls = []

    def fake_login(_page: FakePage, _settings: object) -> None:
        """Record that login ran. A cache hit must never call this.

        Args:
            _page: Unused fake page.
            _settings: Unused sample settings.
        """
        login_calls.append(True)

    # ForbiddenBrowser raises if ensure_storage_state forgets the cache check.
    path = ensure_storage_state(
        ForbiddenBrowser(),
        SAMPLE_SETTINGS,
        root=tmp_path,
        login=fake_login,
    )
    assert path == auth_state_path(tmp_path)
    assert login_calls == []


def test_ensure_storage_state_shows_login_when_flag_is_on(tmp_path: Path) -> None:
    """Prove ACC_SHOW_LOGIN=true opens LoginPage even when a cache exists.

    Args:
        tmp_path: Isolated root that already has auth_state.json.
    """
    # A cache is present so the default path would skip Autodesk ID.
    write_storage_state(SAMPLE_STORAGE_STATE, root=tmp_path)
    settings = replace(SAMPLE_SETTINGS, show_login=True)
    browser = FakeBrowser()
    login_calls = []

    def fake_login(_page: FakePage, _settings: object) -> None:
        """Record that the reviewer asked to show the sign-in form.

        Args:
            _page: Unused fake page.
            _settings: Unused sample settings.
        """
        login_calls.append(True)

    path = ensure_storage_state(
        browser,
        settings,
        root=tmp_path,
        login=fake_login,
    )
    # The flag must ignore the cache and drive LoginPage.
    assert login_calls == [True]
    assert browser.new_context_calls == 1
    assert path == auth_state_path(tmp_path)


def test_ensure_storage_state_logs_in_when_cache_is_missing(tmp_path: Path) -> None:
    """Prove a missing cache logs in once and writes auth_state.json.

    Args:
        tmp_path: Empty project root so the helper must create the file.
    """
    browser = FakeBrowser()
    login_pages = []

    def fake_login(page: FakePage, settings: object) -> None:
        """Stand in for LoginPage.login so this test never opens ACC.

        Args:
            page: Fake page created by FakeContext.
            settings: Sample settings; must be the object we passed in.
        """
        login_pages.append(page)
        # The production helper forwards the same Settings the fixture loaded.
        assert settings is SAMPLE_SETTINGS

    path = ensure_storage_state(
        browser,
        SAMPLE_SETTINGS,
        root=tmp_path,
        login=fake_login,
    )
    # One context, one login, then the file exists for later tests.
    assert browser.new_context_calls == 1
    assert login_pages == [browser.context.page]
    assert browser.context.page.timeout_ms == SAMPLE_SETTINGS.timeout_ms
    assert browser.context.closed is True
    assert path == auth_state_path(tmp_path)
    assert read_storage_state(root=tmp_path) == SAMPLE_STORAGE_STATE


def test_ensure_storage_state_wraps_login_failure(tmp_path: Path) -> None:
    """Prove a failed login raises the setup_auth fallback message.

    Args:
        tmp_path: Empty root so the helper attempts programmatic login.
    """
    browser = FakeBrowser()

    def failing_login(_page: FakePage, _settings: object) -> None:
        """Simulate Arkose or MFA blocking automated Sign in.

        Args:
            _page: Unused fake page.
            _settings: Unused sample settings.
        """
        raise RuntimeError("challenge")

    # match= is a regex; escape the constant so dots in the path stay literal.
    with pytest.raises(AuthError, match=re.escape(MSG_LOGIN_FAILED)):
        ensure_storage_state(
            browser,
            SAMPLE_SETTINGS,
            root=tmp_path,
            login=failing_login,
        )
    # The context still closes so a failed session does not leak a window.
    assert browser.context.closed is True
    # A failed login must not write a partial auth_state.json.
    assert read_storage_state(root=tmp_path) is None
