"""Load test data files. Business values live under data/, not here.

This module only knows paths, how to read JSON, and how to replace
${unique_project} / ${unique_number}. Pytest runs the tests; this file does not.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

# Repository root: utils/test_data.py -> utils -> repo.
REPO_ROOT = Path(__file__).resolve().parents[1]

# Common locations. New suites add a JSON file under data/cases/.
DATA_DIR_NAME = "data"
CASES_DIR_NAME = "cases"
RULES_DIR_NAME = "rules"
FILES_DIR_NAME = "files"
NAMING_RULES_FILE_NAME = "naming.json"

DATA_DIR = REPO_ROOT / DATA_DIR_NAME
CASES_DIR = DATA_DIR / CASES_DIR_NAME
RULES_DIR = DATA_DIR / RULES_DIR_NAME
FILES_DIR = DATA_DIR / FILES_DIR_NAME
NAMING_RULES_PATH = RULES_DIR / NAMING_RULES_FILE_NAME

# Suite name matches data/cases/<suite>.json. Tests import this, they do not inline it.
SUITE_ACCEPTANCE = "acceptance"
# Row id from data/cases/acceptance.json. Tests import this, they do not inline it.
ROW_UPLOAD_DELETE_RESTORE = "upload_delete_restore"

# Cached rules file so each test does not re-read disk.
_cached_rules: dict | None = None
_unique_counter = 0


@dataclass(frozen=True)
class NamingAttributes:
    """The 10 File Naming Standard attribute fields."""

    project: str
    volume: str
    level: str
    type: str
    role: str
    number: str
    status: str
    revision: str
    classification: str
    custom_fields: str


@dataclass(frozen=True)
class CaseData:
    """One data row from data/cases/<suite>.json, with unique placeholders filled."""

    suite: str
    row_id: str
    description: str
    upload_file: Path
    attributes: NamingAttributes


def case_attribute_summary(attributes: NamingAttributes) -> str:
    """Return the ten attribute fields as one log-safe line.

    Args:
        attributes: Values from load_row(...).attributes.

    Returns:
        Space-separated field=value pairs. No secrets live on this object.
    """
    parts = []
    values = asdict(attributes)
    for field in values:
        parts.append(f"{field}={values[field]}")
    return " ".join(parts)


def naming_rules() -> dict:
    """Return the naming rules file. Read once, then reuse.

    Returns:
        Parsed contents of data/rules/naming.json.
    """
    global _cached_rules
    if _cached_rules is None:
        # Rules are committed data, not generated per run.
        text = NAMING_RULES_PATH.read_text(encoding="utf-8")
        _cached_rules = json.loads(text)
    return _cached_rules


def case_file(suite: str) -> Path:
    """Return the JSON file for a suite.

    Args:
        suite: Suite name, for example 'acceptance' or later 'functional'.

    Returns:
        Path to data/cases/<suite>.json.
    """
    # One file per suite keeps later case sets from sharing one giant JSON.
    return CASES_DIR / (suite + ".json")


def load_suite(suite: str) -> list[dict]:
    """Load every raw case row from a suite file.

    Args:
        suite: Suite name that matches a file in data/cases/.

    Returns:
        The 'cases' list from that file.

    Raises:
        FileNotFoundError: The suite file does not exist yet.
        ValueError: The file has no 'cases' list.
    """
    path = case_file(suite)
    # Missing file is a setup error: add data/cases/<suite>.json, do not edit Python.
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("cases")
    if not isinstance(rows, list):
        raise ValueError("Suite file must contain a 'cases' list: " + str(path))
    return rows


def load_row(suite: str, row_id: str) -> CaseData:
    """Load one JSON row and replace unique Project/Number placeholders.

    Args:
        suite: Suite name, for example 'acceptance'.
        row_id: The 'id' field of that row in the suite file.

    Returns:
        Data ready for a page-object flow.

    Raises:
        KeyError: No row with that id exists in the suite file.
    """
    row = _raw_row(suite, row_id)
    raw_attrs = row["attributes"]
    attributes = NamingAttributes(
        project=_resolve_field(raw_attrs["project"], "project"),
        volume=raw_attrs["volume"],
        level=raw_attrs["level"],
        type=raw_attrs["type"],
        role=raw_attrs["role"],
        number=_resolve_field(raw_attrs["number"], "number"),
        status=raw_attrs["status"],
        revision=raw_attrs["revision"],
        classification=raw_attrs["classification"],
        custom_fields=raw_attrs["custom_fields"],
    )
    upload_rel = row["upload_file"]
    return CaseData(
        suite=suite,
        row_id=row_id,
        description=row.get("description", ""),
        upload_file=REPO_ROOT / upload_rel,
        attributes=attributes,
    )


def _raw_row(suite: str, row_id: str) -> dict:
    """Return the raw JSON object for one row.

    Args:
        suite: Suite name that matches a file in data/cases/.
        row_id: The 'id' field of that row.

    Returns:
        The matching dictionary from the suite file.

    Raises:
        KeyError: No row with that id exists.
    """
    rows = load_suite(suite)
    for row in rows:
        if row.get("id") == row_id:
            return row
    raise KeyError("Row not found: " + suite + "/" + row_id)


def unique_project() -> str:
    """Return a unique Project value from the naming rules.

    Returns:
        A value that matches the Project length/charset rules.
    """
    rules = naming_rules()
    project_rules = rules["project"]
    return _unique_token(project_rules["unique_length"], project_rules["charset"])


def unique_number() -> str:
    """Return a unique Number value from the naming rules.

    Returns:
        A value that matches the Number length/charset rules.
    """
    rules = naming_rules()
    number_rules = rules["number"]
    return _unique_token(number_rules["unique_length"], number_rules["charset"])


def delimiter_invalid_project(project: str) -> str:
    """Build the transient Project value used by the delimiter negative check.

    Args:
        project: A valid unique_project() value.

    Returns:
        project plus the delimiter plus the suffix from the rules file.
    """
    rules = naming_rules()
    return project + rules["delimiter"] + rules["delimiter_suffix"]


def expected_file_name(preview_text: str, extension: str) -> str:
    """Turn the live Preview text into the file name we assert on after upload.

    Args:
        preview_text: Text read from the File Validator Preview control.
        extension: File extension including the dot, for example '.txt'.

    Returns:
        Preview plus extension. The composition order is not hardcoded.
    """
    # Q7: the help page 404s, so Preview is the only authoritative name.
    return preview_text + extension


def _resolve_field(raw_value: str, field_name: str) -> str:
    """Replace a placeholder with a generated unique value.

    Args:
        raw_value: Literal from the case file, or a ${unique_*} placeholder.
        field_name: 'project' or 'number'.

    Returns:
        The literal value, or a newly generated unique token.
    """
    rules = naming_rules()
    if field_name == "project" and raw_value == rules["placeholder_unique_project"]:
        return unique_project()
    if field_name == "number" and raw_value == rules["placeholder_unique_number"]:
        return unique_number()
    return raw_value


def _unique_token(length: int, alphabet: str) -> str:
    """Build a unique token and reject demo or illegal values.

    Args:
        length: How many characters to return.
        alphabet: Allowed characters from the rules file.

    Returns:
        A new token that is not a forbidden demo value and has no delimiter.
    """
    global _unique_counter
    rules = naming_rules()
    attempts = 0
    max_attempts = 20
    while attempts < max_attempts:
        _unique_counter = _unique_counter + 1
        seed = time.time_ns() + _unique_counter
        token = _encode_seed(seed, length, alphabet)
        if _is_allowed_token(token, rules):
            return token
        attempts = attempts + 1
    raise RuntimeError("Could not generate a unique token that is not a demo value.")


def _encode_seed(seed: int, length: int, alphabet: str) -> str:
    """Turn a number into a fixed-length token.

    Args:
        seed: Time-based integer that changes on every call.
        length: Output length.
        alphabet: Allowed characters.

    Returns:
        A string of the requested length using only alphabet characters.
    """
    base = len(alphabet)
    chars = []
    remaining = seed
    index = 0
    while index < length:
        digit = remaining % base
        chars.append(alphabet[digit])
        remaining = remaining // base
        index = index + 1
    chars.reverse()
    token = ""
    for char in chars:
        token = token + char
    return token


def _is_allowed_token(token: str, rules: dict) -> bool:
    """Return True when the token is safe to use as generated test data.

    Args:
        token: Candidate Project or Number value.
        rules: Parsed naming rules.

    Returns:
        False for demo values or any token that contains the delimiter.
    """
    if rules["delimiter"] in token:
        return False
    for demo in rules["forbidden_demo_values"]:
        if token.lower() == demo.lower():
            return False
    return True
