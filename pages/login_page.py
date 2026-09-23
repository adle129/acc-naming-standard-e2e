"""Autodesk login form. The session fixture will call login(); tests do not."""

from __future__ import annotations

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.logger import step

# Email/password use input types so labels can stay English in the product UI.
EMAIL_INPUT_SELECTOR = "input[type='email']"
PASSWORD_INPUT_SELECTOR = "input[type='password']"
SUBMIT_BUTTON_SELECTOR = "button[type='submit']"
TEXTBOX_ROLE = "textbox"
BUTTON_ROLE = "button"
YES_BUTTON_NAME = "Yes"
# After Sign in, Autodesk leaves the identity host.
SIGNIN_HOST = "signin.autodesk.com"
# Short wait: stay-signed-in is optional and must not block a fast redirect.
STAY_SIGNED_IN_TIMEOUT_MS = 10000
# Arkose / email verify stays on signin; a headed run must finish it by hand.
CHALLENGE_TIMEOUT_MS = 180000

STEP_FILL_USERNAME = "fill username {username}"
STEP_FILL_PASSWORD = "fill password {password}"
STEP_SUBMIT_LOGIN = "submit login"
STEP_CLICK_NEXT = "click Next"
STEP_WAIT_SIGNED_IN = "wait for Autodesk redirect (complete any on-screen challenge)"
STEP_LOGIN = "login as {username} password={password}"


class LoginPage(BasePage):
    """Sign-in page. Password arguments are redacted by @step."""

    def username_box(self) -> Locator:
        """Return the email field (English or Chinese Autodesk ID).

        Returns:
            Playwright locator.
        """
        email = self.page.locator(EMAIL_INPUT_SELECTOR)
        # Autodesk sometimes uses type=text; the first textbox is the email field.
        if email.count() > 0:
            return email.first
        return self.page.get_by_role(TEXTBOX_ROLE).first

    def password_box(self) -> Locator:
        """Return the password field.

        Returns:
            Playwright locator.
        """
        return self.page.locator(PASSWORD_INPUT_SELECTOR)

    def validate_login_page(self) -> None:
        """Prove the Autodesk sign-in form is on screen (email field)."""
        self.verify_visible(self.username_box())

    def submit_button(self) -> Locator:
        """Return the Sign in control.

        Returns:
            Playwright locator.
        """
        return self.page.locator(SUBMIT_BUTTON_SELECTOR).last

    @step(STEP_FILL_USERNAME)
    def fill_username(self, username: str) -> None:
        """Type the account email.

        Args:
            username: ACC username from settings.
        """
        self.username_box().fill(username)

    @step(STEP_FILL_PASSWORD)
    def fill_password(self, password: str) -> None:
        """Type the password. The step log must show *** not the value.

        Args:
            password: Plaintext password from settings. Never print it.
        """
        self.password_box().fill(password)

    def next_button(self) -> Locator:
        """Return the Next control on the email-only Autodesk screen.

        Returns:
            Playwright locator.
        """
        return self.page.locator(SUBMIT_BUTTON_SELECTOR).last

    @step(STEP_CLICK_NEXT)
    def click_next(self) -> None:
        """Click Next after the email, when Autodesk splits the form."""
        self.next_button().click()

    @step(STEP_SUBMIT_LOGIN)
    def click_sign_in(self) -> None:
        """Click Sign in."""
        self.submit_button().click()

    @step(STEP_SUBMIT_LOGIN)
    def submit(self) -> None:
        """Click Sign in."""
        self.click_sign_in()

    @step(STEP_LOGIN)
    def login(self, username: str, password: str) -> None:
        """Fill both fields and submit. SSO/MFA after this is out of scope.

        Args:
            username: ACC username from settings.
            password: Plaintext password from settings.
        """
        self.fill_username(username)
        # Autodesk ID is email first, then Next, then password.
        self.click_next()
        self.fill_password(password)
        self.click_sign_in()
        self._confirm_stay_signed_in()
        self._wait_until_signed_in()

    @step(STEP_WAIT_SIGNED_IN)
    def _wait_until_signed_in(self) -> None:
        """Wait until Autodesk leaves sign-in. Complete Arkose in the headed window."""
        self.page.wait_for_url(_url_left_signin, timeout=CHALLENGE_TIMEOUT_MS)

    def _confirm_stay_signed_in(self) -> None:
        """Click Yes when Autodesk asks to stay signed in on the same host."""
        yes = self.page.get_by_role(BUTTON_ROLE, name=YES_BUTTON_NAME)
        try:
            yes.click(timeout=STAY_SIGNED_IN_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # No stay-signed-in prompt; login may already be redirecting.
            return


def _url_left_signin(url: str) -> bool:
    """Return True when the browser has left Autodesk's identity host.

    Args:
        url: Current page URL from Playwright.

    Returns:
        True when the URL is no longer signin.autodesk.com.
    """
    return SIGNIN_HOST not in url
