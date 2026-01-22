# ═══════════════════════════════════════════════════════════════
# Subscription Products - P0
# ═══════════════════════════════════════════════════════════════
#
# 后端真理源（证据）：
# - src/Aevatar.Web/Pages/SubscriptionProducts/Index.cshtml
# - src/Aevatar.Web/Pages/SubscriptionProducts/CreateModal.cshtml.cs
#

from __future__ import annotations

import time

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.subscription_products_page import SubscriptionProductsPage
from tests.aevatar.management.subscription_products._helpers import (
    assert_not_redirected_to_login,
    click_confirm,
    wait_for_any_toast,
    wait_mutation_response,
)
from utils.config import ConfigManager
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionProducts")
@allure.story("P0")
@allure.title("test_p0_page_load_subscription_products")
def test_p0_page_load_subscription_products(auth_page: Page):
    logger = TestLogger("test_p0_page_load_subscription_products")
    logger.start()

    page = auth_page
    po = SubscriptionProductsPage(page)

    logger.step("导航到订阅商品页")
    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "subscription products page not loaded"

    po.take_screenshot("aevatar_subscription_products_p0_page_load", full_page=True)
    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionProducts")
@allure.story("P0")
@allure.title("test_p0_create_then_delete_subscription_product")
def test_p0_create_then_delete_subscription_product(auth_page: Page):
    """
    主流程：创建商品并回滚删除（保证可重复执行）。

    校验规则证据（CreateProductInput）：
    - NameKey/DescriptionKey/PlatformProductId: Required + MaxLength(256)
    - PlanType/Platform: Required
    """
    logger = TestLogger("test_p0_create_then_delete_subscription_product")
    logger.start()

    page = auth_page
    po = SubscriptionProductsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    ts = int(time.time())
    name_key = f"qa_name_{ts}"
    desc_key = f"qa_desc_{ts}"
    platform_product_id = f"qa_platform_{ts}"

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    product_id: str | None = None

    def _find_row():
        # PlatformProductId 列是 <code class="small">@product.PlatformProductId</code>
        return page.locator("tr", has=page.locator("code.small", has_text=platform_product_id)).first

    def _delete_by_id(pid: str) -> None:
        resp = page.request.delete(f"{base}/api/admin/subscription/products/{pid}")
        assert resp.status in (200, 204), f"unexpected product delete status: {resp.status}"
        page.reload(wait_until="domcontentloaded")

    try:
        logger.step("打开创建弹窗并填写表单")
        po.open_create_modal()

        # 选择下拉框：优先选第一个非空 option，避免硬编码 enum 值造成漂移
        plan_type_value = (
            page.eval_on_selector(
                po.PLAN_TYPE_SELECT,
                "el => { const opts = Array.from(el.querySelectorAll('option')); const picked = opts.find(o => (o.value||'').trim() && (o.value||'') !== '0') || opts[0]; return picked ? String(picked.value||'') : ''; }",
            )
            or "0"
        )
        platform_value = (
            page.eval_on_selector(
                po.PLATFORM_SELECT,
                "el => { const opts = Array.from(el.querySelectorAll('option')); const picked = opts.find(o => (o.value||'').trim() && (o.value||'') !== '0') || opts[0]; return picked ? String(picked.value||'') : ''; }",
            )
            or "0"
        )

        po.fill_create_form(
            name_key=name_key,
            description_key=desc_key,
            plan_type_value=str(plan_type_value),
            platform_value=str(platform_value),
            platform_product_id=platform_product_id,
            highlight_key=f"qa_highlight_{ts}",
            is_ultimate=False,
        )
        po.take_screenshot("aevatar_subscription_products_p0_before_submit", full_page=False)

        logger.step("提交创建并等待页面刷新/提示")
        po.submit_modal()
        _ = wait_mutation_response(page, timeout_ms=60000)
        wait_for_any_toast(page, timeout_ms=3000)

        # 页面通常会 reload；等待新行出现（以 NameKey 的 code 文本为证据）
        logger.step("验证创建成功（列表中出现 NameKey）")
        expect(page.locator("code", has_text=name_key)).to_be_visible(timeout=20000)
        po.take_screenshot("aevatar_subscription_products_p0_created", full_page=True)

        # 记录：创建的商品（id + platform_product_id/name_key），用于 finally 清理
        row = _find_row()
        expect(row).to_be_visible(timeout=20000)
        product_id = row.get_attribute("data-id") or row.locator(".btn-delete").first.get_attribute("data-id")
        assert product_id, "product id not found on row"
        logger.step(f"记录创建商品: id={product_id} platform_product_id={platform_product_id} name_key={name_key}")

    finally:
        # 回滚：优先用 API 删除（更稳定，避免确认弹窗在无头环境偶发不出现）
        if product_id:
            logger.step(f"清理：删除测试商品 id={product_id}")
            _delete_by_id(product_id)
            product_id = None
        # 强校验：列表中没有刚才创建的记录
        expect(page.locator("code", has_text=name_key)).to_have_count(0, timeout=20000)
        expect(page.locator("code.small", has_text=platform_product_id)).to_have_count(0, timeout=20000)
        po.take_screenshot("aevatar_subscription_products_p0_deleted", full_page=True)

    logger.end(success=True)

