"""Named sample data and helpers for framework tests. No inline hardcode in tests."""

from __future__ import annotations

import json
from pathlib import Path

from utils.config import (
    CREDENTIALS_TOKEN_FIELD,
    CREDENTIALS_USERNAME_FIELD,
    DEFAULT_BROWSER,
    DEFAULT_TIMEOUT_MS,
    ENV_BASE_URL,
    ENV_BROWSER,
    ENV_FOLDER_NAME,
    ENV_HEADLESS,
    ENV_PASSWORD,
    ENV_PROJECT_ID,
    ENV_TIMEOUT_MS,
    ENV_USERNAME,
    FILES_PROJECT_PATH,
    credentials_path,
    fernet_key_path,
)

# Repository root: tests/framework -> tests -> repo.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Isolated values. They are not real ACC secrets; names live here so tests stay readable.
SAMPLE_BASE_URL = "https://acc.autodesk.com"
SAMPLE_PROJECT_ID = "project-id"
SAMPLE_FOLDER_NAME = "Name-standard"
SAMPLE_ENV_USERNAME = "reviewer@example.com"
SAMPLE_ENV_PASSWORD = "plain-from-env"
SAMPLE_CREDENTIALS_USERNAME = "repo-user@example.com"
SAMPLE_IGNORED_USERNAME = "ignored@example.com"
SAMPLE_CLI_USERNAME = "cli@example.com"
SAMPLE_HEADLESS = "true"
SAMPLE_TOKEN_PASSWORD = "token-password"
SAMPLE_FILE_KEY_PASSWORD = "file-key-password"
SAMPLE_HIDDEN_PASSWORD = "hidden-secret"
SAMPLE_ROUNDTRIP_PASSWORD = "roundtrip-secret"
SAMPLE_CLI_PASSWORD = "cli-secret"
SAMPLE_UNUSED_TOKEN = "unused"
SAMPLE_PROJECT_VALUE = "hw472"
SAMPLE_TYPE_VALUE = "CA"
SAMPLE_LOGIN_USERNAME = SAMPLE_ENV_USERNAME
SAMPLE_LOGIN_PASSWORD = "super-secret"
SAMPLE_BANNER_ERROR = "banner still visible"
SAMPLE_SCOPE_ERROR = "boom"
SAMPLE_ACCEPTANCE_TEST_NAME = "test_upload_delete_restore"
SAMPLE_SCREENSHOT_REL = f"reports/screenshots/{SAMPLE_ACCEPTANCE_TEST_NAME}.png"
SAMPLE_SCREENSHOT_STAMP = "20260922_120000_000000"
SAMPLE_SCREENSHOT_BYTES = b"PNG-fake"
SAMPLE_OPEN_URL = SAMPLE_BASE_URL
BASE_PAGE_REL = "pages/base_page.py"
STEP_FILL_PROJECT = "fill Project = {value}"
STEP_EXPECT_BANNER = "expect banner hidden"
STEP_LOGIN = "login as {username} password={password}"
STEP_OPEN_FILES = "open files page"
STEP_CLICK_UPLOAD = "click Upload"
STEP_PICK_TYPE = "pick Type = {value}"
FIRST_STEP_LABEL = "STEP 1"
FORBIDDEN_SLEEP = "time.sleep"
FORBIDDEN_WAIT = "wait_for_timeout"
LOGGER_REL_PATH = "utils/logger.py"
ACCEPTANCE_TEST_REL = "tests/test_acceptance.py"
CANARY_TEST_REL = "tests/test_framework_smoke.py"
AUTH_STATE_REL = "auth_state.json"
SAMPLE_STORAGE_COOKIES_KEY = "cookies"
SAMPLE_STORAGE_ORIGINS_KEY = "origins"
SAMPLE_STORAGE_STATE = {
    SAMPLE_STORAGE_COOKIES_KEY: [],
    SAMPLE_STORAGE_ORIGINS_KEY: [],
}
SAMPLE_INVALID_AUTH_TEXT = "{not-json"
SAMPLE_AUTH_ARRAY_TEXT = "[]"

# Full env used when a test wants the plaintext-password path.
BASE_ENV = {
    ENV_BASE_URL: SAMPLE_BASE_URL,
    ENV_PROJECT_ID: SAMPLE_PROJECT_ID,
    ENV_FOLDER_NAME: SAMPLE_FOLDER_NAME,
    ENV_USERNAME: SAMPLE_ENV_USERNAME,
    ENV_PASSWORD: SAMPLE_ENV_PASSWORD,
    ENV_BROWSER: DEFAULT_BROWSER,
    ENV_HEADLESS: SAMPLE_HEADLESS,
    ENV_TIMEOUT_MS: str(DEFAULT_TIMEOUT_MS),
}


def required_env() -> dict[str, str]:
    """Build the minimum env needed to identify the ACC project.

    Returns:
        A new env mapping that does not include ACC_PASSWORD.
    """
    # Token-decrypt tests must not set ACC_PASSWORD, or the env override wins.
    environ = {
        ENV_BASE_URL: SAMPLE_BASE_URL,
        ENV_PROJECT_ID: SAMPLE_PROJECT_ID,
        ENV_FOLDER_NAME: SAMPLE_FOLDER_NAME,
    }
    return environ


def expected_files_url() -> str:
    """Return the Files URL implied by the sample base URL and project id.

    Returns:
        Absolute ACC Files URL used in assertions.
    """
    # Keep the path fragment in config.py so tests do not repeat the URL shape.
    return f"{SAMPLE_BASE_URL.rstrip('/')}{FILES_PROJECT_PATH}{SAMPLE_PROJECT_ID}"


def write_credentials(root: Path, *, username: str = "", password_token: str = "") -> None:
    """Write a temporary credentials.json under an isolated repo root.

    Args:
        root: Temporary directory treated as the project root.
        username: Value stored in the username field.
        password_token: Fernet token stored in the password_token field.
    """
    # Use the same path helper production code uses.
    path = credentials_path(root)
    # Create config/ even when the temp root is empty.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Persist only the public fields: username + ciphertext.
    path.write_text(
        json.dumps(
            {
                CREDENTIALS_USERNAME_FIELD: username,
                CREDENTIALS_TOKEN_FIELD: password_token,
            }
        ),
        encoding="utf-8",
    )


def write_fernet_key(root: Path, key: str) -> None:
    """Write a temporary git-ignored Fernet key file.

    Args:
        root: Temporary directory treated as the project root.
        key: Fernet key text.
    """
    # Reviewer path: drop the separately shared key next to credentials.json.
    path = fernet_key_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key + "\n", encoding="utf-8")


def read_text(path: Path) -> str:
    """Read a UTF-8 text file.

    Args:
        path: File to read.

    Returns:
        Entire file contents.
    """
    # One helper keeps encoding consistent across framework tests.
    return path.read_text(encoding="utf-8")
