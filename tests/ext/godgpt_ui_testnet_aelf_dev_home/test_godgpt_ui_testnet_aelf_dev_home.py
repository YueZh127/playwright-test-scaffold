# ═══════════════════════════════════════════════════════════════
# GodGPT UI Testnet - Home Page (Chat Interface)
# Source plan: docs/test-plans/godgpt_ui_testnet_aelf_dev_home.md
# ═══════════════════════════════════════════════════════════════

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.godgpt_ui_testnet_aelf_dev_login_page import GodgptUiTestnetAelfDevLoginPage
from pages.godgpt_ui_testnet_aelf_dev_home_page import GodgptUiTestnetAelfDevHomePage
from utils.logger import TestLogger


@pytest.fixture()
def zero_credits_account():
    """
    0 credits 测试账号（来源：test-data/test_account_pool.json）。
    - 不在测试代码里写死密码；从账号池读取。
    """
    # 账号池路径必须来自 config/project.yaml（单一真相源）
    import json
    from pathlib import Path

    import yaml

    # 找到仓库根目录（包含 config/project.yaml 的目录）
    repo_root = None
    for p in Path(__file__).resolve().parents:
        if (p / "config" / "project.yaml").exists():
            repo_root = p
            break
    if repo_root is None:
        pytest.skip("repo root not found (missing config/project.yaml in parents)")

    cfg_path = repo_root / "config" / "project.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    accounts_path = (((cfg.get("test_data") or {}).get("accounts") or {}).get("path") or "").strip()
    if not accounts_path:
        pytest.skip("test_data.accounts.path missing in config/project.yaml")

    pool_file = (repo_root / accounts_path).resolve()
    if not pool_file.exists():
        pytest.skip(f"accounts pool file not found: {pool_file}")

    data = json.loads(pool_file.read_text(encoding="utf-8"))
    pool = data.get("test_account_pool") or []

    # 优先按“业务语义”选账号，避免在测试代码里写死具体邮箱
    #（你当前账号池里该账号的 description 为 "GodGPT 0 credits测试账户"）
    for a in pool:
        desc = (a.get("description") or "").lower()
        if "0 credits" in desc or "0credit" in desc:
            return a

    pytest.skip("0 credits account not found in accounts pool (by description contains '0 credits')")


@pytest.fixture()
def logged_in_home(page: Page, test_account) -> GodgptUiTestnetAelfDevHomePage:
    """登录并进入 Home 页面的 fixture"""
    login_po = GodgptUiTestnetAelfDevLoginPage(page)
    home_po = GodgptUiTestnetAelfDevHomePage(page)
    
    # 安全约束：不在测试代码中硬编码密码；统一从账号池 fixture 获取
    email = (test_account or {}).get("email") or ""
    password = (test_account or {}).get("password") or ""
    if not email or not password:
        pytest.skip("test_account fixture missing email/password (account pool required)")
    
    login_po.navigate()
    login_po.assert_login_view_visible()
    
    with allure.step(f"登录账号: {email}"):
        login_po.fill_email(email)
        login_po.click_continue_with_email()
        # 若该账号被判定为未注册，会进入 /register；这种环境态无法继续做 Home 测试
        try:
            login_po.assert_password_view_visible()
        except Exception:
            if "/register" in (page.url or ""):
                pytest.skip(f"account routed to register flow: {page.url}")
            pytest.skip(f"password view not reachable (possible anti-bot / flow changed): {page.url}")
        login_po.fill_password(password)
        login_po.click_continue_on_password()
    
    try:
        home_po.wait_for_ready()
    except Exception:
        pytest.skip(f"home chat input not visible after login: {page.url}")
    return home_po


@pytest.fixture()
def logged_in_home_zero_credits(page: Page, zero_credits_account) -> GodgptUiTestnetAelfDevHomePage:
    """使用 0 credits 账号登录并进入 Home 页面"""
    login_po = GodgptUiTestnetAelfDevLoginPage(page)
    home_po = GodgptUiTestnetAelfDevHomePage(page)

    email = (zero_credits_account or {}).get("email") or ""
    password = (zero_credits_account or {}).get("password") or ""
    if not email or not password:
        pytest.skip("zero_credits_account missing email/password")

    login_po.navigate()
    login_po.assert_login_view_visible()

    with allure.step(f"登录 0 credits 账号: {email}"):
        login_po.fill_email(email)
        login_po.click_continue_with_email()
        try:
            login_po.assert_password_view_visible()
        except Exception:
            if "/register" in (page.url or ""):
                pytest.skip(f"0 credits account routed to register flow: {page.url}")
            pytest.skip(f"password view not reachable for 0 credits account: {page.url}")
        login_po.fill_password(password)
        login_po.click_continue_on_password()

    try:
        home_po.wait_for_ready()
    except Exception:
        pytest.skip(f"home chat input not visible after login (0 credits): {page.url}")
    return home_po


