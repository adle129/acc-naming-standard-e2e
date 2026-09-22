"""FR-13 tree must exist so later tasks fill files in place."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.framework

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PATHS = [
    "pages/__init__.py",
    "pages/base_page.py",
    "pages/login_page.py",
    "pages/project_page.py",
    "pages/files_page.py",
    "pages/deleted_items_page.py",
    "dialogs/__init__.py",
    "dialogs/validator_dialog.py",
    "dialogs/upload_validator.py",
    "dialogs/restore_validator.py",
    "dialogs/upload_dialog.py",
    "dialogs/restore_confirm_dialog.py",
    "dialogs/restore_items_dialog.py",
    "dialogs/upload_progress_dialog.py",
    "dialogs/delete_dialog.py",
    "components/__init__.py",
    "components/app_nav.py",
    "components/folder_list.py",
    "components/file_toolbar.py",
    "components/file_row.py",
    "components/row_menu.py",
    "components/toast.py",
    "utils/__init__.py",
    "utils/config.py",
    "utils/test_data.py",
    "utils/file_factory.py",
    "utils/logger.py",
    "utils/auth.py",
    "utils/setup_auth.py",
    "utils/encrypt_password.py",
    "data/files/a.txt",
    "config/credentials.json",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/framework/__init__.py",
    "reports/screenshots",
    "logs",
    ".env.example",
    ".gitignore",
    "pytest.ini",
    "requirements.txt",
    "scripts/verify_framework.py",
]


def test_fr13_scaffold_paths_exist() -> None:
    missing = [rel for rel in EXPECTED_PATHS if not (ROOT / rel).exists()]
    assert missing == [], f"Missing scaffold paths: {missing}"


def test_product_tests_are_not_present_yet() -> None:
    assert not (ROOT / "tests/test_acceptance.py").exists()
    assert not (ROOT / "tests/test_framework_smoke.py").exists()
