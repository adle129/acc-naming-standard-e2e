# PRD — ACC Naming Standard E2E Test Framework

| Item                  | Content                                                                              |
| --------------------- | ------------------------------------------------------------------------------------ |
| **Document**          | Product Requirements Document — Test Automation Framework                            |
| **Version**           | 1.2 (minimized per test-case workflow review)                                        |
| **Date**              | 2026-09-22                                                                           |
| **Status**            | Draft for review                                                                     |
| **System under test** | Autodesk Construction Cloud (ACC) — **Files** tool, **File Naming Standard** feature |
| **Target project**    | `yuanyuan.zhang.hw` (`4ac3aedc-e6d5-4bbb-91f3-c49c48af48f4`)                         |
| **Tech stack**        | Python 3.11+ · Playwright (pytest-playwright) · pytest                               |

---

## 1. Background

The Files tool of Autodesk Construction Cloud can enforce a **file naming standard** on a folder. When a file enters such a folder, a **File Validator** checks its name and attribute values before the operation is allowed. The operations in scope are **upload**, **delete**, and **restore**.

This document specifies the requirements for the **test automation framework** that will be used to automate these operations.

### 1.1 Scope of this document

**This PRD specifies requirements only.**

**In scope — build the test framework first:**

- Project structure and coding conventions.
- Configuration, fixtures, multi-browser support, execution modes.
- Reporting, logging, screenshots and failure diagnostics.

**In scope — Phase 1 (this delivery) additionally includes exactly one test case:**

- `tests/test_acceptance.py::test_upload_delete_restore` — the end-to-end flow from `docs/sample_testcase/test-case-steps.txt`: automated login → open the enforced folder → upload with attributes → delete → restore with a renamed project value, including the delimiter negative check. Marked `acceptance`.
- This is the **only** product test in Phase 1. It doubles as the end-to-end verification vehicle for the framework plumbing.

**Out of scope — deferred to Phase 2 (or later):**

- All other test content: smoke / functional / integration test cases, boundary-value datasets, holding-area scenarios, Move/Copy/Rename flows, RowMenu-driven flows.
- (For reference, the test case set that this framework will later support is described in a separate document, `Homework-TestCases-EN.md`, which is **not** part of this PRD.)
- Also out of scope: defect reporting; the functional design of the product feature itself.

> **Working principle for this phase:** deliver a framework plus the one acceptance test that proves it end to end. That single test is a deliverable — not a throwaway sample. All other test content follows in Phase 2.

> **Framework self-verification is in scope (FR-15).** A framework self-test — static checks plus one infrastructure canary — proves the *harness* runs. It asserts infrastructure (browser launch, auth, config, Page Object instantiation), **not** product behaviour, so it does not conflict with the "no product test cases" scope above. It is the acceptance evidence that the framework is runnable.

### 1.2 Users of the framework

| User                      | Needs                                                                        |
| ------------------------- | ---------------------------------------------------------------------------- |
| Test engineer (author)    | Write and run automated flows for the naming-standard lifecycle.             |
| Reviewer / hiring manager | Clone the repository, configure credentials, run the suite, read the report. |
| CI (future)               | Run the smoke suite on each commit without a human.                          |

---

## 2. Requirements overview

| ID    | Requirement                                                | Priority | Phase |
| ----- | ---------------------------------------------------------- | -------- | ----- |
| FR-01 | POM (Page Object Model) design                             | Must     | 1     |
| FR-02 | Playwright + Python implementation                         | Must     | 1     |
| FR-03 | Multi-browser support                                      | Must     | 1     |
| FR-04 | Test suites: smoke / acceptance / functional / integration | Must     | 1+2   |
| FR-05 | Data-driven testing                                        | Must     | 1+2   |
| FR-06 | Visual test report                                         | Must     | 1     |
| FR-07 | Configurable credentials, URL, environment                 | Must     | 1+2   |
| FR-08 | Parallel and serial execution                              | Must     | 1+2   |
| FR-09 | Automatic rerun of failed tests (2 attempts)               | Must     | 1     |
| FR-10 | Screenshot capture on failure                              | Must     | 1     |
| FR-11 | Step-level logging system                                  | Must     | 1     |
| FR-12 | Credentials never stored in plain text                     | Must     | 1     |
| FR-13 | Defined project file structure                             | Must     | 1     |
| FR-14 | README with usage instructions                             | Must     | 1     |
| FR-15 | Framework self-verification (smoke gate)                   | Must     | 1     |

> **Phase legend:** Phase 1 = this delivery. Phase 2 = deferred. 1+2 = partially delivered in Phase 1 — the specific split is stated in the FR section.

---

## 3. Functional requirements

### FR-01 — POM design

The framework must follow the Page Object Model pattern, with three kinds of objects:

