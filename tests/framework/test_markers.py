"""Suite markers must be registered so -m selection works."""

import pytest

from tests.framework.support import PYTEST_INI_REL, REPO_ROOT, read_text
from utils.setup_auth import FLAG_HEADED

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Phase-1 markers from PRD FR-04; --suite aliases stay Phase 2.
REQUIRED_MARKERS = (
    "smoke",
    "acceptance",
    "functional",
    "integration",
    "framework",
)


def test_required_markers_are_registered(pytestconfig: pytest.Config) -> None:
    """Prove pytest.ini registers every suite marker used by later tests.

    Args:
        pytestconfig: Pytest config fixture that exposes getini('markers').
    """
    # Each markers= line is "name: description"; keep only the name.
    names = set()
    for line in pytestconfig.getini("markers"):
        if not line.strip():
            continue
        name = line.split(":", 1)[0].strip()
        names.add(name)
    # Collect unregistered names for a readable failure.
    missing = []
    for name in REQUIRED_MARKERS:
        if name not in names:
            missing.append(name)
    # pytest -m acceptance / -m framework must not warn about unknown marks.
    assert missing == [], f"Unregistered markers: {missing}; found {sorted(names)}"


def test_addopts_defaults_to_headed() -> None:
    """Prove product runs show the browser so Autodesk challenges are visible.

    Framework tests do not request page, so --headed does not open Chromium for them.
    """
    # pytest.ini addopts is the FR-03 default; CLI can still omit headed later in CI.
    text = read_text(REPO_ROOT / PYTEST_INI_REL)
    # Same flag as setup_auth --headed, so a reviewer types one switch name.
    assert FLAG_HEADED in text
