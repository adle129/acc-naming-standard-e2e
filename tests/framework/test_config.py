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

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Repository root: tests/framework -> tests -> repo.
ROOT = Path(__file__).resolve().parents[2]

# Isolated env used by most tests so a local .env cannot leak into assertions.
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
    """Write a temporary credentials.json under an isolated repo root.

    Args:
        root: Temporary directory treated as the project root.
        username: Value stored in credentials.json ``username``.
        password_token: Fernet token stored in credentials.json ``password_token``.
    """
    # Keep the same config/ layout the real loader expects.
    config_dir = root / "config"
    # Create config/ even when the temp root is empty.
    config_dir.mkdir(parents=True, exist_ok=True)
    # Persist username + token so load_settings can read them like production.
    (config_dir / "credentials.json").write_text(
        json.dumps({"username": username, "password_token": password_token}),
        encoding="utf-8",
    )


def test_env_example_documents_every_supported_key() -> None:
    """Prove .env.example lists exactly the keys config.py knows about."""
    # Read the committed template, not a local .env that may contain secrets.
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    # Collect KEY=value names and ignore blank lines and comments.
    documented = {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and "=" in line
    }
    # A drift here means a reviewer cannot configure a newly added setting.
    assert documented == set(ENV_KEYS)


def test_load_settings_prefers_env_password(tmp_path: Path) -> None:
    """Prove ACC_PASSWORD in the environment wins over credentials.json.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Plant a different username/token so a wrong resolution order is visible.
    _write_credentials(tmp_path, username="ignored@example.com", password_token="unused")
    # Load from BASE_ENV instead of the machine's real environment.
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    # Env username must beat the credentials.json username.
    assert settings.username == "reviewer@example.com"
    # Env plaintext password must beat the unused token.
    assert settings.password == "plain-from-env"
    # Folder and browser flags come from BASE_ENV with typed conversion.
    assert settings.folder_name == "Name-standard"
    assert settings.headless is True
    assert settings.timeout_ms == 30000
    # pages/ later navigate with this helper; keep the ACC URL shape stable.
    assert settings.files_url() == "https://acc.autodesk.com/docs/files/projects/project-id"


def test_load_settings_decrypts_token_with_env_key(tmp_path: Path) -> None:
    """Prove a password_token decrypts when ACC_FERNET_KEY is in the env.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Fresh key so this test does not depend on the developer's local key file.
    key = generate_fernet_key()
    # Encrypt a known password; the loader must return this exact value.
    token = encrypt_password_token("token-password", key)
    # Store the token as the public repo would: username + ciphertext only.
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    # No ACC_PASSWORD here, so the token + env key path is the only option.
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
        "ACC_FERNET_KEY": key,
    }
    # Load through the same public API the fixtures will call.
    settings = load_settings(environ=environ, root=tmp_path)
    # Username falls back to credentials.json when ACC_USERNAME is absent.
    assert settings.username == "repo-user@example.com"
    # Decryption must recover the original password, not the token string.
    assert settings.password == "token-password"


def test_load_settings_decrypts_token_with_key_file(tmp_path: Path) -> None:
    """Prove a git-ignored config/fernet.key can decrypt the token.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Generate a key that will live only in the temp key file.
    key = generate_fernet_key()
    # Encrypt a distinct password so this case cannot pass by env fallback.
    token = encrypt_password_token("file-key-password", key)
    # Write the public token file first; that also creates config/.
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    # Reviewer path: drop the separately shared key into config/fernet.key.
    (tmp_path / "config" / "fernet.key").write_text(key + "\n", encoding="utf-8")
    # Neither ACC_PASSWORD nor ACC_FERNET_KEY is set, so only the file remains.
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
    }
    # Loader must find the key file under the isolated root.
    settings = load_settings(environ=environ, root=tmp_path)
    # File-key decryption is the reviewer-run path after they receive the key.
    assert settings.password == "file-key-password"


def test_missing_required_setting_fails_fast(tmp_path: Path) -> None:
    """Prove a missing required env key raises ConfigError immediately.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Copy BASE_ENV so we can delete one key without mutating the constant.
    environ = dict(BASE_ENV)
    # Project ID is required; removing it must stop the run before login.
    del environ["ACC_PROJECT_ID"]
    # The message names the missing key so the reviewer knows what to set.
    with pytest.raises(ConfigError, match="ACC_PROJECT_ID"):
        # Isolated root still needed so credentials lookup stays sandboxed.
        load_settings(environ=environ, root=tmp_path)


