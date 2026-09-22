"""Playwright storage_state save and load. Automated login stays in T10."""

from __future__ import annotations

import json
from pathlib import Path

from utils.config import REPO_ROOT

# Repo-root file. Git-ignored; never committed.
AUTH_STATE_FILE_NAME = "auth_state.json"

# Fail-fast messages. Tests match these constants so wording stays in one place.
MSG_AUTH_STATE_INVALID = "auth_state.json is not valid JSON."
MSG_AUTH_STATE_NOT_OBJECT = "auth_state.json must be a JSON object."
MSG_LOGIN_FAILED = "Automated login failed. Run: python utils/setup_auth.py --headed"


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
