# ═══════════════════════════════════════════════════════════════
# Aevatar - Subscription Labels Page Object
# ═══════════════════════════════════════════════════════════════
"""
商品标签（SubscriptionLabels）管理页。

证据来源（后端真理源）：
- Aevatar.Web/Pages/SubscriptionLabels/Index.cshtml（按钮/表格/动作/API）
- Aevatar.Web/Pages/SubscriptionLabels/CreateModal.cshtml(.cs)（字段与校验：snake_case regex）
"""

from __future__ import annotations

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionLabelsPage(BasePage):
    URL = "/SubscriptionLabels"
    # 仅使用 CSS 选择器，避免混用 selector engines 导致解析失败
    page_loaded_indicator = "#BtnCreateLabel, #BtnCreateFirstLabel"

    CREATE_BUTTON = "#BtnCreateLabel, #BtnCreateFirstLabel"

    LABEL_KEY_INPUT = "input[name='Label.Key'], #Label_Key, input[name='Label.Key']"

    MODAL = ".modal.show, .abp-modal"
    # 注意：不能直接用 f"{MODAL} button..."，否则逗号会破坏选择器语义
    MODAL_SAVE_BUTTON = ".modal.show button[type='submit'], .abp-modal button[type='submit']"
    MODAL_CANCEL_BUTTON = (
        ".modal.show button:has-text('Cancel'), .abp-modal button:has-text('Cancel'), "
        ".modal.show button.btn-secondary, .abp-modal button.btn-secondary"
    )

    DELETE_ACTION = ".dropdown-menu .btn-delete"

    def navigate(self) -> None:
        logger.info("导航到商品标签页")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        return self.is_visible(self.CREATE_BUTTON, timeout=8000) or self.is_visible("abp-card-title", timeout=8000)

    def open_create_modal(self) -> None:
        self.click(self.CREATE_BUTTON)
        self.wait_for_element(self.MODAL, state="visible", timeout=10000)

    def fill_create_form(self, *, key: str) -> None:
        self.fill(self.LABEL_KEY_INPUT, key)

    def submit_modal(self) -> None:
        self.click(self.MODAL_SAVE_BUTTON)

    def cancel_modal(self) -> None:
        self.click(self.MODAL_CANCEL_BUTTON)
