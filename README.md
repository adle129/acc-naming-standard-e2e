# ACC Naming Standard E2E

Playwright (Python, Sync API) + pytest for the Autodesk Construction Cloud **File Naming Standard** flow: sign in, upload a file with attributes, delete it, and restore it.

This is a POM test framework, not a page of raw locators. Tests call page and dialog methods. Page objects wait with Playwright auto-wait. There is no `time.sleep`.

## Reviewer: run this first

1. Python 3.11 or newer. On macOS the command is `python3` (there is no `python` unless you add one).
2. Install dependencies:

```text
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

On Windows use `python` instead of `python3` if that is what `py --version` shows.

3. Copy `.env.example` to `.env` and fill `ACC_PROJECT_ID`, `ACC_FOLDER_NAME`, and username. Put the Fernet key you received out of band in `ACC_FERNET_KEY` or git-ignored `config/fernet.key`. **Never commit `.env`.**
4. Run the headed acceptance path (one command). **Windows** uses PowerShell:

```text
.\run.ps1
```

**macOS or Linux** uses the shell script (not `run.ps1`):

```text
chmod +x run.sh
./run.sh
```

`run.ps1` is for Windows PowerShell only. `run.sh` is for macOS and Linux. Both run the same pytest command. Do not use `.\run.ps1` on a Mac unless you have installed PowerShell 7 (`pwsh`) on purpose.

Both scripts add `--slowmo 500` so each click pauses 500 ms and the reviewer can follow the flow (about two to three minutes). A plain `pytest -m acceptance` without the script stays fast.

That is the same as:

```text
python3 -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo 500 --reruns 0
```

On Windows: `python -m pytest ...` (same flags). `run.sh` already picks `python3` on macOS.

`pytest.ini` already defaults to `--headed`. Watch the Chromium window. The first run may open Autodesk ID; finish any picture challenge once. Later runs reuse git-ignored `auth_state.json` when `ACC_SHOW_LOGIN=false`.

After the run, open the newest file under `logs/` and search `CASE` for sample steps 1–21, or `TEST NAME` / `TEST CASE` for the pytest function and JSON row.

There is no Docker path. The demo needs a real ACC account and a visible browser.

## Framework

The product path is one acceptance test: `tests/test_acceptance.py::test_upload_delete_restore`. It follows `docs/sample_testcase/test-case-steps.txt`: open the naming-standard folder, upload `data/files/a.txt`, fill ten attributes, delete, restore, and check a delimiter error on Project.

Layers:

| Layer | Role |
| --- | --- |
| `tests/test_acceptance.py` | Business flow and `pytest.assume` checks |
| `pages/` `dialogs/` `components/` | How to click and `verify_*` page state |
| `tests/conftest.py` + `tests/live_support.py` | Session login, open the folder, delete this run's leftovers |
| `utils/` | Settings, Fernet credentials, `@step` logger, JSON loaders |
| `data/cases/` + `data/rules/` | Case values and naming rules. Edit JSON to change ZZ / CA / D |

Assertions are split on purpose:

- `validate_*` / `verify_*` on a page object: the control is there. A miss stops the next click.
- `pytest.assume` in the test: field values, list membership, count ±1, banner text. One miss is recorded and later sibling checks still run.

Logging:

- `STEP n` — one page-object action (`click Upload`, `verify visible: Folders`).
- `CASE` — sample story line (`Step 3 - click Upload on the Action Bar`).
- `RUN` — test start/end, config (no password), prepare, cleanup.

Markers in `pytest.ini`:

| Marker | Meaning |
| --- | --- |
| `acceptance` | The interviewer path (this delivery) |
| `framework` | Self-checks with fakes. Does not open ACC |
| `smoke` | Live button/page smoke. Not the full story |
| `functional` / `integration` | Phase 2. No cases yet |

Playwright locale is pinned to `en-US` so ACC shows English (`Upload`, `Folders`) on a Chinese Windows host.

## Daily use

After the first session works, do **not** use `run.ps1` / `run.sh` for every local rerun. Those scripts are slow on purpose.

**Fast acceptance** (headed, no slowmo):

```text
pytest tests/test_acceptance.py -m acceptance --headed --reruns 0
```

`pytest.ini` already adds `--headed`. `--reruns 0` turns off the default two reruns while you are debugging.

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

**Change test data** in `data/cases/acceptance.json` (Volume, Type, Status, and so on) and `data/rules/naming.json` (delimiter, lengths). Do not add a factory method in Python. `${unique_project}` and `${unique_number}` are replaced on each load so the composed file name does not collide.

**Read a run:** newest file in `logs/`. Search `CASE` for the story, `STEP` for the click, `TEST CASE` for the JSON row. Failures also write a PNG under `reports/screenshots/`.

**Cleanup:** `live_acc` remembers the unique Project and composed name, then Delete on the Files list. Delete only moves the file to Deleted items. This account cannot purge that view.

## Login

Login is a session fixture (`tests/conftest.py` + `LoginPage`). Tests do not type credentials.

| `ACC_SHOW_LOGIN` | What happens |
| --- | --- |
| `false` (default) | If `auth_state.json` exists, reuse cookies. **No login page.** Daily runs use this. |
| `true` | Always open Autodesk ID and run `LoginPage`. |

If automated login cannot finish (SSO / MFA / Arkose), run:

```text
python utils/setup_auth.py --headed
```

Complete sign-in in the window, then press Enter. Keep `ACC_SHOW_LOGIN=false` afterwards.

The framework does not solve Autodesk picture challenges. That is account protection, not a missing test step.

## Reports and logs

- Run logs: `logs/run_<timestamp>.log`
- Screenshots on failure: `reports/screenshots/`

## Layout

```text
pages/            Login, project, Files, Deleted items
dialogs/          Upload, delete, restore, validator
components/       Toolbar, folder list, toast, nav
utils/            config, auth, logger, test data
data/cases/       JSON case rows
data/rules/       Naming rules
tests/test_acceptance.py
tests/framework/  Framework self-checks (no ACC)
tests/conftest.py Session login + English locale
run.ps1           Windows reviewer command (headed + slowmo)
run.sh            macOS / Linux reviewer command (same pytest)
```

## Conventions

- POM only: tests call page methods, not `page.get_by_*`.
- No `time.sleep` / `wait_for_timeout`.
- Every page action is wrapped in `@step`.
- Do not commit `.env`, `auth_state.json`, `config/fernet.key`, or a plaintext password.
