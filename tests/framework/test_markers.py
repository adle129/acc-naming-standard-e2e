"""Suite markers must be registered so -m selection works."""

import pytest

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
