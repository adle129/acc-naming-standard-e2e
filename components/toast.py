"""Success/error toast. Tests call expect() on message()."""

from __future__ import annotations

from playwright.sync_api import Locator

from pages.base_page import BasePage

# Exact toast text from the product UI. Change here if ACC wording changes.
TOAST_UPLOADED = "1 file has been successfully uploaded"
TOAST_DELETED = "1 file was deleted"
TOAST_RESTORED = "1 file successfully restored"
WHAT_TOAST = "toast {text}"


class Toast(BasePage):
    """Transient banner after upload, delete, or restore."""

    def message(self, text: str) -> Locator:
        """Return the toast that shows the given text.

        Args:
            text: Exact toast string, usually TOAST_UPLOADED / TOAST_DELETED / TOAST_RESTORED.

        Returns:
            Playwright locator. Tests call expect() on this.
        """
        return self.page.get_by_text(text)

    def verify(self, text: str) -> None:
        """Prove a toast with this text is visible. Tests call this instead of expect().

        Args:
            text: Exact toast string, usually TOAST_UPLOADED / TOAST_DELETED / TOAST_RESTORED.
        """
        self.verify_visible(self.message(text), WHAT_TOAST.format(text=text))
