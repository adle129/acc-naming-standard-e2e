# ACC Naming Standard E2E

Playwright (Python, Sync API) + pytest framework for the Autodesk Construction Cloud **File Naming Standard** flow: sign in, upload a file with attributes, delete it, and restore it. Page objects live under `pages/`, `dialogs/`, and `components/`. Tests do not use raw locators or `time.sleep`.

## Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`
- `playwright install chromium`

## Configuration

Copy `.env.example` to `.env` and fill it. **Never commit `.env`.**

The public repo may contain `config/credentials.json` (username + Fernet token only). The Fernet key is **not** in Git. Put it in `ACC_FERNET_KEY` or git-ignored `config/fernet.key`. A local `ACC_PASSWORD` in `.env` overrides the token.

Change `ACC_PROJECT_ID` and `ACC_FOLDER_NAME` to a project you can edit that has a naming-standard folder. No code change is required.

Playwright is pinned to `locale=en-US` so ACC shows English (`Upload`, `Folders`) even on a Chinese Windows host.

`pytest.ini` defaults to `--headed` so the browser is visible.

## Login: two modes

Login is automated by a session fixture (`tests/conftest.py` + `LoginPage`). Tests do not type credentials.

| `ACC_SHOW_LOGIN` | What happens |
| --- | --- |
| `false` (default) | If `auth_state.json` exists, reuse cookies. **No login page.** Daily upload runs use this. |
| `true` | Always open Autodesk ID and run `LoginPage` (email, Next, password, Sign in). **Login page is shown.** |

Examples:

```text
# Hide login (reuse the saved session)
ACC_SHOW_LOGIN=false

# Show automated login
ACC_SHOW_LOGIN=true
```

`auth_state.json` is git-ignored. After a successful programmatic login the fixture writes it. You can also create it with:

```text
python utils/setup_auth.py --headed
```

Complete sign-in in the window (including any challenge), then press Enter.

### Autodesk human check (Arkose)

Some accounts (especially new or disposable mailboxes) show a picture challenge after password submit. The framework **does not** solve that puzzle. That is Autodesk account protection, not a missing login step.

- **Default (`ACC_SHOW_LOGIN=false`)** after one successful session: later runs skip Autodesk ID, so the challenge usually does not return.
- **`ACC_SHOW_LOGIN=true`** on an account that already triggers Arkose: the challenge will likely appear **every** run. Finish it in the headed window, or use a reviewer Autodesk account that does not enforce the check.

If automated login cannot finish (SSO / MFA / Arkose), use `python utils/setup_auth.py --headed` and keep `ACC_SHOW_LOGIN=false`.

## How to run

```text
pytest -m framework
pytest tests/test_live_smoke.py
pytest -m acceptance
pytest --browser firefox
```

Framework tests use fakes and do not open ACC. Product tests use the session login fixture.

## Reports and logs

- Screenshots: `reports/screenshots/`
- Run logs: `logs/`

## Layout

```text
pages/            Login, project, Files, Deleted items
dialogs/          Upload, delete, restore, validator
components/       Toolbar, folder list, toast, nav
utils/            config, auth, logger, test data
data/cases/       JSON case rows
data/rules/       Naming rules
tests/framework/  Framework self-checks (no ACC)
tests/conftest.py Session login + English locale
```

## Conventions

- POM only: tests call page methods, not `page.get_by_*`.
- No `time.sleep` / `wait_for_timeout`.
- Every page action is wrapped in `@step`.
- Do not commit `.env`, `auth_state.json`, `config/fernet.key`, or a plaintext password.
