"""Suite markers must be registered so -m selection works."""

import pytest

pytestmark = pytest.mark.framework

REQUIRED_MARKERS = (
    "smoke",
    "acceptance",
    "functional",
    "integration",
    "framework",
)


def test_required_markers_are_registered(pytestconfig: pytest.Config) -> None:
    names = {line.split(":", 1)[0].strip() for line in pytestconfig.getini("markers") if line.strip()}
    missing = [name for name in REQUIRED_MARKERS if name not in names]
    assert missing == [], f"Unregistered markers: {missing}; found {sorted(names)}"
