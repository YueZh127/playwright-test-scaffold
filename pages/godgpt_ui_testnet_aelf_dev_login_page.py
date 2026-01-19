# ═══════════════════════════════════════════════════════════════
# GodgptUiTestnetAelfDevLogin Page Object
# - Source plan: docs/test-plans/godgpt_ui_testnet_aelf_dev_login.md
# - URL: https://godgpt-ui-testnet.aelf.dev/ (login view + guest view)
# ═══════════════════════════════════════════════════════════════
"""
GodGPT 登录/游客（同 URL 不跳转）页面对象

说明（来自前端源码证据）：
- 聊天输入框 placeholder（游客态）为 "Ask anything"
  - custom-gpt-frontend/app/chat/[sessionId]/index.tsx
  - custom-gpt-frontend/i18n/locales/en.json (home_ask_anything)
- 游客超限提示 key: signup_continue_alert
  - en: "Sign up to continue and receive 320 FREE credits."
"""

from __future__ import annotations

from typing import Iterable, Optional
from urllib.parse import quote

from playwright.sync_api import Page, expect

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class GodgptUiTestnetAelfDevLoginPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # URL / LOAD
    # ═══════════════════════════════════════════════════════════════
    URL = "/"

    # 登录视图关键控件
    #
    # 注意：ReactNativeWeb 的 DOM 容器嵌套很深，使用 `div:has-text(...)` 容易把祖先容器也匹配进来，
    # 导致 expect/click 触发 strict mode。
    # 因此这里统一优先用 `get_by_text(..., exact=True).first` 进行断言与点击。
    APPLE_BTN_TEXT = "Continue with Apple"
    GOOGLE_BTN_TEXT = "Continue with Google"
    EMAIL_BTN_TEXT = "Continue with Email"
    SKIP_BTN_TEXT = "Skip"

    EMAIL_PLACEHOLDER_TEXT = "Enter your email"
    EMAIL_INPUT = 'input[placeholder="Enter your email"]'

    # 密码页（/email-login）
    PASSWORD_INPUT = 'input[type="password"]'
    PASSWORD_INPUT_PLACEHOLDER = 'input[placeholder="Enter password"]'
    CONTINUE_BTN_TEXT = "Continue"
    EDIT_TEXT = "Edit"
    FORGET_PASSWORD_TEXT = "Forget Password?"

    # 游客聊天输入框（前端源码：home_ask_anything => "Ask anything"）
    CHAT_INPUT_GUEST_CANDIDATES = [
        'textarea[placeholder="Ask anything"]',
        'input[placeholder="Ask anything"]',
        '[contenteditable="true"][data-placeholder="Ask anything"]',
        # 兜底（避免文案微小漂移）
        'textarea[placeholder*="Ask anything"]',
        'input[placeholder*="Ask anything"]',
    ]

    # Toast 文案（前端 i18n en）
    SIGNUP_CONTINUE_ALERT_TEXT = "Sign up to continue and receive 320 FREE credits."
    SIGNIN_EMAIL_TOAST_TEXT = "Please enter an email address"
    SIGNIN_EMAIL_ALERT_TEXT = "Please enter a valid email address"
    # 兜底：部分环境可能使用不同文案（来自 auth.invalid_email_format）
    INVALID_EMAIL_FORMAT_TEXT = "Invalid email format"
    SIGNIN_PASSWORD_TOAST_TEXT = "Please enter a password"
    PASSWORD_MIN_LENGTH_TEXT = "Password should be at least 6 characters"
    PASSWORD_UPPERCASE_REQUIRED_TEXT = "Password must contain at least one uppercase letter ('A'-'Z')"
    PASSWORD_LOWERCASE_REQUIRED_TEXT = "Password must contain at least one lowercase letter ('a'-'z')"
    PASSWORD_DIGIT_REQUIRED_TEXT = "Passwords must have at least one digit ('0'-'9')."
    PASSWORD_SPECIAL_REQUIRED_TEXT = "Password must contain at least one special character (e.g., !, @, #)"
    LOGIN_FAILED_TEXT = "Login failed"

    # 注意：用邮箱输入框作为 load indicator（不会触发 strict mode）
    page_loaded_indicator = EMAIL_INPUT

    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION
    # ═══════════════════════════════════════════════════════════════
    def navigate(self) -> None:
        logger.info("导航到 GodGPT 登录/游客入口（同 URL 登录视图）")
        self.goto(self.URL)
        self.wait_for_page_load(timeout=60000)

    def is_loaded(self) -> bool:
        return self.is_visible(self.page_loaded_indicator, timeout=8000) or self.page.get_by_text(
            self.EMAIL_BTN_TEXT, exact=True
        ).first.is_visible()

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════
    def _first_visible_text(self, texts: Iterable[str], *, timeout_ms: int = 2000) -> Optional[str]:
        for t in texts:
            try:
                loc = self.page.get_by_text(t, exact=True).first
                if loc.is_visible(timeout=timeout_ms):
                    return t
            except Exception:
                continue
        return None

    def _click_text(self, text: str) -> None:
        self.page.get_by_text(text, exact=True).first.click()

    def _email_input_locator(self):
        """
        返回“最可能是用户可见”的邮箱输入框 locator。
        说明：RN-Web 可能渲染多个 input（含隐藏/占位），直接用 CSS 选择器可能会写到不可见 input。
        """
        candidates = [
            self.page.get_by_placeholder(self.EMAIL_PLACEHOLDER_TEXT).first,
            self.page.locator(self.EMAIL_INPUT).first,
        ]
        for loc in candidates:
            try:
                if loc.count() > 0 and loc.is_visible():
                    return loc
            except Exception:
                continue
        # 兜底：即便不可见也返回第一个（让后续 expect 给出更明确的错误）
        return candidates[0]

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS - LOGIN VIEW
    # ═══════════════════════════════════════════════════════════════
    def assert_login_view_visible(self) -> None:
        """断言：登录视图关键控件可见（URL 不跳转）。"""
        # 至少保证 Email 登录入口存在（Apple/Google 可能受环境限制）
        email_text = self._first_visible_text([self.EMAIL_BTN_TEXT], timeout_ms=8000)
        assert email_text, "Continue with Email not visible"
        expect(self.page.get_by_text(self.EMAIL_BTN_TEXT, exact=True).first).to_be_visible()

        # 邮箱输入框通常在登录视图可见
        if self.page.locator(self.EMAIL_INPUT).count() > 0:
            expect(self.page.locator(self.EMAIL_INPUT)).to_be_visible()

    def fill_email(self, email: str) -> None:
        loc = self._email_input_locator()
        expect(loc).to_be_visible(timeout=8000)

        def _input_value_safe() -> str:
            try:
                return (loc.input_value() or "")
            except Exception:
                return ""

        # RN-Web 的输入组件偶发对 `.fill()` 不敏感（尤其是存在多层封装时），这里按“最稳优先”做多策略写入。
        strategies = [
            ("fill", lambda: loc.fill(email)),
            ("type", lambda: loc.type(email, delay=30)),
            ("kbd_type", lambda: self.page.keyboard.type(email, delay=30)),
        ]

        for _, do in strategies:
            try:
                loc.click()
                try:
                    loc.press("Control+A")
                except Exception:
                    pass
                do()
                v = _input_value_safe().strip()
                if v == email.strip() and v != "":
                    return
            except Exception:
                continue

        raise AssertionError("failed to fill visible email input (value did not stick)")

    def click_continue_with_email(self) -> None:
        self._click_text(self.EMAIL_BTN_TEXT)

    def click_continue_with_apple(self) -> None:
        self._click_text(self.APPLE_BTN_TEXT)

    def click_continue_with_google(self) -> None:
        self._click_text(self.GOOGLE_BTN_TEXT)

    def click_skip(self) -> None:
        self._click_text(self.SKIP_BTN_TEXT)

    def goto_password_view(self, email: str) -> None:
        """
        直接进入“输入密码”视图（绕过 /api/account/check-email-registered 的分支），用于纯前端校验矩阵测试。
        说明：expo-router Web 下该路径通常为 /email-login?email=<...>
        """
        safe_email = quote(email or "", safe="")
        self.goto(f"/email-login?email={safe_email}")
        self.page.wait_for_load_state("domcontentloaded", timeout=60000)

    def assert_password_view_visible(self) -> None:
        """
        断言：密码输入视图已出现。
        - 至少应看到 password input + Continue
        """
        # 优先 placeholder 精确定位（更稳定）
        if self.page.locator(self.PASSWORD_INPUT_PLACEHOLDER).count() > 0:
            expect(self.page.locator(self.PASSWORD_INPUT_PLACEHOLDER)).to_be_visible(timeout=15000)
        else:
            expect(self.page.locator(self.PASSWORD_INPUT).first).to_be_visible(timeout=15000)
        expect(self.page.get_by_text(self.CONTINUE_BTN_TEXT, exact=True).first).to_be_visible(timeout=15000)

    def fill_password(self, password: str) -> None:
        # 避免日志泄露：这里不打印密码
        if self.page.locator(self.PASSWORD_INPUT_PLACEHOLDER).count() > 0:
            self.page.fill(self.PASSWORD_INPUT_PLACEHOLDER, password)
        else:
            self.page.fill(self.PASSWORD_INPUT, password)

    def click_continue_on_password(self) -> None:
        self._click_text(self.CONTINUE_BTN_TEXT)

    def assert_password_error_visible(self, expected: str) -> None:
        """断言密码页的错误提示出现（toast/inline 均可）。"""
        expect(self.page.get_by_text(expected).first).to_be_visible(timeout=8000)

    def assert_login_failed_visible(self) -> None:
        """断言：登录失败提示出现（后端 error_description 或 fallback）。"""
        # 既可能是后端返回的具体 message，也可能 fallback 到固定文案
        loc = self.page.get_by_text(self.LOGIN_FAILED_TEXT).first
        expect(loc).to_be_visible(timeout=15000)

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS - GUEST / CHAT
    # ═══════════════════════════════════════════════════════════════
    def wait_for_chat_ready(self) -> None:
        """
        等待聊天输入框出现（登录后与游客态共用）。
        备注：历史上该方法叫 wait_for_guest_chat_ready，但登录成功后也会复用同一套输入框，
        因此这里提供更准确的命名，同时保留旧方法名作为兼容别名。
        """
        self.wait_for_guest_chat_ready()

    def wait_for_guest_chat_ready(self) -> None:
        """等待游客聊天输入框出现。"""
        self.page.wait_for_timeout(500)  # 给视图切换一点缓冲
        self.page.wait_for_load_state("domcontentloaded", timeout=30000)
        last_err = None
        for sel in self.CHAT_INPUT_GUEST_CANDIDATES:
            try:
                self.page.wait_for_selector(sel, state="visible", timeout=60000)
                return
            except Exception as e:
                last_err = e
                continue
        raise AssertionError(f"guest chat input not visible: {last_err}")

    def send_message_by_enter(self, message: str) -> None:
        """发送消息：写入输入框 + Enter（避免定位发送按钮）。"""
        # 每次发送前都重新等待输入框（上一条消息可能触发一次导航/重渲染，输入框会短暂消失）
        self.wait_for_guest_chat_ready()
        for sel in self.CHAT_INPUT_GUEST_CANDIDATES:
            loc = self.page.locator(sel).first
            try:
                if loc.count() > 0 and loc.is_visible():
                    self.page.fill(sel, message)
                    break
            except Exception:
                continue
        else:
            raise AssertionError("guest chat input not found for sending message")
        self.page.keyboard.press("Enter")

    def assert_signup_continue_toast_visible(self) -> None:
        expect(self.page.get_by_text(self.SIGNUP_CONTINUE_ALERT_TEXT)).to_be_visible()

    def assert_email_required_or_invalid_toast_visible(self) -> None:
        """
        登录页 email 必填/格式错误提示（来自前端 i18n en）：
        - signin_email_toast: Please enter an email address
        - signin_email_alert: Please enter a valid email address
        """
        loc1 = self.page.get_by_text(self.SIGNIN_EMAIL_TOAST_TEXT).first
        loc2 = self.page.get_by_text(self.SIGNIN_EMAIL_ALERT_TEXT).first
        loc3 = self.page.get_by_text(self.INVALID_EMAIL_FORMAT_TEXT).first
        try:
            expect(loc1).to_be_visible(timeout=8000)
            return
        except Exception:
            pass
        try:
            expect(loc2).to_be_visible(timeout=8000)
            return
        except Exception:
            pass
        expect(loc3).to_be_visible(timeout=8000)

    def assert_invalid_email_error_visible(self) -> None:
        """
        非法邮箱格式提示（手动执行可见）。
        说明：该错误在 Web 上可能是 inline error（FormInput error prop），也可能是 toast；
        因此这里用“多候选文本”做稳定断言。
        """
        candidates = [
            self.SIGNIN_EMAIL_ALERT_TEXT,
            self.INVALID_EMAIL_FORMAT_TEXT,
            # 兜底：部分构建可能用 auth.invalid_email_format
            "Please enter a valid email address",
        ]
        t = self._first_visible_text(candidates, timeout_ms=8000)
        assert t, f"invalid email error not visible, tried: {candidates}"

    def assert_input_cleared(self) -> None:
        """断言输入框被清空（前端 handleSend 进入时会 setInput('')）。"""
        loc = None
        for sel in self.CHAT_INPUT_GUEST_CANDIDATES:
            candidate = self.page.locator(sel).first
            try:
                if candidate.count() > 0 and candidate.is_visible():
                    loc = candidate
                    break
            except Exception:
                continue
        assert loc is not None, "guest chat input not found for cleared assertion"
        # textarea/input 支持 input_value；contenteditable 用 text_content 兜底
        try:
            v = loc.input_value()
            assert (v or "").strip() == "", f"chat input not cleared, got: {v!r}"
        except Exception:
            txt = (loc.text_content() or "").strip()
            assert txt == "", f"chat input not cleared, got text: {txt!r}"


