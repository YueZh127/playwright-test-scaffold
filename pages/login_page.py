# ═══════════════════════════════════════════════════════════════
# Aevatar - Login Page Object
# ═══════════════════════════════════════════════════════════════
"""
管理端登录页 Page Object。

注意：
- 该项目基于 ABP，默认登录路由通常为 `/Account/Login`
- 密码字段必须使用 `secret_fill`（禁止日志泄露）
"""

from __future__ import annotations

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS（优先稳定 name/type；必要时做小范围 fallback）
    # ═══════════════════════════════════════════════════════════════

    # ABP 默认：LoginInput.UserNameOrEmailAddress / LoginInput.Password
    USERNAME_INPUT = "input[name='LoginInput.UserNameOrEmailAddress'], input[name='username'], input[type='text']"
    PASSWORD_INPUT = "input[name='LoginInput.Password'], input[name='password'], input[type='password']"
    # 注意：Playwright selector engine 不能把 css 与 role=... 用逗号混写；
    # 这里直接使用 ABP 默认表单 submit 按钮（最稳定）。
    SUBMIT_BUTTON = "button[type='submit']"

    URL = "/Account/Login"
    page_loaded_indicator = "form"

    def navigate(self) -> None:
        logger.info("导航到登录页")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        return self.is_visible(self.USERNAME_INPUT, timeout=8000) and self.is_visible(self.PASSWORD_INPUT, timeout=8000)

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def login(self, username: str, password: str) -> None:
        logger.info(f"执行登录: username={username!r} password=***")
        self.fill(self.USERNAME_INPUT, username)
        self.secret_fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BUTTON)

