# PRD Review & Minimized Implementation Plan

**Document**: Review of `PRD.md` v1.1 against the actual test case, DevTools control docs, and Autodesk help documentation
**Date**: 2026-09-22
**Status**: Applied — PRD.md updated to v1.2 and docs/autodesk-field-validation-rules.md updated (2026-09-22)
**Goal**: Shrink the PRD to the minimum that automates the **one** test case in `docs/sample_testcase/test-case-steps.txt` (upload → delete → restore in the "Name-standard" folder), then build the rest later.

---

## 1. Inputs reviewed

| Input | Conclusion |
| --- | --- |
| `PRD.md` v1.1 | Fundamentally sound. Framework-first split is right. ~8 changes + a deferral list needed. |
| `docs/sample_testcase/test-case-steps.txt` | One E2E flow, 21 steps: upload with attributes → delete → deleted items → restore with renamed project value (incl. one negative validation). |
| `docs/sample_testcase/*.png` (16 screenshots) | Confirms toolbar-driven flow (checkbox + Action Bar), validator UI, progress dialog, toasts. |
| `docs/autodesk-*-options.md` (7 files) | 6 custom dropdowns (Volume=2, Level=9, Type=28, Role=20, Status=24, Classification=virtualized/unknown) + 4 text-field validation rules. |
| Help: *Add Files To Naming Standard Enforced Folder* | Confirms the **File Validator is a dialog** opened by upload/restore; error categories incl. **delimiter character**; previous-version values highlighted on restore. |
| Help: *File Naming Standard* | URL 404s — the exact name-composition order is **not** authoritatively documented (see risk R-3). |

---

## 2. Verdict summary

| Verdict | PRD item |
| --- | --- |
| ✅ Confirmed as-is | POM + BasePage, shared `ValidatorDialog` base, `UploadProgressDialog`, `Toast`, storage-state auth (`setup_auth.py`), portal rule for dropdowns, no-`sleep` policy, screenshot/trace on failure, serial-writes rule, canary (FR-15), pytest-html. |
| ✏️ Correct | 10 attributes (not 11); missing dialogs (`UploadDialog` picker, `RestoreItemsDialog`); `FileToolbar` description; "11 attributes" → "10 attribute fields + file name". |
| ➕ Add | Delimiter validation rule (+ exact error text from step 18); "Deleted items" button in toolbar; upload picker dialog; restore previous-version handling; step 15/16 dialog split note. |
| ⏸️ Defer to Phase 2 | `--suite` alias, xdist parallel + guard, boundary datasets, `RowMenu`, Allure, `--env` blocks, WebKit canary automation, full Classification list capture, bulk edit. |
| ❌ Remove | Allure as backend (PRD already marks it optional — drop it to keep the doc honest). |

---

## 3. Findings in detail

### A. What the PRD gets right (keep unchanged)

1. **Validator as a shared dialog** — The help doc confirms the File Validator is a dialog opened by upload and by restore ("the file validator opens…"). The upload flow (steps 6–8) and restore flow (step 17) show the same 10-attribute form + error banner + disabled primary button. `UploadValidator` / `RestoreValidator` inheriting `ValidatorDialog` is the correct model. ✅
2. **`UploadProgressDialog`** — step 8 exactly: per-file status `Uploading - 0%` → `Uploaded to Name-standard`, then `Done` (step 9). ✅
3. **`Toast`** — three exact messages in the flow: "1 file has been successfully uploaded" (step 8), "1 file was deleted" (step 12), "1 file successfully restored" (step 20). ✅
4. **Portal rule (FR-01)** — all 6 attribute dropdowns are React custom dropdowns with `role='option'` overlays (per DevTools docs). Portal-rooted locators are mandatory. ✅
5. **Storage-state auth (FR-12)** — Autodesk ID + enterprise SSO makes programmatic login fragile; `setup_auth.py --headed` bootstrap is the right call. ✅
6. **Serial writes (FR-08)** — shared project, single folder; the rule stands (and phase 1 has only one test anyway). ✅
7. **Restore pre-fill (FR-13 note)** — help doc: values inherited from the previous version appear highlighted yellow with **Accept** buttons. `restore_validator.py` must not only assert pre-fill but also dismiss/accept those values before editing. (Extends, not replaces, the PRD note.)

### B. Corrections — PRD changes needed for the test case

**B-1. The attribute count is 10, not 11.**
Steps 7a–7k enumerate 10 fields: Project, Volume/System, Level/Location, Type, Role, Number, Status, Revision, Classification, custom fields. The 11th element is the composed file name. Fix FR-01, FR-05 and FR-13 wording ("11 attributes" → "10 attribute fields + file name"; `NamingAttributes` describes 10 fields).

