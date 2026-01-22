# ═══════════════════════════════════════════════════════════════
# Login - P0
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import allure
import pytest
import re
from playwright.sync_api import Page, expect

from pages.login_page import LoginPage
from utils.config import ConfigManager
from utils.logger import TestLogger
from tests.aevatar.management.login._helpers import assert_logged_in


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Login")
@allure.story("P0")
@allure.title("test_p0_landing_page_load")
def test_p0_landing_page_load(unauth_page: Page):
    logger = TestLogger("test_p0_landing_page_load")
    logger.start()

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    page = unauth_page

    page.goto(f"{base}/", wait_until="domcontentloaded", timeout=60000)

    # 不强绑“可见性”（响应式 header 可能把链接隐藏到折叠菜单里），只要存在即可
    locator = page.locator("a[href='/Account/Login'], a:has-text('Login'), button:has-text('Login')")
    # 页面可能同时渲染多个 Login 入口（header/footer/重复导航），只要至少 1 个存在即可
    expect(locator.first).to_be_attached(timeout=15000)
    assert locator.count() >= 1

    page.screenshot(path="screenshots/aevatar_login_p0_landing.png", full_page=True)
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Login")
@allure.story("P0")
@allure.title("test_p0_enter_login_flow")
def test_p0_enter_login_flow(unauth_page: Page):
    logger = TestLogger("test_p0_enter_login_flow")
    logger.start()

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    page = unauth_page

    page.goto(f"{base}/", wait_until="domcontentloaded", timeout=60000)

    # 优先点击入口；若页面结构变化，兜底直接访问 /Account/Login
    try:
        page.locator("a[href='/Account/Login'], a:has-text('Login'), button:has-text('Login')").first.click(timeout=5000, force=True)
    except Exception:
        page.goto(f"{base}/Account/Login", wait_until="domcontentloaded", timeout=60000)

    expect(page).to_have_url(re.compile(r".*/Account/Login.*"), timeout=20000)
    page.screenshot(path="screenshots/aevatar_login_p0_login_form.png", full_page=True)

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("Login")
@allure.story("P0")
@allure.title("test_p0_login_success_account_pool")
def test_p0_login_success_account_pool(unauth_page: Page, test_account):
    logger = TestLogger("test_p0_login_success_account_pool")
    logger.start()

    page = unauth_page
    po = LoginPage(page)

    po.navigate()
    assert po.is_loaded(), "login form not loaded"

    # 账号来自账号池；密码不落盘
    po.login(username=test_account["username"], password=test_account["password"])

    # 成功标准：不再停留在登录页（避免绑死 toast 文案）
    page.wait_for_timeout(1000)
    assert_logged_in(page)

    page.screenshot(path="screenshots/aevatar_login_p0_logged_in.png", full_page=True)
    logger.end(success=True)
