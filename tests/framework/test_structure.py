"""FR-13 tree must exist so later tasks fill files in place."""

from pathlib import Path

import pytest

from tests.framework.support import ACCEPTANCE_TEST_REL, CANARY_TEST_REL

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Repository root: tests/framework -> tests -> repo.
ROOT = Path(__file__).resolve().parents[2]

# Paths required by PRD FR-13. Later tasks fill these files; they must exist now.
EXPECTED_PATHS = [
    "pages/__init__.py",
    "pages/base_page.py",
    "pages/login_page.py",
    "pages/project_page.py",
    "pages/files_page.py",
    "pages/deleted_items_page.py",
    "pages/upload_files_page.py",
    "pages/restore_files_page.py",
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
    "components/file_list.py",
    "components/validator_item.py",
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
    "data/cases/acceptance.json",
    "data/rules/naming.json",
    "config/credentials.json",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/live_support.py",
    "tests/framework/__init__.py",
    "reports/screenshots",
    "logs",
    ".env.example",
    ".gitignore",
    "pytest.ini",
    "requirements.txt",
    "README.md",
    "scripts/verify_framework.py",
]


def test_fr13_scaffold_paths_exist() -> None:
    """Prove every FR-13 scaffold path is already on disk."""
    # Missing names are easier to fix than a single boolean failure.
    missing = []
    for rel in EXPECTED_PATHS:
        if not (ROOT / rel).exists():
            missing.append(rel)
    # An empty list means later tasks can edit files in place.
    assert missing == [], f"Missing scaffold paths: {missing}"


def test_product_tests_are_not_present_yet() -> None:
    """Prove Stage 1 has not created product or canary test modules yet."""
    # Acceptance test is Stage 2 / M5; creating it now would violate the skill.
    assert not (ROOT / ACCEPTANCE_TEST_REL).exists()
    # Canary is also M5; Layer A lives under tests/framework/ until then.
    assert not (ROOT / CANARY_TEST_REL).exists()
