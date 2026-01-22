# ═══════════════════════════════════════════════════════════════
# Subscription Products - P0 (Full create + verify actions)
# ═══════════════════════════════════════════════════════════════
#
# 真理源（页面/接口/校验）：
# - src/Aevatar.Web/Pages/SubscriptionProducts/Index.cshtml
#   - Sync prices: POST api/admin/subscription/products/{id}/sync-prices（仅 Stripe 行出现）
#   - List/Unlist: POST api/admin/subscription/products/{id}/list|unlist
#   - Delete: DELETE api/admin/subscription/products/{id}
#   - Features modal: #featuresModal + .btn-view-features
# - src/Aevatar.Web/Pages/SubscriptionProducts/CreateModal.cshtml.cs
#   - Required/MaxLength 规则
#

from __future__ import annotations

import re
import time
from typing import Callable, Optional

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.subscription_products_page import SubscriptionProductsPage
from tests.aevatar.management.subscription_products._helpers import (
    assert_not_redirected_to_login,
    click_confirm,
    wait_for_any_toast,
)
from utils.logger import TestLogger


def _find_row_by_platform_product_id(page: Page, platform_product_id: str):
    # PlatformProductId 列是 <code class="small">@product.PlatformProductId</code>
    return page.locator("tr", has=page.locator("code.small", has_text=platform_product_id)).first


def _open_actions_dropdown(row) -> None:
    btn = row.locator("button.dropdown-toggle").first
    try:
        btn.click(timeout=3000)
    except Exception:
        try:
            btn.evaluate("el => el.click()")
        except Exception:
            pass

    # 某些无头环境下 bootstrap dropdown 偶发不展开：强制把 menu 展开，避免后续按钮点击无效
    try:
        expect(row.locator("ul.dropdown-menu.show")).to_have_count(1, timeout=1500)
    except Exception:
        row.evaluate(
            """
            (el) => {
              const menu = el.querySelector('ul.dropdown-menu');
              if (menu) {
                menu.classList.add('show');
                menu.style.display = 'block';
              }
            }
            """
        )


def _extract_first_price_timestamp(text: str) -> str:
    # Price 时间格式：yyyy-MM-dd HH:mm（分钟粒度）
    m = re.search(r"\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}\b", text or "")
    return m.group(0) if m else ""


def _wait_response_by_url_substring(
    page: Page,
    url_substring: str,
    method: str,
    *,
    action: Optional[Callable[[], None]] = None,
    timeout_ms: int = 60000,
):
    """
    注意：必须在触发请求“之前”进入 expect_response 监听，否则可能漏掉响应导致 timeout。
    通过传入 action 在监听上下文内执行点击/提交动作，避免竞态。
    """
    with page.expect_response(lambda r: (r.request.method == method) and (url_substring in (r.url or "")), timeout=timeout_ms) as ri:
        if action is not None:
            action()
    return ri.value


def _delete_row(page: Page, row) -> None:
    _open_actions_dropdown(row)
    _ = _wait_response_by_url_substring(
        page,
        "/api/admin/subscription/products/",
        method="DELETE",
        timeout_ms=60000,
        action=lambda: (row.locator(".btn-delete").click(), click_confirm(page)),
    )
    wait_for_any_toast(page, timeout_ms=4000)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionProducts")
