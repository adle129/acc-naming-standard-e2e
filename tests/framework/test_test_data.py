"""FR-05: test_data.py reads JSON rows; business values stay in data/."""

from __future__ import annotations

from dataclasses import fields

import pytest

from utils.test_data import (
    CASES_DIR,
    NAMING_RULES_PATH,
    SUITE_ACCEPTANCE,
    CaseData,
    NamingAttributes,
    case_file,
    delimiter_invalid_project,
    expected_file_name,
    load_row,
    load_suite,
    naming_rules,
    unique_number,
    unique_project,
)

# Mark every test in this module as a framework self-check, not a product case.
pytestmark = pytest.mark.framework

# Loader contract values. The row id lives in data/cases/acceptance.json.
EXPECTED_FIELD_COUNT = 10
ACCEPTANCE_ROW_ID = "upload_delete_restore"
SAMPLE_PREVIEW = "ZZ-ZZ-CA"
SAMPLE_EXTENSION = ".txt"


def test_naming_attributes_has_ten_fields() -> None:
    """Prove NamingAttributes models the 10 validator fields, not the file name."""
    names = []
    # Walk the dataclass so a renamed field shows up in this list.
    for item in fields(NamingAttributes):
        names.append(item.name)
    # A missing field would break later fill helpers.
    assert len(names) == EXPECTED_FIELD_COUNT
    # Project is first because unique values are required on every create.
    assert names[0] == "project"


def test_case_file_path_uses_the_suite_name() -> None:
    """Prove a new suite is a new JSON file, not a change to test_data.py."""
    # Acceptance today; functional later is data/cases/functional.json.
    path = case_file(SUITE_ACCEPTANCE)
    # The helper must point at the committed cases directory.
    assert path.parent == CASES_DIR
    # The file name is the suite name plus .json.
    assert path.name == SUITE_ACCEPTANCE + ".json"
    # The Phase-1 file must already exist so later tests can load it.
    assert path.exists()


def test_load_suite_reads_acceptance_rows_from_json() -> None:
    """Prove the acceptance file is readable as a list of data rows."""
    # This is the only business suite in Phase 1.
    rows = load_suite(SUITE_ACCEPTANCE)
    # An empty file would mean the acceptance test has no input data.
    assert len(rows) >= 1
    ids = []
    for row in rows:
        ids.append(row["id"])
    # The Phase-1 row must stay in the JSON file.
    assert ACCEPTANCE_ROW_ID in ids


def test_load_row_is_the_product_test_entry() -> None:
    """Prove a product test gets usable data from one load_row() call."""
    # M5 will call this once at the start of test_upload_delete_restore.
    data = load_row(SUITE_ACCEPTANCE, ACCEPTANCE_ROW_ID)
    # The return type is data, not a pytest test object.
    assert isinstance(data, CaseData)
    assert data.suite == SUITE_ACCEPTANCE
    assert data.row_id == ACCEPTANCE_ROW_ID
    # Placeholders must already be gone when the test body starts.
    assert data.attributes.project != naming_rules()["placeholder_unique_project"]
    assert data.attributes.number != naming_rules()["placeholder_unique_number"]
    # Fixed dropdowns still come from the JSON file, not from Python constants.
    raw = None
    for row in load_suite(SUITE_ACCEPTANCE):
        if row["id"] == ACCEPTANCE_ROW_ID:
            raw = row
    assert raw is not None
    assert data.attributes.volume == raw["attributes"]["volume"]
    assert data.attributes.type == raw["attributes"]["type"]
    # The upload path must resolve to a real file before Playwright sees it.
    assert data.upload_file.exists()


def test_load_row_fills_new_unique_values_each_time() -> None:
    """Prove two loads do not reuse Project or Number."""
    # Shared-folder duplicates are the failure mode this helper exists to avoid.
    first = load_row(SUITE_ACCEPTANCE, ACCEPTANCE_ROW_ID)
    second = load_row(SUITE_ACCEPTANCE, ACCEPTANCE_ROW_ID)
    assert first.attributes.project != second.attributes.project
    assert first.attributes.number != second.attributes.number


def test_unique_project_meets_rules_file() -> None:
    """Prove unique_project() follows data/rules/naming.json."""
    rules = naming_rules()
    project_rules = rules["project"]
    value = unique_project()
    # Length must stay inside the Project rule from the JSON file.
    assert project_rules["min_length"] <= len(value) <= project_rules["max_length"]
    assert len(value) == project_rules["unique_length"]
    # Every character must come from the rules charset.
    for char in value:
        assert char in project_rules["charset"]
    # A hyphen would already fail the delimiter rule.
    assert rules["delimiter"] not in value


def test_unique_project_changes_between_calls() -> None:
    """Prove two generator calls do not reuse the same Project value."""
    first = unique_project()
    second = unique_project()
    # Shared-folder duplicates are the failure mode this helper exists to avoid.
    assert first != second


def test_unique_values_avoid_demo_names_from_rules() -> None:
    """Prove generated tokens never match forbidden demo values in the rules file."""
    rules = naming_rules()
    values = []
    index = 0
    while index < 8:
        values.append(unique_project())
        values.append(unique_number())
        index = index + 1
    for value in values:
        for demo in rules["forbidden_demo_values"]:
            assert value.lower() != demo.lower()


def test_delimiter_invalid_project_uses_rules_file() -> None:
    """Prove the negative Project value uses delimiter settings from the rules file."""
    rules = naming_rules()
    project = unique_project()
    invalid = delimiter_invalid_project(project)
    # The helper must not invent a second delimiter character.
    assert invalid == project + rules["delimiter"] + rules["delimiter_suffix"]
    # The UI error text is maintained in JSON, not copied into tests.
    assert "delimiter character" in rules["delimiter_error_text"]
    # The rules file itself must be the committed source of those strings.
    assert NAMING_RULES_PATH.exists()


def test_expected_file_name_uses_live_preview() -> None:
    """Prove the expected name is Preview plus extension, not a hardcoded order."""
    name = expected_file_name(SAMPLE_PREVIEW, SAMPLE_EXTENSION)
    # Upload assertions compare the files-list row to this string.
    assert name == SAMPLE_PREVIEW + SAMPLE_EXTENSION
