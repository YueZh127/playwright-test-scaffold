# ═══════════════════════════════════════════════════════════════
# Aevatar - Subscription Features Page Object
# ═══════════════════════════════════════════════════════════════
"""
功能特性（SubscriptionFeatures）管理页。

证据来源（后端真理源）：
- Aevatar.Web/Pages/SubscriptionFeatures/Index.cshtml（按钮/表格/动作/API）
- Aevatar.Web/Pages/SubscriptionFeatures/CreateModal.cshtml(.cs)（字段与校验）
"""

from __future__ import annotations

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionFeaturesPage(BasePage):
    URL = "/SubscriptionFeatures"
    # 仅使用 CSS 选择器，避免混用 selector engines 导致解析失败
    page_loaded_indicator = "#BtnCreateFeature, #BtnCreateFirstFeature, #featuresTable"

    CREATE_BUTTON = "#BtnCreateFeature, #BtnCreateFirstFeature"

    NAME_KEY_INPUT = "input[name='Feature.NameKey'], #Feature_NameKey"
    DESCRIPTION_KEY_INPUT = "input[name='Feature.DescriptionKey'], #Feature_DescriptionKey"
    TYPE_SELECT = "select[name='Feature.Type'], #Feature_Type"
    DISPLAY_ORDER_INPUT = "input[name='Feature.DisplayOrder'], #Feature_DisplayOrder"

    MODAL = ".modal.show, .abp-modal"
    # 注意：不能直接用 f"{MODAL} button..."，否则逗号会破坏选择器语义
    MODAL_SAVE_BUTTON = ".modal.show button[type='submit'], .abp-modal button[type='submit']"
    MODAL_CANCEL_BUTTON = (
        ".modal.show button:has-text('Cancel'), .abp-modal button:has-text('Cancel'), "
        ".modal.show button.btn-secondary, .abp-modal button.btn-secondary"
    )

    FEATURES_TABLE = "#featuresTable"
    FEATURES_LIST = "#featuresList"
    DRAG_HANDLE = ".drag-handle"

    DELETE_ACTION = ".dropdown-menu .btn-delete"

    def navigate(self) -> None:
        logger.info("导航到功能特性页")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        return self.is_visible(self.CREATE_BUTTON, timeout=8000) or self.is_visible(self.FEATURES_TABLE, timeout=8000)

    def open_create_modal(self) -> None:
        self.click(self.CREATE_BUTTON)
        self.wait_for_element(self.MODAL, state="visible", timeout=10000)

    def fill_create_form(self, *, name_key: str, type_value: str, display_order: int = 0, description_key: str = "") -> None:
        self.fill(self.NAME_KEY_INPUT, name_key)
        if description_key:
            self.fill(self.DESCRIPTION_KEY_INPUT, description_key)
        self.select_option(self.TYPE_SELECT, type_value)
        self.fill(self.DISPLAY_ORDER_INPUT, str(display_order))

    def submit_modal(self) -> None:
        self.click(self.MODAL_SAVE_BUTTON)

    def cancel_modal(self) -> None:
        self.click(self.MODAL_CANCEL_BUTTON)
