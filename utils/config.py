"""Typed settings from .env and encrypted credentials."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

# Repository root: utils/config.py -> utils -> repo.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Layout of the committed credentials file and the local-only key file.
CONFIG_DIR_NAME = "config"
CREDENTIALS_FILE_NAME = "credentials.json"
FERNET_KEY_FILE_NAME = "fernet.key"
DOTENV_FILE_NAME = ".env"

# Env key names. Keep in sync with .env.example (enforced by a framework test).
ENV_BASE_URL = "ACC_BASE_URL"
ENV_PROJECT_ID = "ACC_PROJECT_ID"
ENV_FOLDER_NAME = "ACC_FOLDER_NAME"
ENV_USERNAME = "ACC_USERNAME"
ENV_PASSWORD = "ACC_PASSWORD"
ENV_FERNET_KEY = "ACC_FERNET_KEY"
ENV_BROWSER = "BROWSER"
ENV_HEADLESS = "HEADLESS"
ENV_TIMEOUT_MS = "TIMEOUT_MS"

ENV_KEYS = (
    ENV_BASE_URL,
    ENV_PROJECT_ID,
    ENV_FOLDER_NAME,
    ENV_USERNAME,
    ENV_PASSWORD,
    ENV_FERNET_KEY,
    ENV_BROWSER,
    ENV_HEADLESS,
    ENV_TIMEOUT_MS,
)

# A run cannot start without a target ACC project/folder.
REQUIRED_ENV_KEYS = (
    ENV_BASE_URL,
    ENV_PROJECT_ID,
    ENV_FOLDER_NAME,
)

# Defaults used only when the optional browser/timeout keys are omitted.
DEFAULT_BROWSER = "chromium"
DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_HEADLESS = True

# ACC Files URL shape used by later page objects.
FILES_PROJECT_PATH = "/docs/files/projects/"

# JSON fields inside credentials.json.
CREDENTIALS_USERNAME_FIELD = "username"
CREDENTIALS_TOKEN_FIELD = "password_token"

# Fail-fast messages. Tests match these constants so wording stays in one place.
MSG_MISSING_SETTINGS = "Missing required setting(s): {keys}. Copy .env.example to .env."
MSG_MISSING_USERNAME = "Missing username. Set ACC_USERNAME in .env or config/credentials.json."
MSG_MISSING_PASSWORD = (
    "Missing password. Set ACC_PASSWORD in .env, or provide "
    "config/credentials.json password_token plus a local Fernet key."
)
MSG_MISSING_FERNET_KEY = (
    "Missing Fernet key. Set ACC_FERNET_KEY in .env or create config/fernet.key. "
    "The reviewer receives this key separately; it is not in the repository."
)
MSG_DECRYPT_FAILED = (
    "Could not decrypt config/credentials.json password_token. "
    "Check ACC_FERNET_KEY or config/fernet.key."
)
MSG_TIMEOUT_NOT_INT = "TIMEOUT_MS must be an integer."
MSG_CREDENTIALS_NOT_JSON = "config/credentials.json is not valid JSON."
MSG_CREDENTIALS_NOT_OBJECT = "config/credentials.json must be a JSON object."

_TRUTHY = {"1", "true", "yes", "on"}


class ConfigError(RuntimeError):
    """Missing or invalid configuration. Messages must never include secrets."""


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings. Password is excluded from repr."""

    base_url: str
    project_id: str
    folder_name: str
    username: str
    password: str = field(repr=False)
    browser: str
    headless: bool
    timeout_ms: int

    def files_url(self) -> str:
        """Return the ACC Files URL for the configured project.

        Returns:
            Absolute Files-tool URL built from base_url and project_id.
        """
        # Strip a trailing slash so the path constant can start with '/'.
        return f"{self.base_url.rstrip('/')}{FILES_PROJECT_PATH}{self.project_id}"


_CACHED_SETTINGS: Settings | None = None


