# ACC Naming Standard E2E

A Playwright (Python, Sync API) + pytest **page-object** suite for Autodesk Construction Cloud **File Naming Standard**.

It automates the live path: sign in, open an enforced naming folder, upload a file with ten attributes, delete it, restore it, and prove that a forbidden delimiter in Project is rejected. A visitor who only reads this file should know what was built, how the framework is layered, and which script to run.

## What this repo implements

**Live product path** (`tests/test_acceptance.py::test_upload_delete_restore`, marker `acceptance`):

- Sign in to Autodesk ID and open the ACC project Files module.
- Enter the naming-standard folder (`ACC_FOLDER_NAME` in `.env`).
- Upload the committed sample `data/files/a.txt`.
- Fill ten naming attributes from `data/cases/acceptance.json`: Project, Volume/System, Level/Location, Type, Role, Number, Status, Revision, Classification, Custom fields.
- Unique Project and Number replace `${unique_project}` / `${unique_number}` on each load so the composed file name does not collide.
- Assert the file lands on Files (count +1, name in the list, upload toast).
- Delete it, then restore it from Deleted items (toasts, list membership, count ±1).
- Retry Project with the forbidden delimiter from `data/rules/naming.json` and assert the live error banner (`doesn't comply` / `special characters`).
- After the test, delete only the file this run uploaded. Delete moves it to Deleted items; this account cannot purge that view.

The sample story is `docs/sample_testcase/test-case-steps.txt` (steps 1–21), with screenshots next to it.

**Test case design** (86 cases, definitions only — not all are automated):

- Readable HTML: [`docs/ACC-Files-TestCaseDesign.html`](docs/ACC-Files-TestCaseDesign.html)
- Spreadsheet: [`docs/ACC-Files-TestCaseDesign.xlsx`](docs/ACC-Files-TestCaseDesign.xlsx)
- Source lists (edit then regenerate): `docs/generate_testcases.py`

Modules A–H cover folder permission, Action Bar, upload, naming attributes, delete, restore, validator errors, and browser notes. **Acceptance** in that document is the must-pass set; **Functional** is negative / boundary. This repo automates the upload → delete → restore walkthrough (plus the Project delimiter check). The other cases stay as design.

**Also implemented:**

- Page objects for Login, Project, Files, Upload files, Restore files, and Deleted items; dialogs for upload, progress, validator, delete, and restore; shared components (toolbar, folder list, file row, toast, nav).
- Session login that can reuse git-ignored `auth_state.json`, or decrypt `config/credentials.json` with a local Fernet key.
- Layered checks: page `verify_*` / `validate_*` stop a missing control; `pytest.assume` records a business miss and continues sibling checks.
- Step logs under `logs/` (`STEP` / `CASE` / `RUN`) and a PNG under `reports/screenshots/` on failure. Passwords and keys are not written to logs.
- Framework self-checks (`tests/framework/`, marker `framework`) that use fakes and never open ACC.
- Live smoke (`tests/test_live_smoke.py`, marker `smoke`): open Files, the upload picker, the validator, and Deleted items. It does not finish upload → delete → restore.
- Headed demo scripts `run.ps1` (Windows) and `run.sh` (macOS / Linux) with `--slowmo 500`.

**Not in this repo yet:** Phase 2 `functional` / `integration` case files. The pytest markers exist; there are no JSON suites for them.

## Framework

This is a POM test framework, not a page of raw locators.

Design rules:

- Tests call page and dialog methods. They do not call `page.get_by_*`.
- Page objects wait with Playwright auto-wait. There is no `time.sleep` / `wait_for_timeout`.
- Case values and naming rules live in JSON. Edit `data/cases/acceptance.json` and `data/rules/naming.json` to change ZZ / CA / D or the delimiter. Do not add a factory method in Python.
- `tests/framework/` never opens ACC. That gate is `pytest -m framework` (or `python scripts/verify_framework.py`).
- Playwright locale is pinned to `en-US` so ACC shows English (`Upload`, `Folders`) on a Chinese Windows host.

Layers:

