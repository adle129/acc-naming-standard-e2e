# -*- coding: utf-8 -*-
"""
Generate the ACC Files-tool Web UI test-case design as:
  - ACC-Files-TestCaseDesign.xlsx  (editable spreadsheet)
  - ACC-Files-TestCaseDesign.html  (readable in a browser)

Source of truth = the CASES / FIELD_RULES / COVERAGE lists
below. Edit here, then re-run to regenerate both artifacts.
"""
import html as _html
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont

OUT_BASE = "ACC-Files-TestCaseDesign"
OUT_XLSX = OUT_BASE + ".xlsx"
OUT_HTML = OUT_BASE + ".html"

# ---------------------------------------------------------------------------
# Test case data
# Columns: no, id, module, name, desc, steps(list), expected(list),
#          category(Acceptance/Functional), priority(P1/P2/P3)
# Optional: precondition (unnumbered line above steps),
#           condition (highlighted "test condition" inside the Description)
# ---------------------------------------------------------------------------
CASES = [
    # ===== A. Project Member Folder Permission =====
    # Covers the Autodesk "Project Member Folder Permission Levels" model.
    # Two intentionally non-overlapping sub-themes:
    #   - Upload permission   : TC-ACC-01..05  (who may upload, by permission level)
    #   - Delete/Restore perm : TC-PRM-01, TC-PRM-02, TC-DEL-04
    # Ref: https://help.autodesk.com/view/DOCS/ENU/?guid=Folder_Permission_Levels
    # We do NOT test the login mechanism; we verify whether the signed-in account's
    # folder permission level permits the upload / delete / restore operations.
    dict(no=1, id="TC-ACC-01", module="A. Project Member Folder Permission",
         name="Account with NO project access cannot see or use the project",
         desc="A test account that is not a member of the project must not even see the project, "
              "so it can never reach the upload / delete / restore flow.",
         precondition="provision a test account with NO membership / access to the target project.",
         steps=[
             "Sign in with that account.",
             "Look for the project in the project list / home; also try the assignment deep-link directly.",
         ],
         expected=[
             "The project is not listed for this account.",
             "Opening the deep-link is rejected (no access / not found).",
             "There is no path to the folder, therefore no upload / delete / restore is possible.",
         ],
         category="Functional", priority="P1"),

    dict(no=2, id="TC-ACC-02", module="A. Project Member Folder Permission",
         name="Read-only (Viewer) account sees project but cannot upload",
         desc="A read-only account can open the project and the folder, but every upload entry point is "
              "blocked; the server must enforce this, not just the UI.",
         precondition="provision a test account with Read-only (Viewer) permission on the project / folder.",
         steps=[
             "Sign in and open the naming-standard folder.",
             "Inspect the Action Bar / row menu for Upload, drag-and-drop, and any upload deep-link.",
             "Attempt to start an upload through every available path.",
         ],
         expected=[
             "The project and folder are visible (read access works).",
             "Upload control is hidden or disabled; no UI path starts an upload.",
             "A direct upload request is rejected server-side (not only UI-hidden) — see TC-PRM-01.",
         ],
         category="Functional", priority="P1"),

    dict(no=3, id="TC-ACC-03", module="A. Project Member Folder Permission",
         name="Edit (Editor) account can open folder and upload",
         desc="An account with Edit permission can reach the folder, see the Upload button, open the "
              "validator dialog and complete an upload.",
         precondition="provision a test account with Edit permission on the project / folder.",
         steps=[
             "Sign in and open the naming-standard folder (via folder tree or deep-link).",
             "Click Upload; confirm the validator dialog opens.",
             "Fill the attributes and complete the upload of a compliant .txt.",
         ],
         expected=[
             "Folder is visible; the Upload button is enabled.",
             "The Upload validator dialog opens.",
             "The upload succeeds; the file appears in the folder (see Group D for attribute rules).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=4, id="TC-ACC-04", module="A. Project Member Folder Permission",
         name="Project Admin account can open folder and upload",
         desc="A Project Admin account can reach the folder, see the Upload button, open the validator "
              "dialog and complete an upload (same capability as Editor for this flow).",
         precondition="provision a test account with Project Admin permission on the project / folder.",
         steps=[
             "Sign in and open the naming-standard folder.",
             "Click Upload; confirm the validator dialog opens.",
             "Fill the attributes and complete the upload of a compliant .txt.",
         ],
         expected=[
             "Folder is visible; the Upload button is enabled.",
             "The Upload validator dialog opens.",
            "The upload succeeds; the file appears in the folder.",
        ],
        category="Acceptance", priority="P1"),

    dict(no=5, id="TC-ACC-05", module="A. Project Member Folder Permission",
         name="Create + Upload permission can upload files",
         desc="A member granted the 'Create + Upload' folder-permission level (below Edit) can reach the folder "
              "and perform an upload — per the documented model, 'Upload files / Upload to a folder' is granted "
              "at the Create + Upload level and above.",
         precondition="provision a test account with 'Create + Upload' folder permission on the project / folder.",
         steps=[
             "Sign in and open the naming-standard folder.",
             "Confirm the Upload button is present and enabled.",
             "Click Upload, complete the validator, and upload a compliant .txt.",
         ],
         expected=[
             "Folder is visible; the Upload button is enabled (Create + Upload grants upload).",
             "The upload succeeds; the file appears in the folder.",
             "Note: Create + Upload does NOT grant Delete / Restore (those are Edit-level) — see TC-PRM-01 / TC-PRM-02.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=6, id="TC-PRM-01", module="A. Project Member Folder Permission",
         name="Delete / Restore permission matrix — every role",
         condition="Across 3 permission levels — Project Admin (Manage), Editor (Edit), Read-only (View) — each attempting Delete and Restore. (Upload permission is covered separately by TC-ACC-01..05.)",
         desc="Delete and Restore are file actions granted at the Edit level and inherited by Manage (Project Admin); "
              "they are NOT available at View-only levels. This case verifies Delete/Restore availability across "
              "roles — upload is intentionally excluded to avoid overlap with the TC-ACC upload cases.",
         steps=[
             "For each role (Project Admin / Manage, Editor / Edit, Read-only / View), attempt: delete a file and restore a file.",
             "Record for each combination whether the action is available in the UI and whether it succeeds server-side.",
         ],
         expected=[
             "Project Admin (Manage): Delete and Restore both allowed.",
             "Editor (Edit): Delete and Restore both allowed (Restore requires Edit level — see help docs).",
             "Read-only (View): Delete and Restore both blocked (hidden/disabled in UI and enforced server-side).",
         ],
         category="Functional", priority="P1"),

    dict(no=7, id="TC-PRM-02", module="A. Project Member Folder Permission",
         name="Delete & Restore require Edit (or higher: Project Admin); no Edit/Manage → blocked",
         condition="Users WITHOUT Edit/Manage permission (View-only / View+Download / Create+Upload) vs users WITH Edit (Editor) and WITH Manage (Project Admin). Each attempts Delete and Restore.",
         desc="Per the documented permission model, Delete and Restore are file actions granted at the Edit level "
              "and inherited by Manage (Project Admin has Manage on all folders by default). A user with neither "
              "Edit nor Manage cannot perform them.",
         steps=[
             "Sign in as a user with neither Edit nor Manage permission (e.g. View-only or Create+Upload).",
             "Attempt Delete from the row menu and Restore from Deleted Items.",
             "Sign in as an Editor (Edit) and repeat both operations.",
             "Sign in as a Project Admin (Manage) and repeat both operations.",
         ],
         expected=[
             "Without Edit/Manage: Delete and Restore are hidden or disabled; server rejects direct attempts.",
             "With Edit (Editor): Delete and Restore both succeed.",
             "With Manage (Project Admin): Delete and Restore both succeed — Admin inherits edit-level file operations.",
             "Reference: Project Member Folder Permission Levels (Delete / Restore at Edit level; locked files cannot be deleted — TC-DEL-04).",
         ],
         category="Functional", priority="P2"),

    dict(no=8, id="TC-DEL-04", module="A. Project Member Folder Permission",
         name="Delete a locked file is blocked",
         condition="Target file is LOCKED by another user.",
         desc="A file locked by another user cannot be deleted, regardless of the acting user's permission.",
         steps=[
             "Open a file locked by another user → attempt Delete.",
         ],
         expected=[
             "Delete action is disabled / blocked with an explanatory message.",
         ],
         category="Functional", priority="P2"),

    # ===== B. Action Bar / Upload Entry =====
    dict(no=9, id="TC-AB-01", module="B. Action Bar / Upload Entry",
         name="Upload button present and enabled in Action Bar",
         desc="The Action Bar on the Files page exposes an enabled Upload control for an authorized user.",
         steps=[
             "Open the naming-standard folder as an Editor/Admin.",
             "Locate the Action Bar at the top of the Files page.",
         ],
         expected=[
             "An 'Upload' button (split button) is visible and enabled.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=10, id="TC-AB-02", module="B. Action Bar / Upload Entry",
         name="Clicking Upload opens the Upload dialog without URL change",
         desc="Triggering Upload shows the file-selection/upload dialog; the main route does not navigate away.",
         steps=[
             "Click the 'Upload' button in the Action Bar.",
             "Observe the URL and the modal that appears.",
         ],
         expected=[
             "An Upload dialog/modal appears.",
             "The browser URL is unchanged (no full navigation) — it is an in-page overlay.",
         ],
         category="Functional", priority="P2"),

    dict(no=11, id="TC-AB-03", module="B. Action Bar / Upload Entry",
         name="'Deleted Items' entry present in Action Bar",
         desc="The Action Bar exposes the Deleted Items entry used later in the restore flow.",
         steps=[
             "With at least one deleted file, inspect the Action Bar.",
             "Click 'Deleted Items'.",
         ],
         expected=[
             "A 'Deleted Items' button is present.",
             "Clicking it navigates to moduleId=deleted and lists deleted files.",
         ],
         category="Functional", priority="P2"),

    # ===== C. Upload (Workflow & Controls) =====
    # ----- Workflow: end-to-end upload-flow outcomes (single .txt, then two-file) -----
    dict(no=12, id="TC-UPL-01", module="C. Upload (Workflow & Controls)",
         name="Workflow — Upload a compliant .txt file (happy path)",
         desc="End-to-end upload of a single valid .txt file with all 11 attributes filled correctly. This is the reference flow reused by the other workflow cases.",
         steps=[
             "Click Upload -> Select files -> choose a.txt.",
             "On the 'Upload files' page, fill all 11 attributes (Project=test2, Originator=XXX, Volume=ZZ, Level=ZZ, Type=CA, Role=D, Number=1234, Status=S0, Revision=dff, Classification=Ac_05, custom fields=222).",
             "Click Upload; wait for progress 0%->100%->'Uploaded to Name-standard'.",
             "Click Done.",
         ],
         expected=[
             "Validator errors clear and Upload is enabled once all fields valid.",
             "Toast: '1 file has been successfully uploaded.'",
             "After Done the folder view shows the new file: composed name 'test2-XXX-ZZ-ZZ-CA-D-1234.txt' with version badge V1 — correct name/version in the Files list (file-list verification folded in here; no separate list-only case).",
             "The row displays the name and version badge; the 4 associated attributes (Status / Revision / Classification / custom fields) are shown as metadata and are NOT part of the file name.",
             "The row is selectable via its checkbox and the Action Bar reacts to the selection (list rendering + selectability verified as part of this flow).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=13, id="TC-UPL-09", module="C. Upload (Workflow & Controls)",
         name="Workflow — 'Remove all' -> Remove returns to Upload dialog; Done leaves no new file",
         desc="After a successful .txt upload, on the 'Upload files' page choose 'Remove all' -> confirm 'Remove'; the flow returns to the Upload dialog and Done produces no new file in the folder.",
         steps=[
             "Complete the upload of a .txt up to the 'Upload files' page (files uploaded successfully).",
             "Click 'Remove all'.",
             "In the Remove-all confirmation dialog, click 'Remove'.",
             "The page returns to the Upload dialog (no pending file).",
             "Click 'Done'.",
         ],
         expected=[
             "No file is created in the folder.",
             "The Files list shows no new entry.",
         ],
         category="Functional", priority="P2"),

    dict(no=14, id="TC-UPL-26", module="C. Upload (Workflow & Controls)",
         name="Workflow — 'Cancel' on Upload files page returns to Upload dialog; Done leaves no new file",
         desc="After a successful .txt upload, clicking 'Cancel' on the 'Upload files' page returns to the Upload dialog; 'Done' then leaves no new file in the folder.",
         steps=[
             "Complete the upload of a .txt up to the 'Upload files' page (files uploaded successfully).",
             "Click 'Cancel' on the 'Upload files' page.",
             "The page returns to the Upload dialog (no pending file).",
             "Click 'Done'.",
         ],
         expected=[
             "No file is created in the folder.",
             "The Files list shows no new entry.",
         ],
         category="Functional", priority="P2"),

    dict(no=15, id="TC-UPL-27", module="C. Upload (Workflow & Controls)",
         name="Workflow — 'Remove all' -> Cancel stays on Upload files page",
         desc="After a successful .txt upload, choosing 'Remove all' then cancelling the confirmation keeps the user on the 'Upload files' page with the file still pending.",
         steps=[
             "Complete the upload of a .txt up to the 'Upload files' page (files uploaded successfully).",
             "Click 'Remove all'.",
             "In the Remove-all confirmation dialog, click 'Cancel'.",
         ],
         expected=[
             "The page stays on the 'Upload files' page; the pending upload is retained, not removed.",
         ],
         category="Functional", priority="P3"),

    dict(no=16, id="TC-UPL-28", module="C. Upload (Workflow & Controls)",
         name="Workflow — Bypass naming standard -> confirm Upload -> lands in Holding area",
         desc="After a successful .txt upload, leave at least one naming-standard error unresolved and click 'Upload'; the 'Upload file?' confirmation appears, and confirming routes the file to the Holding area (Viewable).",
         steps=[
             "Complete the upload of a .txt up to the 'Upload files' page, leaving >=1 naming-standard error unresolved.",
             "Click 'Upload'.",
             "The 'Upload file?' dialog appears with the message: \"This file will not display in Name-standard applied folder yet as it doesn't conform to the compliance settings. You can validate the file later in the holding area.\"",
             "Click 'Upload' in that confirmation dialog.",
             "The page returns to the Upload dialog; the upload status shows 'Viewable in holding area'.",
             "Click 'View' to navigate to the Holding area page.",
         ],
         expected=[
             "The file is NOT placed in the Name-standard applied folder.",
             "On the Holding area page (moduleId=holding-area) the just-added file is listed.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=17, id="TC-UPL-29", module="C. Upload (Workflow & Controls)",
         name="Workflow — Bypass naming standard -> Cancel confirmation stays on Upload files page",
         desc="After a successful .txt upload, clicking 'Upload' with unresolved errors shows the 'Upload file?' dialog; cancelling it returns to the 'Upload files' page with the file still pending.",
         steps=[
             "Complete the upload of a .txt up to the 'Upload files' page, leaving >=1 naming-standard error unresolved.",
             "Click 'Upload'; the 'Upload file?' confirmation dialog appears.",
             "Click 'Cancel' in the confirmation dialog.",
         ],
         expected=[
             "The page returns to the 'Upload files' page; the pending file is retained (not uploaded, not in holding area).",
         ],
         category="Functional", priority="P2"),

    dict(no=18, id="TC-UPL-30", module="C. Upload (Workflow & Controls)",
         name="Workflow — Upload two differently-named .txt files; both listed in Upload dialog",
         desc="Repeat the happy-path upload for a second .txt with a different name; after returning to the Upload dialog both uploaded files are listed together.",
         steps=[
             "Repeat TC-UPL-01 to upload a first .txt (name A).",
             "Start a second upload of a different .txt (name B) and complete it up to the 'Upload files' page.",
             "Click 'Upload', then return to the Upload dialog.",
         ],
         expected=[
             "The Upload dialog lists both uploaded files (name A and name B) together.",
         ],
         category="Functional", priority="P2"),

    dict(no=19, id="TC-UPL-25", module="C. Upload (Workflow & Controls)",
         name="Workflow — Re-upload an existing file name -> version increments (V1 -> V2)",
         desc="Uploading a .txt whose composed name equals an existing file (e.g. test-XXX-ZZ-XX-AF-A-12345.txt) must not create a second file — it should create a new version.",
         steps=[
             "Ensure the folder already contains test-XXX-ZZ-XX-AF-A-12345.txt at V1.",
             "Upload another local .txt with an identical attribute set and complete the validator.",
             "Inspect the folder listing and the file's version badge.",
         ],
         expected=[
             "The folder still lists exactly ONE test-XXX-ZZ-XX-AF-A-12345 file.",
             "Its version increments from V1 to V2; no duplicate row appears.",
         ],
         category="Acceptance", priority="P1"),


    #
    dict(no=20, id="TC-UPL-31", module="C. Upload (Workflow & Controls)",
         name="Workflow — Uploaded file persists across a sign-out / sign-in cycle",
         precondition="a compliant .txt upload has just completed (TC-UPL-01) and the file is visible in the Files list.",
         desc="The upload is committed server-side, not just rendered optimistically in the client: after signing out and signing back in, the file is still present with the same name, version and attributes.",
         steps=[
             "Complete TC-UPL-01 and confirm the file is listed (name 'test2-XXX-ZZ-ZZ-CA-D-1234.txt', V1).",
             "Sign out of ACC.",
             "Sign back in with the same account and open the same project / folder.",
             "Locate the file and open its detail.",
         ],
         expected=[
             "The file is still present in the folder after re-authentication.",
             "Composed name and version (V1) are unchanged.",
             "All 11 attributes are intact, including the 4 associated attributes stored as metadata (Status / Revision / Classification / custom fields).",
             "If the file is MISSING after re-login, the earlier success toast was an optimistic UI update that was never committed — log as a defect (data loss).",
         ],
         category="Acceptance", priority="P1"),

    # ----- Controls / UI: validator fields, error presentation, boundaries, holding-area config -----
    dict(no=21, id="TC-UPL-02", module="C. Upload (Workflow & Controls)",
         name="Control — File name composed from the 7 naming-convention attributes only",
         desc="Verify the stored file name is built only from naming attributes, and associated attributes never leak into the name.",
         steps=[
             "Upload with distinct values per attribute (e.g. test2-XXX-ZZ-ZZ-CA-D-1234).",
             "Open the file's attribute detail after upload.",
         ],
         expected=[
             "Stored name = Project-Originator-Volume-Level-Type-Role-Number + '.txt'.",
             "Status / Revision / Classification / custom fields are stored as metadata and do NOT appear in the file name.",
         ],
         category="Functional", priority="P1"),

    dict(no=22, id="TC-UPL-03", module="C. Upload (Workflow & Controls)",
         name="Control — Original .txt extension is preserved",
         desc="The original file extension is kept and not renamed or stripped during composition.",
         steps=[
             "Upload a .txt file and complete the validator.",
         ],
         expected=[
             "Composed name ends with '.txt'; the extension is preserved exactly.",
         ],
         category="Functional", priority="P1"),

    dict(no=23, id="TC-UPL-04", module="C. Upload (Workflow & Controls)",
         name="Control — Upload enabled only when all errors resolved",
         desc="The Upload button stays disabled while any validation error is present and enables the moment the last error clears.",
         steps=[
             "Open the validator with all fields empty; observe the Upload button.",
             "Fill attributes one by one; observe the button state after each.",
         ],
         expected=[
             "Upload is disabled while any error is present.",
             "Upload becomes enabled exactly when the last error clears.",
         ],
         category="Functional", priority="P1"),

    dict(no=24, id="TC-UPL-05", module="C. Upload (Workflow & Controls)",
         name="Control — Attribute values persisted after upload",
         desc="All 11 attribute values entered at upload are stored exactly as entered.",
         steps=[
             "Complete TC-UPL-01, then open the file's attribute editor.",
         ],
         expected=[
             "All 11 attributes show exactly the values entered at upload (no truncation/normalisation surprises).",
         ],
         category="Functional", priority="P2"),

    dict(no=25, id="TC-UPL-06", module="C. Upload (Workflow & Controls)",
         name="Control — Upload with all attributes empty blocked",
         desc="Submitting with nothing filled shows the compliance banner and disables Upload.",
         steps=[
             "Select a file; leave all 11 attributes empty.",
         ],
         expected=[
             "Red banner: '1 file doesn't comply with compliance settings. Resolve errors with: naming standard (1), and required attributes (1).'",
             "All 11 cells flagged; Upload disabled.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=26, id="TC-UPL-07", module="C. Upload (Workflow & Controls)",
         name="Control — One required attribute left empty flagged",
         desc="Leaving a single required attribute (Number) empty produces a targeted error.",
         steps=[
             "Fill 10 of 11 attributes; leave Number empty.",
         ],
         expected=[
             "Banner shows 'required attributes (1)'; the Number cell is flagged red; Upload disabled.",
         ],
         category="Functional", priority="P1"),

    dict(no=27, id="TC-UPL-08", module="C. Upload (Workflow & Controls)",
         name="Control — Required-attribute tooltip content is correct",
         desc="Hovering a flagged cell shows the exact rule (required / char type / length).",
         steps=[
             "On the flagged Number cell, hover the validation indicator.",
         ],
         expected=[
             "Tooltip: 'Value must be: 1. Value is required 2. Character type: Numeric 3. Character length: 4 to 6'.",
         ],
         category="Functional", priority="P2"),

    dict(no=28, id="TC-UPL-10", module="C. Upload (Workflow & Controls)",
         name="Control — Attribute character-length boundaries (data-driven)",
         desc="Each text attribute is validated at min-1 / min / max / max+1. Values tried per attribute:",
         steps=[
             "Project (Alphanumeric 2-6): a / ab / abcdef / abcdefg",
             "Number (Numeric 4-6): 123 / 1234 / 123456 / 1234567",
             "Revision (Alphanumeric 3-8): ab / dff / abcdefgh / abcdefghi",
             "custom fields (Numeric 2-5): 1 / 22 / 22222 / 222222",
             "Enter each value and observe validation + Upload state.",
         ],
         expected=[
             "Length 1 and max+1 rejected; min and max accepted (e.g. Project 1 & 7 fail, 2 & 6 pass).",
             "Upload disabled for any out-of-range value.",
         ],
         category="Functional", priority="P2"),

    dict(no=29, id="TC-UPL-11", module="C. Upload (Workflow & Controls)",
         name="Control — Non-numeric value in a Numeric field",
         desc="Entering letters in Number (a Numeric field) is rejected.",
         steps=[
             "Enter 'abcd' in the Number attribute.",
         ],
         expected=[
             "Validation error (Character type: Numeric); Upload disabled.",
         ],
         category="Functional", priority="P2"),

    dict(no=30, id="TC-UPL-12", module="C. Upload (Workflow & Controls)",
         name="Control — Special characters in Project",
         desc="Special characters in an attribute value are rejected by the naming standard.",
         steps=[
             "Enter 'test@#' in the Project attribute.",
         ],
         expected=[
             "'special characters' error listed in the banner; Upload disabled.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=31, id="TC-UPL-13", module="C. Upload (Workflow & Controls)",
         name="Control — Value contains the delimiter '-' (key negative)",
         desc="An attribute value that itself contains the filename delimiter must be rejected — the product's documented limitation.",
         steps=[
             "Enter 'test-re-' in the Project attribute (delimiter is '-').",
         ],
         expected=[
             "Banner reports 'naming standard (1), and special characters (1)'.",
             "The cell is flagged; Upload disabled; name preview shows the ambiguity.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=32, id="TC-UPL-14", module="C. Upload (Workflow & Controls)",
         name="Control — Delimiter-inside-value across configured delimiters",
         desc="Same behaviour when the standard is configured for '-', '_', or '.' in turn.",
         steps=[
             "Repeat TC-UPL-13 with the standard configured for each of '-', '_', '.' delimiters.",
         ],
         expected=[
             "A value containing the active delimiter is rejected in all three configurations.",
         ],
         category="Functional", priority="P2"),

    dict(no=33, id="TC-UPL-16", module="C. Upload (Workflow & Controls)",
         name="Control — Leading / trailing spaces in a value",
         desc="Whitespace handling must be explicit and consistent, never silently stored.",
         steps=[
             "Enter '  test2  ' in the Project attribute.",
         ],
         expected=[
             "Either trimmed-and-accepted or rejected as invalid — behaviour must be explicit and consistent.",
         ],
         category="Functional", priority="P3"),

    dict(no=34, id="TC-UPL-17", module="C. Upload (Workflow & Controls)",
         name="Control — Non-compliant file with Holding area ON",
         desc="When the Holding area is enabled, a non-compliant file is quarantined there instead of the folder (see the bypass workflow TC-UPL-28/29 for the user-facing path).",
         steps=[
             "With Holding area ON, upload a file and leave errors unresolved; choose to continue without fixing.",
         ],
         expected=[
             "Compliant files land in the folder; the non-compliant file lands in the Holding area tab and is not a normal file.",
         ],
         category="Functional", priority="P2"),

    dict(no=35, id="TC-UPL-18", module="C. Upload (Workflow & Controls)",
         name="Control — Non-compliant file with Holding area OFF (test-project config)",
         desc="In the test project (Holding area OFF), an unresolved file cannot enter the folder — Upload is blocked.",
         steps=[
             "With Holding area OFF, upload a file and leave errors unresolved.",
         ],
         expected=[
             "Upload is blocked (button disabled) — the file cannot enter the folder unresolved.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=36, id="TC-UPL-20", module="C. Upload (Workflow & Controls)",
         name="Control — Remove a single file from the validator",
         desc="Removing one row from a multi-file selection recalculates the banner.",
         steps=[
             "Add 2 files, click the remove (X) on one row.",
         ],
         expected=[
             "Row removed; banner recalculates for the remaining file(s).",
         ],
         category="Functional", priority="P3"),

    dict(no=37, id="TC-UPL-22", module="C. Upload (Workflow & Controls)",
         name="Control — Original file name containing special characters < > : \" / | ? * \\",
         desc="The local .txt file name itself contains special characters; verify how upload treats them given the stored name is composed from attributes.",
         steps=[
             "Prepare a .txt file whose local name contains special characters, e.g. a<b>c:d\"e|f?g*h.txt (create where the OS allows).",
             "Click Upload -> Select files -> choose the file.",
             "Observe the validator / file-list behaviour; complete the 11 attributes if allowed.",
         ],
         expected=[
             "Behaviour is explicit: either the file is rejected with a clear message, or the stored name is composed from the 7 naming attributes so the special characters never propagate into ACC.",
             "No file whose stored name contains special characters can be created (they would break the naming standard). Record actual behaviour.",
         ],
         category="Functional", priority="P2"),

    dict(no=38, id="TC-UPL-23", module="C. Upload (Workflow & Controls)",
         name="Control — Original file name containing spaces",
         desc="A local .txt file name with spaces (e.g. 'my test file.txt') is uploaded; verify space handling.",
         steps=[
             "Prepare 'my test file.txt' and select it for upload.",
             "Complete the 11 attributes and submit.",
         ],
         expected=[
             "Spaces in the original local name are handled explicitly (trimmed / rejected / ignored) — never silently stored.",
             "The stored name (composed from attributes) contains no spaces; behaviour is consistent across uploads. Record actual.",
         ],
         category="Functional", priority="P2"),

    dict(no=39, id="TC-UPL-24", module="C. Upload (Workflow & Controls)",
         name="Control — Original file name of 257 characters (length boundary)",
         desc="Upload a .txt whose local name is 257 chars; check whether the naming standard / folder imposes a total-name length limit.",
         steps=[
             "Prepare a .txt with a 257-character file name and select it for upload.",
             "Observe whether the validator or the folder's naming standard flags a length error.",
             "Cross-check the File Naming Standard help page for any total-length rule.",
         ],
         expected=[
             "If a length limit exists, the file is rejected with a clear message; if not, the composed name (bounded by per-attribute lengths) is stored and the original 257-char name does not propagate.",
             "Documented rule confirmed and recorded as actual result.",
         ],
         category="Functional", priority="P2"),

    # ----- Failure handling: uploading a local file fails at the Upload / processing stage -----
    dict(no=40, id="TC-NET-01", module="C. Upload (Workflow & Controls)",
         name="Failure — No network connection at upload start",
         desc="The workstation has no network connectivity when the user attempts an upload.",
         steps=[
             "Disconnect the network, then open the Files page and start an upload.",
             "Fill valid attributes and click Upload.",
             "Reconnect the network and observe the recovery path.",
         ],
         expected=[
             "A clear failure message is shown (no silent hang, no partial/corrupt file created).",
             "Per docs: 'Click Retry to try again if network or server issues are resolved' — after reconnection, Retry (or re-upload) completes successfully.",
         ],
         category="Functional", priority="P2"),

    dict(no=41, id="TC-NET-02", module="C. Upload (Workflow & Controls)",
         name="Failure — Server error responses (500 / 502 / 503 / 504) when Upload is clicked",
         desc="The Upload-stage server check fails with each common server / gateway error code in turn (500, 502, 503, 504); all four must surface an explicit failure and offer the same Retry path.",
         steps=[
             "Fill all 11 attributes with valid values.",
             "For each status code in turn (500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout): simulate the server returning that code (proxy/mock, e.g. Playwright route fulfil), then click Upload.",
             "Observe and record the error surface for each code — message wording, whether Retry is offered, whether the dialog stays usable.",
             "Restore the server (remove the mock) and click Retry; confirm the upload completes.",
         ],
         expected=[
             "For every one of 500 / 502 / 503 / 504: Upload fails with an explicit error — files can't be added to the Files tool (documented Upload-stage failure).",
             "Failure handling is CONSISTENT across the four codes: no silent hang, no stuck progress bar, no blank/broken error surface; a Retry option is offered in all four.",
             "After server recovery, Retry completes the upload; no duplicate or partial file is created by any failed attempt.",
             "Record any difference in wording between codes (e.g. 503 'service unavailable' vs 504 'gateway timeout') — differences are a finding, not a failure.",
         ],
         category="Functional", priority="P2"),

    dict(no=42, id="TC-NET-03", module="C. Upload (Workflow & Controls)",
         name="Failure — Network disconnected at the moment of clicking Upload",
         desc="Settings are filled, the user clicks Upload and the network drops exactly at submit time.",
         steps=[
             "Fill all 11 attributes with valid values.",
             "Disable the network immediately when clicking Upload.",
             "Observe the result, then reconnect and retry.",
         ],
         expected=[
             "Explicit failure feedback (network connectivity is one of the documented Upload-stage checks).",
             "Retry / re-upload succeeds after reconnection; no partial file, no phantom entry in the list.",
         ],
         category="Functional", priority="P2"),

    dict(no=43, id="TC-NET-04", module="C. Upload (Workflow & Controls)",
         name="Failure — Network drops during processing (after successful submit)",
         desc="Upload is submitted OK, the upload dialog shows processing progress, then the network drops mid-processing.",
         steps=[
             "Submit a valid upload; while the dialog shows processing (0%→100%), disconnect the network.",
             "Observe the dialog / toast / final state.",
             "Reconnect and use Retry if offered.",
         ],
         expected=[
             "The failure is surfaced clearly (not a silent success, no stuck progress bar without feedback).",
             "Retry / re-upload completes; final state is consistent — exactly one file, correct version, no orphan entry.",
             "Record whether any automatic retry exists or only manual Retry.",
         ],
         category="Functional", priority="P2"),

    dict(no=44, id="TC-NET-05", module="C. Upload (Workflow & Controls)",
         name="Failure — Backend server unavailable during processing",
         desc="Upload submitted OK; the backend server becomes unavailable (500/504) while the upload dialog is processing.",
         steps=[
             "Submit a valid upload; during processing, make the server return 500/504 (proxy/mock or outage).",
             "Observe the dialog / toast / final state.",
             "Recover the server and retry.",
         ],
         expected=[
             "Processing failure is reported explicitly; the file is not added to the Files tool on failure (documented behaviour).",
             "Retry after recovery completes the upload; no duplicate/partial result. Record actual retry behaviour.",
         ],
         category="Functional", priority="P2"),

    dict(no=45, id="TC-FILE-01", module="C. Upload (Workflow & Controls)",
         name="Failure — File size over 5 TB",
         desc="A .txt larger than 5 TB exceeds the documented limit — files over 5 TB are listed as a common Process-for-viewing failure.",
         steps=[
             "Prepare (or simulate at API level) a .txt larger than 5 TB and upload it with valid attributes.",
             "Observe the Upload stage, then the Process-for-viewing stage.",
         ],
         expected=[
             "Documented behaviour: files over 5 TB can't be viewed / compared / published to sheets / marked up / exported.",
             "Record actual Upload-stage UI behaviour (accepted vs rejected) and the error surface.",
             "Note: a real 5 TB file is likely infeasible in the test environment — verify via documentation plus the largest feasible probe; mark as design-verified.",
         ],
         category="Functional", priority="P3"),

    dict(no=46, id="TC-FILE-02", module="C. Upload (Workflow & Controls)",
         name="Failure — Password-protected file upload",
         desc="A password-protected file passes the Upload stage but fails the Process-for-viewing checks (documented).",
         steps=[
             "Upload a password-protected file (e.g. password-protected Office/zip container) with valid naming attributes.",
             "Observe the Upload stage result, then attempt to view / compare / export it.",
         ],
         expected=[
             "Upload stage succeeds (file type & name comply); the file is stored with its compliant composed name.",
             "Process-for-viewing fails as documented: can't be viewed, compared, published to sheets, marked up, or exported.",
             "Error messaging is clear; record actual behaviour.",
         ],
         category="Functional", priority="P2"),

    # ===== D. Delete (Workflow & Controls) =====
    # ----- Workflow: delete outcomes that change the file's state -----
    dict(no=47, id="TC-DEL-01", module="D. Delete (Workflow & Controls)",
         name="Workflow — Delete a compliant file",
         precondition="the project folder already contains a compliant .txt file (uploaded per TC-UPL-01).",
         desc="Delete a file via the row menu / Action Bar Delete, then confirm it moved to Deleted Items. Row selectability is verified here as part of the delete flow (no separate list-only case).",
         steps=[
             "In the Files list, select the uploaded file's row via its checkbox — the row highlights and the Action Bar reacts.",
             "Open the row's '…' (More) menu → Delete (or use the Action Bar Delete).",
             "Confirm in the Delete dialog.",
             "Open 'Deleted Items' and observe the item count / list.",
         ],
         expected=[
             "Toast: '1 file was deleted.'",
             "The row disappears from the Files list; after a page refresh it is still absent.",
             "Deleted Items count increases by exactly 1 and now lists the deleted file (was 0 before, 1 after).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=48, id="TC-DEL-03", module="D. Delete (Workflow & Controls)",
         name="Workflow — Delete is a soft delete (recoverable)",
         precondition="the project folder already contains a compliant .txt file.",
         desc="A deleted file remains recoverable via Deleted Items / Restore.",
         steps=[
             "Delete the file (per TC-DEL-01) and confirm it leaves the Files list.",
             "Open Deleted Items: the file is listed and the count went up by 1.",
             "Restore it (see Group F) and return to Deleted Items.",
         ],
         expected=[
             "Deleted Items count decreased by 1 again after the restore.",
             "File returns to the folder with its version and all attribute values intact.",
         ],
         category="Functional", priority="P1"),

    dict(no=49, id="TC-DEL-06", module="D. Delete (Workflow & Controls)",
         name="Workflow — Cancel delete confirmation leaves file intact",
         precondition="the project folder already contains a compliant .txt file.",
         desc="Cancelling at the confirmation dialog changes nothing.",
         steps=[
             "Select the file, trigger Delete, then Cancel at the confirmation dialog.",
             "Open Deleted Items and check the item count.",
         ],
         expected=[
             "No toast; file remains in the folder.",
             "Deleted Items count is unchanged (file absent from the list).",
         ],
         category="Functional", priority="P3"),

    # ----- Controls / UI: row menu and delete dialog -----
    dict(no=50, id="TC-RM-01", module="D. Delete (Workflow & Controls)",
         name="Control — Row '…' (More) menu opens and lists actions",
         precondition="the project folder already contains a compliant .txt file.",
         desc="The per-row overflow menu (portal-rendered) opens and exposes Delete/Open/Download etc.",
         steps=[
             "Hover/click the row's '…' button.",
             "Observe the menu items.",
         ],
         expected=[
             "A menu opens (rendered in a portal, not inside the row); items include at least Delete, Open, Download.",
             "Clicking outside closes it without side effects.",
         ],
         category="Functional", priority="P1"),

    dict(no=51, id="TC-DEL-02", module="D. Delete (Workflow & Controls)",
         name="Control — Delete confirmation dialog appears",
         precondition="the project folder already contains a compliant .txt file.",
         desc="Delete requires an explicit confirmation dialog before execution.",
         steps=[
             "Trigger Delete from the row menu.",
         ],
         expected=[
             "A Delete confirmation dialog appears; the delete does not execute without confirmation.",
         ],
         category="Functional", priority="P2"),

    dict(no=52, id="TC-DEL-07", module="D. Delete (Workflow & Controls)",
         name="Control — Delete is not offered in the Action Bar when no file is selected",
         precondition="the project folder already contains a compliant .txt file.",
         desc="With no row selected, the Action Bar must not expose a Delete action (it only appears once one or more files are selected).",
         steps=[
             "Open the folder with the .txt file present and select NOTHING (clear any checkbox).",
             "Observe the Action Bar and the per-row '…' menu.",
             "Now select one file and re-observe the Action Bar; then select two files and observe again.",
         ],
         expected=[
             "With no selection: no Delete action is shown in the Action Bar (Upload etc. remain available).",
             "After selecting 1 file: Delete appears and applies to that file.",
             "After selecting 2 files: Delete appears and applies to the whole selection (label reflects the count).",
         ],
         category="Functional", priority="P2"),

    dict(no=53, id="TC-DEL-08", module="D. Delete (Workflow & Controls)",
         name="Workflow — Holding area 'Delete all' (no file selected)",
         precondition="a non-compliant .txt has been uploaded and is showing in the Holding area; NO file is selected in the list.",
         desc="With nothing selected the Holding area action bar offers 'Delete all'; the confirmation dialog can be cancelled or confirmed, and confirming removes the file from the Holding area and moves it to Deleted Items.",
         steps=[
             "Open the Holding area (the non-compliant .txt is listed, nothing selected).",
             "Confirm the action bar shows 'Delete all' (bulk action available with no selection).",
             "Click 'Delete all' → the 'Delete file?' dialog appears → click 'Cancel'.",
             "Confirm you are returned to the Holding area with the file still listed.",
             "Click 'Delete all' again → in the 'Delete file?' dialog click 'Delete'.",
             "Observe the Holding area list, then open Deleted Items.",
         ],
         expected=[
             "With no selection, the bulk action reads 'Delete all'.",
             "Cancel returns to the Holding area with the file still present (no change).",
             "Confirming Delete removes the file from the Holding area list.",
             "The file now appears in Deleted Items (count +1).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=54, id="TC-DEL-09", module="D. Delete (Workflow & Controls)",
         name="Workflow — Holding area 'Delete (n)' with a file selected",
         precondition="a non-compliant .txt is showing in the Holding area; the file IS selected (checkbox checked).",
         desc="With one file selected the Holding area action bar offers 'Delete (1)'; cancelling keeps the file, confirming removes it from the Holding area and moves it to Deleted Items.",
         steps=[
             "Open the Holding area and select the file's checkbox.",
             "Confirm the action bar shows 'Delete (1)' (count reflects the selection).",
             "Click 'Delete (1)' → the 'Delete file?' dialog appears → click 'Cancel'.",
             "Confirm you are returned to the Holding area with the file still selected/listed.",
             "Click 'Delete (1)' again → in the 'Delete file?' dialog click 'Delete'.",
             "Observe the Holding area list, then open Deleted Items.",
         ],
         expected=[
             "With 1 file selected, the action reads 'Delete (1)'; with n selected it reads 'Delete (n)'.",
             "Cancel returns to the Holding area with the file still present (no change).",
             "Confirming Delete removes the file from the Holding area list.",
             "The file now appears in Deleted Items (count +1).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=55, id="TC-DI-01", module="D. Delete (Workflow & Controls)",
         name="Deleted Items — Deleted file appears in Deleted Items",
         precondition="the project folder already contains a compliant .txt file, and it has just been deleted (per TC-DEL-01).",
         desc="After deletion, the file is listed in Deleted Items.",
         condition="Deleted Items item count before the delete = N; expected after = N+1.",
         steps=[
             "Complete TC-DEL-01, then click 'Deleted Items' in the Action Bar.",
         ],
         expected=[
             "The file is listed with Name and File name populated.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=56, id="TC-DI-02", module="D. Delete (Workflow & Controls)",
         name="Deleted Items — Deleted item shows Deleted-by / Deleted-date",
         precondition="at least one file has been deleted and is listed in Deleted Items.",
         desc="Each deleted item records who/when it was deleted.",
         steps=[
             "Inspect a deleted item's columns.",
         ],
         expected=[
             "'Deleted by' and 'Deleted date' are populated correctly.",
         ],
         category="Functional", priority="P2"),

    dict(no=57, id="TC-DI-03", module="D. Delete (Workflow & Controls)",
         name="Deleted Items — 'No deleted items' empty state",
         precondition="Deleted Items contains no recoverable file (nothing deleted, or all restored).",
         desc="When nothing is deleted, the page shows an empty state.",
         steps=[
             "Restore all deleted files (or start with an empty Deleted Items).",
         ],
         expected=[
             "An empty state 'No deleted items' is displayed.",
         ],
         category="Functional", priority="P2"),

    dict(no=58, id="TC-DI-04", module="D. Delete (Workflow & Controls)",
         name="Deleted Items — Restore button appears after selecting an item",
         precondition="at least one file is listed in Deleted Items and no item is currently selected.",
         desc="Selecting a deleted item reveals the Restore action in the Action Bar.",
         steps=[
             "Select the checkbox of a deleted item.",
         ],
         expected=[
             "A 'Restore' button appears in the Action Bar and is enabled.",
         ],
         category="Functional", priority="P2"),

    # ===== E. Restore (Workflow & Controls) =====
    # ----- Workflow: end-to-end restore-flow outcomes -----
    dict(no=59, id="TC-RST-01", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore with the original name",
         precondition="a compliant .txt exists in Deleted Items and no file with the same composed name exists in the target folder.",
         desc="Restore a deleted file without changing any attribute.",
         steps=[
             "Deleted Items → select file → Restore → confirm in Restore dialog → Continue.",
             "In the restore validator, click Restore without changes.",
         ],
         expected=[
             "Validator opens with all attributes pre-filled; no errors; file restored under its original name.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=60, id="TC-RST-02", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore with a NEW file name (core assignment)",
         precondition="a deleted .txt is in Deleted Items; the target folder does NOT already contain the new composed name.",
         desc="Restore and rename by changing Project from test2 to res1 — the heart of the assignment.",
         steps=[
             "Deleted Items → select file → Restore → Continue.",
             "In the restore validator, change Project from 'test2' to 'res1'.",
             "Confirm the delimiter error is dismissed, then click Restore.",
         ],
         expected=[
             "Name preview updates to 'res1-XXX-ZZ-ZZ-CA-D-1234.txt' with the old name struck through.",
             "Restore enabled; toast '1 file successfully restored'; file appears in Files list under the new name.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=61, id="TC-RST-03", module="E. Restore (Workflow & Controls)",
         name="Workflow — Validator re-runs on restore into a naming-standard folder",
         precondition="the target folder has a compliance (naming-standard) setting applied; a file is present in Deleted Items.",
         desc="Restoring into an enforced folder re-opens the validator, not a silent restore.",
         steps=[
             "Delete then Restore a file.",
         ],
         expected=[
             "The validator opens for the restore operation and re-validates the name.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=62, id="TC-RST-12", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore 'Restore Items?' confirmation and Continue",
         precondition="at least one file is listed in Deleted Items and none is selected.",
         desc="Selecting a deleted item reveals 'Restore (n)'; clicking it opens the 'Restore items?' dialog, and Continue proceeds into the Restore validator page.",
         steps=[
             "Click Restore in the Delete-items Restore dialog; observe the 'Restore Items' dialog.",
             "Click Continue.",
         ],
         expected=[
             "The 'Restore Items' dialog appears; Continue proceeds to the restore validator page.",
         ],
         category="Functional", priority="P2"),

    dict(no=63, id="TC-RST-11", module="E. Restore (Workflow & Controls)",
         name="Workflow — Cancel restore keeps file deleted",
         precondition="a file is listed in Deleted Items and the 'Restore items?' dialog is open.",
         desc="Cancelling the restore leaves the file in Deleted Items.",
         steps=[
             "Open the restore validator, click Cancel.",
         ],
         expected=[
             "File stays in Deleted Items; nothing appears in the folder.",
         ],
         category="Functional", priority="P2"),

    dict(no=64, id="TC-RST-09", module="E. Restore (Workflow & Controls)",
         name="Workflow — Deleted Items empties after restoring the only file",
         precondition="Deleted Items contains exactly ONE file, and no same-name file exists in the target folder.",
         desc="Restoring the sole deleted item yields the empty state.",
         steps=[
             "Restore the only file in Deleted Items; return to Deleted Items.",
         ],
         expected=[
             "'No deleted items' empty state is shown.",
         ],
         category="Functional", priority="P2"),

    dict(no=65, id="TC-RST-13", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore Items? dialog, Continue routes to the Restore validator",
         precondition="the target folder already contains 'res1-XXX-ZZ-ZZ-CA-D-1234.txt' AND Deleted Items holds a file with the same name.",
         desc="The two-step restore confirmation: 'Restore (1)' opens the 'Restore items?' dialog (compliance re-validation notice) whose 'Continue' leads to the Restore validator page; 'Cancel' returns to Deleted Items with no change.",
         steps=[
             "In Deleted Items, select the file (checkbox).",
             "Click 'Restore (1)' — the first 'Restore items?' dialog appears with: \"Files restored to a folder with a compliance setting applied will be validated to check they conform with the compliance settings.\"",
             "Click 'Cancel' — you are returned to the Deleted Items page with the file still listed and still selected.",
             "Select the file again and click 'Restore (1)'; in the dialog click 'Continue'.",
         ],
         expected=[
             "'Restore (1)' opens the 'Restore items?' dialog carrying the compliance re-validation message.",
             "Cancel returns to Deleted Items; the item count and the file are UNCHANGED (no restore happened).",
             "Continue navigates to the Restore validator page (URL contains moduleId=deleted / the Restore page with the file's attributes pre-filled).",
         ],
         category="Acceptance", priority="P1"),

    dict(no=66, id="TC-RST-14", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore with a changed name succeeds (duplicate resolved)",
         precondition="on the Restore validator page reached from TC-RST-13, the folder still holds 'res1-XXX-ZZ-ZZ-CA-D-1234.txt'.",
         desc="Resolving the duplicate by renaming during restore: change the composed name so it no longer collides, then Restore — the file is written into the folder listing under the new name.",
         steps=[
             "On the Restore validator page (reached via TC-RST-13), leave everything apart from the name-affecting attribute(s) untouched.",
             "Change the attribute(s) so the composed name differs from the existing 'res1-XXX-ZZ-ZZ-CA-D-1234.txt' (e.g. change Number 1234 → 1235).",
             "Confirm the name preview updates and no duplicates error remains.",
             "Click 'Restore'.",
         ],
         expected=[
             "The name preview shows the NEW composed name; the previously colliding name is no longer used.",
             "The 'duplicates' error is cleared and 'Restore' is enabled.",
             "After Restore, the file is listed in the Files list under the new name (no 'Couldn't restore' banner).",
             "The original file with the old name in the folder is untouched; Deleted Items no longer lists the restored file.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=67, id="TC-RST-15", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore with the name unchanged fails and reports the duplicate",
         precondition="on the Restore validator page reached from TC-RST-13, with the folder still holding 'res1-XXX-ZZ-ZZ-CA-D-1234.txt'.",
         desc="The negative branch of TC-RST-14: leaving the name and every attribute unchanged and clicking Restore returns to the file list and surfaces an error message saying a file with this name already exists.",
         steps=[
             "On the Restore validator page, change NOTHING (name and all 11 attributes stay as pre-filled).",
             "Click 'Restore'.",
             "Observe the page transition and the error message.",
             "Open Deleted Items and the target folder.",
         ],
         expected=[
             "The page returns to the file list.",
             "An error message is displayed: \"Couldn't restore 1 file. A file with this name already exists.\"",
             "No new file is added to the folder; the original file is unchanged.",
             "The file remains in Deleted Items (item count unchanged).",
         ],
         category="Acceptance", priority="P1",
         comment="USABILITY OBSERVATION (not raised as a defect): the failure reported here is CORRECT, but it is surfaced on the file list AFTER the page navigates away from the Restore validator. The user must then go back into Deleted Items and start the restore again before they can fix the name. A smoother behaviour would keep the user on the validator with the duplicate error shown inline, so the rename can be applied immediately (see TC-RST-14 for the successful rename path). Raising this as a UX suggestion for the team to triage."),

    dict(no=68, id="TC-RST-07", module="E. Restore (Workflow & Controls)",
         name="Workflow — Restore blocked when the same name already exists in the folder",
         precondition="the target folder contains 'res1-XXX-ZZ-ZZ-CA-D-1234.txt' AND Deleted Items contains another file with the SAME composed name.",
         desc="Unlike Upload (which increments the version), Restore is BLOCKED when a file with the same name already exists in the destination folder. Confirmed via the 'Couldn't restore 1 file. A file with this name already exists.' banner.",
         steps=[
             "In Deleted Items, select the duplicate-named file.",
             "Click 'Restore (1)' → in the 'Restore items?' dialog click 'Continue'.",
             "On the Restore validator page, leave the name/attributes unchanged and click 'Restore'.",
             "Observe the banner / message and inspect the folder + Deleted Items.",
         ],
         expected=[
             "The restore FAILS with the banner: \"Couldn't restore 1 file. A file with this name already exists.\"",
             "No new file is created in the folder; the file stays listed in Deleted Items.",
             "Documented asymmetry: same-name UPLOAD is allowed (version increments, TC-UPL-25) but same-name RESTORE is rejected — recorded as a product finding.",
         ],
         category="Acceptance", priority="P1",
         comment="PRODUCT FINDING — question raised to the team: why is the same-name rule inconsistent between the two write paths? On UPLOAD (TC-UPL-25) a file with an identical composed name is ACCEPTED and becomes a new version (V1 -> V2); on RESTORE (this case) the identical name is REJECTED with 'A file with this name already exists.' Both operations write into the same naming-standard folder and both result in 'a file with this name', so the version-increment path that Upload already applies would appear to be available to Restore as well. Possible explanations to check with the product team: (a) Restore is implemented as a move/recreate of the original item, so version history is not re-resolvable the way a fresh upload is; (b) a deliberate guard to avoid silently resurrecting a deleted item as a newer version of a different file; (c) simply an unaligned implementation between the two services. Not logged as a defect until the intended behaviour is confirmed."),

    # ----- Controls / UI: restore validator fields and rules -----
    dict(no=69, id="TC-RST-04", module="E. Restore (Workflow & Controls)",
         name="Control — Attributes pre-filled from before deletion",
         precondition="a file with known attribute values has been deleted and is in Deleted Items.",
         desc="Restore validator is pre-populated with the pre-deletion values (no data loss).",
         steps=[
             "Delete a file with known attributes, then open Restore.",
         ],
         expected=[
             "All 11 attributes show the pre-deletion values.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=70, id="TC-RST-05", module="E. Restore (Workflow & Controls)",
         name="Control — Delimiter in value during restore is blocked",
         precondition="the Restore validator page is open for a deleted file.",
         desc="Entering a delimiter inside a value on restore is rejected, mirroring upload.",
         steps=[
             "In the restore validator, set Project to 'test-re-'.",
         ],
         expected=[
             "Banner: 'naming standard (1), and special characters (1)'; Restore button disabled.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=71, id="TC-RST-06", module="E. Restore (Workflow & Controls)",
         name="Control — Clear a required attribute during restore blocked",
         precondition="the Restore validator page is open for a deleted file (all attributes pre-filled).",
         desc="Clearing a required attribute on restore keeps Restore disabled.",
         steps=[
             "In the restore validator, clear the Number attribute.",
         ],
         expected=[
             "'required attributes (1)' error; Restore disabled.",
         ],
         category="Functional", priority="P1"),

    dict(no=72, id="TC-RST-08", module="E. Restore (Workflow & Controls)",
         name="Control — Out-of-range value during restore blocked",
         precondition="the Restore validator page is open for a deleted file.",
         desc="An out-of-range attribute on restore is rejected.",
         steps=[
             "Set Number to '12' (below the 4–6 range) in the restore validator.",
         ],
         expected=[
             "Validation error; Restore disabled.",
         ],
         category="Functional", priority="P2"),

    dict(no=73, id="TC-RST-10", module="E. Restore (Workflow & Controls)",
         name="Control — Restore preserves version and associated attributes",
         precondition="a compliant file has been deleted (version + associated attributes known) and no same-name conflict exists.",
         desc="Restored file keeps its version and the 4 associated (non-name) attributes.",
         steps=[
             "Restore a file, then inspect its detail.",
         ],
         expected=[
             "Version preserved (V1); Status/Revision/Classification/custom fields unchanged from before deletion.",
         ],
         category="Functional", priority="P2"),

    # ===== F. Toast & Error Notifications =====
    # ----- Success notifications -----
    dict(no=74, id="TC-TOA-01", module="F. Toast & Error Notifications",
         name="Success toast on upload",
         precondition="a compliant .txt is ready to upload and the target folder has no name conflict.",
         desc="A success toast confirms a completed upload.",
         steps=[
             "Complete an upload (TC-UPL-01).",
         ],
         expected=[
             "Toast: '1 file has been successfully uploaded.' is shown and auto-dismisses.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=75, id="TC-TOA-02", module="F. Toast & Error Notifications",
         name="Success toast on delete",
         precondition="the project folder already contains a compliant .txt file.",
         desc="A success toast confirms deletion.",
         steps=[
             "Complete a delete (TC-DEL-01).",
         ],
         expected=[
             "Toast: '1 file was deleted.' is shown.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=76, id="TC-TOA-03", module="F. Toast & Error Notifications",
         name="Success toast on restore",
         precondition="a file is in Deleted Items and no same-name file exists in the target folder.",
         desc="A success toast confirms restoration.",
         steps=[
             "Complete a restore (TC-RST-02).",
         ],
         expected=[
             "Toast: '1 file successfully restored' is shown after the file reappears in Files.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=77, id="TC-TOA-04", module="F. Toast & Error Notifications",
         name="Success notification on bulk delete from the Holding area",
         precondition="a non-compliant .txt is listed in the Holding area.",
         desc="Deleting from the Holding area ('Delete all' / 'Delete (n)') also confirms with a notification, same as a folder delete.",
         steps=[
             "Run TC-DEL-08 or TC-DEL-09 and confirm the delete in the 'Delete file?' dialog.",
             "Observe the notification shown after the delete completes.",
         ],
         expected=[
             "A success notification is shown (expected to mirror '1 file was deleted.').",
             "Record the exact wording; if no notification appears, record that as the actual behaviour — the list update alone must still make the result unambiguous.",
         ],
         category="Functional", priority="P2"),

    # ----- Failure / error notifications -----
    dict(no=78, id="TC-TOA-05", module="F. Toast & Error Notifications",
         name="Failure notification on restore — duplicate name (confirmed wording)",
         precondition="the target folder already contains a file with the same composed name AND Deleted Items holds another file with that name (TC-RST-15 / TC-RST-07).",
         desc="A FAILED restore must surface an explicit error notification, not silence. Wording confirmed by execution: \"Couldn't restore 1 file. A file with this name already exists.\"",
         steps=[
             "Restore a deleted file whose composed name already exists in the folder, without changing any attribute (TC-RST-15).",
             "Observe the notification that appears after the page returns to the file list.",
         ],
         expected=[
             "An error notification is shown with the text: \"Couldn't restore 1 file. A file with this name already exists.\"",
             "The notification is styled as an ERROR (distinguishable from the green success toast) and names the reason explicitly.",
             "No success toast is shown for the failed operation.",
         ],
         category="Acceptance", priority="P1"),

    dict(no=79, id="TC-TOA-06", module="F. Toast & Error Notifications",
         name="Failure notification on upload (network / server error)",
         precondition="valid attributes are filled and the upload can be forced to fail (TC-NET-01..05).",
         desc="Upload failures caused by network or server conditions (500 / 502 / 503 / 504, offline) must also be reported explicitly, with Retry offered.",
         steps=[
             "Force each failure condition in turn (offline at start, 500/502/503/504 at submit, drop during processing) and click Upload.",
             "Observe the notification / error surface and whether a Retry affordance is offered.",
         ],
         expected=[
             "Each failure is reported explicitly — no silent hang and no misleading success notification.",
             "The message does not claim the file was uploaded; a Retry option is offered where documented.",
             "Record the EXACT wording per condition, and whether it is a toast, an inline error, or a dialog — differences across the conditions are a finding.",
         ],
         category="Functional", priority="P2"),

    dict(no=80, id="TC-TOA-07", module="F. Toast & Error Notifications",
         name="Validation error banner (upload / restore)",
         precondition="the upload or restore validator is open with at least one invalid attribute.",
         desc="Validation failures surface as a clear inline banner listing the failing rules (not a silent block, not a toast).",
         steps=[
             "Trigger any upload/restore validation error (e.g. TC-UPL-06 empty attributes, TC-RST-05 delimiter).",
         ],
         expected=[
             "A red error banner lists the exact failing rules, e.g. '1 file doesn't comply with compliance settings. Resolve errors with: naming standard (1), and required attributes (1).'",
             "Upload/Restore stays disabled while the banner is present.",
         ],
         category="Functional", priority="P2"),

    # ----- Notification behaviour (controls) -----
    dict(no=81, id="TC-TOA-08", module="F. Toast & Error Notifications",
         name="Notification behaviour — dismiss, stacking, and no-notification cases",
         precondition="operations that produce notifications (TC-TOA-01..03) and operations that must NOT (cancel paths, TC-DEL-06 / TC-RST-11).",
         desc="Notifications behave consistently: they auto-dismiss or are dismissible, several do not hide each other, and cancelled operations produce no success notification.",
         steps=[
             "Trigger a success notification and observe whether it auto-dismisses and how long it stays.",
             "Trigger two notifications in quick succession; check they stack / queue rather than replace each other.",
             "Cancel a delete (TC-DEL-06) and cancel a restore (TC-RST-11); check no success notification appears.",
         ],
         expected=[
             "Success notifications are visible long enough to read and then auto-dismiss (or are manually dismissible).",
             "Two concurrent notifications are both readable (stacked/queued), not silently overwritten.",
             "Cancelled operations raise NO success notification — silence must not be mistaken for success.",
         ],
         category="Functional", priority="P3"),

    # ===== G. Non-functional =====
    # Behaviour / environment cases that are NOT about access control or the
    # happy-path flow (concurrency, cross-client listing, file-type support).
    dict(no=82, id="TC-NFR-02", module="G. Non-functional",
         name="Concurrency: two users restore to the same name",
         desc="Parallel restores with identical attributes must not create two files with one name.",
         steps=[
             "Two sessions restore files with an identical attribute set near-simultaneously.",
         ],
         expected=[
             "Reconcile with the same-name UPLOAD finding (TC-UPL-25): verify whether the "
             "second restore is version-incremented or still blocked; record the actual behaviour.",
         ],
         category="Functional", priority="P3"),

    dict(no=83, id="TC-NFR-05", module="G. Non-functional",
         name="State survives a sign-out / sign-in cycle (delete & restore)",
         precondition="a file has been deleted and is listed in Deleted Items; another file has been restored into the folder.",
         desc="Session independence for the two state-changing operations besides upload: a deleted file stays in Deleted Items and a restored file stays in the folder across re-authentication.",
         steps=[
             "Delete a file and confirm it moved to Deleted Items; restore another file and confirm it is back in the folder.",
             "Sign out, then sign back in with the same account.",
             "Open Deleted Items and the target folder.",
         ],
         expected=[
             "The deleted file is STILL listed in Deleted Items (with the same Deleted-by / Deleted-date).",
             "The restored file is STILL in the folder under its (possibly new) name and version.",
             "No state silently reverts after re-authentication — a revert here means the operation was not persisted.",
         ],
         category="Functional", priority="P2"),

    
# ===== H. Cross-browser Compatibility =====
    dict(no=84, id="TC-CB-01", module="H. Cross-browser Compatibility",
         name="Core upload / delete / restore flow behaves identically in Chromium and Firefox",
         precondition="the same test account, the same project folder and the same starting folder state are available in each browser; the folder has the naming standard applied.",
         desc="The assignment flow is a business-critical user journey, so it must not depend on which browser the user happens to open. The same steps are performed in Chromium and in Firefox and the observable behaviour is compared step by step. This case defines WHAT to compare; how the two browsers are driven is an implementation decision.",
         steps=[
             "In Chromium: sign in, open the project folder, upload a compliant .txt (test2-XXX-ZZ-ZZ-CA-D-1234.txt) and confirm it appears in the file list.",
             "In Chromium: delete the file, confirm it moves to Deleted Items, restore it under a new compliant name and confirm it returns to the file list.",
             "In Firefox: repeat the same two steps from the same starting folder state.",
             "Compare the two runs step by step: file-list rendering, upload progress and success toast, delete confirmation dialog, restore dialog and compliance message, final file row (name, version badge, associated attributes).",
         ],
         expected=[
             "Both browsers reach the same end state: the restored file is listed once under the new compliant name, with the same version badge and the same associated attributes.",
             "Every intermediate screen is equivalent across the two browsers: same controls present and enabled, same wording, same toast messages, same dialog behaviour.",
             "A difference in either browser (a control missing, misplaced or disabled; different wording; the flow breaking) is logged as a compatibility defect with the browser name and version.",
         ],
         category="Functional", priority="P2"),

    dict(no=85, id="TC-CB-02", module="H. Cross-browser Compatibility",
         name="WebKit / Safari — core flow usable, engine-specific findings reported separately",
         precondition="the core flow has already been verified in Chromium and Firefox.",
         desc="WebKit is supported but is the lowest-usage engine. The purpose is to confirm the journey is USABLE, not pixel-identical: ACC's heavy WebGL / Canvas viewer can produce engine-specific rendering or timing artefacts that are not functional defects.",
         steps=[
             "In Safari (WebKit): perform the same core flow — upload a compliant .txt, delete it, restore it under a new name.",
             "For each difference observed, classify it as a functional failure, a rendering / timing artefact of the engine, or something that only appears at a particular viewport size.",
         ],
         expected=[
             "The user can complete upload, delete and restore in WebKit; no step is blocked.",
             "Purely visual or timing differences (layout, animation, slower load) are recorded as engine / compatibility observations with the browser and version, and are NOT counted as functional defects or treated as a delivery blocker.",
             "A genuine functional difference is raised as its own defect with repro steps and the engine version.",
         ],
         category="Functional", priority="P3"),

    dict(no=86, id="TC-CB-03", module="H. Cross-browser Compatibility",
         name="Browser-dependent interactions: file selection, overflow menu, modal dialogs",
         precondition="a compliant local .txt file is available and at least one file exists in the folder.",
         desc="Three interaction types are historically the most browser-sensitive in this UI: the file-selection control, the row overflow ('...') menu, and the modal dialogs (Delete File / Restore Items / naming validator). Each is exercised on every browser in scope.",
         steps=[
             "On each browser in scope: use the Upload entry point, choose a local .txt through the file-selection control and complete the upload.",
             "On each browser: open the row overflow ('...') menu and confirm each item can be clicked.",
             "On each browser: open a modal dialog (Delete File / Restore Items / naming validator), type into it, then dismiss it with Cancel and with the confirm button.",
         ],
         expected=[
             "File selection and upload complete on every browser in scope.",
             "The overflow menu opens and its items respond to clicks on every browser in scope.",
             "Each modal dialog opens, accepts input and closes on every browser in scope, returning the user to the correct page (Cancel = no change; confirm = the action is applied).",
             "A deviation seen on only one browser is recorded with the browser name and version.",
         ],
         category="Functional", priority="P2"),

]

# ---------------------------------------------------------------------------
# Field rules (naming-standard context for the design document)
# ---------------------------------------------------------------------------
FIELD_RULES = [
    # attribute, in_filename, type, rule, notes
    ("Project", "Yes (naming)", "Text / Alphanumeric", "Length 2–6", "e.g. test2, res1"),
    ("Originator", "Yes (naming)", "Text / Alphanumeric", "Project-defined", "In demo = XXX; length per project config"),
    ("Volume/System", "Yes (naming)", "Dropdown", "Enumerated", "ZZ, XX"),
    ("Level/Location", "Yes (naming)", "Dropdown", "Enumerated", "ZZ, XX, 00, 01, 02, M1, M2, B1, B2"),
    ("Type", "Yes (naming)", "Dropdown (custom)", "Enumerated", "28 items, e.g. CA"),
    ("Role", "Yes (naming)", "Dropdown (custom)", "Enumerated", "e.g. D"),
    ("Number", "Yes (naming)", "Text / Numeric", "Length 4–6", "e.g. 1234"),
    ("Status", "No (associated)", "Dropdown (custom)", "Enumerated", "e.g. S0"),
    ("Revision", "No (associated)", "Text / Alphanumeric", "Length 3–8", "e.g. dff"),
    ("Classification", "No (associated)", "Dropdown (custom)", "Enumerated", "e.g. Ac_05"),
    ("custom fields", "No (associated)", "Text / Numeric", "Length 2–5", "e.g. 222"),
]

# ---------------------------------------------------------------------------
# Coverage matrix: validation rule -> cases
# ---------------------------------------------------------------------------
# Coverage matrix: coverage item (rule / risk) -> cases, grouped by module
# ---------------------------------------------------------------------------
COVERAGE = [
    # --- A. Project Member Folder Permission ---
    ("A. Project visibility by role (no access / read-only)", "TC-ACC-01, TC-ACC-02"),
    ("A. Upload granted at Create+Upload and above", "TC-ACC-03, TC-ACC-04, TC-ACC-05"),
    ("A. Delete / Restore require Edit or higher", "TC-PRM-01, TC-PRM-02"),
    ("A. Locked file cannot be deleted", "TC-DEL-04"),

    # --- B. Action Bar / Upload Entry ---
    ("B. Upload entry present, enabled, opens the dialog", "TC-AB-01, TC-AB-02"),
    ("B. Deleted Items entry present in the Action Bar", "TC-AB-03"),

    # --- C. Upload: happy path & name composition ---
    ("C. Upload happy path (compliant .txt)", "TC-UPL-01"),
    ("C. File-name composed from the 7 naming attributes only", "TC-UPL-02, TC-UPL-03"),
    ("C. Associated attributes stored as metadata, never in the name", "TC-UPL-02, TC-UPL-05, TC-RST-10"),
    ("C. Attribute values persisted after upload", "TC-UPL-05"),

    # --- C. Upload: field validation ---
    ("C. Required attributes (all empty / one empty / tooltip)", "TC-UPL-06, TC-UPL-07, TC-UPL-08, TC-RST-06"),
    ("C. Character type (Numeric vs Alphanumeric)", "TC-UPL-11, TC-RST-08"),
    ("C. Character length boundaries (min / max +/-1)", "TC-UPL-10, TC-RST-08"),
    ("C. Special characters in a value", "TC-UPL-12, TC-RST-05"),
    ("C. Delimiter inside a value (key negative)", "TC-UPL-13, TC-UPL-14, TC-RST-05"),
    ("C. Leading / trailing spaces in a value", "TC-UPL-16"),
    ("C. Original file name: special characters / spaces / 257 chars", "TC-UPL-22, TC-UPL-23, TC-UPL-24"),
    ("C. Upload blocked until all validation errors are resolved", "TC-UPL-04"),

    # --- C. Upload: workflow branches ---
    ("C. Cancel / Remove-all paths leave no new file", "TC-UPL-09, TC-UPL-20, TC-UPL-26, TC-UPL-27"),
    ("C. Multiple files in one upload", "TC-UPL-30"),
    ("C. Same-name re-upload is allowed, version increments V1->V2", "TC-UPL-25"),
    ("C. Non-compliant file routes to the Holding area", "TC-UPL-17, TC-UPL-18"),
    ("C. Bypass naming standard -> confirm / cancel", "TC-UPL-28, TC-UPL-29"),

    # --- C. Upload: failure handling ---
    ("C. Network / server failure at upload and processing", "TC-NET-01, TC-NET-02, TC-NET-03, TC-NET-04, TC-NET-05"),
    ("C. File-level failures (size over 5 TB, password-protected)", "TC-FILE-01, TC-FILE-02"),

    # --- D. Delete & Deleted Items ---
    ("D. Delete a compliant file (workflow + confirmation)", "TC-DEL-01, TC-DEL-02, TC-DEL-06"),
    ("D. Row overflow ('...') menu lists the actions", "TC-RM-01"),
    ("D. Delete offered only when a file is selected", "TC-DEL-07"),
    ("D. Soft delete — recoverable, Deleted-by / Deleted-date shown", "TC-DEL-03, TC-DI-01, TC-DI-02"),
    ("D. Holding-area delete (all / selected)", "TC-DEL-08, TC-DEL-09"),
    ("D. Deleted Items empty state and Restore entry", "TC-DI-03, TC-DI-04"),

    # --- E. Restore ---
    ("E. Restore with the original name", "TC-RST-01"),
    ("E. Restore with a NEW file name (core assignment)", "TC-RST-02, TC-RST-12, TC-RST-13"),
    ("E. Validator re-runs on restore into a naming-standard folder", "TC-RST-03, TC-RST-04"),
    ("E. Cancel restore keeps the file deleted", "TC-RST-11"),
    ("E. Same-name restore is rejected (duplicate)", "TC-RST-07, TC-RST-15, TC-TOA-05"),
    ("E. Renaming resolves the duplicate and restores", "TC-RST-14"),
    ("E. Restore preserves version and associated attributes", "TC-RST-10"),
    ("E. Deleted Items empties after restoring the only file", "TC-RST-09"),

    # --- F. Toast & Error Notifications ---
    ("F. Success notifications (upload / delete / restore / bulk delete)", "TC-TOA-01, TC-TOA-02, TC-TOA-03, TC-TOA-04"),
    ("F. Failure and validation messages", "TC-TOA-05, TC-TOA-06, TC-TOA-07"),
    ("F. Notification behaviour — dismiss, stacking, absence", "TC-TOA-08"),

    # --- G. Non-functional ---
    ("G. State persists across a sign-out / sign-in cycle", "TC-UPL-31, TC-NFR-05"),
    ("G. Concurrency — two users restore to the same name", "TC-NFR-02"),
    ("G. Unsupported / large file types — stored, viewing pipeline fails", "TC-FILE-01, TC-FILE-02"),

    # --- H. Cross-browser Compatibility ---
    ("H. Cross-browser equivalence — Chromium vs Firefox", "TC-CB-01"),
    ("H. WebKit / Safari usability (non-blocking)", "TC-CB-02"),
    ("H. Browser-sensitive controls — file picker, overflow menu, dialogs", "TC-CB-03"),
]


MODULE_ORDER = [
    "A. Project Member Folder Permission",
    "B. Action Bar / Upload Entry",
    "C. Upload (Workflow & Controls)",
    "D. Delete (Workflow & Controls)",
    "E. Restore (Workflow & Controls)",
    "F. Toast & Error Notifications",
    "G. Non-functional",
    "H. Cross-browser Compatibility",
]

OVERVIEW = [
        ("Goal", "Upload a new .txt file to a naming-standard-applied folder in ACC Files, then delete it, restore it with a new file name."),
        ("Project", "https://acc.autodesk.com/docs/files/projects/xxxx"),
        ("Scope", "Design only — test-case DEFINITIONS, not executed results. No execution status is recorded in this document."),
        ("Naming", "7 naming-convention attributes in the file name (delimiter '-'); 4 associated attributes stored as metadata, never in the name."),
        ("Permission", "Folder permission levels (View-only / View+Download / Create+Upload / Edit / Manage). Upload granted at Create+Upload and above; Delete & Restore at Edit and above. See Autodesk 'Project Member Folder Permission Levels'."),
        ("Grouping", f"Cases are organised by page / dialog / flow ({MODULE_ORDER[0][0]}–{MODULE_ORDER[-1][0]}). Each case focuses on one small flow and assumes other prerequisites are correct."),
        ("Categories", "Acceptance = end-to-end / must-pass user scenario.  Functional = specific behaviour, negative or boundary."),
        ("Priority", "P1 = must pass before sign-off; P2 = important; P3 = nice to have."),
        ("Open items", "1) Full Type / Role / Status / Classification code lists — needed to parameterise the dropdowns. 2) Exact length rule for Originator. 3) Permission level of the supplied account. 4) Is the project folder shared (concurrent writers)? 5) Is there a total file-name length limit (e.g. 257 chars)? — determines the expected result of TC-UPL-24. 6) Product team: is the Upload-vs-Restore difference on same names intended? (Upload allows V1->V2; Restore rejects with \"A file with this name already exists.\")"),
        ("Browsers", "Chromium = primary browser, all cases, blocking. Firefox = Acceptance / P1 set. WebKit (Safari) = spot-check, non-blocking. This is an EXECUTION scope decision, not a test case: module H defines what to compare across browsers, not how the runs are driven."),
        ("Sheets", "Test Cases | Field Rules | Coverage Matrix"),
        ("Legend (columns)", "No. | Test Case ID | Module / Page | Test Case Name | Description | Test Steps | Expected Result | Category | Priority | Comment"),
        ("Comment", "Optional designer's note for a case — e.g. a usability observation or a product finding that is explicitly NOT counted as a defect. Leave blank when nothing to add."),
]

HEADERS = ["No.", "Test Case ID", "Module / Page", "Test Case Name",
           "Description", "Test Steps", "Expected Result", "Category",
           "Priority", "Comment"]


# ===========================================================================
# Excel builder
# ===========================================================================
def build_xlsx(path):
    wb = Workbook()
    # ---- Sheet 1: Overview ----
    ws0 = wb.active
    ws0.title = "Overview"
    title_font = Font(bold=True, size=14, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="1F4E79")
    wrap = Alignment(wrap_text=True, vertical="top")
    ws0["A1"] = "ACC Files Tool — Web UI Test Case Design"
    ws0["A1"].font = Font(bold=True, size=16)
    overview = OVERVIEW
    r = 3
    for k, v in overview:
        ws0.cell(r, 1, k).font = Font(bold=True)
        c = ws0.cell(r, 2, v)
        c.alignment = wrap
        r += 1
    ws0.column_dimensions["A"].width = 22
    ws0.column_dimensions["B"].width = 100

    # ---- Sheet 2: Test Cases ----
    ws = wb.create_sheet("Test Cases")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for ci, h in enumerate(HEADERS, 1):
        c = ws.cell(1, ci, h)
        c.font = title_font
        c.fill = hdr_fill
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        c.border = border
    ws.freeze_panes = "A2"
    cat_fill = {
        "Acceptance": PatternFill("solid", fgColor="E2EFDA"),
        "Functional": PatternFill("solid", fgColor="DDEBF7"),
    }
    for idx, row in enumerate(CASES):
        row["no"] = idx + 1          # renumber sequentially in module-grouped order
        pre = row.get("precondition")
        steps = ("Pre-condition: " + pre + "\n" if pre else "") + \
                "\n".join(f"{i+1}. {s}" for i, s in enumerate(row["steps"]))
        exp = "\n".join(f"• {s}" for s in row["expected"])
        cond = row.get("condition")
        if cond:
            desc_val = CellRichText(
                TextBlock(InlineFont(b=True, color="1F4E79"), "Test condition: "),
                TextBlock(InlineFont(b=True, color="C00000"), cond + "\n"),
                row["desc"],
            )
        else:
            desc_val = row["desc"]
        vals = [row["no"], row["id"], row["module"], row["name"], desc_val,
                steps, exp, row["category"], row["priority"],
                row.get("comment", "")]
        rr = idx + 2
        for ci, v in enumerate(vals, 1):
            c = ws.cell(rr, ci, v)
            c.alignment = wrap
            c.border = border
        ws.cell(rr, 8).fill = cat_fill.get(row["category"], PatternFill())
        if row.get("comment"):
            cc = ws.cell(rr, 10)
            cc.font = Font(italic=True, color="7A5A13")
            cc.fill = PatternFill("solid", fgColor="FFF2CC")
    widths = [6, 12, 24, 30, 40, 52, 52, 12, 9, 34]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    # estimate row heights from longest cell
    for rr in range(2, len(CASES) + 2):
        maxlines = 1
        for ci in (5, 6, 7):
            v = ws.cell(rr, ci).value
            txt = str(v) if v is not None else ""
            lines = txt.count("\n") + 1
            # approx chars per line for wrapped columns
            chars = max((len(t) for t in txt.split("\n")), default=0)
            approx = lines + chars // (widths[ci-1] * 1.1)
            maxlines = max(maxlines, approx)
        ws.row_dimensions[rr].height = max(30, min(240, maxlines * 15))

    # ---- Sheet 3: Field Rules ----
    ws3 = wb.create_sheet("Field Rules")
    fr_head = ["Attribute", "In file name?", "Type", "Rule", "Notes / demo value"]
    for ci, h in enumerate(fr_head, 1):
        c = ws3.cell(1, ci, h)
        c.font = title_font
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
    for ri, row in enumerate(FIELD_RULES, 2):
        for ci, v in enumerate(row, 1):
            c = ws3.cell(ri, ci, v)
            c.alignment = wrap
            c.border = border
            if ci == 2:
                c.fill = PatternFill("solid", fgColor="E2EFDA" if v.startswith("Yes") else "FCE4D6")
    for i, w in enumerate([18, 16, 20, 22, 44], 1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    # ---- Sheet 4: Coverage Matrix ----
    ws4 = wb.create_sheet("Coverage Matrix")
    cm_head = ["Coverage item", "Covered by"]
    for ci, h in enumerate(cm_head, 1):
        c = ws4.cell(1, ci, h)
        c.font = title_font
        c.fill = hdr_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border
    for ri, row in enumerate(COVERAGE, 2):
        for ci, v in enumerate(row, 1):
            c = ws4.cell(ri, ci, v)
            c.alignment = wrap
            c.border = border
    ws4.column_dimensions["A"].width = 38
    ws4.column_dimensions["B"].width = 60

    wb.save(path)


# ===========================================================================
# HTML builder
# ===========================================================================
def _esc(s):
    return _html.escape(str(s)).replace("\n", "<br>")


def build_html(path):
    sections = ""
    for mod in MODULE_ORDER:
        rows = [c for c in CASES if c["module"] == mod]
        if not rows:
            continue
        body = ""
        for row in rows:
            pre = row.get("precondition")
            pre_html = f'<p class="precond"><strong>Pre-condition:</strong> {_esc(pre)}</p>' if pre else ""
            cond = row.get("condition")
            cond_html = f'<p class="cond"><strong>Test condition:</strong> {_esc(cond)}</p>' if cond else ""
            steps = "".join(f"<li>{_esc(s)}</li>" for s in row["steps"])
            exp = "".join(f"<li>{_esc(s)}</li>" for s in row["expected"])
            cls = "acc" if row["category"] == "Acceptance" else "func"
            cmt = row.get("comment")
            cmt_html = f'<span class="cmt-tag">{_esc(cmt)}</span>' if cmt else ""
            body += f"""
            <tr class="{cls}">
              <td class="num">{row['no']}</td>
              <td class="id">{_html.escape(row['id'])}</td>
              <td>{_html.escape(row['name'])}</td>
              <td>{cond_html}{_esc(row['desc'])}</td>
              <td>{pre_html}<ol>{steps}</ol></td>
              <td><ul>{exp}</ul></td>
              <td class="cat">{row['category']}</td>
              <td class="pri">{row['priority']}</td>
              <td class="cmt">{cmt_html}</td>
            </tr>"""
        sections += f"""
        <section>
          <h2>{_html.escape(mod)}</h2>
          <table class="cases">
            <thead><tr>
              <th>№</th><th>ID</th><th>Test Case</th><th>Description</th>
              <th>Steps</th><th>Expected</th><th>Category</th><th>Pri</th><th>Comment</th>
            </tr></thead>
            <tbody>{body}</tbody>
          </table>
        </section>"""

    field_rows = "".join(
        f"<tr><td>{_esc(a)}</td><td>{_esc(b)}</td><td>{_esc(c)}</td><td>{_esc(d)}</td><td>{_esc(e)}</td></tr>"
        for a, b, c, d, e in FIELD_RULES)
    cov_rows = "".join(f"<tr><td>{_esc(r)}</td><td>{_esc(c)}</td></tr>" for r, c in COVERAGE)
    ov_rows = "".join(
        f"<tr><td><b>{_esc(k)}</b></td><td>{_esc(v)}</td></tr>"
        for k, v in OVERVIEW if k not in ("Sheets", "Legend (columns)"))

    total = len(CASES)
    acc = sum(1 for c in CASES if c["category"] == "Acceptance")
    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ACC Files Tool — Web UI Test Case Design</title>
<style>
  :root {{ --blue:#1F4E79; --acc:#E2EFDA; --func:#DDEBF7; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         color:#222; margin:0; background:#f6f8fa; }}
  header {{ background:var(--blue); color:#fff; padding:24px 32px; }}
  header h1 {{ margin:0 0 6px; font-size:22px; }}
  header p {{ margin:2px 0; font-size:13px; opacity:.92; }}
  main {{ max-width:1200px; margin:0 auto; padding:24px 20px 60px; }}
  .summary {{ display:flex; gap:16px; flex-wrap:wrap; margin:18px 0 26px; }}
  .summary .card {{ background:#fff; border:1px solid #e3e8ee; border-radius:10px;
                   padding:14px 18px; min-width:120px; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
  .summary .card b {{ display:block; font-size:24px; color:var(--blue); }}
  .summary .card span {{ font-size:12px; color:#666; }}
  section {{ background:#fff; border:1px solid #e3e8ee; border-radius:10px;
            padding:8px 16px 16px; margin-bottom:22px; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
  h2 {{ color:var(--blue); border-bottom:2px solid #e3e8ee; padding-bottom:6px; font-size:18px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ border:1px solid #dfe4ea; padding:8px 10px; vertical-align:top; text-align:left; }}
  thead th {{ background:#eef2f7; position:sticky; top:0; font-size:12px; }}
  tr.acc td.cat {{ background:var(--acc); }}
  tr.func td.cat {{ background:var(--func); }}
  td.num {{ text-align:center; width:34px; color:#888; }}
  td.id {{ font-family:ui-monospace,Menlo,Consolas,monospace; white-space:nowrap; color:#1F4E79; }}
  td.pri {{ text-align:center; font-weight:600; }}
  td.cmt {{ font-size:12px; color:#7a5a13; font-style:italic; }}
  span.cmt-tag {{ display:block; padding:6px 8px; background:#fff2cc; border-left:3px solid #e0a030; border-radius:3px; }}
  ol, ul {{ margin:0; padding-left:18px; }}
  li {{ margin:2px 0; }}
  p.precond {{ margin:0 0 6px; padding:6px 8px; background:#fbf3e4; border-left:3px solid #e0a030; color:#7a5a13; font-size:13px; border-radius:3px; }}
  p.precond strong {{ color:#9a6a10; }}
  p.cond {{ margin:0 0 6px; padding:6px 8px; background:#eaf1fb; border-left:3px solid #2f6fb0; color:#13476e; font-size:13px; border-radius:3px; }}
  p.cond strong {{ color:#1c5a8a; }}
  .meta h3 {{ color:var(--blue); margin:26px 0 8px; }}
  table.ov {{ table-layout:fixed; margin:2px 0 4px; }}
  table.ov th:first-child, table.ov td:first-child {{ width:104px; font-weight:600; }}
  table.ov td {{ vertical-align:top; word-wrap:break-word; }}
  table.ov th, table.ov td {{ padding:6px 12px; }}
  .meta table th {{ background:#eef2f7; }}
  footer {{ text-align:center; color:#999; font-size:12px; padding:20px; }}
  @media print {{
    @page {{ size:A4 landscape; margin:8mm; }}
    body {{ background:#fff; font-size:11px; }}
    header {{ padding:10px 14px; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    header h1 {{ font-size:17px; }}
    header p {{ font-size:11px; }}
    main {{ max-width:none; padding:0; }}
    .summary {{ margin:8px 0 10px; gap:10px; }}
    .summary .card {{ box-shadow:none; padding:8px 12px; min-width:90px; }}
    .summary .card b {{ font-size:18px; }}
    .summary .card span {{ font-size:10px; }}
    section {{ box-shadow:none; padding:4px 10px 10px; margin-bottom:12px; break-inside:auto; }}
    h2 {{ font-size:15px; margin:6px 0 8px; }}
    table {{ font-size:10px; }}
    th, td {{ padding:3px 4px; }}
    thead th {{ position:static; font-size:9.5px; }}
    tr {{ break-inside:avoid; }}
    table.cases {{ table-layout:fixed; }}
    table.cases th:nth-child(1), table.cases td.num {{ width:20px; }}
    table.cases th:nth-child(2), table.cases td.id {{ width:82px; }}
    table.cases th:nth-child(4), table.cases td:nth-child(4) {{ width:23%; }}
    table.cases th:nth-child(7), table.cases td.cat {{ width:62px; }}
    table.cases th:nth-child(8), table.cases td.pri {{ width:26px; }}
    table.cases th:nth-child(9), table.cases td.cmt {{ width:8%; }}
    .meta table, .meta th, .meta td {{ font-size:9.5px; }}
    table.ov {{ table-layout:fixed; }}
    table.ov th:first-child, table.ov td:first-child {{ width:22mm; }}
    table.ov th, table.ov td {{ padding:3px 7px; font-size:9.5px; }}
    table.ov td:first-child {{ font-size:9.5px; }}
    section {{ page-break-inside:auto; }}
    p.precond, p.cond {{ font-size:10px; padding:3px 5px; }}
    td.cmt {{ font-size:9.5px; }}
    ol, ul {{ padding-left:15px; }}
    footer {{ padding:6px; }}
  }}
</style></head>
<body>
<header>
  <h1>ACC Files Tool — Web UI Test Case Design</h1>
  <p><b>Goal:</b> Upload a new .txt file to a naming-standard-applied folder in ACC Files, then delete it, restore it with a new file name.</p>
  <p><b>Test project:</b> acc.autodesk.com/docs/files/projects/xxxx</p>
  <p><b>Scope:</b> Design only — definitions, not executed results. No execution status is recorded in this document.</p>
</header>
<main>
  <div class="summary">
    <div class="card"><b>{total}</b><span>Total cases</span></div>
    <div class="card"><b>{acc}</b><span>Acceptance</span></div>
    <div class="card"><b>{total-acc}</b><span>Functional</span></div>
    <div class="card"><b>{len(MODULE_ORDER)}</b><span>Modules {MODULE_ORDER[0][0]}\u2013{MODULE_ORDER[-1][0]}</span></div>
    <div class="card"><b>P1/P2/P3</b><span>Priority</span></div>
  </div>
  <p style="font-size:13px;color:#555">
    Cases are grouped by page / dialog / flow ({MODULE_ORDER[0][0]}\u2013{MODULE_ORDER[-1][0]}). Each case focuses on one small flow and assumes other prerequisites are correct.
    <b>Acceptance</b> = end-to-end / must-pass scenario; <b>Functional</b> = specific behaviour, negative or boundary.
  </p>
  <section>
    <h2>Overview</h2>
    <table class="ov">
      <thead><tr><th>Item</th><th>Detail</th></tr></thead>
      <tbody>{ov_rows}</tbody>
    </table>
  </section>
  {sections}
  <div class="meta">
    <h3>Field Rules (naming standard)</h3>
    <table><thead><tr><th>Attribute</th><th>In file name?</th><th>Type</th><th>Rule</th><th>Notes / demo value</th></tr></thead>
    <tbody>{field_rows}</tbody></table>
    <h3>Coverage Matrix</h3>
    <table><thead><tr><th>Coverage item</th><th>Covered by</th></tr></thead><tbody>{cov_rows}</tbody></table>
  </div>
  <footer>ACC Files Tool — Web UI Test Case Design • {total} cases • xxxx</footer>
</main>
</body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)


def build_pdf(html_path, pdf_path):
    """Print the self-contained HTML to A4-landscape PDF via Chromium.
    Skipped (with a message) when Playwright is unavailable."""
    from playwright.sync_api import sync_playwright

    url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="load")
        page.emulate_media(media="print")
        page.pdf(path=pdf_path, format="A4", landscape=True,
                 print_background=True,
                 margin={"top": "8mm", "bottom": "8mm",
                         "left": "8mm", "right": "8mm"})
        browser.close()


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    xlsx = os.path.join(here, OUT_XLSX)
    html_f = os.path.join(here, OUT_HTML)
    pdf_f = os.path.join(here, OUT_BASE + ".pdf")
    try:
        build_xlsx(xlsx)
        print("Wrote", xlsx)
    except PermissionError:
        print("SKIPPED", xlsx, "- file is open in Excel / a viewer. Close it and re-run.")
    build_html(html_f)
    print("Wrote", html_f)
    try:
        build_pdf(html_f, pdf_f)
        print("Wrote", pdf_f)
    except Exception as exc:                     # noqa: BLE001
        print("PDF skipped —", type(exc).__name__, exc)
    print("Total cases:", len(CASES))
