# ═══════════════════════════════════════════════════════════════
# Helpers - Subscription Products
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Optional

from playwright.sync_api import Page, expect, Response


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/Account/Login" not in url, f"redirected to login: {url}"


def wait_for_any_toast(page: Page, timeout_ms: int = 4000) -> None:
    # ABP 通知可能来自不同组件（toast/alert），这里用宽松集合兜底
    candidates = [
        ".abp-notification",
        ".toast",
        ".Toastify__toast",
        "[role='alert']",
        ".alert",
    ]
    for sel in candidates:
        try:
            if page.locator(sel).first.is_visible(timeout=timeout_ms):
                return
        except Exception:
            continue


def click_confirm(page: Page) -> None:
    """
    删除确认弹窗：尽量兼容 ABP/Bootstrap/SweetAlert2。
    不硬绑文案，按常见 confirm 按钮 class + 文案兜底。
    """
    selectors = [
        "button.swal2-confirm",
        "button:has-text('Yes')",
        "button:has-text('OK')",
        "button:has-text('Confirm')",
        "button:has-text('确定')",
        "button:has-text('确认')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=500) and btn.is_enabled():
                btn.click()
                return
        except Exception:
            continue
    raise AssertionError("confirm button not found")


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    try:
        with page.expect_response(lambda r: r.request.method in ("POST", "PUT", "PATCH", "DELETE"), timeout=timeout_ms) as ri:
            pass
        return ri.value
    except Exception:
        return None


def wait_for_url_contains(page: Page, text: str, timeout_ms: int = 15000) -> None:
    expect(page).to_have_url(re.compile(rf".*{re.escape(text)}.*"), timeout=timeout_ms)

