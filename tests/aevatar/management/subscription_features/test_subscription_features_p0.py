# ═══════════════════════════════════════════════════════════════
# Subscription Features - P0
# ═══════════════════════════════════════════════════════════════
#
# 后端真理源（证据）：
# - src/Aevatar.Web/Pages/SubscriptionFeatures/Index.cshtml
# - src/Aevatar.Web/Pages/SubscriptionFeatures/CreateModal.cshtml.cs
#

from __future__ import annotations

import time

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.subscription_features_page import SubscriptionFeaturesPage
from tests.aevatar.management.subscription_features._helpers import (
    assert_not_redirected_to_login,
    wait_mutation_response,
)
from utils.config import ConfigManager
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionFeatures")
@allure.story("P0")
@allure.title("test_p0_page_load_subscription_features")
def test_p0_page_load_subscription_features(auth_page: Page):
    logger = TestLogger("test_p0_page_load_subscription_features")
    logger.start()

    page = auth_page
    po = SubscriptionFeaturesPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "subscription features page not loaded"
    po.take_screenshot("aevatar_subscription_features_p0_page_load", full_page=True)

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionFeatures")
@allure.story("P0")
@allure.title("test_p0_create_then_delete_subscription_feature")
def test_p0_create_then_delete_subscription_feature(auth_page: Page):
    """
    主流程：创建功能特性并回滚删除。

    校验规则证据（CreateFeatureInput）：
    - NameKey: [Required][MaxLength(256)]
    - Type: [Required]
    - DescriptionKey: [MaxLength(256)]
    """
    logger = TestLogger("test_p0_create_then_delete_subscription_feature")
    logger.start()

    page = auth_page
    po = SubscriptionFeaturesPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    # 固定 NameKey：便于重复执行与稳定回滚验证
    name_key = "qa_feature_p0_fixed"
    desc_key = "qa_desc_p0_fixed"

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    def find_row_by_name_key():
        # NameKey 在列表中以 <code> 展示；用 has 精确定位，避免误匹配其它列文案
        return page.locator("tr", has=page.locator("code", has_text=name_key)).first

    def delete_by_name_key_if_exists() -> None:
        """
        按 NameKey 找到对应行并删除：
        - 从 row[data-id] 取 feature id
        - 调用同源 API DELETE /api/admin/subscription/features/{id}
        - reload 并确认列表中不再出现该 NameKey
        """
        row = find_row_by_name_key()
        if row.count() == 0:
            return

        fid = row.get_attribute("data-id")
        assert fid, "feature id not found on row"

        resp_del = page.request.delete(f"{base}/api/admin/subscription/features/{fid}")
        assert resp_del.status in (200, 204), f"unexpected delete status: {resp_del.status}"

        # 页面数据可能需要刷新才能反映删除结果
        page.reload(wait_until="domcontentloaded")
        expect(page.locator("code", has_text=name_key)).to_have_count(0, timeout=20000)

    # 先清理：保证固定 NameKey 不会撞到历史脏数据
    delete_by_name_key_if_exists()

    fid_created: str | None = None
    try:
        po.open_create_modal()

        # Type options 在 cshtml.cs 中是字符串（Core/Advanced）；选择第一个“有效”选项（跳过 None）
        type_value = (
            page.eval_on_selector(
                po.TYPE_SELECT,
                "el => { const opts = Array.from(el.querySelectorAll('option')); const picked = opts.find(o => (o.value||'').trim() && (o.value||'') !== 'None') || opts[0]; return picked ? String(picked.value||'') : ''; }",
            )
            or "Core"
        )
        po.fill_create_form(name_key=name_key, type_value=str(type_value), display_order=0, description_key=desc_key)
        po.take_screenshot("aevatar_subscription_features_p0_before_submit", full_page=False)

        # 提交创建：显式等待 CreateModal 的 POST 响应（避免“提交没发生/权限不足/被拦截”却继续断言）
        with page.expect_response(lambda r: (r.request.method == "POST") and ("/SubscriptionFeatures/CreateModal" in (r.url or "")), timeout=60000) as ri:
            po.submit_modal()
        resp = ri.value
        assert resp is not None and resp.status < 400, f"unexpected create response status: {getattr(resp, 'status', None)} url={getattr(resp, 'url', None)}"

        # ABP modal 成功后通常会触发 reload
        try:
            page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:
            pass

        # 记录：创建的 Feature（id + NameKey），用于 finally 清理
        row = find_row_by_name_key()
        expect(row).to_be_visible(timeout=20000)
        fid_created = row.get_attribute("data-id")
        assert fid_created, "feature id not found on row"
        logger.step(f"记录创建特性: id={fid_created} name_key={name_key}")

        # 验证创建：列表出现 NameKey code
        expect(page.locator("code", has_text=name_key)).to_be_visible(timeout=20000)
        po.take_screenshot("aevatar_subscription_features_p0_created", full_page=True)

    finally:
        # 删除回滚（失败也要清理）
        if fid_created:
            logger.step(f"清理：删除测试特性 id={fid_created}")
        delete_by_name_key_if_exists()
        expect(page.locator("code", has_text=name_key)).to_have_count(0, timeout=20000)
        po.take_screenshot("aevatar_subscription_features_p0_deleted", full_page=True)

    logger.end(success=True)