| Kind          | Criterion                                                  | Examples                                                                                |
| ------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Page**      | Has its own URL and can be opened directly                 | `LoginPage`, `ProjectPage`, `FilesPage`, `DeletedItemsPage`                             |
| **Dialog**    | A modal rendered on top of a page; the URL does not change | `ValidatorDialog` (base), `UploadValidator`, `RestoreValidator`, `UploadProgressDialog` |
| **Component** | Reused by several pages/views, **or** complex enough to warrant its own locators (trees, portal dropdowns) | `AppNav`, `FileToolbar`, `FolderTree`, `FileRow`, `RowMenu`, `Toast`                    |

Rules:

- All page/dialog/component classes inherit from `BasePage`.
- `UploadValidator` and `RestoreValidator` **must** inherit from a shared `ValidatorDialog` base class — the two dialogs are structurally identical (10 attribute fields + file name, error banner, disabled primary button).
- **Locators live inside page objects.** A page object exposes *typed `Locator` properties / factory methods* (e.g. `files_page.submit_button`, `files_page.file_row(name)`). Test methods obtain elements only through those properties and assert with Playwright web-first assertions: `expect(files_page.submit_button).to_be_enabled()`.
- **Forbidden in `tests/`:** a *raw selector string* written against `page` directly — e.g. `page.locator("div.btn-primary")` or an inline `page.get_by_role("button", name="Submit")` inside a test. The `locator` / `get_by_role` keywords are allowed inside page objects, and a `Locator` object received from a page property is allowed in tests.
- **Row composition:** `FilesPage.row(name)` is a factory returning a `FileRow` (checkbox, name link, version pill, `⋮` button). Row actions that open the `⋮` dropdown delegate to a `RowMenu`.
- **Portal rule (⭐ flakiness guard):** the `RowMenu` dropdown — like all dialogs — renders in a **portal** outside the triggering row's DOM. Its locators are defined in its own class, rooted at the overlay container, and are **never** scoped under the row locator (`row.locator(...)`). Row-scoped menu locators are a top cause of *detached element* failures.

Example composition — the checkbox + toolbar path used by the Phase-1 acceptance test:

```python
files_page.row(expected_name).select()            # FileRow checkbox
files_page.toolbar.delete()                       # Action Bar button
expect(files_page.toast.success).to_be_visible()
```

(Deferred to Phase 2 — the ⋮ RowMenu path: `files_page.row(name).open_menu().delete()`. The portal rule below applies to RowMenu and to all attribute dropdowns.)

**Acceptance criteria:** in any file under `tests/`, no locator is built from a hardcoded selector string on `page` directly; all element access flows through a page-object `Locator` property. (Grep guard: zero `page.locator("` / `page.get_by_role("` with an inline string literal under `tests/`.)

### FR-02 — Playwright + Python

- Python 3.11+, Playwright Python SDK, driven by **pytest** via `pytest-playwright`.
- Async API is **not** required; the sync API is used.
- Dependencies are declared in `requirements.txt` with pinned versions.

### FR-03 — Multi-browser support

- Support **Chromium, Firefox, WebKit** through the standard `--browser` option.
- Selection must work three ways: CLI option, environment variable, and default in config.
- Headless / headed switchable (`--headed`), configurable default in `pytest.ini`.

```
pytest --browser chromium
pytest --browser firefox --headed
BROWSER=webkit pytest
```

**Acceptance criteria:** the same test runs on **Chromium and Firefox** with no code change. WebKit is supported via `--browser webkit` but is **Tier-3 (optional)** — see the tier table below; it is excluded from the default CI gate because ACC's heavy WebGL/Canvas front-end can produce engine-specific rendering glitches unrelated to the framework.

| Tier | Engine   | Role in CI / gate                                                 |
| ---- | -------- | ----------------------------------------------------------------- |
| 1    | Chromium | Blocking gate — must pass                                         |
| 2    | Firefox  | Supported — run in CI; non-blocking on first failures             |
| 3    | WebKit   | Optional — run manually; never blocks framework delivery          |


### FR-04 — Test suites (smoke / acceptance / functional / integration)

The framework must define four suites and let the user run any of them.

| Suite           | Meaning                                                     | Typical content                                                  | Phase |
| --------------- | ----------------------------------------------------------- | ---------------------------------------------------------------- | ----- |
| **smoke**       | Fastest sanity check; proves the environment and login work | Login + open folder + one upload                                 | 2     |
| **acceptance**  | The business-critical path the stakeholder cares about      | Upload → delete → restore with a new name                        | 1     |
| **functional**  | Full coverage of validation rules                           | Boundary values, character types, special characters, duplicates | 2     |
| **integration** | Cross-component / cross-view flows                          | Files ↔ Deleted items ↔ restore, permission variations           | 2     |