def test_token_without_key_fails_fast(tmp_path: Path) -> None:
    """Prove a token without any Fernet key fails with a clear error.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Build a valid token so the failure is "missing key", not "missing token".
    key = generate_fernet_key()
    token = encrypt_password_token("hidden", key)
    # Publish only the token, as the real repository does.
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    # Omit ACC_PASSWORD and ACC_FERNET_KEY and do not write fernet.key.
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
    }
    # Reviewers who forgot the out-of-band key should see this, not a crypto traceback.
    with pytest.raises(ConfigError, match="Fernet key"):
        load_settings(environ=environ, root=tmp_path)


def test_wrong_key_fails_fast_without_leaking_secrets(tmp_path: Path) -> None:
    """Prove a wrong key fails without printing the password or the key.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Encrypt with one key, then attempt decrypt with a different key.
    token = encrypt_password_token("hidden-secret", generate_fernet_key())
    # Store the ciphertext the same way the public repo would.
    _write_credentials(tmp_path, username="repo-user@example.com", password_token=token)
    # Supply a brand-new key that cannot decrypt the token above.
    environ = {
        "ACC_BASE_URL": "https://acc.autodesk.com",
        "ACC_PROJECT_ID": "project-id",
        "ACC_FOLDER_NAME": "Name-standard",
        "ACC_FERNET_KEY": generate_fernet_key(),
    }
    # Capture the exception so we can inspect the message for leaks.
    with pytest.raises(ConfigError, match="Could not decrypt") as exc_info:
        load_settings(environ=environ, root=tmp_path)
    # Plaintext password must never appear in the fail-fast message.
    assert "hidden-secret" not in str(exc_info.value)
    # The Fernet key itself must also stay out of the message.
    assert environ["ACC_FERNET_KEY"] not in str(exc_info.value)


def test_settings_repr_hides_password(tmp_path: Path) -> None:
    """Prove Settings.__repr__ cannot accidentally log the password.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Empty credentials.json is enough because BASE_ENV already has a password.
    _write_credentials(tmp_path)
    # Load a real Settings object so repr uses the dataclass field flags.
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    # Debug prints and pytest assertion dumps call repr().
    rendered = repr(settings)
    # The env password value must not show up in the dumped object.
    assert "plain-from-env" not in rendered
    # The password field itself is omitted from repr (field(repr=False)).
    assert "password=" not in rendered


def test_encrypt_decrypt_roundtrip() -> None:
    """Prove the encrypt helper reverses with the matching key."""
    # One-off key; not written to disk so nothing leaks into the workspace.
    key = generate_fernet_key()
    # Encrypt a known secret used only inside this test.
    token = encrypt_password_token("roundtrip-secret", key)
    # The token must decrypt back to the original password.
    assert decrypt_password_token(token, key) == "roundtrip-secret"
    # Ciphertext must not contain the plaintext (gitleaks / casual inspection).
    assert "roundtrip-secret" not in token


def test_encrypt_cli_writes_token_and_local_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove the CLI writes the token and a local key, never the plaintext.

    Args:
        tmp_path: Isolated project root where the CLI writes config files.
        monkeypatch: Used to stub getpass so the test is non-interactive.
    """
    # Replace the hidden prompt with a fixed password; never type in CI.
    monkeypatch.setattr("utils.encrypt_password.getpass.getpass", lambda _prompt: "cli-secret")
    # Run the same entry point a developer would run from the command line.
    assert encrypt_main(["--username", "cli@example.com", "--root", str(tmp_path)]) == 0

    # Read back the public credentials file the CLI just wrote.
    credentials = json.loads((tmp_path / "config" / "credentials.json").read_text(encoding="utf-8"))
    # The key file is git-ignored in production; here it lives under tmp_path.
    key = (tmp_path / "config" / "fernet.key").read_text(encoding="utf-8").strip()
    # Username is stored in plaintext because it is not a secret.
    assert credentials["username"] == "cli@example.com"
    # The token plus local key must recover the password getpass returned.
    assert decrypt_password_token(credentials["password_token"], key) == "cli-secret"
    # The committed-style token file must not contain the raw password.
    assert "cli-secret" not in credentials["password_token"]
