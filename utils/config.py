"""Typed settings from .env and encrypted credentials."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS_PATH = REPO_ROOT / "config" / "credentials.json"
FERNET_KEY_PATH = REPO_ROOT / "config" / "fernet.key"

ENV_KEYS = (
    "ACC_BASE_URL",
    "ACC_PROJECT_ID",
    "ACC_FOLDER_NAME",
    "ACC_USERNAME",
    "ACC_PASSWORD",
    "ACC_FERNET_KEY",
    "BROWSER",
    "HEADLESS",
    "TIMEOUT_MS",
)

REQUIRED_ENV_KEYS = (
    "ACC_BASE_URL",
    "ACC_PROJECT_ID",
    "ACC_FOLDER_NAME",
)

_TRUTHY = {"1", "true", "yes", "on"}


class ConfigError(RuntimeError):
    """Missing or invalid configuration. Messages must never include secrets."""


@dataclass(frozen=True)
class Settings:
    base_url: str
    project_id: str
    folder_name: str
    username: str
    password: str = field(repr=False)
    browser: str
    headless: bool
    timeout_ms: int

    def files_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/docs/files/projects/{self.project_id}"


_CACHED_SETTINGS: Settings | None = None


def reset_settings_cache() -> None:
    global _CACHED_SETTINGS
    _CACHED_SETTINGS = None


def get_settings() -> Settings:
    global _CACHED_SETTINGS
    if _CACHED_SETTINGS is None:
        _CACHED_SETTINGS = load_settings()
    return _CACHED_SETTINGS


def load_settings(
    *,
    environ: Mapping[str, str] | None = None,
    root: Path | None = None,
) -> Settings:
    """Load typed settings. `environ`/`root` isolate tests from the real machine."""
    root = REPO_ROOT if root is None else Path(root)
    if environ is None:
        load_dotenv(root / ".env", override=False)
        environ = os.environ

    missing = [key for key in REQUIRED_ENV_KEYS if not _clean(environ.get(key))]
    if missing:
        raise ConfigError(f"Missing required setting(s): {', '.join(missing)}. Copy .env.example to .env.")

    credentials = _load_credentials(root / "config" / "credentials.json")
    username = _clean(environ.get("ACC_USERNAME")) or _clean(credentials.get("username"))
    if not username:
        raise ConfigError(
            "Missing username. Set ACC_USERNAME in .env or config/credentials.json."
        )

    password = _resolve_password(environ, credentials, root)
    browser = (_clean(environ.get("BROWSER")) or "chromium").lower()
    timeout_raw = _clean(environ.get("TIMEOUT_MS")) or "30000"
    try:
        timeout_ms = int(timeout_raw)
    except ValueError as exc:
        raise ConfigError("TIMEOUT_MS must be an integer.") from exc

    return Settings(
        base_url=_clean(environ.get("ACC_BASE_URL")) or "",
        project_id=_clean(environ.get("ACC_PROJECT_ID")) or "",
        folder_name=_clean(environ.get("ACC_FOLDER_NAME")) or "",
        username=username,
        password=password,
        browser=browser,
        headless=_as_bool(environ.get("HEADLESS"), default=True),
        timeout_ms=timeout_ms,
    )


def resolve_fernet_key(environ: Mapping[str, str], root: Path | None = None) -> str:
    root = REPO_ROOT if root is None else Path(root)
    key = _clean(environ.get("ACC_FERNET_KEY"))
    if key:
        return key
    key_path = root / "config" / "fernet.key"
    if key_path.exists():
        file_key = _clean(key_path.read_text(encoding="utf-8"))
        if file_key:
            return file_key
    raise ConfigError(
        "Missing Fernet key. Set ACC_FERNET_KEY in .env or create config/fernet.key. "
        "The reviewer receives this key separately; it is not in the repository."
    )


def decrypt_password_token(token: str, key: str) -> str:
    try:
        return Fernet(key.encode("ascii")).decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise ConfigError(
            "Could not decrypt config/credentials.json password_token. "
            "Check ACC_FERNET_KEY or config/fernet.key."
        ) from exc


def encrypt_password_token(password: str, key: str) -> str:
    return Fernet(key.encode("ascii")).encrypt(password.encode("utf-8")).decode("ascii")


def generate_fernet_key() -> str:
    return Fernet.generate_key().decode("ascii")


def _resolve_password(
    environ: Mapping[str, str],
    credentials: dict[str, str],
    root: Path,
) -> str:
    env_password = environ.get("ACC_PASSWORD")
    if env_password is not None and env_password != "":
        return env_password

    token = _clean(credentials.get("password_token"))
    if not token:
        raise ConfigError(
            "Missing password. Set ACC_PASSWORD in .env, or provide "
            "config/credentials.json password_token plus a local Fernet key."
        )
    return decrypt_password_token(token, resolve_fernet_key(environ, root))


def _load_credentials(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError("config/credentials.json is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ConfigError("config/credentials.json must be a JSON object.")
    return {str(key): "" if value is None else str(value) for key, value in payload.items()}


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in _TRUTHY