**B-2. Two dialogs are missing from FR-13.**
- `dialogs/upload_dialog.py` — the step-3 dialog ("Select files" → OS file picker). Phase-1 shape: one method `select_files(path)` that internally handles `expect_file_chooser()` + `set_files`. Without it, the first step of the test has no home.
- `dialogs/restore_items_dialog.py` — the step-16 "Restore items" dialog with its **Continue** button. Distinct from the step-15 confirm dialog. ⚠️ Steps 15 and 16 may be one dialog with two stages or two separate dialogs (no screenshot for step 15) — verify at runtime; model both buttons in one class if they are the same dialog.

**B-3. `FileToolbar` description is incomplete.**
The test uses the toolbar for everything: Upload (step 3), Delete (step 10), Deleted items (step 13), Restore (step 14). FR-13's description lists "Upload split-button, Export, Search and filter, view toggle" — **add: "Deleted items" button, and contextual Delete / Restore buttons (Restore appears only after a checkbox is selected, step 14)**.

**B-4. The primary test path is checkbox + toolbar, not the ⋮ RowMenu.**
Steps 10 and 14 select the row checkbox and use Action Bar buttons; the ⋮ menu is never touched in this test case. Update the FR-01 example to show the toolbar path as the pattern used by the acceptance test, and **defer `row_menu.py` to Phase 2** (keep the portal rule — it applies to the attribute dropdowns regardless).

