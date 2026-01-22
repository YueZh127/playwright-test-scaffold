# ═══════════════════════════════════════════════════════════════
# Login - Security
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import re

import allure
import pytest
from playwright.sync_api import Page

from utils.config import ConfigManager
from utils.logger import TestLogger


@pytest.mark.P1
@pytest.mark.security
@allure.feature("Login")
@allure.story("Security")
@allure.title("test_security_unauth_access_redirects_to_login")
def test_security_unauth_access_redirects_to_login(unauth_page: Page):
    logger = TestLogger("test_security_unauth_access_redirects_to_login")
    logger.start()

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    page = unauth_page
    page.goto(f"{base}/SubscriptionProducts", wait_until="commit", timeout=60000)
    page.wait_for_url(re.compile(r".*/Account/Login.*"), timeout=60000)

    logger.end(success=True)