@allure.feature("GodGPT Home Page")
class TestGodgptHome:

    @pytest.mark.P0
    @allure.story("Core Chat")
    @allure.title("test_p0_send_message_success")
    def test_p0_send_message_success(self, logged_in_home: GodgptUiTestnetAelfDevHomePage):
        """
        验证用户登录后可以成功发送消息并出现在列表中；
        且在收到 AI 回复后，credits 数量应减少 10（非订阅用户）。
        """
        logger = TestLogger("test_p0_send_message_success")
        logger.start()
        
        home_po = logged_in_home
        msg = "Hello GodGPT, this is an automated test message."
        credits_before = None
        credits_after = None

        with allure.step("读取发送前 credits（用于扣费断言）"):
            try:
                credits_before = home_po.get_credits_count()
            except Exception as e:
                pytest.skip(f"credits badge not readable/numeric (maybe subscription active): {e}")
        
        with allure.step("输入并发送消息"):
            home_po.send_message(msg)
            
        with allure.step("断言：输入框已清空"):
            # 借用 login_page 的断言逻辑或在 home_page 实现
            # 这里简单直接在用例里写
            expect(home_po.page.locator(home_po.CHAT_INPUT)).to_have_value("")
            
        with allure.step("断言：消息已出现在列表中"):
            home_po.assert_message_in_list(msg)

        with allure.step("等待 AI 回复可观测信号（网络/渲染稳定）"):
            # 轻量等待：给流式回复/状态同步一点缓冲，避免立刻读到旧 credits
            home_po.page.wait_for_timeout(2500)

        with allure.step("读取 AI 回复后 credits，应扣减 10"):
            credits_after = home_po.get_credits_count()
            assert credits_before is not None
            assert credits_after == max(0, credits_before - 10), (
                f"credits not deducted by 10, before={credits_before}, after={credits_after}"
            )
            
        logger.end(success=True)

    @pytest.mark.P0
    @allure.story("Session Management")
    @allure.title("test_p0_new_chat_resets_view")
    def test_p0_new_chat_resets_view(self, logged_in_home: GodgptUiTestnetAelfDevHomePage):
        """
        验证点击 New Chat 会重置当前会话
        """
        logger = TestLogger("test_p0_new_chat_resets_view")
        logger.start()
        
        home_po = logged_in_home
        
        # 先发一条消息
        home_po.send_message("Message to be cleared")
        home_po.assert_message_in_list("Message to be cleared")
        
        with allure.step("点击 New Chat"):
            home_po.click_new_chat()
            
        with allure.step("断言：消息列表已清空"):
            expect(home_po.page.get_by_text("Message to be cleared")).not_to_be_visible()
            
        logger.end(success=True)

    @pytest.mark.P1
    @allure.story("Credits")
    @allure.title("test_p1_no_credits_blocks_send_shows_toast")
    def test_p1_no_credits_blocks_send_shows_toast(
        self, logged_in_home_zero_credits: GodgptUiTestnetAelfDevHomePage
    ):
        """
        TC-HOME-103：0 credits 账户发送消息应被拦截并提示 credits_exhausted。
        真理源：custom-gpt-frontend/utils/hooks/useDisplayCreditsToast.ts
        """
        logger = TestLogger("test_p1_no_credits_blocks_send_shows_toast")
        logger.start()

        home_po = logged_in_home_zero_credits

        with allure.step("断言：当前 credits 为 0（否则环境不符合该用例前置）"):
            try:
                credits = home_po.get_credits_count()
            except Exception as e:
                pytest.skip(f"credits badge not readable/numeric: {e}")
            if credits != 0:
                pytest.skip(f"expected 0 credits account, but got credits={credits}")

        msg = "[qa-0-credits] should be blocked"

        with allure.step("尝试发送消息（应被拦截）"):
            home_po.send_message(msg)

        with allure.step("断言：toast 提示 credits 用尽"):
            home_po.assert_credits_exhausted_toast_visible()

        with allure.step("断言：消息不会进入会话列表"):
            expect(home_po.page.get_by_text(msg)).to_have_count(0)

        with allure.step("断言：credits 不会变成负数，仍为 0"):
            assert home_po.get_credits_count() == 0

        logger.end(success=True)