def credentials_path(root: Path | None = None) -> Path:
    """Return config/credentials.json under the given (or repo) root.

    Args:
        root: Project root. Defaults to this repository.

    Returns:
        Absolute path to the committed credentials file.
    """
    # Tests pass a temp root so production files are never overwritten.
    return (REPO_ROOT if root is None else Path(root)) / CONFIG_DIR_NAME / CREDENTIALS_FILE_NAME


def fernet_key_path(root: Path | None = None) -> Path:
    """Return config/fernet.key under the given (or repo) root.

    Args:
        root: Project root. Defaults to this repository.

    Returns:
        Absolute path to the git-ignored Fernet key file.
    """
    # Same layout as credentials.json, but this file must never be committed.
    return (REPO_ROOT if root is None else Path(root)) / CONFIG_DIR_NAME / FERNET_KEY_FILE_NAME


CREDENTIALS_PATH = credentials_path()
FERNET_KEY_PATH = fernet_key_path()


def reset_settings_cache() -> None:
    """Drop the process-wide Settings cache so the next load reads again."""
    global _CACHED_SETTINGS
    # Fixtures call this when they need a clean load_settings() result.
    _CACHED_SETTINGS = None


def get_settings() -> Settings:
    """Return cached Settings, loading from .env on the first call.

    Returns:
        The session Settings object.
    """
    global _CACHED_SETTINGS
    # Later fixtures should call get_settings() instead of load_settings().
    if _CACHED_SETTINGS is None:
        _CACHED_SETTINGS = load_settings()
    return _CACHED_SETTINGS


def load_settings(
    *,
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
) -> Settings:
    """Load typed settings from env vars plus optional encrypted credentials.

    Args:
        environ: Explicit env mapping. When omitted, .env + os.environ are used.
        root: Project root used to find .env and config files.

    Returns:
        Resolved Settings. Password is never included in repr.

    Raises:
        ConfigError: Required values are missing or the token cannot be decrypted.
    """
    # Tests pass root=tmp_path so we never read the developer's real files.
    root = REPO_ROOT if root is None else Path(root)
    if environ is None:
        # override=False keeps CI/export values ahead of the file.
        load_dotenv(root / DOTENV_FILE_NAME, override=False)
        environ = os.environ

    # Fail before login if the target project cannot be identified.
    missing = []
    for key in REQUIRED_ENV_KEYS:
        value = _clean(environ.get(key))
        if not value:
            missing.append(key)
    if missing:
        raise ConfigError(MSG_MISSING_SETTINGS.format(keys=", ".join(missing)))

    # Username may come from .env or from the committed credentials file.
    credentials = _load_credentials(credentials_path(root))
    username = _clean(environ.get(ENV_USERNAME))
    if not username:
        username = _clean(credentials.get(CREDENTIALS_USERNAME_FIELD))
    if not username:
        raise ConfigError(MSG_MISSING_USERNAME)

    # Password resolution is isolated so the error never includes the secret.
    password = _resolve_password(environ, credentials, root)
    browser = _clean(environ.get(ENV_BROWSER))
    if not browser:
        browser = DEFAULT_BROWSER
    browser = browser.lower()
    timeout_raw = _clean(environ.get(ENV_TIMEOUT_MS))
    if not timeout_raw:
        timeout_raw = str(DEFAULT_TIMEOUT_MS)
    try:
        timeout_ms = int(timeout_raw)
    except ValueError as exc:
        raise ConfigError(MSG_TIMEOUT_NOT_INT) from exc

    return Settings(
        base_url=_clean(environ.get(ENV_BASE_URL)),
        project_id=_clean(environ.get(ENV_PROJECT_ID)),
        folder_name=_clean(environ.get(ENV_FOLDER_NAME)),
        username=username,
        password=password,
        browser=browser,
        headless=_as_bool(environ.get(ENV_HEADLESS), default=DEFAULT_HEADLESS),
        timeout_ms=timeout_ms,
    )