Implementation:

- Registered as pytest markers in `pytest.ini` (`markers = smoke, acceptance, functional, integration`). `-m` is the canonical selection mechanism.
- **Phase 1** ships content for the `acceptance` marker only: `test_upload_delete_restore` (upload → delete → restore with a new name). Smoke / functional / integration content is Phase 2.
- A `--suite` convenience option is planned as a **thin alias**: it will map directly to pytest's `markexpr` (e.g. `--suite smoke` ⇒ `-m smoke`) via `pytest_addoption` + assignment to `config.option.markexpr`. It must **not** implement a separate collection / traversal filter. **Deferred to Phase 2** — in Phase 1 markers are selected directly with `-m`.
- Fixtures are layered: `session` (browser, auth state), `module` (project context), `function` (page, test data, cleanup).

```
pytest -m acceptance
pytest -m acceptance --browser firefox
```

**Acceptance criteria:** `pytest -m acceptance` selects exactly the tests marked `acceptance`, and unmarked tests are reported as not selected rather than silently skipped.

### FR-05 — Data-driven testing

- Test data is defined outside the test logic, in `utils/test_data.py`.
- Suites must be parameterisable via `@pytest.mark.parametrize` over datasets of `(field, value, expected_result)`.
- The framework provides:
  - a `NamingAttributes` data class describing all **10 attribute fields** (Project, Volume/System, Level/Location, Type, Role, Number, Status, Revision, Classification, custom fields); the composed file name is the 11th element, produced by `expected_file_name()`;
  - `expected_file_name()` — the file-name composition rule defined **once** and reused by assertions. The exact composition order is verified at runtime from the validator's live **Preview** and documented here once observed (see Open questions Q7);
  - `unique_project()` — generates a value that satisfies the field constraint (Alphanumeric, 2–6) while staying unique per run, to avoid `duplicates` errors on repeated runs;
  - boundary datasets (min−1 / min / max / max+1) and negative datasets — **deferred to Phase 2** (functional suite).
- **Delimiter rule (Phase 1, exercised by the acceptance test):** an attribute value must not contain the naming standard's delimiter (`-`) nor the forbidden characters `< > : " / | ? * \`. The UI error text is exactly: *"The delimiter character can't be used in an attribute value"*. `test_data.py` exposes the delimiter value and this error text.

Rules for data usage:
- Every test that **creates** a file must use `unique_project()` — never a fixed value.
- ⚠️ Values seen in the demo (`test2`, `res1`, `1234`) **must not** be used as regression data: those names may already exist in the shared project and would trigger false `duplicates` failures. They belong to the manual walkthrough only.
- The single exception is the **duplicates** test case, which intentionally submits the same attribute set twice.

**Acceptance criteria:** adding a new data row requires no change to test code.

### FR-06 — Visual test report

- Every run produces an HTML report with pass/fail counts, duration, per-test status, and failure messages.
- Backend: `pytest-html` (Allure is out of scope).
- Failed tests embed the screenshot inline where the backend supports it.
- Reports are written to `reports/` and ignored by git, except when explicitly archived.

```
pytest --html=reports/report.html --self-contained-html
```

**Acceptance criteria:** a single self-contained HTML file that opens without a server.

### FR-07 — Configurability

All environment-dependent values are externalised — never hardcoded.

| Setting            | Source                         | Example                                |
| ------------------ | ------------------------------ | -------------------------------------- |
| Base URL           | `.env`                         | `https://acc.autodesk.com`             |
| Project ID         | `.env`                         | `4ac3aedc-e6d5-4bbb-91f3-c49c48af48f4` |
| Folder name        | `.env`                         | `Name-standard` (the enforced folder)  |
| Username           | `.env`                         | —                                      |
| Password           | `.env`                         | —                                      |
| Environment name   | `--env dev\|staging\|prod`     | Phase 2 — deferred                     |
| Browser / headless | CLI or `.env`                  | `chromium` / `true`                    |
| Timeouts           | `pytest.ini` + `.env` override | 30 000 ms                              |

- `utils/config.py` loads `.env` via `python-dotenv` and exposes typed settings.
- Missing required settings must fail fast with a clear message at session start.

**Acceptance criteria:** the same code runs against a different environment by changing `.env` only.

### FR-08 — Parallel and serial execution