| Layer | Role |
| --- | --- |
| `tests/test_acceptance.py` | Business flow and `pytest.assume` checks |
| `pages/` `dialogs/` `components/` | How to click and `verify_*` page state |
| `tests/conftest.py` + `tests/live_support.py` | Session login, open the folder, delete this run's leftovers |
| `utils/` | Settings, Fernet credentials, `@step` logger, JSON loaders |
| `data/cases/` + `data/rules/` | Case values and naming rules |

Assertions:

- `validate_*` / `verify_*` on a page object: the control is there. A miss stops the next click.
- `pytest.assume` in the test: field values, list membership, count ±1, banner text. One miss is recorded and later sibling checks still run.

Logging:

- `STEP n` — one page-object action (`click Upload`, `verify visible: Folders`).
- `CASE` — sample story line (`Step 3 - click Upload on the Action Bar`).
- `RUN` — test start/end, config (no password), prepare, cleanup.

Markers in `pytest.ini`:

| Marker | Meaning |
| --- | --- |
| `acceptance` | Live upload → delete → restore on ACC |
| `framework` | Self-checks with fakes. Does not open ACC |
| `smoke` | Live button/page smoke. Not the full story |
| `functional` / `integration` | Later suites. No cases yet |

## Scripts and how to run

You need Python 3.11 or newer, Chromium, and an Autodesk account that can open the target ACC project. On macOS the command is `python3`. There is no Docker path: the demo needs a real account and a visible browser.

| Script | What it does | How to run |
| --- | --- | --- |
| `run.ps1` | Windows headed demo: acceptance test, `--slowmo 500`, no reruns | `.\run.ps1 you@company.com` |
| `run.sh` | Same pytest on macOS / Linux; prefers `.venv`, then `python3` | `./run.sh you@company.com` |
| `scripts/verify_framework.py` | Offline gate: `ruff check .`, collect tests, `pytest -m framework` | `python scripts/verify_framework.py` |
| `utils/setup_auth.py` | Headed sign-in when SSO / MFA / Arkose blocks automation; writes `auth_state.json` | `python3 utils/setup_auth.py --headed` |
| `utils/encrypt_password.py` | Writes a local Fernet key and token for `config/credentials.json` | `python utils/encrypt_password.py` |

`run.ps1` is PowerShell only. `run.sh` is bash. Do not use `.\run.ps1` on a Mac unless you installed PowerShell 7 (`pwsh`) on purpose.

### 1. Install

