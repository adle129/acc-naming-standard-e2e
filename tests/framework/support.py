"""Named sample data and helpers for framework tests. No inline hardcode in tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

from utils.config import (
    CREDENTIALS_TOKEN_FIELD,
    CREDENTIALS_USERNAME_FIELD,
    DEFAULT_BROWSER,
    DEFAULT_HEADLESS,
    DEFAULT_SHOW_LOGIN,
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
    Settings,
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
SAMPLE_ORIGINATOR_VALUE = "XXX"
SAMPLE_VOLUME_VALUE = "ZZ"
SAMPLE_LEVEL_VALUE = "ZZ"
SAMPLE_TYPE_VALUE = "CA"
SAMPLE_ROLE_VALUE = "D"
SAMPLE_NUMBER_VALUE = "1234"
SAMPLE_STATUS_VALUE = "S0"
SAMPLE_REVISION_VALUE = "dff"
SAMPLE_CLASSIFICATION_VALUE = "Ac_05"
SAMPLE_CUSTOM_FIELDS_VALUE = "222"
SAMPLE_LOGIN_USERNAME = SAMPLE_ENV_USERNAME
SAMPLE_LOGIN_PASSWORD = "super-secret"
SAMPLE_BANNER_ERROR = "banner still visible"
SAMPLE_SCOPE_ERROR = "boom"
SAMPLE_ACCEPTANCE_TEST_NAME = "test_upload_delete_restore"
SAMPLE_SCREENSHOT_REL = f"reports/screenshots/{SAMPLE_ACCEPTANCE_TEST_NAME}.png"
SAMPLE_FILE_NAME = "ZZ-ZZ-CA.txt"
SAMPLE_UPLOAD_FILE_NAME = "a.txt"
SAMPLE_COMPOSED_FILE_NAME = "WDR5-XXX-ZZ-ZZ-CA-D-4802.txt"
SAMPLE_SHOWING_TWO_ITEMS = "Showing 2 items"
SAMPLE_ITEM_COUNT = 2
SAMPLE_ASSUME_FAIL_MESSAGE = "soft check failed on purpose"
SAMPLE_ASSUME_PASS_MESSAGE = "soft check should stay silent"
SAMPLE_ASSUME_CONTINUED = "later step still ran"
ASSUME_PROBE_FILE_NAME = "test_assume_probe.py"
ASSUME_ADDOPTS_EMPTY = "addopts="
MSG_COUNT_EQUALS_LIST = "item count {count} must equal name list length {length}"
MSG_ITEM_IN_LIST = "{name} must be in the item list"
MSG_ATTRIBUTE_VALUE = "{field} expected {expected}, got {actual}"
STATUS_PROBE_FILE_NAME = "status_probe.txt"
STATUS_PROBE_PATH = REPO_ROOT / "reports" / STATUS_PROBE_FILE_NAME
RESTORE_PROBE_FILE_NAME = "restore_probe.txt"
RESTORE_PROBE_PATH = REPO_ROOT / "reports" / RESTORE_PROBE_FILE_NAME
PROBE_LIST_TIMEOUT_MS = 5000
LIST_SETTLE_MS = 15000
SHOWING_NONEMPTY_PATTERN = re.compile(r"Showing [1-9]")
PROBE_OPTION_LIMIT = 20
PROBE_TEXT_LIMIT = 20
RESTORE_TEXT_HINT = "Restore"
ACCEPT_TEXT_HINT = "Accept"
PROBE_RESTORE_NOT_OPENED = "Restore files page not opened"
PROBE_RESTORE_NOT_VISIBLE = "Restore button not visible after select"
PROBE_SEEDED_DELETED = "seeded a deleted file with upload then delete"
MSG_UPLOADED_NAME_MISSING = "uploaded file containing {project} was not on the Files list"
LISTITEM_ROLE = "listitem"
ASSUME_PROBE_SOURCE = (
    "import pytest\n"
    "\n"
    "def test_probe_failed_assume_continues():\n"
    f"    pytest.assume(False, {SAMPLE_ASSUME_FAIL_MESSAGE!r})\n"
    f"    print({SAMPLE_ASSUME_CONTINUED!r})\n"
)
SAMPLE_SCREENSHOT_STAMP = "20260922_120000_000000"
SAMPLE_SCREENSHOT_BYTES = b"PNG-fake"
SAMPLE_OPEN_URL = SAMPLE_BASE_URL
BASE_PAGE_REL = "pages/base_page.py"
FILES_PAGE_REL = "pages/files_page.py"
FOLDER_LIST_REL = "components/folder_list.py"
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
PYTEST_INI_REL = "pytest.ini"
SAMPLE_STORAGE_COOKIES_KEY = "cookies"
SAMPLE_STORAGE_ORIGINS_KEY = "origins"
SAMPLE_STORAGE_STATE = {
    SAMPLE_STORAGE_COOKIES_KEY: [],
    SAMPLE_STORAGE_ORIGINS_KEY: [],
}
SAMPLE_CONTEXT_IGNORE_HTTPS = True
SAMPLE_CONTEXT_ARGS = {"ignore_https_errors": SAMPLE_CONTEXT_IGNORE_HTTPS}
SAMPLE_SETTINGS = Settings(
    base_url=SAMPLE_BASE_URL,
    project_id=SAMPLE_PROJECT_ID,
    folder_name=SAMPLE_FOLDER_NAME,
    username=SAMPLE_ENV_USERNAME,
    password=SAMPLE_ENV_PASSWORD,
    browser=DEFAULT_BROWSER,
    headless=DEFAULT_HEADLESS,
    timeout_ms=DEFAULT_TIMEOUT_MS,
    show_login=DEFAULT_SHOW_LOGIN,
)
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
