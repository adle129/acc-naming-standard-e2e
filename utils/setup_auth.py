"""Interactive headed auth bootstrap. Fallback when automated login cannot finish SSO/MFA."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils.auth import AUTH_STATE_FILE_NAME, write_storage_state  # noqa: E402
from utils.config import (  # noqa: E402
    REPO_ROOT,
    ConfigError,
    Settings,
    load_settings,
)

# CLI flag. Tests import this so they do not inline the switch name.
FLAG_HEADED = "--headed"

# Exit codes and user-facing text. Tests import these constants.
EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_USAGE = 2
MSG_NEED_HEADED = "Run with --headed so you can complete SSO or MFA in the browser."
MSG_LOGIN_PROMPT = "Complete login in the browser, including SSO or MFA, then press Enter."
MSG_SAVED = "Saved login state to {path}."

CaptureFn = Callable[[Settings, Callable[[], None]], dict]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse setup_auth CLI arguments.

    Args:
        argv: Argument list. Defaults to sys.argv[1:].

    Returns:
        Parsed namespace with headed and root.
    """
    parser = argparse.ArgumentParser(
        description="Open a headed browser so you can finish Autodesk SSO or MFA, then save auth_state.json."
    )
    parser.add_argument(
        FLAG_HEADED,
        action="store_true",
        help="Required. Opens a visible browser so you can complete login yourself.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def capture_storage_state(settings: Settings, wait_for_enter: Callable[[], None]) -> dict:
    """Open a headed browser, wait for the user to log in, then return storage_state.

    Args:
        settings: Resolved settings. Only base_url is used to open ACC.
        wait_for_enter: Blocks until the user finishes login in the browser.

    Returns:
        Playwright storage_state payload (cookies and origins).
    """
    # Import here so framework tests that stub this function never launch Playwright.
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    try:
        # The user completes SSO/MFA in this window; we do not type the password.
        page.goto(settings.base_url)
        wait_for_enter()
        return context.storage_state()
    finally:
        context.close()
        browser.close()
        playwright.stop()


def main(
    argv: list[str] | None = None,
    *,
    environ: dict[str, str] | None = None,
    capture: CaptureFn | None = None,
    wait_for_enter: Callable[[], None] | None = None,
) -> int:
    """Run the headed bootstrap CLI.

    Args:
        argv: CLI arguments, including --headed.
        environ: Optional env mapping for tests. Production reads .env.
        capture: Optional storage_state collector. Tests inject a fake.
        wait_for_enter: Optional prompt. Tests inject a no-op.

    Returns:
        EXIT_OK, EXIT_USAGE when --headed is missing, or EXIT_CONFIG on settings errors.
    """
    args = parse_args(argv)
    if not args.headed:
        print(MSG_NEED_HEADED, file=sys.stderr)
        return EXIT_USAGE

    try:
        settings = load_settings(environ=environ, root=args.root)
    except ConfigError as exc:
        # ConfigError messages are written without passwords or keys.
        print(str(exc), file=sys.stderr)
        return EXIT_CONFIG

    wait = wait_for_enter
    if wait is None:
        wait = _prompt_for_enter
    collector = capture
    if collector is None:
        collector = capture_storage_state
    payload = collector(settings, wait)
    write_storage_state(payload, root=args.root)
    print(MSG_SAVED.format(path=AUTH_STATE_FILE_NAME))
    return EXIT_OK


def _prompt_for_enter() -> None:
    """Block until the user presses Enter after finishing login in the browser."""
    input(MSG_LOGIN_PROMPT)


if __name__ == "__main__":
    raise SystemExit(main())
