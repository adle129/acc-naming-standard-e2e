"""FR-07 / FR-12: config loads from env + encrypted credentials."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.framework.support import (
    BASE_ENV,
    SAMPLE_CLI_PASSWORD,
    SAMPLE_CLI_USERNAME,
    SAMPLE_CREDENTIALS_USERNAME,
    SAMPLE_ENV_PASSWORD,
    SAMPLE_ENV_USERNAME,
    SAMPLE_FILE_KEY_PASSWORD,
    SAMPLE_FOLDER_NAME,
    SAMPLE_HIDDEN_PASSWORD,
    SAMPLE_IGNORED_USERNAME,
    SAMPLE_PROJECT_ID,
    SAMPLE_ROUNDTRIP_PASSWORD,
    SAMPLE_SETTINGS,
    SAMPLE_TOKEN_PASSWORD,
    SAMPLE_UNUSED_TOKEN,
    expected_files_url,
    required_env,
    write_credentials,
    write_fernet_key,
)
from utils.config import (
    CREDENTIALS_TOKEN_FIELD,
    CREDENTIALS_USERNAME_FIELD,
    DEFAULT_TIMEOUT_MS,
    ENV_FERNET_KEY,
    ENV_KEYS,
    ENV_PROJECT_ID,
    MSG_DECRYPT_FAILED,
    MSG_MISSING_FERNET_KEY,
    ConfigError,
    credentials_path,
    decrypt_password_token,
    encrypt_password_token,
    fernet_key_path,
    generate_fernet_key,
    load_settings,
    safe_settings_summary,
)
from utils.encrypt_password import main as encrypt_main

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Repository root used only to read committed templates such as .env.example.
ROOT = Path(__file__).resolve().parents[2]


def test_env_example_documents_every_supported_key() -> None:
    """Prove .env.example lists exactly the keys config.py knows about."""
    # Read the committed template, not a local .env that may contain secrets.
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    # Collect KEY=value names and ignore blank lines and comments.
    documented = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        documented.add(key)
    # A drift here means a reviewer cannot configure a newly added setting.
    assert documented == set(ENV_KEYS)


def test_load_settings_prefers_env_password(tmp_path: Path) -> None:
    """Prove ACC_PASSWORD in the environment wins over credentials.json.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Plant a different username/token so a wrong resolution order is visible.
    write_credentials(tmp_path, username=SAMPLE_IGNORED_USERNAME, password_token=SAMPLE_UNUSED_TOKEN)
    # Load from BASE_ENV instead of the machine's real environment.
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    # Env username must beat the credentials.json username.
    assert settings.username == SAMPLE_ENV_USERNAME
    # Env plaintext password must beat the unused token.
    assert settings.password == SAMPLE_ENV_PASSWORD
    # Folder and timeout come from BASE_ENV with typed conversion.
    assert settings.folder_name == SAMPLE_FOLDER_NAME
    assert settings.headless is True
    assert settings.timeout_ms == DEFAULT_TIMEOUT_MS
    # Daily runs reuse auth_state.json unless ACC_SHOW_LOGIN is set.
    assert settings.show_login is False
    # pages/ later navigate with this helper; keep the ACC URL shape stable.
    assert settings.files_url() == expected_files_url()


def test_load_settings_decrypts_token_with_env_key(tmp_path: Path) -> None:
    """Prove a password_token decrypts when ACC_FERNET_KEY is in the env.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Fresh key so this test does not depend on the developer's local key file.
    key = generate_fernet_key()
    # Encrypt a known password; the loader must return this exact value.
    token = encrypt_password_token(SAMPLE_TOKEN_PASSWORD, key)
    # Store the token as the public repo would: username + ciphertext only.
    write_credentials(tmp_path, username=SAMPLE_CREDENTIALS_USERNAME, password_token=token)
    # No ACC_PASSWORD here, so the token + env key path is the only option.
    environ = required_env()
    environ[ENV_FERNET_KEY] = key
    # Load through the same public API the fixtures will call.
    settings = load_settings(environ=environ, root=tmp_path)
    # Username falls back to credentials.json when ACC_USERNAME is absent.
    assert settings.username == SAMPLE_CREDENTIALS_USERNAME
    # Decryption must recover the original password, not the token string.
    assert settings.password == SAMPLE_TOKEN_PASSWORD


def test_load_settings_decrypts_token_with_key_file(tmp_path: Path) -> None:
    """Prove a git-ignored config/fernet.key can decrypt the token.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Generate a key that will live only in the temp key file.
    key = generate_fernet_key()
    # Encrypt a distinct password so this case cannot pass by env fallback.
    token = encrypt_password_token(SAMPLE_FILE_KEY_PASSWORD, key)
    # Write the public token file first; that also creates config/.
    write_credentials(tmp_path, username=SAMPLE_CREDENTIALS_USERNAME, password_token=token)
    # Reviewer path: drop the separately shared key into config/fernet.key.
    write_fernet_key(tmp_path, key)
    # Neither ACC_PASSWORD nor ACC_FERNET_KEY is set, so only the file remains.
    environ = required_env()
    # Loader must find the key file under the isolated root.
    settings = load_settings(environ=environ, root=tmp_path)
    # File-key decryption is the reviewer-run path after they receive the key.
    assert settings.password == SAMPLE_FILE_KEY_PASSWORD


