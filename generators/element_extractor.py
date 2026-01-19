# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Element Extractor
# ═══════════════════════════════════════════════════════════════
"""
元素提取器 - 从页面中提取各种类型的元素
"""

from playwright.sync_api import Page
from typing import List, Optional, Dict
import re
from generators.page_types import PageElement
from utils.logger import get_logger

logger = get_logger(__name__)


class ElementExtractor:
    """元素提取器"""

    def _get_elements(self, page: Page) -> List[PageElement]:
        """
        获取页面元素
        
        Args:
            page: Playwright页面对象
            
        Returns:
            List[PageElement]: 元素列表
        """
        elements = []
        
        # 获取输入框
        inputs = self._get_inputs(page)
        elements.extend(inputs)
        
        # 获取按钮
        buttons = self._get_buttons(page)
        elements.extend(buttons)
        
        # 获取链接
        links = self._get_links(page)
        elements.extend(links)
        
        # 获取下拉框
        selects = self._get_selects(page)
        elements.extend(selects)

        # 获取“可点击但不是 button/a”的元素（常见于 RN-Web / 自定义组件）
        clickables = self._get_clickables(page)
        # 去重：按 selector
        existing = {e.selector for e in elements if getattr(e, "selector", None)}
        for e in clickables:
            if e and e.selector and e.selector not in existing:
                elements.append(e)
                existing.add(e.selector)
        
        return elements

    def _get_clickables(self, page: Page) -> List[PageElement]:
        """
        获取“可点击元素”：
        - 很多页面的按钮不是 <button> 或 <a>，而是 <div tabindex=0> / cursor:pointer 的自定义组件
        - 这里通过 DOM 特征抓取候选，并用 `:has-text()` 生成可定位 selector
        """
        elements: List[PageElement] = []

        try:
            candidates = page.evaluate(
                """() => {
  const isVisible = (el) => {
    const r = el.getBoundingClientRect();
    if (!r || r.width <= 1 || r.height <= 1) return false;
    const s = window.getComputedStyle(el);
    if (!s) return false;
    if (s.visibility === 'hidden' || s.display === 'none' || Number(s.opacity || '1') === 0) return false;
    return true;
  };

  const pickText = (el) => {
    const t = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
    if (!t) return '';
    // 太长的不当成“按钮/链接”
    if (t.length > 60) return '';
    return t;
  };

  const out = [];
  const all = Array.from(document.querySelectorAll('*'));
  for (const el of all) {
    if (out.length >= 80) break;
    if (!isVisible(el)) continue;

    const tag = (el.tagName || '').toLowerCase();
    if (!tag || tag === 'html' || tag === 'body' || tag === 'script' || tag === 'style') continue;

    const role = el.getAttribute('role') || '';
    const tabindex = el.getAttribute('tabindex');
    const onclick = el.getAttribute('onclick');
    const aria = el.getAttribute('aria-label') || '';
    const href = el.getAttribute('href') || '';
    const cursor = (window.getComputedStyle(el).cursor || '');

    const likelyClickable =
      role === 'button' ||
      role === 'link' ||
      onclick != null ||
      tabindex != null ||
      cursor === 'pointer' ||
      href; // 有 href 但可能不是 a（少见）

    if (!likelyClickable) continue;

    const text = pickText(el);
    if (!text && !aria) continue;

    out.push({
      tag,
      role,
      tabindex: tabindex || '',
      aria,
      href,
      text,
      id: el.getAttribute('id') || '',
      className: el.getAttribute('class') || '',
    });
  }
  return out;
}"""
            )
        except Exception:
            candidates = []

        # 生成 locator → PageElement
        seen = set()
        for c in candidates or []:
            try:
                tag = (c.get("tag") or "div").strip() or "div"
                text = (c.get("text") or "").strip()
                aria = (c.get("aria") or "").strip()
                role = (c.get("role") or "").strip()
                href = (c.get("href") or "").strip()
                element_id = (c.get("id") or "").strip()

                # selector 生成策略：id > href > role+text > aria > text
                if element_id:
                    sel = f"#{element_id}"
                elif href and tag == "a":
                    sel = f"a[href='{href}']"
                elif role and text:
                    sel = f"[role='{role}']:has-text('{text}')"
                elif aria and tag:
                    sel = f"{tag}[aria-label='{aria}']"
                elif text:
                    sel = f"{tag}:has-text('{text}')"
                else:
                    continue

                # 去重：同 selector 不重复
                if sel in seen:
                    continue
                seen.add(sel)

                loc = page.locator(sel).first
                # 这类元素按“button/link”语义归类：有 href 或 role=link -> link，否则 button
                et = "link" if (href or role == "link") else "button"
                pe = self._extract_element_info(loc, et)
                if pe:
                    # 使用我们计算的 selector（比 _build_selector 更贴合可点击语义）
                    pe.selector = sel
                    # 关键：避免 locator.text_content() 把整屏文本都塞进来，强制用候选短文本
                    pe.text = text or aria or pe.text
                    elements.append(pe)
            except Exception:
                continue

        return elements
    
    def _get_inputs(self, page: Page) -> List[PageElement]:
        """获取输入框元素"""
        elements = []
        
        # 各种输入类型
        input_types = [
            "input[type='text']",
            "input[type='email']",
            "input[type='password']",
            "input[type='number']",
            "input[type='tel']",
            "input[type='url']",
            "input[type='search']",
            "input:not([type])",
            "textarea",
        ]
        
        for selector in input_types:
            try:
                locators = page.locator(selector).all()
                for i, loc in enumerate(locators):
                    try:
                        element = self._extract_element_info(loc, "input")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_buttons(self, page: Page) -> List[PageElement]:
        """获取按钮元素"""
        elements = []
        
        button_selectors = [
            "button",
            "input[type='submit']",
            "input[type='button']",
            "[role='button']",
        ]
        
        for selector in button_selectors:
            try:
                locators = page.locator(selector).all()
                for loc in locators:
                    try:
                        element = self._extract_element_info(loc, "button")
                        if element:
                            elements.append(element)
                    except:
                        pass
            except:
                pass
        
        return elements
    
    def _get_links(self, page: Page) -> List[PageElement]:
        """获取链接元素"""
        elements = []
        
        try:
            locators = page.locator("a[href]").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "link")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _get_selects(self, page: Page) -> List[PageElement]:
        """获取下拉框元素"""
        elements = []
        
        try:
            locators = page.locator("select").all()
            for loc in locators:
                try:
                    element = self._extract_element_info(loc, "select")
                    if element:
                        elements.append(element)
                except:
                    pass
        except:
            pass
        
        return elements
    
    def _extract_element_info(self, locator, element_type: str) -> Optional[PageElement]:
        """
        提取元素信息
        
        Args:
            locator: Playwright定位器
            element_type: 元素类型
            
        Returns:
            PageElement: 元素信息
        """
        try:
            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            selector = self._build_selector(locator, tag)
            attributes = self._extract_attributes(locator)
            
            return PageElement(
                selector=selector,
                tag=tag,
                type=element_type,
                text=locator.text_content() or "",
                placeholder=locator.get_attribute("placeholder") or "",
                name=locator.get_attribute("name") or "",
                id=locator.get_attribute("id") or "",
                role=locator.get_attribute("role") or "",
                required=locator.get_attribute("required") is not None,
                disabled=locator.get_attribute("disabled") is not None,
                attributes=attributes
            )
        except Exception as e:
            logger.debug(f"提取元素信息失败: {e}")
            return None
    
    def _build_selector(self, locator, tag: str) -> str:
        """构建元素选择器"""
        def _esc(v: str) -> str:
            # CSS attribute selector: keep it simple and safe for single quotes
            return (v or "").replace("\\", "\\\\").replace("'", "\\'")

        element_id = locator.get_attribute("id") or ""
        element_name = locator.get_attribute("name") or ""
        element_class = locator.get_attribute("class") or ""

        href = locator.get_attribute("href") or ""
        aria = locator.get_attribute("aria-label") or ""
        role = locator.get_attribute("role") or ""
        typ = locator.get_attribute("type") or ""

        # 优先级：id > 可判定的关键属性（href/aria/type/name）> class > tag
        if element_id:
            return f"#{_esc(element_id)}"

        # link：优先 href，避免生成 a.flex 这类不可区分 selector
        if tag == "a" and href:
            return f"a[href='{_esc(href)}']"

        # button：优先 aria-label / type
        if tag == "button" and aria:
            return f"button[aria-label='{_esc(aria)}']"
        if tag == "button" and typ:
            return f"button[type='{_esc(typ)}']"

        # input/select：优先 name（稳定字段）
        if element_name:
            return f"[name='{_esc(element_name)}']"

        # role 兜底：有些组件会用 role 标识
        if role:
            return f"[role='{_esc(role)}']"

        # 文本兜底：对“自定义按钮/链接”非常有效（例如 div tabindex=0）
        try:
            txt = (locator.text_content() or "").strip()
            txt = re.sub(r"\\s+", " ", txt)
            if 0 < len(txt) <= 40:
                return f"{tag}:has-text('{_esc(txt)}')"
        except Exception:
            pass

        # 最后才退化到 class（低质量/易漂移）
        if element_class:
            first_class = element_class.split()[0] if element_class else ""
            return f"{tag}.{first_class}" if first_class else tag

        return tag
    
    def _extract_attributes(self, locator) -> Dict[str, str]:
        """提取元素属性"""
        return {
            "type": locator.get_attribute("type") or "",
            "maxlength": locator.get_attribute("maxlength") or "",
            "pattern": locator.get_attribute("pattern") or "",
        }
    def _get_forms(self, page: Page) -> List[Dict]:
        """获取表单信息"""
        forms = []
        
        try:
            form_locators = page.locator("form").all()
            for form_loc in form_locators:
                try:
                    form_info = {
                        "id": form_loc.get_attribute("id") or "",
                        "action": form_loc.get_attribute("action") or "",
                        "method": form_loc.get_attribute("method") or "GET",
                        "inputs": [],
                    }
                    
                    # 获取表单内的输入框
                    inputs = form_loc.locator("input, textarea, select").all()
                    for inp in inputs:
                        form_info["inputs"].append({
                            "name": inp.get_attribute("name") or "",
                            "type": inp.get_attribute("type") or "text",
                            "required": inp.get_attribute("required") is not None,
                        })
                    
                    forms.append(form_info)
                except:
                    pass
        except:
            pass
        
        return forms
    
    def _get_navigation(self, page: Page) -> List[Dict]:
        """获取导航信息"""
        navigation = []
        
        nav_selectors = ["nav a", "header a", ".navbar a", ".menu a", ".nav a"]
        
        for selector in nav_selectors:
            try:
                links = page.locator(selector).all()
                for link in links:
                    try:
                        nav_item = {
                            "text": link.text_content() or "",
                            "href": link.get_attribute("href") or "",
                        }
                        if nav_item["text"] and nav_item["href"]:
                            navigation.append(nav_item)
                    except:
                        pass
            except:
                pass
        
        return navigation
    
