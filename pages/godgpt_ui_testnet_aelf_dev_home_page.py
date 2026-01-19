# ═══════════════════════════════════════════════════════════════
# GodgptUiTestnetAelfDevHome Page Object
# - Source plan: docs/test-plans/godgpt_ui_testnet_aelf_dev_home.md
# - URL: https://godgpt-ui-testnet.aelf.dev/ (after login)
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations
import re
from typing import Optional

from playwright.sync_api import expect

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class GodgptUiTestnetAelfDevHomePage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════
    
    # 聊天输入框 (RN-Web 渲染为 textarea 或 div contenteditable)
    CHAT_INPUT = 'textarea[placeholder="Ask anything"]'
    CHAT_INPUT_FALLBACK = 'textarea[placeholder*="Ask"]'
    
    # 发送按钮
    SEND_BUTTON = 'button:has(svg)' # 具体的可以通过 aria-label 或 inner svg 进一步定位
    
    # 侧边栏与导航
    NEW_CHAT_BUTTON = 'text="New Chat"'
    SIDEBAR_TOGGLE = 'button:has(svg)' # Logo 所在的按钮
    
    # 消息列表
    MESSAGE_LIST_CONTAINER = '[role="main"]'
    CHAT_MESSAGES = '.r-1oszu61' # 示例，实际可能需要根据 text 动态查找
    
    # 用户相关
    USER_AVATAR_BUTTON = 'button:has-text("A")' # 示例，通常是首字母
    
    URL = "/" # 登录后重定向到该 URL 或 /(app)

    # Credits 显示（Header 中的 CreditsRechargeBadge）
    # - 非订阅：按钮文字为纯数字（credits 数量）
    # - 订阅：按钮文字为 Daily/Weekly/Monthly/Annual 等
    CREDITS_BADGE_ROLE = "button"
    CREDITS_BADGE_NUMERIC_RE = re.compile(r"^\\s*\\d+\\s*$")
    CREDITS_EXHAUSTED_TEXT_EN = "You've run out of credits."
    CREDITS_EXHAUSTED_TEXT_ZH = "你的积分已用完。"

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION & LOAD
    # ═══════════════════════════════════════════════════════════════

    def navigate(self) -> None:
        """导航到 Home 页面（通常需要登录态）"""
        logger.info("导航到 GodGPT Home 页面")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        """检查页面是否加载完成"""
        return self.is_visible(self.CHAT_INPUT, timeout=15000)

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════
    
    def wait_for_ready(self) -> None:
        """等待页面加载完成（以输入框可见为准）"""
        logger.info("等待 Home 页面聊天输入框可见")
        try:
            self.page.wait_for_selector(self.CHAT_INPUT, state="visible", timeout=30000)
            return
        except Exception:
            # 兜底：i18n 或 placeholder 微漂移时，使用模糊匹配
            self.page.wait_for_selector(self.CHAT_INPUT_FALLBACK, state="visible", timeout=30000)

    def send_message(self, message: str) -> None:
        """发送消息"""
        logger.info(f"发送消息: {message}")
        self.fill(self.CHAT_INPUT, message)
        self.page.keyboard.press("Enter")
        # 或者点击发送按钮
        # self.click(self.SEND_BUTTON)

    def click_new_chat(self) -> None:
        """点击 New Chat"""
        logger.info("点击 New Chat 按钮")
        self.click(self.NEW_CHAT_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def get_last_ai_message(self) -> str:
        """获取最后一条 AI 回复的内容"""
        # 这是一个示例逻辑，实际可能需要等待 isDone 状态
        # 根据前端代码，AI 消息通常是 !list.chatRole
        self.page.wait_for_timeout(2000) # 等待流式输出开始
        # 简单实现：查找最后一条非用户消息的内容
        messages = self.page.locator('text="GodGPT"').all() # 假设 AI 消息有 Logo 或名称
        if messages:
            return messages[-1].inner_text()
        return ""

    def assert_chat_input_visible(self) -> None:
        """断言输入框可见"""
        try:
            expect(self.page.locator(self.CHAT_INPUT)).to_be_visible()
        except Exception:
            expect(self.page.locator(self.CHAT_INPUT_FALLBACK)).to_be_visible()

    def assert_message_in_list(self, message: str) -> None:
        """断言消息出现在列表中"""
        expect(self.page.get_by_text(message).first).to_be_visible()

    def get_credits_count(self) -> int:
        """
        获取当前用户 credits 数量（来自 Header 的 CreditsRechargeBadge）。

        注意：
        - 非订阅用户时，badge 文案是纯数字（credits）。
        - 订阅用户时，badge 文案是计划名（Daily/Weekly/...），此时无法用该方法断言扣费。
        """
        loc = self.page.get_by_role(self.CREDITS_BADGE_ROLE, name=self.CREDITS_BADGE_NUMERIC_RE).first
        expect(loc).to_be_visible(timeout=15000)
        txt = (loc.text_content() or "").strip()
        if not re.fullmatch(r"\\d+", txt):
            raise AssertionError(f"credits badge not numeric (maybe subscription active?), got: {txt!r}")
        return int(txt)

    def assert_credits_exhausted_toast_visible(self) -> None:
        """
        断言：出现 credits 不足 toast。
        真理源：custom-gpt-frontend/utils/hooks/useDisplayCreditsToast.ts -> t('credits_exhausted')
        """
        loc_en = self.page.get_by_text(self.CREDITS_EXHAUSTED_TEXT_EN).first
        loc_zh = self.page.get_by_text(self.CREDITS_EXHAUSTED_TEXT_ZH).first
        try:
            expect(loc_en).to_be_visible(timeout=8000)
            return
        except Exception:
            expect(loc_zh).to_be_visible(timeout=8000)