def resolve_fernet_key(environ: Mapping[str, str], root: Path | None = None) -> str:
    """Resolve the Fernet key from env first, then the local key file.

    Args:
        environ: Env mapping that may contain ACC_FERNET_KEY.
        root: Project root used to find config/fernet.key.

    Returns:
        The Fernet key string.

    Raises:
        ConfigError: Neither the env var nor the key file is available.
    """
    # Env wins so a reviewer can paste ACC_FERNET_KEY without creating a file.
    root = REPO_ROOT if root is None else Path(root)
    key = _clean(environ.get(ENV_FERNET_KEY))
    if key:
        return key
    key_file = fernet_key_path(root)
    if key_file.exists():
        file_key = _clean(key_file.read_text(encoding="utf-8"))
        if file_key:
            return file_key
    raise ConfigError(MSG_MISSING_FERNET_KEY)


def decrypt_password_token(token: str, key: str) -> str:
    """Decrypt a Fernet password token.

    Args:
        token: Ciphertext stored in credentials.json.
        key: Fernet key from env or config/fernet.key.

    Returns:
        The plaintext password.

    Raises:
        ConfigError: The key does not match the token. The message has no secrets.
    """
    try:
        # Fernet keys and tokens are url-safe base64 ASCII.
        return Fernet(key.encode("ascii")).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ConfigError(MSG_DECRYPT_FAILED) from exc


def encrypt_password_token(password: str, key: str) -> str:
    """Encrypt a plaintext password into a Fernet token.

    Args:
        password: Plaintext ACC password. Never log this value.
        key: Fernet key that must stay local.

    Returns:
        ASCII Fernet token suitable for credentials.json.
    """
    # UTF-8 so non-ASCII passwords still round-trip.
    return Fernet(key.encode("ascii")).encrypt(password.encode("utf-8")).decode("ascii")


def generate_fernet_key() -> str:
    """Return a new Fernet key as an ASCII string.

    Returns:
        A url-safe base64 key for ACC_FERNET_KEY / config/fernet.key.
    """
    # cryptography already produces the correct key length and encoding.
    return Fernet.generate_key().decode("ascii")


def _resolve_password(
    environ: Mapping[str, str],
    credentials: dict[str, str],
    root: Path,
) -> str:
    """Choose ACC_PASSWORD or decrypt the committed token.

    Args:
        environ: Env mapping that may contain a plaintext override.
        credentials: Parsed credentials.json.
        root: Project root used to find the Fernet key file.

    Returns:
        The plaintext password.

    Raises:
        ConfigError: Neither password path is available.
    """
    # Empty string is treated as "not set" so .env.example blanks fall through.
    env_password = environ.get(ENV_PASSWORD)
    if env_password is not None and env_password != "":
        return env_password

    token = _clean(credentials.get(CREDENTIALS_TOKEN_FIELD))
    if not token:
        raise ConfigError(MSG_MISSING_PASSWORD)
    return decrypt_password_token(token, resolve_fernet_key(environ, root))


def _load_credentials(path: Path) -> dict[str, str]:
    """Read credentials.json as a string-to-string mapping.

    Args:
        path: Path to credentials.json.

    Returns:
        Parsed object, or {} when the file is absent.

    Raises:
        ConfigError: The file exists but is not a JSON object.
    """
    if not path.exists():
        # Owner-only runs can rely entirely on .env and skip the file.
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(MSG_CREDENTIALS_NOT_JSON) from exc
    if not isinstance(payload, dict):
        raise ConfigError(MSG_CREDENTIALS_NOT_OBJECT)
    # Normalize None to "" so later _clean() calls stay simple.
    cleaned = {}
    for key, value in payload.items():
        if value is None:
            cleaned[str(key)] = ""
        else:
            cleaned[str(key)] = str(value)
    return cleaned


def _clean(value: str | None) -> str:
    """Strip whitespace and treat None as an empty string.

    Args:
        value: Raw env or JSON value.

    Returns:
        Trimmed string, possibly empty.
    """
    return (value or "").strip()


def _as_bool(value: str | None, *, default: bool) -> bool:
    """Parse a truthy env flag.

    Args:
        value: Raw HEADLESS-style string.
        default: Value used when the key is missing or blank.

    Returns:
        True for 1/true/yes/on; otherwise False unless default applies.
    """
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in _TRUTHY