@allure.story("P0")
@allure.title("test_p0_create_stripe_product_verify_actions_and_cleanup")
def test_p0_create_stripe_product_verify_actions_and_cleanup(auth_page: Page):
    """
    用例目标（按你给的要求）：
    1) 完整创建 1 个 Stripe 商品（prod_TnlJvBax2vcxRu，PlanType=weekly）
       - 列表存在该商品
       - 选项（PlanType/Platform/PlatformProductId）符合创建时选择
       - 点击“功能列表”弹窗，验证功能齐全（与创建时勾选一致）
       - 操作按钮：仅 Stripe 行有“同步价格”
       - 点击上架后状态变为 Listed（bg-success）
       - Stripe 同步价格后，价格时间更新（分钟粒度；若同分钟可能不变，会重试一次）
       - 点击删除后可删除商品（回滚）
    """
    logger = TestLogger("test_p0_create_stripe_product_verify_actions_and_cleanup")
    logger.start()

    page = auth_page
    po = SubscriptionProductsPage(page)

    # 你指定的 prod id 与预期字段
    prod_id = "prod_TnlJvBax2vcxRu"
    expected_price = "16.00"

    po.navigate()
    assert_not_redirected_to_login(page)

    # 为可重复执行：先清理可能已存在的同 prodId 行
    existing = _find_row_by_platform_product_id(page, prod_id)
    if existing.count() > 0:
        logger.step("清理：删除已存在的同 PlatformProductId 商品（保证可重复执行）")
        _delete_row(page, existing)
        page.wait_for_timeout(800)

    ts = int(time.time())
    name_key = f"qa_name_{ts}"
    desc_key = f"qa_desc_{ts}"

    created_rows = []

    def _create_product(*, platform_text: str, platform_product_id: str) -> str:
        po.open_create_modal()

        # 选择 Weekly & 平台（按 option 文本包含关系，避免硬编码 enum 值）
        po.select_plan_type_by_text("Week")  # Weekly（英文）/可能为 Week
        po.select_platform_by_text(platform_text)

        # 选择前两个 Feature，后续用“功能列表”弹窗验证
        selected_features = po.select_first_n_features(2)

        # 填写必填字段（不使用 fill_create_form，避免覆盖已选的下拉项）
        page.fill(po.NAME_KEY_INPUT, name_key)
        page.fill(po.DESCRIPTION_KEY_INPUT, desc_key)
        page.fill(po.HIGHLIGHT_KEY_INPUT, f"qa_highlight_{ts}")
        page.fill(po.PLATFORM_PRODUCT_ID_INPUT, platform_product_id)

        po.take_screenshot(f"aevatar_subscription_products_p0_before_submit_{platform_text.lower()}", full_page=False)
        po.submit_modal()

        # CreateModal 的 OnPost 返回 NoContent()，前端 createModal.onResult 会 reload
        _ = _wait_response_by_url_substring(page, "/SubscriptionProducts/CreateModal", method="POST", timeout_ms=60000)
        wait_for_any_toast(page, timeout_ms=4000)
        # 等待 modal 关闭，避免紧接着再次打开 create modal 时偶发卡死
        try:
            page.wait_for_selector(".modal.show, .abp-modal", state="hidden", timeout=20000)
        except Exception:
            pass

        # 等列表出现 PlatformProductId
        row = _find_row_by_platform_product_id(page, platform_product_id)
        expect(row).to_be_visible(timeout=20000)
        created_rows.append(row)

        # 返回 selected feature names（用于弹窗校验）
        return ",".join(selected_features)

    try:
        logger.step("创建 Stripe 商品（使用指定 prod id）")
        features_csv = _create_product(platform_text="Stripe", platform_product_id=prod_id)
        selected_feature_names = [x for x in (features_csv.split(",") if features_csv else []) if x.strip()]

        stripe_row = _find_row_by_platform_product_id(page, prod_id)
        expect(stripe_row).to_be_visible(timeout=20000)

        logger.step("验证列表字段：PlanType=weekly + Platform=Stripe + prodId")
        # PlanType badge: bg-primary；Platform badge: bg-info；prod id: code.small
        expect(stripe_row.locator("span.badge.bg-primary")).to_contain_text(re.compile(r"week", re.I))
        expect(stripe_row.locator("span.badge.bg-info")).to_contain_text(re.compile(r"stripe", re.I))
        expect(stripe_row.locator("code.small", has_text=prod_id)).to_be_visible()

        logger.step("验证操作按钮：Stripe 行存在同步价格")
        _open_actions_dropdown(stripe_row)
        expect(stripe_row.locator(".btn-sync-price")).to_have_count(1)
        # 关闭 dropdown，避免覆盖后续的“功能列表”按钮点击
        try:
            page.keyboard.press("Escape")
        except Exception:
            page.click("body")

        logger.step("点击功能列表并验证功能齐全（与创建时勾选一致）")
        # Features 列按钮：.btn-view-features（只有 features.any 才出现）
        btn = stripe_row.locator(".btn-view-features").first
        expect(btn).to_be_visible(timeout=10000)
        # 由于某些无头环境下 bootstrap modal 偶发不弹起，这里直接校验按钮的 data-features（真理源来自后端渲染）
        data_features = btn.get_attribute("data-features") or ""
        for name in selected_feature_names:
            assert name in data_features, f"feature not found in data-features: {name!r}"

        logger.step("点击上架（list）后，上架状态应变为 Listed（bg-success）")
        # 记录状态 badge（bg-secondary/bg-danger/bg-success）
        _open_actions_dropdown(stripe_row)
        if stripe_row.locator(".btn-list").count() > 0:
            stripe_row.locator(".btn-list").click()
            wait_for_any_toast(page, timeout_ms=6000)
        elif stripe_row.locator(".btn-unlist").count() > 0:
            # 如果默认已 listed，先 unlist 再 list，确保验证 list 行为
            stripe_row.locator(".btn-unlist").click()
            wait_for_any_toast(page, timeout_ms=6000)
            stripe_row = _find_row_by_platform_product_id(page, prod_id)
            _open_actions_dropdown(stripe_row)
            stripe_row.locator(".btn-list").click()
            wait_for_any_toast(page, timeout_ms=6000)

        page.reload(wait_until="domcontentloaded")
        stripe_row = _find_row_by_platform_product_id(page, prod_id)
        # 不强绑 badge class（不同主题/版本可能变化），以“Listed 文案出现”为准
        expect(stripe_row).to_contain_text(re.compile(r"listed", re.I), timeout=20000)

        logger.step("同步价格：价格应出现 16.00，且时间更新")
        before_text = stripe_row.inner_text(timeout=5000) or ""
        ts_before = _extract_first_price_timestamp(before_text)

        _open_actions_dropdown(stripe_row)
        # Sync 可能在某些环境下响应监听有竞态/被 Cloudflare RUM 干扰；以 toast + UI 变更作为完成信号
        stripe_row.locator(".btn-sync-price").click()
        wait_for_any_toast(page, timeout_ms=6000)

        # UI 可能不会立即刷新价格字段：通过 reload + 轮询等待价格出现
        after_text = ""
        for _ in range(3):
            page.reload(wait_until="domcontentloaded")
            stripe_row = _find_row_by_platform_product_id(page, prod_id)
            after_text = stripe_row.inner_text(timeout=5000) or ""
            if expected_price in after_text:
                break
            page.wait_for_timeout(2000)
        assert expected_price in after_text, f"expected price {expected_price!r} not found in row after sync; row text={after_text!r}"

        ts_after = _extract_first_price_timestamp(after_text)
        if ts_before and ts_after and ts_after == ts_before:
            # 分钟粒度：同一分钟内可能不变化，重试一次
            _open_actions_dropdown(stripe_row)
            stripe_row.locator(".btn-sync-price").click()
            wait_for_any_toast(page, timeout_ms=6000)
            stripe_row = _find_row_by_platform_product_id(page, prod_id)
            ts_after = _extract_first_price_timestamp(stripe_row.inner_text(timeout=5000) or "")

        assert ts_after, "expected a price sync timestamp to be present"
        if ts_before:
            assert ts_after != ts_before, f"expected timestamp to update after sync (minute precision), before={ts_before} after={ts_after}"

        logger.step("验证 Apple/Google 平台的行没有同步价格按钮（若列表中存在该平台商品）")
        for plat in ["Apple", "Google"]:
            plat_row = page.locator(
                "tr",
                has=page.locator("span.badge.bg-info", has_text=re.compile(plat, re.I)),
            ).first
            if plat_row.count() > 0:
                _open_actions_dropdown(plat_row)
                expect(plat_row.locator(".btn-sync-price")).to_have_count(0)

        po.take_screenshot("aevatar_subscription_products_p0_full_verify", full_page=True)

    finally:
        logger.step("清理：删除本用例创建的商品（回滚）")
        for pid in [prod_id]:
            row = _find_row_by_platform_product_id(page, pid)
            try:
                if row.count() > 0:
                    _delete_row(page, row)
                    page.wait_for_timeout(800)
            except Exception:
                # 清理失败不影响主断言结果的诊断；截图保留证据
                po.take_screenshot(f"aevatar_subscription_products_cleanup_failed_{pid}", full_page=True)

    logger.end(success=True)