- **Serial** (default): `pytest` with no options. **Phase 1 runs serial only.**
- **Parallel**: `pytest-xdist`, `pytest -n auto` or `-n 4` — **deferred to Phase 2.**
- The framework must remain correct in both modes: per-test data isolation, no shared mutable state, unique file names.
- ⚠️ **Shared-folder write operations are forced serial.** The target ACC project is shared; even with unique file names, concurrent upload / delete on the same folder triggers server-pushed DOM re-renders (list rows shift, toasts overlap) that cause *Element detached / stale element* flakiness. Therefore **all write operations (upload / delete / rename / restore) on a shared folder run serially by default.** Phase 1 complies by construction (one serial test); Phase 2 adds enforcement.
- Parallel (`-n auto`) will be permitted **only** for read-only / smoke runs **and** only when each worker operates on a **distinct, worker-owned sub-folder** — never the shared root folder. This precondition must be documented and enforced by a fixture guard (Phase 2).

**Acceptance criteria (Phase 1):** the acceptance test runs serially and leaves the shared folder in the documented end state. Phase 2: `pytest -n 2` and `pytest` produce the same result for the smoke suite (read-only); a write suite refuses to run in parallel against the shared root folder.

### FR-09 — Rerun failed tests

- Rerun a failed test up to **2** times before marking it failed, via `pytest-rerunfailures`.
- Default in `pytest.ini`: `--reruns 2 --reruns-delay 1`.
- Rerun history must appear in the report so flaky tests are distinguishable from real failures.

### FR-10 — Screenshot on failure

- On any test failure, capture a full-page screenshot automatically.
- Save to `reports/screenshots/<test_name>_<timestamp>.png`.
- The screenshot path is written to the log and, where supported, embedded in the HTML report.
- Implemented in a `pytest_runtest_makereport` hook in `conftest.py` — no per-test code required.

**Acceptance criteria:** a deliberate failure produces a PNG file and a log line referencing it.


### FR-11 — Logging system

The framework must provide a dedicated logging system with **step-level** granularity.

Requirements:

- One log file per test run: `logs/run_<timestamp>.log`; optionally grouped per test.
- Every **step** of every test is logged — not just pass/fail. A `@step("...")` decorator (or context manager) wraps page-object actions and emits:  
  `timestamp | level | test_name | step | action/selector | result | duration_ms`
- Log levels: DEBUG / INFO / WARNING / ERROR, configurable.
- On failure, the log includes the exception, the failing step, and the screenshot path.
- Console output and file output use different levels (console INFO, file DEBUG).
- **No `time.sleep()`** — all waits are Playwright's automatic waiting or web-first assertions; the log records actual wait durations.

Example output:

```
2026-09-21 22:40:11.203 | INFO  | test_upload_delete_restore | STEP 3.2 | fill Project = hw472 | OK | 128ms
2026-09-21 22:40:11.905 | INFO  | test_upload_delete_restore | STEP 3.3 | pick Type = CA | OK | 640ms
2026-09-21 22:40:12.010 | ERROR | test_upload_delete_restore | STEP 3.4 | expect banner hidden | FAIL | screenshot: reports/screenshots/...png
```

**Acceptance criteria:** a failed test can be diagnosed from the log alone, without re-running it.

> **Implementation note — step reporting:** the `@step` decorator above is a *custom* Python implementation (pytest hook + log emission). Playwright's native `test.step` API exists **only in `@playwright/test` (TypeScript / JavaScript)** and is **not available in the Python / pytest stack** used here, so it cannot be "synced in". Optionally, step boundaries can also be surfaced in the Playwright Trace Viewer via the tracing API, but the canonical step log is the `@step` decorator.

### FR-12 — Credential security & auth bootstrap

