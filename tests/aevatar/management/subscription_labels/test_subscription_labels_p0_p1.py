# ═══════════════════════════════════════════════════════════════
# Subscription Labels - P0/P1
# ═══════════════════════════════════════════════════════════════
#
# 后端真理源（字段校验）：
# - src/Aevatar.Web/Pages/SubscriptionLabels/CreateModal.cshtml.cs
#   - Key: [Required][MaxLength(128)]
#   - Key: [RegularExpression(@"^[a-z][a-z0-9_]*$")]
#

from __future__ import annotations

import time

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.subscription_labels_page import SubscriptionLabelsPage
from tests.aevatar.management.subscription_labels._helpers import (
    assert_not_redirected_to_login,
    click_confirm,
    has_validation_evidence,
    wait_mutation_response,
)
from utils.config import ConfigManager
from utils.logger import TestLogger


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionLabels")
@allure.story("P0")
@allure.title("test_p0_page_load_subscription_labels")
def test_p0_page_load_subscription_labels(auth_page: Page):
    logger = TestLogger("test_p0_page_load_subscription_labels")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)
    assert po.is_loaded(), "subscription labels page not loaded"
    po.take_screenshot("aevatar_subscription_labels_p0_page_load", full_page=True)

    logger.end(success=True)


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("SubscriptionLabels")
@allure.story("P0")
@allure.title("test_p0_create_then_delete_subscription_label")
def test_p0_create_then_delete_subscription_label(auth_page: Page):
    logger = TestLogger("test_p0_create_then_delete_subscription_label")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    # 固定 Key：便于重复执行与稳定回滚验证
    key = "qa_label_p0_fixed"

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    def find_row_by_key():
        # Key 在列表中以 <code> 展示；用 has 精确定位，避免误匹配其它列文案
        return page.locator("tr", has=page.locator("code", has_text=key)).first

    def delete_by_key_if_exists() -> None:
        """
        按 Key 找到对应行并删除：
        - 从该行 delete link 的 data-id 取 label id
        - 调用同源 API DELETE /api/admin/subscription/labels/{id}
        - reload 并确认列表中不再出现该 Key
        """
        row = find_row_by_key()
        if row.count() == 0:
            return

        label_id = row.locator("a.btn-delete").first.get_attribute("data-id")
        assert label_id, "label id not found on delete link"

        resp_del = page.request.delete(f"{base}/api/admin/subscription/labels/{label_id}")
        assert resp_del.status in (200, 204), f"unexpected delete status: {resp_del.status}"

        page.reload(wait_until="domcontentloaded")
        expect(page.locator("code", has_text=key)).to_have_count(0, timeout=20000)

    # 先清理：保证固定 Key 不会撞到历史脏数据
    delete_by_key_if_exists()

    label_id_created: str | None = None
    try:
        po.open_create_modal()
        po.fill_create_form(key=key)
        po.take_screenshot("aevatar_subscription_labels_p0_before_submit", full_page=False)

        po.submit_modal()
        _ = wait_mutation_response(page, timeout_ms=60000)

        expect(page.locator("code", has_text=key)).to_be_visible(timeout=20000)
        po.take_screenshot("aevatar_subscription_labels_p0_created", full_page=True)

        # 记录：创建的 Label（id + key），用于 finally 清理
        row = find_row_by_key()
        expect(row).to_be_visible(timeout=20000)
        label_id_created = row.locator("a.btn-delete").first.get_attribute("data-id")
        assert label_id_created, "label id not found on delete link"
        logger.step(f"记录创建标签: id={label_id_created} key={key}")

    finally:
        # 删除回滚（失败也要清理）
        if label_id_created:
            logger.step(f"清理：删除测试标签 id={label_id_created}")
        delete_by_key_if_exists()
        expect(page.locator("code", has_text=key)).to_have_count(0, timeout=20000)
        po.take_screenshot("aevatar_subscription_labels_p0_deleted", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_label_key_regex_snake_case_should_fail")
def test_p1_label_key_regex_snake_case_should_fail(auth_page: Page):
    """
    Regex 证据：^[a-z][a-z0-9_]*$
    - 以小写字母开头
    - 仅允许小写/数字/下划线
    """
    logger = TestLogger("test_p1_label_key_regex_snake_case_should_fail")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    po.open_create_modal()
    po.fill_create_form(key="Bad-KEY")
    po.submit_modal()

    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None:
        assert 400 <= resp.status < 500 or resp.status in (200, 204), f"unexpected status for invalid key submit: {resp.status}"

    assert has_validation_evidence(page) is True, "expected validation evidence for invalid snake_case key"
    po.take_screenshot("aevatar_subscription_labels_p1_regex_error", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.validation
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_label_key_invalid_snake_case_matrix_should_fail")
@pytest.mark.parametrize(
    "bad_key",
    [
        "MostPopular",        # 大写字母
        "most-popular",       # 连字符
        "most popular",       # 空格
        "1st_popular",        # 不能数字开头
        "_most_popular",      # 不能下划线开头
        "most_popular!",      # 特殊字符
    ],
)
def test_p1_label_key_invalid_snake_case_matrix_should_fail(auth_page: Page, bad_key: str):
    """
    规则真理源：
    - snake_case format: lowercase letters, numbers, underscores
    - Regex: ^[a-z][a-z0-9_]*$
    """
    logger = TestLogger("test_p1_label_key_invalid_snake_case_matrix_should_fail")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    po.open_create_modal()
    po.fill_create_form(key=bad_key)
    po.submit_modal()

    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None:
        assert 400 <= resp.status < 500 or resp.status in (200, 204), f"unexpected status for invalid key submit: {resp.status}"

    assert has_validation_evidence(page) is True, f"expected validation evidence for invalid key: {bad_key!r}"
    po.take_screenshot("aevatar_subscription_labels_p1_invalid_snake_case_matrix", full_page=True)
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_label_key_valid_snake_case_should_create_and_cleanup")
def test_p1_label_key_valid_snake_case_should_create_and_cleanup(auth_page: Page):
    """
    正向规则验证（带回滚）：
    snake_case format: lowercase letters, numbers, underscores (e.g., most_popular)
    """
    logger = TestLogger("test_p1_label_key_valid_snake_case_should_create_and_cleanup")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    cfg = ConfigManager()
    base = (cfg.get_service_url("frontend") or "").rstrip("/")

    po.navigate()
    assert_not_redirected_to_login(page)

    key = "most_popular_2026"

    def find_row_by_key():
        return page.locator("tr", has=page.locator("code", has_text=key)).first

    def delete_by_key_if_exists():
        row = find_row_by_key()
        if row.count() == 0:
            return
        label_id = row.locator("a.btn-delete").first.get_attribute("data-id")
        assert label_id
        resp_del = page.request.delete(f"{base}/api/admin/subscription/labels/{label_id}")
        assert resp_del.status in (200, 204)
        page.reload(wait_until="domcontentloaded")

    # 先清理再创建，保证可重复执行
    delete_by_key_if_exists()

    po.open_create_modal()
    po.fill_create_form(key=key)
    po.submit_modal()
    _ = wait_mutation_response(page, timeout_ms=60000)

    expect(page.locator("code", has_text=key)).to_be_visible(timeout=20000)
    po.take_screenshot("aevatar_subscription_labels_p1_snake_case_valid_created", full_page=True)

    # 回滚删除 + 验证列表不再出现
    delete_by_key_if_exists()
    expect(page.locator("code", has_text=key)).to_have_count(0, timeout=20000)
    po.take_screenshot("aevatar_subscription_labels_p1_snake_case_valid_deleted", full_page=True)
    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.boundary
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_label_key_maxlength_128_boundary")
def test_p1_label_key_maxlength_128_boundary(auth_page: Page):
    logger = TestLogger("test_p1_label_key_maxlength_128_boundary")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    po.open_create_modal()

    # len=129 should fail
    po.fill_create_form(key=("a" + ("b" * 128)))
    # 若前端 maxlength 生效会被截断到 128；否则提交后应出现校验错误证据
    v = page.locator(po.LABEL_KEY_INPUT).input_value(timeout=3000) or ""
    if len(v) <= 128:
        assert len(v) == 128, f"expected input to truncate to 128, got len={len(v)}"
    else:
        po.submit_modal()
        resp = wait_mutation_response(page, timeout_ms=1500)
        if resp is not None:
            assert 400 <= resp.status < 500 or resp.status in (200, 204), f"unexpected status: {resp.status}"
        assert has_validation_evidence(page) is True, "expected validation evidence for maxlength overflow"

    # len=128 should be accepted by input (不强制提交成功，避免污染数据)
    po.fill_create_form(key=("a" + ("b" * 127)))
    expect(page.locator(po.LABEL_KEY_INPUT)).to_have_value("a" + ("b" * 127))

    po.take_screenshot("aevatar_subscription_labels_p1_maxlength_boundary", full_page=True)
    logger.end(success=True)



@pytest.mark.P1
@pytest.mark.validation
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_label_key_required_empty_should_fail")
def test_p1_label_key_required_empty_should_fail(auth_page: Page):
    """必填校验：Key [Required]（真理源：CreateModal.cshtml.cs）"""
    logger = TestLogger("test_p1_label_key_required_empty_should_fail")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    po.open_create_modal()
    po.fill_create_form(key="")
    po.submit_modal()

    resp = wait_mutation_response(page, timeout_ms=1500)
    if resp is not None:
        assert 400 <= resp.status < 500 or resp.status in (200, 204), f"unexpected status for empty key submit: {resp.status}"

    assert has_validation_evidence(page) is True, "expected validation evidence for required key"
    po.take_screenshot("aevatar_subscription_labels_p1_required_empty", full_page=True)

    logger.end(success=True)


@pytest.mark.P1
@pytest.mark.functional
@allure.feature("SubscriptionLabels")
@allure.story("P1")
@allure.title("test_p1_create_label_fill_then_cancel_should_not_create")
def test_p1_create_label_fill_then_cancel_should_not_create(auth_page: Page):
    """创建之后不保存退出：Cancel 后列表不应新增该 Key。"""
    logger = TestLogger("test_p1_create_label_fill_then_cancel_should_not_create")
    logger.start()

    page = auth_page
    po = SubscriptionLabelsPage(page)

    po.navigate()
    assert_not_redirected_to_login(page)

    ts = int(time.time())
    key = f"qa_label_cancel_{ts}"

    po.open_create_modal()
    po.fill_create_form(key=key)
    po.take_screenshot("aevatar_subscription_labels_p1_cancel_before", full_page=False)

    po.cancel_modal()
    try:
        page.wait_for_selector(po.MODAL, state="hidden", timeout=10000)
    except Exception:
        page.keyboard.press("Escape")

    page.wait_for_timeout(500)
    assert page.locator("code", has_text=key).count() == 0, "unexpected record found after cancel"

    po.take_screenshot("aevatar_subscription_labels_p1_cancel_after", full_page=True)
    logger.end(success=True)
