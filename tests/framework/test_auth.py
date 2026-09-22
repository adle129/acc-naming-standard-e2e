"""FR-12: storage_state is saved and loaded without opening ACC."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.framework.support import (
    AUTH_STATE_REL,
    BASE_ENV,
    SAMPLE_AUTH_ARRAY_TEXT,
    SAMPLE_ENV_PASSWORD,
    SAMPLE_INVALID_AUTH_TEXT,
    SAMPLE_STORAGE_COOKIES_KEY,
    SAMPLE_STORAGE_STATE,
    write_credentials,
)
from utils.auth import (
    AUTH_STATE_FILE_NAME,
    MSG_AUTH_STATE_INVALID,
    MSG_AUTH_STATE_NOT_OBJECT,
    MSG_LOGIN_FAILED,
    AuthError,
    auth_state_path,
    read_storage_state,
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