**B-5. The delimiter validation rule is missing from the test-data docs.**
Step 18: Project = `res-1` → error "**The delimiter character can't be used in an attribute value**"; step 19: `res1` → error dismissed. The help doc confirms the error category: forbidden characters `< > : " / | ? * \` **plus the delimiter** (`-` in this standard). `docs/autodesk-field-validation-rules.md` must add this rule, and `utils/test_data.py` must expose it (delimiter value + exact error text). This negative check is part of the single test case, so it is **Phase-1 scope**, not a "functional suite" luxury.

**B-6. `deleted_items_page.py` — open question Q3 resolved.**
Step 13 shows Deleted items has its own URL discriminator: `…?folderUrn=…&viewModel=detail&moduleId=deleted` vs `moduleId=folders` for the Files view. It **is** a Page. Remove the "⚠️ verify at runtime" marker.

**B-7. `expected_file_name()` cannot be hardcoded yet.**
The repo nowhere documents the composition order/delimiter, and the *File Naming Standard* help URL 404s. Robust phase-1 strategy (no hardcoded format): in the validator, read the live **Preview** text (help doc: the File name tab shows a live preview), then after upload/restore assert the files-list row name equals the captured preview (+ extension). The composition rule gets documented once observed. (See risk R-3.)

**B-8. Cleanup policy vs NFR-06.**
The test case's final state is the file **restored** into the folder (step 21). True cleanup (purge from Deleted items) is not part of the test case. Decision: phase 1 leaves one uniquely-named restored file per run (harmless — unique project values prevent duplicate conflicts); README notes a manual purge. NFR-06 is satisfied in spirit (unique names, no duplicate collisions); document the deviation.

### C. Deferrals — PRD tasks that shrink phase 1

| PRD item | Action | Why |
| --- | --- | --- |
| FR-04 `--suite` alias option | Defer | pytest markers alone select the one test; alias adds no value until multiple suites exist. |
| FR-05 boundary datasets (min−1/min/max/max+1, wrong-type, whitespace) | Defer | Belongs to the *functional* suite; the one test needs only the acceptance dataset + the delimiter negative case. |
| FR-08 xdist parallel + fixture guard | Defer | One serial test; keep the "writes are serial" rule as documentation only. |
| FR-06 Allure backend | Remove | pytest-html alone meets FR-06's acceptance criterion (self-contained HTML). |
| FR-07 `--env dev|staging|prod` blocks | Defer | Only one target exists (prod ACC). `.env` suffices; add `FOLDER_NAME=Name-standard` to the settings table. |
| FR-13 `row_menu.py` | Defer | Not used by this test case. |
| FR-03 WebKit canary automation | Defer | PRD already marks WebKit Tier-3/manual; phase-1 canary runs Chromium + Firefox only. |
| Classification full-list capture (docs says "unknown, ≥ 11") | Defer | Phase 1 needs only *selecting* `Ac_05` — via filter/type-ahead in the virtualized list (see risk R-1). Full capture + count assertions are phase 2. |
| Validator bulk edit (`Edit all` / `Edit (x)`) | Defer | Single-file test; manual per-field edit only. |
| `LoginPage` beyond `setup_auth.py` | Defer | No login steps in test runs; only the bootstrap script touches it. |

---

## 4. The test case mapped to the minimized framework

This table is the acceptance proof that the shrunk framework covers every step of the test case:

| Step (test-case-steps) | Page Object | Key API (conceptual) |
| --- | --- | --- |
| 1 access project URL | `FilesPage.open()` (via fixture) | `goto(BASE_URL/docs/files/projects/{PROJECT_ID})` |
| 2 click folder "Name-standard" | `FilesPage.folder_list` | `open_folder("Name-standard")` |
| 3 Upload → dialog | `FileToolbar.upload` + `UploadDialog` | `upload_button.click()` → `select_files(["data/files/a.txt"])` |
| 4–5 Select files → OS picker | `UploadDialog` | `expect_file_chooser()` + `set_files` (handles native "OK") |
| 6 validator opens, 1 file awaiting | `UploadValidator(ValidatorDialog)` | `expect(file_row("a.txt")).to_be_visible()` |
| 7a–7k edit 10 attributes | `ValidatorDialog` fields | `fill_project(unique_project())`, `select_volume("ZZ")`, `select_level("ZZ")`, `select_type("CA")`, `select_role("D")`, `fill_number("1234")`, `select_status("S0")`, `fill_revision("dff")`, `select_classification("Ac_05")`, `fill_custom_fields("222")`; read **Preview** text |
| 8 Upload → progress | `UploadValidator.upload()` → `UploadProgressDialog` | expect status `Uploaded to Name-standard`; `Toast`: "1 file has been successfully uploaded" |
| 9 Done | `UploadProgressDialog.done()` | back to `FilesPage`, `expect(file_row(expected_name)).to_be_visible()` |
| 10 select + Delete | `FileRow.checkbox` + `FileToolbar.delete` | select row by expected name |
| 11 confirm | `DeleteDialog` (implicit in FR-13 `FilesPage`) | `confirm_delete()` |
| 12 toast + row gone | `Toast` / `FilesPage` | `expect(file_row(...)).to_be_hidden()` |
| 13 Deleted items | `FileToolbar.deleted_items` → `DeletedItemsPage` | URL contains `moduleId=deleted` |
| 14 select + Restore appears | `DeletedItemsPage` row + toolbar | `expect(restore_button).to_be_visible()` after checkbox |
| 15–16 confirm + Continue | `RestoreDialog` / `RestoreItemsDialog` | confirm, then Continue (single class if same dialog) |
| 17 restore validator, pre-filled | `RestoreValidator(ValidatorDialog)` | assert pre-fill from previous version; accept/dismiss yellow values |
| 18 negative: `res-1` | `ValidatorDialog` | `fill_project(f"{prefix}-1")` → `expect(error_banner).to_contain_text("delimiter character")` |
| 19 fix to `res1`-unique, error dismissed | `ValidatorDialog` | `expect(error_banner).to_be_hidden()`; `restore()` |
| 20 row gone + toast | `DeletedItemsPage` / `Toast` | "1 file successfully restored" |
| 21 back to Files, file restored | `FilesPage` | row visible with new expected name |

**One test function**, marked `acceptance`: `test_upload_delete_restore`. It is deliberately one E2E test — delete depends on the uploaded file and restore on the deleted file; splitting into three "independent" tests would need fragile state hand-off. The `@step` logging (FR-11) keeps each of the 21 steps visible in the log/report.

---

## 5. Minimized Phase-1 scope

### Deliverables (what gets built now)

```
acc-naming-standard-e2e/
├── pages/            base_page, files_page, deleted_items_page, login_page (bootstrap only)
├── dialogs/          validator_dialog (base), upload_validator, restore_validator,
│                     upload_dialog (file picker), upload_progress_dialog,
│                     restore_items_dialog (Continue)
├── components/       toast, file_toolbar, file_row, folder_list   # no row_menu
├── utils/            config, logger (@step), test_data, auth, setup_auth
├── data/files/a.txt  # static upload sample
├── tests/            conftest.py, test_framework_smoke.py (FR-15 canary),
│                     test_acceptance.py::test_upload_delete_restore
├── .env.example / .gitignore / pytest.ini / requirements.txt / README.md
```

### Verification gate (delivery evidence)

1. `ruff check .` — clean.
2. `pytest --collect-only` — zero errors.
3. `pytest tests/test_framework_smoke.py` — canary green on **Chromium + Firefox** (asserts harness, not product).
4. `pytest -m acceptance --browser chromium --headed` — first live run headed (watch the flow), then headless to prove stability.
5. `pytest-html` report + step log + screenshot/trace artifacts verified for one deliberately-induced failure (FR-10/NFR-07 evidence).

### Test data (phase 1)

- `unique_project()` for Project (both upload and restore) — never `test2`/`res1` (PRD FR-05 rule kept).
- Fixed per docs: ZZ / ZZ / CA / D / 1234 / S0 / dff / Ac_05 / 222 (combination stays unique via Project).
- Negative case: `f"{prefix}-1"` transient value for the delimiter check (step 18) — never persisted.
- `FOLDER_NAME=Name-standard` in `.env`.

### Milestones (replaces PRD §6 for this delivery)

| M | Content | PRD items exercised |
| --- | --- | --- |
| M1 | Skeleton: pytest.ini, requirements.txt, .env.example, .gitignore | FR-02, FR-07, FR-09, FR-12 |
| M2 | utils/: config, logger `@step`, test_data, auth + setup_auth | FR-05(min), FR-11, FR-12 |
| M3 | pages/ + components/ (no row_menu) | FR-01, FR-13 |
| M4 | dialogs/: ValidatorDialog + upload/restore/progress/restore-items | FR-01 |
| M5 | conftest + canary + **the one acceptance test** | FR-03, FR-04(markers), FR-10, FR-15, NFR-01…07 |
| M6 | README + full gate run | FR-14 |

### Phase-2 backlog (explicitly out of this delivery)

`--suite` alias · xdist parallel + write-guard · functional boundary datasets (per-field min−1/min/max/max+1) · RowMenu flows · Allure (dropped) · `--env` blocks · WebKit automation · Classification full-list capture · validator bulk edit · holding-area scenarios · Move/Copy/Rename flows.

---

## 6. Applied edits to PRD.md (v1.2)

1. FR-01: "11 attributes" → "10 attribute fields (+ file name)"; example composition replaced with the checkbox+toolbar pattern (keep ⋮ RowMenu example marked Phase 2).
2. FR-04: keep markers; annotate `--suite` alias as Phase 2.
3. FR-05: `NamingAttributes` = 10 fields; add delimiter rule + exact error text; mark boundary datasets Phase 2.
4. FR-06: remove Allure mention.
5. FR-07: defer `--env` blocks; add `FOLDER_NAME` to the settings table.
6. FR-08: parallel guard annotated Phase 2 (rule kept as documentation).
7. FR-13: add `upload_dialog.py`, `restore_items_dialog.py`; update `file_toolbar.py` description (Deleted items + contextual Delete/Restore); remove "verify at runtime" from `deleted_items_page.py` (resolved: Page); mark `row_menu.py` Phase 2; note restore validator handles previous-version Accept UI.
8. FR-13/NFR-06: document the phase-1 cleanup deviation (restored file left per run; manual purge).
9. §6 Milestones: replace with the Phase-1 table above + Phase-2 backlog.
10. §8 Open questions: close Q3 (Deleted items = Page) and Q6 (Type=28, etc. per docs); add Q: exact name-composition order (verify via Preview), Q: steps 15/16 one dialog or two, Q: Classification virtualized-list selection strategy.
11. `docs/autodesk-field-validation-rules.md`: add the delimiter rule row + step-18 exact error text.
12. FR-15: unchanged (Chromium + Firefox canary).

---

## 7. Risks & mitigations

| # | Risk | Mitigation |
| --- | --- | --- |
| R-1 | **Classification dropdown is virtualized**; `Ac_05` is not in the observed 11-option sample — selection needs scrolling/filtering in a virtualized list | Use type-ahead/filter (docs' own recommendation) to select `Ac_05`; spike this control first during M4. |
| R-2 | ✅ Resolved — steps 15/16 are **two separate dialogs** (restore confirm; then "Restore items" with Continue) | Modeled as two dialog classes in PRD v1.2; no runtime verification needed. |
| R-3 | Exact file-name composition order not documented (help URL 404s) | Assert against the validator's live **Preview** text captured during the run, never a hardcoded full name. |
| R-4 | Restore validator may surface yellow "previous version" Accept UI before editing | Handle Accept/dismiss in `restore_validator` during M4 spike. |
| R-5 | Upload/restore validator may be a full-screen overlay rather than a small modal (screenshots are wide) | Irrelevant to the POM contract (own locators rooted at dialog container, no URL) — verify container during M4. |
| R-6 | Shared folder accumulates one restored file per run | Unique Project values per run; README documents manual purge; NFR-06 deviation documented (§6.8). |

---

## 8. Decisions status

1. **Cleanup policy** — ✅ decided: leave the restored file per run (matches the test case's final state); documented as the Phase-1 NFR-06 deviation in PRD.
2. **Apply the PRD edits** — ✅ done: PRD.md is now v1.2; field-validation-rules.md updated.
3. **Credentials/account** — ✅ decided: automated login in the test run with `.env` credentials (homework requires login automation); `setup_auth.py` kept as MFA/SSO fallback only.
4. **Password encryption for GitHub** — ✅ decided: password ships as a Fernet-encrypted token in `config/credentials.json` (decrypted at runtime; local `.env` plaintext override takes precedence). The Fernet key is **not** committed; the reviewer receives it out of band and puts it in `ACC_FERNET_KEY` or `config/fernet.key`.
