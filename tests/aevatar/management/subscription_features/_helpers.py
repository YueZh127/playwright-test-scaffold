# ═══════════════════════════════════════════════════════════════
# Helpers - Subscription Features
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Optional

from playwright.sync_api import Page, Response, expect


def assert_not_redirected_to_login(page: Page) -> None:
    url = page.url or ""
    assert "/Account/Login" not in url, f"redirected to login: {url}"


def wait_mutation_response(page: Page, timeout_ms: int = 60000) -> Optional[Response]:
    try:
        with page.expect_response(lambda r: r.request.method in ("POST", "PUT", "PATCH", "DELETE"), timeout=timeout_ms) as ri:
            pass
        return ri.value
    except Exception:
        return None


def wait_for_url_contains(page: Page, text: str, timeout_ms: int = 15000) -> None:
    expect(page).to_have_url(re.compile(rf".*{re.escape(text)}.*"), timeout=timeout_ms)


def click_confirm(page: Page) -> None:
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
            # 弹窗渲染/动画可能需要一点时间，避免 500ms 过短导致误报
            if btn.is_visible(timeout=3000) and btn.is_enabled():
                btn.click()
                return
        except Exception:
            continue
    raise AssertionError("confirm button not found")