def test_missing_required_setting_fails_fast(tmp_path: Path) -> None:
    """Prove a missing required env key raises ConfigError immediately.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Copy BASE_ENV so we can delete one key without mutating the constant.
    environ = dict(BASE_ENV)
    # Project ID is required; removing it must stop the run before login.
    del environ[ENV_PROJECT_ID]
    # The message names the missing key so the reviewer knows what to set.
    with pytest.raises(ConfigError, match=ENV_PROJECT_ID):
        # Isolated root still needed so credentials lookup stays sandboxed.
        load_settings(environ=environ, root=tmp_path)


def test_token_without_key_fails_fast(tmp_path: Path) -> None:
    """Prove a token without any Fernet key fails with a clear error.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Build a valid token so the failure is "missing key", not "missing token".
    key = generate_fernet_key()
    token = encrypt_password_token(SAMPLE_HIDDEN_PASSWORD, key)
    # Publish only the token, as the real repository does.
    write_credentials(tmp_path, username=SAMPLE_CREDENTIALS_USERNAME, password_token=token)
    # Omit ACC_PASSWORD and ACC_FERNET_KEY and do not write fernet.key.
    environ = required_env()
    # Reviewers who forgot the out-of-band key should see this, not a crypto traceback.
    with pytest.raises(ConfigError, match=re.escape(MSG_MISSING_FERNET_KEY)):
        load_settings(environ=environ, root=tmp_path)


def test_wrong_key_fails_fast_without_leaking_secrets(tmp_path: Path) -> None:
    """Prove a wrong key fails without printing the password or the key.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Encrypt with one key, then attempt decrypt with a different key.
    token = encrypt_password_token(SAMPLE_HIDDEN_PASSWORD, generate_fernet_key())
    # Store the ciphertext the same way the public repo would.
    write_credentials(tmp_path, username=SAMPLE_CREDENTIALS_USERNAME, password_token=token)
    # Supply a brand-new key that cannot decrypt the token above.
    environ = required_env()
    environ[ENV_FERNET_KEY] = generate_fernet_key()
    # Capture the exception so we can inspect the message for leaks.
    with pytest.raises(ConfigError, match=re.escape(MSG_DECRYPT_FAILED)) as exc_info:
        load_settings(environ=environ, root=tmp_path)
    # Plaintext password must never appear in the fail-fast message.
    assert SAMPLE_HIDDEN_PASSWORD not in str(exc_info.value)
    # The Fernet key itself must also stay out of the message.
    assert environ[ENV_FERNET_KEY] not in str(exc_info.value)


def test_settings_repr_hides_password(tmp_path: Path) -> None:
    """Prove Settings.__repr__ cannot accidentally log the password.

    Args:
        tmp_path: Pytest temp directory used as an isolated project root.
    """
    # Empty credentials.json is enough because BASE_ENV already has a password.
    write_credentials(tmp_path)
    # Load a real Settings object so repr uses the dataclass field flags.
    settings = load_settings(environ=BASE_ENV, root=tmp_path)
    # Debug prints and pytest assertion dumps call repr().
    rendered = repr(settings)
    # The env password value must not show up in the dumped object.
    assert SAMPLE_ENV_PASSWORD not in rendered
    # The password field itself is omitted from repr (field(repr=False)).
    assert f"{CREDENTIALS_TOKEN_FIELD}=" not in rendered
    assert "password=" not in rendered


def test_safe_settings_summary_omits_password() -> None:
    """Prove the run-config log line names folder and user, never the password."""
    # SAMPLE_SETTINGS is the same shape live_acc logs at TEST START.
    text = safe_settings_summary(SAMPLE_SETTINGS)
    # Folder and project id are what a reviewer needs to know the target.
    assert SAMPLE_FOLDER_NAME in text
    assert SAMPLE_PROJECT_ID in text
    # Username is not a secret; it already appears on the login step.
    assert SAMPLE_ENV_USERNAME in text
    # The plaintext password must never appear in a log line.
    assert SAMPLE_ENV_PASSWORD not in text
    # A field named password= would also leak the secret if it were added.
    assert "password=" not in text


def test_encrypt_decrypt_roundtrip() -> None:
    """Prove the encrypt helper reverses with the matching key."""
    # One-off key; not written to disk so nothing leaks into the workspace.
    key = generate_fernet_key()
    # Encrypt a known secret used only inside this test.
    token = encrypt_password_token(SAMPLE_ROUNDTRIP_PASSWORD, key)
    # The token must decrypt back to the original password.
    assert decrypt_password_token(token, key) == SAMPLE_ROUNDTRIP_PASSWORD
    # Ciphertext must not contain the plaintext (gitleaks / casual inspection).
    assert SAMPLE_ROUNDTRIP_PASSWORD not in token


def test_encrypt_cli_writes_token_and_local_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove the CLI writes the token and a local key, never the plaintext.

    Args:
        tmp_path: Isolated project root where the CLI writes config files.
        monkeypatch: Used to stub getpass so the test is non-interactive.
    """
    # Replace the hidden prompt with a fixed password; never type in CI.
    monkeypatch.setattr("utils.encrypt_password.getpass.getpass", lambda _prompt: SAMPLE_CLI_PASSWORD)
    # Run the same entry point a developer would run from the command line.
    assert encrypt_main(["--username", SAMPLE_CLI_USERNAME, "--root", str(tmp_path)]) == 0

    # Read back the public credentials file the CLI just wrote.
    credentials = json.loads(credentials_path(tmp_path).read_text(encoding="utf-8"))
    # The key file is git-ignored in production; here it lives under tmp_path.
    key = fernet_key_path(tmp_path).read_text(encoding="utf-8").strip()
    # Username is stored in plaintext because it is not a secret.
    assert credentials[CREDENTIALS_USERNAME_FIELD] == SAMPLE_CLI_USERNAME
    # The token plus local key must recover the password getpass returned.
    assert decrypt_password_token(credentials[CREDENTIALS_TOKEN_FIELD], key) == SAMPLE_CLI_PASSWORD
    # The committed-style token file must not contain the raw password.
    assert SAMPLE_CLI_PASSWORD not in credentials[CREDENTIALS_TOKEN_FIELD]