- **Password encryption for the public repository:** the committed `config/credentials.json` holds the username and a **Fernet-encrypted password token** (`cryptography` library); `utils/config.py` decrypts it at runtime. The plaintext password never appears in the repo, logs, or reports.
- **The Fernet decryption key is not committed.** The reviewer receives it out of band and places it in local `.env` as `ACC_FERNET_KEY`, or in git-ignored `config/fernet.key`. Without the key, the encrypted token cannot be decrypted.
- Credential resolution order: local `ACC_PASSWORD` in `.env` (owner's own credentials — not committed) → encrypted token in `config/credentials.json` plus the local Fernet key. Fail fast if neither password path is available, or if the token is present but the key is missing.
- `.env.example` is committed with key names and placeholders only.
- Rotation: `python utils/encrypt_password.py` generates a fresh key + token pair. The token is written to `config/credentials.json`; the key is written only to local `.env` / `config/fernet.key` and must never be committed.
- `auth_state.json` (Playwright storage state) is git-ignored.
- The framework must never print credentials, and must not write them into logs or reports.
- A pre-commit / CI check ensures `.env`, `auth_state.json`, and `config/fernet.key` are not tracked.

**Authentication — automated login inside the test run** (required by the homework statement: "Automate the steps, including the login"). The suite must be runnable in one command with no manual step:

- A session-scoped login fixture (`conftest.py` + a `LoginPage` action) logs in automatically with credentials from `.env`. Credentials are never hardcoded, logged, or printed.
- Optional caching: if `auth_state.json` exists and is valid, the fixture may reuse it to skip one login round-trip; otherwise it logs in programmatically. Phase-1 default is plain programmatic login each run — simplest and always correct.
- `utils/setup_auth.py --headed` remains as a **fallback** for accounts whose SSO / MFA challenges block automated login; it saves `auth_state.json` for reuse by the fixture.
- If automated login fails, the run fails fast with a clear message pointing to the fallback script. No fragile MFA-bypass code is built into the framework.

⚠️ **Known risk (Open questions Q1):** if the account enforces MFA / SSO, automated login may not be possible and the fallback becomes mandatory — verify on the first live run.


### FR-13 — Project file structure

The framework must implement exactly this structure:

```
acc-naming-standard-e2e/
├── pages/                          # Page objects (own a URL)
│   ├── __init__.py
│   ├── base_page.py                # Common waits, screenshot, step logging base
│   ├── login_page.py               # Login; used by setup_auth.py only (no login steps in tests)
│   ├── project_page.py             # Project landing page
│   ├── files_page.py               # Files tool: folder list, file list, toolbar
│   └── deleted_items_page.py       # Deleted items view (moduleId=deleted — own URL, so a Page)
├── dialogs/                        # Modal dialogs (no URL)
│   ├── __init__.py
│   ├── validator_dialog.py         # ⭐ Base: shared 10 attribute fields, banner, buttons
│   ├── upload_validator.py         # extends ValidatorDialog (upload review screen)
│   ├── restore_validator.py        # extends ValidatorDialog; asserts pre-fill and handles
│   │                               #   yellow "previous version" Accept values
│   ├── upload_dialog.py            # Step-3 file picker: "Select files" → OS file chooser
│   ├── restore_confirm_dialog.py   # Step-15 restore confirmation ("Restore" button)
│   ├── restore_items_dialog.py     # Step-16 "Restore items" dialog + Continue
│   └── upload_progress_dialog.py   # Upload progress + Done
├── components/                     # Reusable UI blocks
│   ├── __init__.py
│   ├── app_nav.py                  # Left navigation rail
│   ├── folder_list.py              # Folder list: open folder by name (Phase-1 minimal API;
│   │                               #   nested-tree expansion is Phase 2)
│   ├── file_toolbar.py             # Top action bar: Upload split-button, contextual Delete /
│   │                               #   Restore (Restore appears only after a row is selected),
│   │                               #   Deleted items, Export, Search and filter, view toggle
│   ├── file_row.py                 # One file row: checkbox, name, version pill, ⋮ button
│   ├── row_menu.py                 # ⋮ dropdown — portal overlay, own locators (never row-scoped);
│   │                               #   ⏸ Phase 2 (not used by the Phase-1 test)
│   └── toast.py                    # Success/error toast assertions
├── utils/
│   ├── __init__.py
│   ├── config.py                   # .env loading, typed settings, encrypted-password resolution, fail-fast validation
│   ├── test_data.py                # NamingAttributes, expected_file_name(), datasets
│   ├── file_factory.py             # ⏸ Phase 2 — Phase 1 uploads the static data/files/a.txt
│   ├── logger.py                   # ⭐ Logging system + @step decorator
│   ├── auth.py                     # storage_state save / load (optional login cache; automated login is primary)
│   ├── setup_auth.py               # Interactive headed bootstrap → auth_state.json (handles SSO/MFA)
│   └── encrypt_password.py         # CLI helper: local Fernet key + token for config/credentials.json
├── data/
│   └── files/                      # Static sample files (committed); Phase 1 needs a.txt only
│       └── a.txt                   #   (generated/ + file_factory deferred to Phase 2)
├── config/
│   └── credentials.json            # Committed: username + Fernet-encrypted password token (key is local-only)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures, hooks, screenshot-on-failure
│   ├── test_framework_smoke.py     # FR-15 canary (framework self-test)
│   └── test_acceptance.py          # ⭐ The Phase-1 deliverable: test_upload_delete_restore
├── reports/                        # HTML reports + screenshots (git-ignored)
│   └── screenshots/
├── logs/                           # Run logs (git-ignored)
├── .env.example                    # Committed template
├── .env                            # Real values — NOT committed
├── .gitignore
├── pytest.ini                      # Markers, default options (reruns, html)
├── requirements.txt
├── PRD.md                          # This document
└── README.md                       # Framework overview + usage
```

### FR-14 — README

The repository root must contain `README.md` (English) covering:

1. What the framework is and what it tests.
2. Prerequisites (Python version, `pip install -r requirements.txt`, `playwright install`).
3. Configuration — copy `.env.example` to `.env` and fill it; **never commit `.env`**. The reviewer also places the separately provided Fernet key in `ACC_FERNET_KEY` (or `config/fernet.key`).
4. How to run: the **first** commands must be the reviewer path (`pip` / `playwright install` → copy `.env` → one headed `pytest -m acceptance`, or `run.ps1` / `run.sh`). Then default, by suite, by browser, parallel. Do not lead with framework-only commands.
5. Where to find reports, screenshots and logs.
6. How to regenerate the login state (`auth_state.json`), including the MFA note.
7. Project structure at a glance.
8. Coding conventions: POM, no raw locators in tests, no `sleep`, every action wrapped in `@step`.

---

## 3b. Framework self-verification (FR-15)

The framework must include a **self-verification mechanism** so that breakage *inside the framework itself* — a broken `BasePage`, a malfunctioning `conftest` fixture, a misconfigured config loader, a wrong `storage_state` path — is caught **before any product test is attempted**, and reports "framework broken" rather than a confusing cascade of product-test failures.

Two layers, both **in scope** even though product test cases are out of scope:

### Layer A — Static / structural checks (no browser, fast, runs first)

- Every module under `pages/`, `dialogs/`, `components/`, `utils/` imports without error.
- `pytest --collect-only` over `tests/` completes with **zero** collection errors (catches broken fixtures, imports, and locator syntax before a browser is ever launched).
- A linter (`ruff check .`, or `flake8`) passes in CI and locally.
- `utils/config.py` loads and all keys documented in `.env.example` resolve.

### Layer B — Runtime infrastructure canary (one minimal, always-green test)

A single framework-internal test (excluded from the product suite markers) that proves the harness end to end:

1. Launch the configured browser — **Chromium (Tier-1, blocking)** and **Firefox (Tier-2)**; WebKit (Tier-3) is exercised manually and never blocks the canary.
2. Load config and authenticate via the automated login fixture.
3. Instantiate `BasePage` and at least one concrete Page Object.
4. Perform **one trivial assertion** on a loaded page (e.g., a known static element on the login page is present).

This test must stay green. Its failure means the *harness* is broken, not the product. It asserts infrastructure only — it is **not** a product test case.

### Gate / ordering

- Static checks (Layer A) run first; they need no browser and fail fast on typos, broken imports, or broken fixtures.
- The canary (Layer B) runs next.
- Product suites (FR-04) run only after both pass. If the canary fails, the build fails fast with a clear "framework" signal.

**What is explicitly NOT required:** unit tests for individual POM methods. Page objects are themselves test code; testing them is brittle and a maintenance sink. The canary verifies the harness, not the product UI logic.

**Acceptance criteria:**

- `pytest --collect-only` finishes with zero errors on a fresh clone.
- The framework canary passes on **Chromium and Firefox** (Tier-1 + Tier-2). WebKit is optional and excluded from the blocking gate.
- Intentionally breaking `BasePage` (e.g., renaming a method the canary uses) makes the canary fail clearly and immediately — proving the guard actually catches regressions.

---

## 4. Non-functional requirements

| ID     | Requirement                                                                                                                 |
| ------ | --------------------------------------------------------------------------------------------------------------------------- |
| NFR-01 | **Stability** — no `time.sleep()`; all synchronisation uses Playwright auto-waiting or `expect()` assertions.               |
| NFR-02 | **Readability** — test methods read like business steps; all UI detail is encapsulated in page objects.                     |
| NFR-03 | **Traceability** — every failure is reproducible from logs + screenshot + trace.                                            |
| NFR-04 | **Portability** — runs on Windows / macOS / Linux; no OS-specific paths in code.                                            |
| NFR-05 | **CI readiness** — a single command runs the acceptance test headless and returns a proper exit code.                        |
| NFR-06 | **Clean test data** — tests create uniquely named files and clean up after themselves; the shared ACC project is left tidy. Phase-1 deviation (documented): the acceptance test's expected end state *is* the restored file, so one uniquely-named file remains per run and is purged manually — noted in README. |
| NFR-07 | **Trace on failure** — Playwright tracing enabled (`retain-on-failure`) so failures can be replayed in Trace Viewer.        |

---

## 5. Execution matrix

| Purpose                     | Command                                                 | Phase |
| --------------------------- | ------------------------------------------------------- | ----- |
| Reviewer one-shot (M6)      | `run.ps1` (Windows) or `run.sh` (macOS / Linux)         | 1     |
| Acceptance (default)        | `pytest -m acceptance`                                  | 1     |
| Acceptance, headed (dev)    | `pytest -m acceptance --headed`                         | 1     |
| Acceptance, Firefox         | `pytest -m acceptance --browser firefox`                | 1     |
| Serial, verbose             | `pytest -s -v`                                          | 1     |
| Debug a single test         | `pytest tests/test_acceptance.py::test_upload_delete_restore -s --headed --reruns 0` | 1 |
| Framework self-check        | `ruff check . && pytest --collect-only && pytest tests/test_framework_smoke.py` | 1 |
| Smoke only                  | `pytest --suite smoke`                                  | 2     |
| Parallel (read-only suites) | `pytest --suite smoke -n auto`                          | 2     |
| Custom environment          | `pytest --env staging`                                  | 2     |

---

## 6. Deliverables and milestones

### Phase 1 (this delivery)

| Milestone | Content                                                                                 | Status  |
| --------- | --------------------------------------------------------------------------------------- | ------- |
| M1        | Repository skeleton + `pytest.ini` + `requirements.txt` + `.env.example` + `.gitignore` | Pending |
| M2        | `utils/` — config, logger (`@step`), test_data, auth + `setup_auth.py` (interactive SSO) | Pending |
| M3        | `pages/` + `components/` — base, files, deleted items, login (bootstrap only), toolbar, file row, folder list, toast | Pending |
| M4        | `dialogs/` — ValidatorDialog base + upload validator / picker / progress, restore validator + restore confirm / restore-items | Pending |
| M5        | `test_upload_delete_restore`: login (reuse session) + upload → delete → restore on live ACC, including delimiter steps 18–19. | Done |
| M6        | Reviewer README (one command first) + `run.ps1` / `run.sh`. No Docker. | Done |

### Phase 2 (deferred backlog)

`--suite` alias · xdist parallel + write-guard fixture · functional boundary datasets · RowMenu flows · holding-area scenarios · Move/Copy/Rename flows · full Classification list capture · `--env` blocks · WebKit automation · validator bulk edit (`Edit all`).

**Note:** Phase 1 delivers exactly one product test (`test_upload_delete_restore`); it is a deliverable in its own right and doubles as the framework's end-to-end verification, alongside the FR-15 canary.

---

## 7. Acceptance checklist

Tick every row before the framework is considered done:

| #  | Requirement                | How to verify                                                                     | Phase | Done |
| -- | -------------------------- | --------------------------------------------------------------------------------- | ----- | ---- |
| 1  | FR-01 No raw locators      | Search `tests/` for `locator(` / `get_by_` — zero hits                            | 1     | ☐    |
| 2  | FR-01 Shared validator     | Upload and Restore validators both inherit `ValidatorDialog`                      | 1     | ☐    |
| 3  | FR-02 Dependencies         | `pip install -r requirements.txt` works from a clean virtualenv                   | 1     | ☐    |
| 4  | FR-03 Multi-browser        | Acceptance + canary pass on Chromium (gate) + Firefox; WebKit optional, not blocking | 1  | ☐    |
| 5  | FR-04 Four suites          | Markers registered; Phase 1 verifies `-m acceptance`; `--suite` alias selection is Phase 2 | 1+2 | ☐ |
| 6  | FR-05 Data-driven          | Adding a row to the Phase-1 acceptance dataset needs no test-code change          | 1     | ☐    |
| 7  | FR-05 Demo values not reused | `test2` / `res1` / `1234` must appear nowhere under `tests/`                    | 1     | ☐    |
| 8  | FR-06 Report               | One self-contained `reports/report.html` opens standalone                         | 1     | ☐    |
| 9  | FR-07 Config               | Changing `.env` targets another project/folder with no code edit                  | 1     | ☐    |
| 10 | FR-08 Serial and parallel  | Phase 1: serial-only run is stable; Phase 2: `-n 2` equals default + write guard  | 1+2   | ☐    |
| 11 | FR-09 Rerun                | A deliberately flaky test is retried twice, then reported with its history        | 1     | ☐    |
| 12 | FR-10 Screenshot           | A deliberate failure produces a PNG referenced in the log                         | 1     | ☐    |
| 13 | FR-11 Step logging         | Every page action emits a step line; a failure is diagnosable from the log alone  | 1     | ☐    |
| 14 | FR-11 No sleeps            | Search for `time.sleep` / `wait_for_timeout` — zero unjustified hits              | 1     | ☐    |
| 15 | FR-12 Secrets              | `.env`, `auth_state.json`, and `config/fernet.key` are git-ignored; the password exists in the repo only as a Fernet token in `config/credentials.json`; the decryption key is local-only / sent out of band; no credential appears in logs | 1 | ☐ |
| 16 | FR-13 Structure            | Directory tree matches FR-13 exactly                                              | 1     | ☐    |
| 17 | FR-14 README               | All eight required sections are present                                           | 1     | ☐    |
| 18 | NFR-06 Clean test data     | A run leaves at most one uniquely-named restored file (documented Phase-1 deviation) | 1  | ☐    |
| 19 | NFR-07 Trace               | Failures produce a `trace.zip` openable in Trace Viewer                           | 1     | ☐    |
| 20 | End to end                 | Fresh clone + `.env` + `pytest -m acceptance` works                               | 1     | ☐    |
| 21 | FR-15 Static + canary      | `pytest --collect-only` zero errors; canary passes on Chromium + Firefox (WebKit optional) | 1 | ☐ |
| 22 | FR-15 Break detection      | Intentionally breaking `BasePage` makes the canary fail clearly and immediately   | 1     | ☐    |
| 23 | Acceptance test            | `test_upload_delete_restore` covers automated login + all 21 steps of `docs/sample_testcase/test-case-steps.txt`, incl. the delimiter negative check | 1 | ☐ |



---

## 8. Open questions

1. Does the test account have **MFA** enabled? Primary path is automated login with `.env` credentials (FR-12); if the account enforces MFA / SSO, automated login fails and `setup_auth.py --headed` becomes mandatory — verify on the first live run.
2. Is the **Holding area** enabled in the project? (Affects which validator branches are reachable. The recorded upload completed compliantly, so Phase 1 is unaffected; matters for Phase-2 scenarios.)
3. ✅ **Resolved** — Deleted items has its own URL discriminator (`moduleId=deleted`) → it stays a Page object.
4. What permission level does the account have — Viewer, Editor, or Project Admin? (The account can upload/delete/restore, so at least Editor.)
5. ✅ **Resolved** — the environment is a shared project; write operations remain serial (Phase 1 by construction).
6. ✅ **Resolved** — dropdown option lists captured in `docs/`: Volume=2, Level=9, Type=28, Role=20, Status=24. Classification is virtualized (see Q9).
7. What is the exact **file-name composition order** and delimiter? The *File Naming Standard* help URL 404s; Phase 1 avoids hardcoding by asserting against the validator's live **Preview** text, and the composition rule is documented once observed at runtime.
8. ✅ **Resolved** — two separate dialogs: the step-15 restore confirmation ("Restore" button) and the step-16 "Restore items" dialog with Continue.
9. ✅ **Resolved** — the Classification dropdown accepts direct text input: type `Ac_05` and select the matching option; no scrolling required.

---

## 9. References

### Official help documentation (Autodesk)

| Link | Covers |
| --- | --- |
| [File Naming Standard](https://help.autodesk.com/view/DOCS/ENU/?guid=File_Naming_Standard) | Feature overview — naming standard on folders, file validator, attributes. (URL returned 404 at review time; see Open questions Q7.) |
| [Add Files To Naming Standard Enforced Folder](https://help.autodesk.com/view/DOCS/ENU/?guid=Add_Files_To_Naming_Standard_Enforced_Folder) | Validator dialog behavior: error categories (incl. the delimiter / special characters), previous-version values on restore, bulk edit, holding area. |
| [Upload files](https://help.autodesk.com/view/DOCS/ENU/?guid=Upload_files#how-to-upload-files) | Standard upload flow and file operations. |
| [Delete Files](https://help.autodesk.com/view/DOCS/ENU/?guid=Delete_Files_Docs) | Delete flow and Deleted items behavior. |

### Target environment

- Project: `yuanyuan.zhang.hw` — https://acc.autodesk.com/docs/files/projects/4ac3aedc-e6d5-4bbb-91f3-c49c48af48f4
- Enforced folder: `Name-standard`

### Local reference documents (this repository)

| Path | Content |
| --- | --- |
| `docs/sample_testcase/test-case-steps.txt` | The 21-step manual walkthrough that the Phase-1 test automates |
| `docs/sample_testcase/step*.png` | Screenshots of each manual step |
| `docs/autodesk-field-validation-rules.md` | Field validation rules incl. the delimiter rule |
| `docs/autodesk-{volume,level,type,role,status,classification}-options.md` | Captured dropdown option lists for the six attribute dropdowns |
| `docs/prd-review-and-minimized-plan.md` | Review that led to v1.2 + the minimized Phase-1 plan |

---

## 10. Execution addendum (T1 scaffold)

These items are part of Phase 1 delivery and keep the repo aligned with the Stage 1 plan:

- `dialogs/delete_dialog.py` — Delete confirmation (testcase step 11).
- `scripts/verify_framework.py` — one-click FR-15 gate: `ruff check .` → `pytest --collect-only` → `pytest -m framework`.
- `framework` pytest marker and `tests/framework/` — FR-15 Layer A. Not a product suite.
- `components/row_menu.py` and `utils/file_factory.py` exist as Phase 2 shells so the FR-13 tree is complete.
