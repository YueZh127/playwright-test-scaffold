# ═══════════════════════════════════════════════════════════════
# Aevatar - Subscription Products Page Object
# ═══════════════════════════════════════════════════════════════
"""
订阅商品（SubscriptionProducts）管理页。

证据来源（后端真理源）：
- Aevatar.Web/Pages/SubscriptionProducts/Index.cshtml（按钮/表格/动作 class）
- Aevatar.Web/Pages/SubscriptionProducts/CreateModal.cshtml(.cs)（表单字段与校验）
"""

from __future__ import annotations

from core.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionProductsPage(BasePage):
    # ═══════════════════════════════════════════════════════════════
    # SELECTORS
    # ═══════════════════════════════════════════════════════════════

    # URL: "~/SubscriptionProducts"
    URL = "/SubscriptionProducts"
    # 仅使用 CSS 选择器，避免混用 selector engines 导致解析失败
    page_loaded_indicator = "#BtnCreateProduct, #BtnCreateFirstProduct"

    CREATE_BUTTON = "#BtnCreateProduct, #BtnCreateFirstProduct"

    # Create/Edit modal fields (tag helpers generate id like Product_NameKey)
    NAME_KEY_INPUT = "input[name='Product.NameKey'], #Product_NameKey"
    PLAN_TYPE_SELECT = "select[name='Product.PlanType'], #Product_PlanType"
    DESCRIPTION_KEY_INPUT = "input[name='Product.DescriptionKey'], #Product_DescriptionKey"
    HIGHLIGHT_KEY_INPUT = "input[name='Product.HighlightKey'], #Product_HighlightKey"
    PLATFORM_SELECT = "select[name='Product.Platform'], #Product_Platform"
    PLATFORM_PRODUCT_ID_INPUT = "input[name='Product.PlatformProductId'], #Product_PlatformProductId"
    FEATURE_IDS_SELECT = "select[name='Product.FeatureIds'], #Product_FeatureIds"
    LABEL_ID_SELECT = "select[name='Product.LabelId'], #Product_LabelId"
    IS_ULTIMATE_CHECKBOX = "input[name='Product.IsUltimate'], #Product_IsUltimate"

    MODAL = ".modal.show, .abp-modal"
    # 注意：不能直接用 f"{MODAL} button..."，否则逗号会破坏选择器语义
    MODAL_SAVE_BUTTON = ".modal.show button[type='submit'], .abp-modal button[type='submit']"
    MODAL_CANCEL_BUTTON = (
        ".modal.show button:has-text('Cancel'), .abp-modal button:has-text('Cancel'), "
        ".modal.show button.btn-secondary, .abp-modal button.btn-secondary"
    )

    # Table action entries (from Index.cshtml)
    ACTIONS_DROPDOWN_BUTTON = "button.dropdown-toggle:has-text('Actions'), button.dropdown-toggle:has-text('操作')"
    EDIT_ACTION = ".dropdown-menu .btn-edit"
    DELETE_ACTION = ".dropdown-menu .btn-delete"
    LIST_ACTION = ".dropdown-menu .btn-list"
    UNLIST_ACTION = ".dropdown-menu .btn-unlist"

    def navigate(self) -> None:
        logger.info("导航到订阅商品页")
        self.goto(self.URL)
        self.wait_for_page_load()

    def is_loaded(self) -> bool:
        return self.is_visible(self.CREATE_BUTTON, timeout=8000) or self.is_visible("abp-card-title", timeout=8000)

    # ═══════════════════════════════════════════════════════════════
    # ACTIONS
    # ═══════════════════════════════════════════════════════════════

    def open_create_modal(self) -> None:
        self.click(self.CREATE_BUTTON)
        # ABP modal 首次加载可能较慢（脚本/资源加载），放宽等待避免偶发超时
        self.wait_for_element(self.MODAL, state="visible", timeout=20000)

    def fill_create_form(
        self,
        *,
        name_key: str,
        description_key: str,
        plan_type_value: str,
        platform_value: str,
        platform_product_id: str,
        highlight_key: str = "",
        is_ultimate: bool = False,
    ) -> None:
        self.fill(self.NAME_KEY_INPUT, name_key)
        self.select_option(self.PLAN_TYPE_SELECT, plan_type_value)
        self.fill(self.DESCRIPTION_KEY_INPUT, description_key)
        if highlight_key:
            self.fill(self.HIGHLIGHT_KEY_INPUT, highlight_key)
        self.select_option(self.PLATFORM_SELECT, platform_value)
        self.fill(self.PLATFORM_PRODUCT_ID_INPUT, platform_product_id)
        if is_ultimate:
            self.check(self.IS_ULTIMATE_CHECKBOX)

    def submit_modal(self) -> None:
        self.click(self.MODAL_SAVE_BUTTON)

    # ═══════════════════════════════════════════════════════════════
    # Helpers - Selects / Multi-select
    # ═══════════════════════════════════════════════════════════════

    def _select_value_by_text_contains(self, selector: str, needle: str) -> str:
        """
        从 <select> 里按 option 文本包含关系选择（大小写不敏感）。
        返回被选中的 value（用于断言/复用）。
        """
        n = (needle or "").strip().lower()
        js = """
        (p) => {
          const sel = p.sel;
          const needleLower = p.needleLower;
          const el = document.querySelector(sel);
          if (!el) return "";
          const opts = Array.from(el.querySelectorAll("option"));
          if (opts.length === 0) return "";
          const picked = opts.find(o => (o.textContent || "").trim().toLowerCase().includes(needleLower)) || opts[0];
          return (picked && picked.value) ? String(picked.value) : "";
        }
        """
        value = (self.page.evaluate(js, {"sel": selector, "needleLower": n}) or "").strip()
        if value:
            self.page.select_option(selector, value=value)
        return value

    def select_plan_type_by_text(self, text_contains: str) -> str:
        """按文本选择套餐类型，例如：Weekly/Monthly/Yearly（以实际 option 为准）。"""
        return self._select_value_by_text_contains(self.PLAN_TYPE_SELECT, text_contains)

    def select_platform_by_text(self, text_contains: str) -> str:
        """按文本选择平台：Stripe / Apple / Google（以实际 option 为准）。"""
        return self._select_value_by_text_contains(self.PLATFORM_SELECT, text_contains)

    def select_first_n_features(self, n: int = 2) -> list[str]:
        """
        选择前 N 个可用功能（FeatureIds 多选）。
        返回选择的 feature name（去掉括号里的 TypeName）。
        """
        js = """
        (p) => {
          const sel = p.sel;
          const n = p.n;
          const el = document.querySelector(sel);
          if (!el) return { values: [], names: [] };
          const opts = Array.from(el.querySelectorAll("option"));
          const picked = opts.filter(o => (o.value || "").trim() !== "").slice(0, Math.max(0, n|0));
          const values = picked.map(o => String(o.value || ""));
          const names = picked.map(o => {
            const t = (o.textContent || "").trim();
            const i = t.indexOf(" (");
            return (i > 0 ? t.slice(0, i) : t).trim();
          });
          return { values, names };
        }
        """
        obj = self.page.evaluate(js, {"sel": self.FEATURE_IDS_SELECT, "n": int(n)}) or {}
        values = obj.get("values") or []
        names = obj.get("names") or []
        if values:
            self.page.select_option(self.FEATURE_IDS_SELECT, value=values)
        return [str(x) for x in names if str(x).strip()]

    def select_features_by_name_contains(self, names: list[str]) -> list[str]:
        """
        在 FeatureIds 多选框中按 option 文本包含关系选择指定 features。
        返回实际命中的 feature name（去掉括号里的 TypeName）。
        """
        needles = [str(x).strip() for x in (names or []) if str(x).strip()]
        if not needles:
            return []
        js = """
        (p) => {
          const sel = p.sel;
          const needles = (p.needles || []).map(s => String(s || '').trim().toLowerCase()).filter(Boolean);
          const el = document.querySelector(sel);
          if (!el) return { values: [], names: [] };
          const opts = Array.from(el.querySelectorAll('option'));
          const picked = [];
          for (const n of needles) {
            const o = opts.find(x => ((x.textContent||'').trim().toLowerCase().includes(n)) && String(x.value||'').trim() !== '');
            if (o) picked.push(o);
          }
          const values = picked.map(o => String(o.value||''));
          const names2 = picked.map(o => {
            const t = (o.textContent || '').trim();
            const i = t.indexOf(' (');
            return (i > 0 ? t.slice(0, i) : t).trim();
          });
          return { values, names: names2 };
        }
        """
        obj = self.page.evaluate(js, {"sel": self.FEATURE_IDS_SELECT, "needles": needles}) or {}
        values = obj.get("values") or []
        picked_names = obj.get("names") or []
        if values:
            self.page.select_option(self.FEATURE_IDS_SELECT, value=[str(v) for v in values])
        return [str(x) for x in picked_names if str(x).strip()]

    def select_label_by_text_contains(self, text_contains: str) -> str:
        """
        在 LabelId 下拉中按 option 文本包含关系选择（大小写不敏感）。
        返回被选中的 value（用于断言/复用）。
        """
        return self._select_value_by_text_contains(self.LABEL_ID_SELECT, text_contains)
