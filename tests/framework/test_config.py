"""FR-07 / FR-12: config loads from env + encrypted credentials."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.config import (
    ENV_KEYS,
    ConfigError,
    decrypt_password_token,
    encrypt_password_token,
    generate_fernet_key,
    load_settings,
)
from utils.encrypt_password import main as encrypt_main

pytestmark = pytest.mark.framework

ROOT = Path(__file__).resolve().parents[2]

BASE_ENV = {
    "ACC_BASE_URL": "https://acc.autodesk.com",
    "ACC_PROJECT_ID": "project-id",
    "ACC_FOLDER_NAME": "Name-standard",
    "ACC_USERNAME": "reviewer@example.com",
    "ACC_PASSWORD": "plain-from-env",
    "BROWSER": "chromium",
    "HEADLESS": "true",
    "TIMEOUT_MS": "30000",
}


def _write_credentials(root: Path, *, username: str = "", password_token: str = "") -> None:
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "credentials.json").write_text(
        json.dumps({"username": username, "password_token": password_token}),
        encoding="utf-8",
    )


def test_env_example_documents_every_supported_key() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    documented = {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    }
    assert documented == set(ENV_KEYS)


def test_load_settings_prefers_env_password(tmp_path: Path) -> None:
    _write_credentials(tmp_path, username="ignored@example.com", password_token="unused")
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    assert settings.username == "reviewer@example.com"
    assert settings.password == "plain-from-env"
    assert settings.folder_name == "Name-standard"
    assert settings.headless is True
    assert settings.timeout_ms == 30000
    assert settings.files_url() == "https://acc.autodesk.com/docs/files/projects/project-id"


def test_load_settings_decrypts_token_with_env_key(tmp_path: Path) -> None:
    key = generate_fernet_key()
    token = encrypt_password_token("token-password", key)
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
        "ACC_FERNET_KEY": key,
    }
    settings = load_settings(environ=environ, root=tmp_path)
    assert settings.username == "repo-user@example.com"
    assert settings.password == "token-password"


def test_load_settings_decrypts_token_with_key_file(tmp_path: Path) -> None:
    key = generate_fernet_key()
    token = encrypt_password_token("file-key-password", key)
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    (tmp_path / "config" / "fernet.key").write_text(key + "\n", encoding="utf-8")
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
    }
    settings = load_settings(environ=environ, root=tmp_path)
    assert settings.password == "file-key-password"


def test_missing_required_setting_fails_fast(tmp_path: Path) -> None:
    environ = dict(BASE_ENV)
    del environ["ACC_PROJECT_ID"]
    with pytest.raises(ConfigError, match="ACC_PROJECT_ID"):
        load_settings(environ=environ, root=tmp_path)


def test_token_without_key_fails_fast(tmp_path: Path) -> None:
    key = generate_fernet_key()
    token = encrypt_password_token("hidden", key)
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
    }
    with pytest.raises(ConfigError, match="Fernet key"):
        load_settings(environ=environ, root=tmp_path)


def test_wrong_key_fails_fast_without_leaking_secrets(tmp_path: Path) -> None:
    token = encrypt_password_token("hidden-secret", generate_fernet_key())
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
        "ACC_FERNET_KEY": generate_fernet_key(),
    }
    with pytest.raises(ConfigError, match="Could not decrypt") as exc_info:
        load_settings(environ=environ, root=tmp_path)
    assert "hidden-secret" not in str(exc_info.value)
    assert environ["ACC_FERNET_KEY"] not in str(exc_info.value)


def test_settings_repr_hides_password(tmp_path: Path) -> None:
    _write_credentials(tmp_path)
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    rendered = repr(settings)
    assert "plain-from-env" not in rendered
    assert "password=" not in rendered


def test_encrypt_decrypt_roundtrip() -> None:
    key = generate_fernet_key()
    token = encrypt_password_token("roundtrip-secret", key)
    assert decrypt_password_token(token, key) == "roundtrip-secret"
    assert "roundtrip-secret" not in token


def test_encrypt_cli_writes_token_and_local_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("utils.encrypt_password.getpass.getpass", lambda _prompt: "cli-secret")
    assert encrypt_main(["--username", "cli@example.com", "--root", str(tmp_path)]) == 0

    credentials = json.loads((tmp_path / "config" / "credentials.json").read_text(encoding="utf-8"))
    key = (tmp_path / "config" / "fernet.key").read_text(encoding="utf-8").strip()
    assert credentials["username"] == "cli@example.com"
    assert decrypt_password_token(credentials["password_token"], key) == "cli-secret"
    assert "cli-secret" not in credentials["password_token"]
