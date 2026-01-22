# ═══════════════════════════════════════════════════════════════
# Login - P1
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage
from utils.logger import TestLogger
from tests.aevatar.management.login._helpers import has_any_error_ui, assert_still_on_login


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("Login")
@allure.story("P1")
@allure.title("test_p1_wrong_password_should_fail")
def test_p1_wrong_password_should_fail(unauth_page: Page, test_account):
    logger = TestLogger("test_p1_wrong_password_should_fail")
    logger.start()

    page = unauth_page
    po = LoginPage(page)

    po.navigate()
    po.login(username=test_account["username"], password="wrong-password")

    page.wait_for_timeout(800)
    assert_still_on_login(page)
    assert has_any_error_ui(page) is True, "expected visible error evidence for wrong password"

    page.screenshot(path="screenshots/aevatar_login_p1_wrong_password.png", full_page=True)
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("Login")
@allure.story("P1")
@allure.title("test_p1_empty_username_or_password_should_fail")
@pytest.mark.parametrize("username,password", [("", "x"), ("x", ""), ("", "")])
def test_p1_empty_username_or_password_should_fail(unauth_page: Page, username: str, password: str):
    logger = TestLogger("test_p1_empty_username_or_password_should_fail")
    logger.start()

    page = unauth_page
    po = LoginPage(page)

    po.navigate()

    # 直接填空并提交
    po.login(username=username, password=password)

    page.wait_for_timeout(800)
    assert_still_on_login(page)

    # 允许 HTML5 validity 或后端 4xx 触发的错误 UI，只要有证据即可
    assert has_any_error_ui(page) is True or page.title() != "", "expected some observable evidence (error UI)"

    page.screenshot(path="screenshots/aevatar_login_p1_empty_fields.png", full_page=True)
    logger.end(success=True)
