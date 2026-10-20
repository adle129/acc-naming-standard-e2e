# Autodesk ACC — Field Validation Rules

- **Source**: probed from the file detail form (field-level validation messages)
- **Purpose**: test-data baseline for validation tests — each rule maps directly to boundary-value test cases

## Validation Rules

| Field | Required | Character type | Length range |
|---|---|---|---|
| Project | ✅ | Alphanumeric | 2 – 6 |
| Number | ✅ | Numeric | 4 – 6 |
| Revision | ✅ | Alphanumeric | 3 – 8 |
| custom fields | ✅ | Numeric | 2 – 5 |

## Delimiter / forbidden-character rule (all attribute fields)

- Attribute values must not contain the naming standard's **delimiter** (`-`) or the forbidden characters `< > : " / | ? * \`.
- Violation message (exact UI text, observed in the restore flow — testcase step 18):
  **"The delimiter character can't be used in an attribute value"**
- Covered by the acceptance test's negative check: Project = `res-1` → error shown; Project = `res1` → error dismissed.

## Boundary-Value Test Cases

For each field, generate cases from its rules (equivalence partitioning + boundary analysis):

| Case | Input example (Project) | Expected |
|---|---|---|
| Empty | `""` | Error: Value is required |
| Too short (min − 1) | `"A"` | Error: length 2 to 6 |
| Minimum valid (min) | `"AB"` | Accepted |
| Maximum valid (max) | `"ABCDEF"` | Accepted |
| Too long (max + 1) | `"ABCDEFG"` | Error: length 2 to 6 |
| Wrong type | `"12"` is alphanumeric ✅; use `"#@"` (not alphanumeric) | Error: type must be Alphanumeric |
| Delimiter in value | `"res-1"` (Project) | Error: The delimiter character can't be used in an attribute value |
| Whitespace-only | `"  "` | Error (required) |

- **Number / custom fields** (Numeric): replace the wrong-type case with letters (e.g. `"ab12"` → type error), and use `123` vs `1234` for the length boundary.
- **Revision** (Alphanumeric): length boundaries are 3 / 8.

## Assertion Notes

- The form surfaces the three rules as explicit messages — assert on the **message text** (or its presence) for each violated rule, not just "some error appeared".
- Test one violation at a time so the failing rule is unambiguous.
- If the same validation component drives all four fields, consider parametrizing the boundary cases across fields to keep the test suite DRY:

  ```python
  @pytest.mark.parametrize("field, value, expected_error", [
      ("Project", "A", "Character length = 2 to 6"),
      ("Number", "12", "Character length = 4 to 6"),
      ...
  ])
  def test_field_validation(field, value, expected_error):
      ...
  ```

- Validation rules are business logic — if the rules change, update this document and the corresponding test data together.