```text
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

On Windows use `python` instead of `python3` if that is what `py --version` shows.

### 2. Configure

Copy `.env.example` to `.env`. Fill `ACC_PROJECT_ID` and `ACC_FOLDER_NAME` for a project you can open. **Never commit `.env`.**

### 3. Headed demo (watch the browser)

Both `run` scripts wrap:

```text
python3 -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo 500 --reruns 0
```

`--slowmo 500` pauses 500 ms between Playwright actions so the flow is easy to follow (about two to three minutes). After the first session works, skip the scripts and run pytest without `--slowmo` (see Daily use).

**Option 1 (recommended): your Autodesk account.** Pass the username only. The script asks for the password so `!` `&` `(` in zsh or PowerShell are not treated as shell syntax. Autodesk may send a code to *your* inbox and may show a picture challenge.

```text
.\run.ps1 you@company.com
chmod +x run.sh && ./run.sh you@company.com
```

If you pass the password on the command line, wrap it in single quotes: `./run.sh you@company.com 'p@ss!word'`.

If you already used a different account, delete `auth_state.json` first so the run does not reuse that session.

**Option 2: encrypted credentials in this repo.** Put a local Fernet key in `ACC_FERNET_KEY` or git-ignored `config/fernet.key`, then run with no login arguments:

```text
.\run.ps1
./run.sh
```

Use this only if you can decrypt `config/credentials.json` and open that account's inbox. A public clone does not include the Fernet key.

`pytest.ini` already defaults to `--headed`. Watch the Chromium window. The first run opens Autodesk ID. Finish the email code and any picture challenge in that window (about five minutes). Later runs reuse git-ignored `auth_state.json` when `ACC_SHOW_LOGIN=false`.

After the run, open the newest file under `logs/` and search `CASE` for sample steps 1–21, or `TEST NAME` / `TEST CASE` for the pytest function and JSON row.

### Sample run

A headed `./run.sh` on macOS. The script asks for the password; it is not printed.

```text
$ ./run.sh you@company.com
Password:
============================= test session starts ==============================
platform darwin -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0
rootdir: /path/to/acc-naming-standard-e2e
configfile: pytest.ini
plugins: assume-2.13.0, playwright-0.7.0, html-4.2.0, metadata-3.1.1, rerunfailures-16.0.1, anyio-4.11.0, base-url-2.1.0
collected 1 item

tests/test_acceptance.py .                                               [100%]

============================== 1 passed in 65.14s ==============================
```

Chromium stays visible for the upload → delete → restore flow. `--slowmo 500` makes this about one minute.

## Daily use

After the first session works, do **not** use `run.ps1` / `run.sh` for every local rerun. Those scripts are slow on purpose.

**Fast acceptance** (headed, no slowmo):

```text
pytest tests/test_acceptance.py -m acceptance --headed --reruns 0
```

`--reruns 0` turns off the default two reruns while you are debugging.

**Framework gate** (no browser, no ACC):

```text
ruff check .
pytest --collect-only
pytest -m framework
```

Or: `python scripts/verify_framework.py`.

**Live smoke** (opens ACC, does not finish upload → delete → restore):

```text
pytest tests/test_live_smoke.py
```

**Another browser:**

```text
pytest -m acceptance --browser firefox
```

**Change test data** in `data/cases/acceptance.json` and `data/rules/naming.json`. `${unique_project}` and `${unique_number}` are replaced on each load.

**Read a run:** newest file in `logs/`. Search `CASE` for the story, `STEP` for the click, `TEST CASE` for the JSON row. Failures also write a PNG under `reports/screenshots/`.

## Login

Login is a session fixture (`tests/conftest.py` + `LoginPage`). Tests do not type credentials. Pick one of the two paths above: Option 1 passes the username to `run.sh` / `run.ps1` (password is prompted); Option 2 decrypts `config/credentials.json` with a local Fernet key. Project id and folder stay in `.env`.

| `ACC_SHOW_LOGIN` | What happens |
| --- | --- |
| `false` (default) | If `auth_state.json` exists, reuse cookies. **No login page.** Daily runs use this. |
| `true` | Always open Autodesk ID and run `LoginPage`. |

If automated login cannot finish (SSO / MFA / Arkose), run `python3 utils/setup_auth.py --headed` (Windows: `python`). Complete sign-in in the window, then press Enter. Keep `ACC_SHOW_LOGIN=false` afterwards.

The framework does not solve Autodesk picture challenges or email codes. That is account protection, not a missing test step.

## Reports and logs

- Run logs: `logs/run_<timestamp>.log`
- Screenshots on failure: `reports/screenshots/`

## Layout

```text
pages/            Login, project, Files, Upload files, Restore files, Deleted items
dialogs/          Upload, progress, validator, delete, restore
components/       Toolbar, folder list, file row, toast, nav
utils/            config, auth, logger, test data
data/cases/       JSON case rows
data/rules/       Naming rules
data/files/       Sample upload (a.txt)
docs/sample_testcase/  Manual walkthrough + screenshots
docs/ACC-Files-TestCaseDesign.html  86-case design (open in a browser)
docs/ACC-Files-TestCaseDesign.xlsx  Same design as a spreadsheet
docs/generate_testcases.py          Regenerates the HTML and xlsx
tests/test_acceptance.py
tests/test_live_smoke.py
tests/framework/  Framework self-checks (no ACC)
tests/conftest.py Session login + English locale
run.ps1           Windows headed demo (slowmo)
run.sh            macOS / Linux headed demo (same pytest)
scripts/verify_framework.py
```

## Conventions

- POM only: tests call page methods, not `page.get_by_*`.
- No `time.sleep` / `wait_for_timeout`.
- Every page action is wrapped in `@step`.
- Do not commit `.env`, `auth_state.json`, `config/fernet.key`, or a plaintext password.
