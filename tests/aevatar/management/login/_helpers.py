# ═══════════════════════════════════════════════════════════════
# Helpers - Login
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

from playwright.sync_api import Page


ERROR_SELECTORS = [
    ".alert-danger",
    ".text-danger",
    ".invalid-feedback",
    ".field-validation-error",
    "[role='alert']",
]


def has_any_error_ui(page: Page) -> bool:
    for sel in ERROR_SELECTORS:
        try:
            if page.locator(sel).first.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


def assert_logged_in(page: Page) -> None:
    url = page.url or ""
    assert "/Account/Login" not in url, f"expected logged-in state, got redirected to login: {url}"


def assert_still_on_login(page: Page) -> None:
    url = page.url or ""
    assert "/Account/Login" in url, f"expected still on login page, got: {url}"
