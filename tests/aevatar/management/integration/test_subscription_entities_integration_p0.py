# ═══════════════════════════════════════════════════════════════
# Integration - Subscription Feature/Label/Product (P0)
# ═══════════════════════════════════════════════════════════════
#
# 用例目标（联合测试）：
# 1. 创建特性 1 个 + 标签 1 个
# 2. 创建商品，关联特性和标签，勾选旗舰版；验证创建后商品符合预期（旗舰版、特性、标签齐全）
# 3. 删除创建的特性和标签
# 4. 删除特性/标签后，在商品页面验证商品中的特性/标签已消失
# 5. 删除商品（回滚）
#

from __future__ import annotations

import re
import time

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.subscription_features_page import SubscriptionFeaturesPage
from pages.subscription_labels_page import SubscriptionLabelsPage
from pages.subscription_products_page import SubscriptionProductsPage
from utils.config import ConfigManager
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.functional
@pytest.mark.integration
@allure.feature("Integration")
@allure.story("SubscriptionManagement")
@allure.title("test_p0_feature_label_product_link_and_cascade_verify")
def test_p0_feature_label_product_link_and_cascade_verify(auth_page: Page):
    logger = TestLogger("test_p0_feature_label_product_link_and_cascade_verify")
    logger.start()

    page = auth_page
    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    ts = int(time.time())
    feature_name_key = f"qa_feature_integration_{ts}"
    feature_desc_key = f"qa_desc_integration_{ts}"
    label_key = f"qa_label_integration_{ts}"
    prod_platform_product_id = f"qa_prod_integration_{ts}"
    prod_name_key = f"qa_prod_name_{ts}"
    prod_desc_key = f"qa_prod_desc_{ts}"

    feature_id: str | None = None
    label_id: str | None = None
    product_id: str | None = None

    def _delete_feature_by_id(fid: str) -> None:
        resp = page.request.delete(f"{base}/api/admin/subscription/features/{fid}")
        assert resp.status in (200, 204), f"unexpected feature delete status: {resp.status}"

    def _delete_label_by_id(lid: str) -> None:
        resp = page.request.delete(f"{base}/api/admin/subscription/labels/{lid}")
        assert resp.status in (200, 204), f"unexpected label delete status: {resp.status}"

    def _delete_product_by_id(pid: str) -> None:
        resp = page.request.delete(f"{base}/api/admin/subscription/products/{pid}")
        assert resp.status in (200, 204), f"unexpected product delete status: {resp.status}"

    try:
        # ───────────────────────────────────────────────────────────
        # 1) Create Feature
        # ───────────────────────────────────────────────────────────
        logger.step("创建 Feature 1 个")
        fpo = SubscriptionFeaturesPage(page)
        fpo.navigate()

        fpo.open_create_modal()
        type_value = (
            page.eval_on_selector(
                fpo.TYPE_SELECT,
                "el => { const opts = Array.from(el.querySelectorAll('option')); const picked = opts.find(o => (o.value||'').trim() && (o.value||'') !== 'None') || opts[0]; return picked ? String(picked.value||'') : ''; }",
            )
            or "Core"
        )
        fpo.fill_create_form(name_key=feature_name_key, type_value=str(type_value), display_order=0, description_key=feature_desc_key)
        fpo.submit_modal()
        page.wait_for_timeout(800)
        expect(page.locator("code", has_text=feature_name_key)).to_be_visible(timeout=20000)

        feature_row = page.locator("tr", has=page.locator("code", has_text=feature_name_key)).first
        feature_id = feature_row.get_attribute("data-id")
        assert feature_id, "feature id not found on row"

        # ───────────────────────────────────────────────────────────
        # 2) Create Label
        # ───────────────────────────────────────────────────────────
        logger.step("创建 Label 1 个")
        lpo = SubscriptionLabelsPage(page)
        lpo.navigate()

        lpo.open_create_modal()
        lpo.fill_create_form(key=label_key)
        lpo.submit_modal()
        page.wait_for_timeout(800)
        expect(page.locator("code", has_text=label_key)).to_be_visible(timeout=20000)

        label_row = page.locator("tr", has=page.locator("code", has_text=label_key)).first
        label_id = label_row.locator("a.btn-delete").first.get_attribute("data-id")
        assert label_id, "label id not found on delete link"

        # ───────────────────────────────────────────────────────────
        # 3) Create Product linked to Feature + Label + Ultimate
        # ───────────────────────────────────────────────────────────
        logger.step("创建 Product：关联 Feature+Label，勾选旗舰版")
        ppo = SubscriptionProductsPage(page)
        ppo.navigate()

        ppo.open_create_modal()
        # plan type: prefer Week
        ppo.select_plan_type_by_text("Week")
        ppo.select_platform_by_text("Stripe")

        # associate feature + label
        picked_features = ppo.select_features_by_name_contains([feature_name_key])
        assert picked_features and picked_features[0] in feature_name_key or feature_name_key in picked_features[0], "failed to pick the created feature"
        _ = ppo.select_label_by_text_contains(label_key)

        page.fill(ppo.NAME_KEY_INPUT, prod_name_key)
        page.fill(ppo.DESCRIPTION_KEY_INPUT, prod_desc_key)
        page.fill(ppo.PLATFORM_PRODUCT_ID_INPUT, prod_platform_product_id)
        page.check(ppo.IS_ULTIMATE_CHECKBOX)

        ppo.take_screenshot("aevatar_integration_product_before_submit", full_page=False)
        ppo.submit_modal()
        # wait for create modal POST to occur
        try:
            with page.expect_response(lambda r: (r.request.method == "POST") and ("/SubscriptionProducts/CreateModal" in (r.url or "")), timeout=60000):
                pass
        except Exception:
            pass

        product_row = page.locator("tr", has=page.locator("code.small", has_text=prod_platform_product_id)).first
        expect(product_row).to_be_visible(timeout=20000)

        product_id = product_row.get_attribute("data-id")
        if not product_id:
            # fallback: use delete link data-id
            product_id = product_row.locator(".btn-delete").first.get_attribute("data-id")
        assert product_id, "product id not found on row"

        # Verify product expectations
        logger.step("验证 Product：旗舰版/特性/标签")
        # Ultimate: avoid hard binding exact badge class; require text hint
        expect(product_row).to_contain_text(re.compile(r"ultimate|旗舰", re.I))
        # Feature: button includes data-features JSON; assert contains created feature name_key
        features_btn = product_row.locator(".btn-view-features").first
        expect(features_btn).to_be_visible(timeout=10000)
        data_features = features_btn.get_attribute("data-features") or ""
        assert feature_name_key in data_features, "created feature not present in product data-features"
        # Label: row text should include label key
        assert label_key in (product_row.inner_text(timeout=5000) or ""), "created label not present in product row"

        # ───────────────────────────────────────────────────────────
        # 4) Delete Feature+Label, then verify product linkage removed
        # ───────────────────────────────────────────────────────────
        logger.step("删除 Feature + Label")
        _delete_feature_by_id(feature_id)
        feature_id = None
        _delete_label_by_id(label_id)
        label_id = None

        logger.step("回到商品页验证：Feature/Label 关联已消失")
        ppo.navigate()

        # poll reload a few times for eventual consistency
        for _ in range(3):
            product_row = page.locator("tr", has=page.locator("code.small", has_text=prod_platform_product_id)).first
            if product_row.count() == 0:
                break
            features_btn = product_row.locator(".btn-view-features").first
            data_features = (features_btn.get_attribute("data-features") or "") if features_btn.count() > 0 else ""
            row_text = product_row.inner_text(timeout=3000) or ""
            if (feature_name_key not in data_features) and (label_key not in row_text):
                break
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        # Final assertions
        product_row = page.locator("tr", has=page.locator("code.small", has_text=prod_platform_product_id)).first
        expect(product_row).to_be_visible(timeout=20000)
        features_btn = product_row.locator(".btn-view-features").first
        data_features = (features_btn.get_attribute("data-features") or "") if features_btn.count() > 0 else ""
        assert feature_name_key not in data_features, "feature still linked after feature deletion"
        assert label_key not in (product_row.inner_text(timeout=5000) or ""), "label still linked after label deletion"

        # ───────────────────────────────────────────────────────────
        # 5) Delete Product
        # ───────────────────────────────────────────────────────────
        logger.step("删除 Product 回滚")
        _delete_product_by_id(product_id)
        product_id = None
        page.reload(wait_until="domcontentloaded")
        expect(page.locator("code.small", has_text=prod_platform_product_id)).to_have_count(0, timeout=20000)

        logger.end(success=True)

    finally:
        # Best-effort cleanup (do not raise)
        try:
            if product_id:
                _delete_product_by_id(product_id)
        except Exception:
            pass
        try:
            if label_id:
                _delete_label_by_id(label_id)
        except Exception:
            pass
        try:
            if feature_id:
                _delete_feature_by_id(feature_id)
        except Exception:
            pass

