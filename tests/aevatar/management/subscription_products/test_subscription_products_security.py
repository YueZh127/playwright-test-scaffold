# ═══════════════════════════════════════════════════════════════
# Subscription Products - Security
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
@allure.feature("SubscriptionProducts")
@allure.story("Security")
@allure.title("test_security_unauth_redirects_to_login_subscription_products")
def test_security_unauth_redirects_to_login_subscription_products(unauth_page: Page):
    logger = TestLogger("test_security_unauth_redirects_to_login_subscription_products")
    logger.start()

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")
    url = f"{base}/SubscriptionProducts"

    page = unauth_page
    page.goto(url, wait_until="commit", timeout=60000)
    page.wait_for_url(re.compile(r".*/Account/Login.*"), timeout=60000)

    logger.end(success=True)

