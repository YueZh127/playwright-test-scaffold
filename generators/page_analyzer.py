# ═══════════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Page Analyzer (Coordinator)
# ═══════════════════════════════════════════════════════════════════
"""
页面分析器 - 协调器

职责：
- 使用 Playwright 打开页面（支持带登录态 storage_state）
- 提取可交互元素/表单/导航信息
- 粗略识别页面类型（LOGIN/FORM/SETTINGS/...）

额外（为“可审计的动态分析”服务）：
- 可选把动态分析产物落盘：DOM、截图、a11y snapshot
  这类产物等价于你在 Cursor/Playwright MCP 里看到的“动态结构快照”，
  用于让 CLI 链路也能复现/审阅分析过程。
"""

import re
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional, Callable, Any

from playwright.sync_api import sync_playwright, Page

from generators.page_types import PageInfo
from generators.element_extractor import ElementExtractor
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class PageAnalyzer:
    """
    页面分析器
    
    自动分析页面结构，识别：
    - 输入框（text, email, password, number等）
    - 按钮（submit, button, link-button）
    - 链接（导航、操作）
    - 表单结构
    - 页面类型
    
    使用方式:
        analyzer = PageAnalyzer()
        page_info = analyzer.analyze("https://example.com/login")
        print(page_info.page_type)  # LOGIN
        print(page_info.elements)   # [PageElement(...), ...]
    """
    
    # 页面类型识别规则
    PAGE_TYPE_RULES = {
        "LOGIN": {
            "url_patterns": [r"/login", r"/signin", r"/auth"],
            "element_patterns": ["input[type='password']", "button:has-text('Login')", "button:has-text('Sign in')"],
        },
        "REGISTER": {
            "url_patterns": [r"/register", r"/signup", r"/join"],
            "element_patterns": ["input[type='password']", "button:has-text('Register')", "button:has-text('Sign up')"],
        },
        "FORM": {
            "url_patterns": [r"/edit", r"/create", r"/new", r"/add"],
            "element_patterns": ["form", "input", "textarea", "select"],
        },
        "LIST": {
            "url_patterns": [r"/list", r"/index", r"/all"],
            "element_patterns": ["table", "[role='grid']", ".pagination", ".list-item"],
        },
        "DETAIL": {
            "url_patterns": [r"/view", r"/detail", r"/show", r"/\d+$"],
            "element_patterns": [".detail", ".view", "button:has-text('Edit')"],
        },
        "DASHBOARD": {
            "url_patterns": [r"/dashboard", r"/home", r"/overview"],
            "element_patterns": [".card", ".widget", ".chart", ".stats"],
        },
        "SETTINGS": {
            "url_patterns": [r"/settings", r"/profile", r"/preferences", r"/config"],
            "element_patterns": ["input", "select", "button:has-text('Save')"],
        },
    }
    
    def __init__(self):
        """初始化分析器"""
        self.config = ConfigManager()
        self.extractor = ElementExtractor()
    
    def analyze(
        self,
        url: str,
        auth_callback: Optional[Callable[[Page], None]] = None,
        storage_state_path: Optional[str] = None,
        artifacts_dir: Optional[str] = None,
        headless: bool = True,
        timeout_ms: int = 60000,
    ) -> PageInfo:
        """
        分析页面
        
        Args:
            url: 页面URL
            auth_callback: 认证回调函数（如果页面需要登录）
            storage_state_path: 登录态缓存文件（Playwright storage_state.json）
            headless: 是否启用无头模式
            timeout_ms: 页面导航超时（毫秒）
            
        Returns:
            PageInfo: 页面信息
        """
        logger.info(f"开始分析页面: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)

            # 从配置读取浏览器参数（避免硬编码导致页面渲染分支不同）
            viewport_cfg = self.config.get("browser.viewport", {}) or {}
            vw = int(viewport_cfg.get("width", 1920) or 1920)
            vh = int(viewport_cfg.get("height", 1080) or 1080)
            user_agent = (self.config.get("browser.user_agent", "") or "").strip()
            locale = (self.config.get("browser.locale", "") or "").strip()

            context_kwargs: Dict = {
                "viewport": {"width": vw, "height": vh},
                "ignore_https_errors": True,
            }
            if user_agent:
                context_kwargs["user_agent"] = user_agent
            if locale:
                context_kwargs["locale"] = locale
            if storage_state_path:
                sp = Path(storage_state_path)
                if sp.exists() and sp.stat().st_size > 0:
                    context_kwargs["storage_state"] = str(sp)
                else:
                    logger.warning(f"storage_state 不存在或为空: {storage_state_path}（将以未登录态分析）")

            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            
            try:
                # 如果需要认证
                if auth_callback:
                    auth_callback(page)
                
                # 导航到页面
                resp = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                page.wait_for_timeout(2000)

                # 可选：落盘动态分析产物（便于审计/复盘）
                try:
                    status = resp.status if resp is not None else None
                except Exception:
                    status = None
                self._dump_artifacts(
                    page,
                    requested_url=url,
                    final_url=(page.url or ""),
                    response_status=status,
                    artifacts_dir=artifacts_dir,
                )
                
                # 分析页面
                page_info = self._analyze_page(page, url)
                
                logger.info(f"页面分析完成: {page_info.page_type}")
                return page_info
                
            finally:
                browser.close()

    # ═══════════════════════════════════════════════════════════════
    # Artifacts (dynamic snapshot)
    # ═══════════════════════════════════════════════════════════════

    def _dump_artifacts(
        self,
        page: Page,
        *,
        requested_url: str,
        final_url: str,
        response_status: Optional[int],
        artifacts_dir: Optional[str],
    ) -> None:
        """
        将动态分析的关键证据落盘，避免“黑盒分析”。

        产物：
        - dom.html: 当前页面 DOM
        - screenshot.png: 当前页面截图
        - a11y.json: Playwright accessibility snapshot（结构化）

        注意：
        - 任何落盘失败都不应影响测试生成主流程（记录 warning 即可）。
        """
        if not artifacts_dir:
            return

        try:
            out_dir = Path(artifacts_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"创建 artifacts_dir 失败: {artifacts_dir} err={e}")
            return

        def _safe_write_text(name: str, text: str) -> None:
            try:
                (out_dir / name).write_text(text or "", encoding="utf-8")
            except Exception as e:
                logger.warning(f"写入 {name} 失败: {e}")

        def _safe_write_json(name: str, obj: Any) -> None:
            try:
                (out_dir / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                logger.warning(f"写入 {name} 失败: {e}")

        try:
            _safe_write_text("requested_url.txt", (requested_url or "") + "\n")
            _safe_write_text("final_url.txt", (final_url or "") + "\n")
            _safe_write_text("response_status.txt", (str(response_status) if response_status is not None else "") + "\n")
            _safe_write_text("title.txt", (page.title() or "") + "\n")
        except Exception:
            pass

        # DOM
        try:
            _safe_write_text("dom.html", page.content())
        except Exception as e:
            logger.warning(f"导出 DOM 失败: {e}")

        # Screenshot
        try:
            page.screenshot(path=str(out_dir / "screenshot.png"), full_page=True)
        except Exception as e:
            logger.warning(f"导出截图失败: {e}")

        # Accessibility snapshot
        try:
            a11y = page.accessibility.snapshot()
            _safe_write_json("a11y.json", a11y)
        except Exception as e:
            # 某些页面/浏览器版本可能不支持或会抛异常
            logger.warning(f"导出 a11y snapshot 失败: {e}")
    
    def _analyze_page(self, page: Page, url: str) -> PageInfo:
        """
        分析页面内容
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            PageInfo: 页面信息
        """
        # 某些页面在 networkidle 后仍可能继续跳转/重建执行上下文；title() 需要容错
        try:
            title = page.title()
        except Exception:
            title = ""
        
        # 识别页面类型
        page_type = self._detect_page_type(page, url)
        
        # 获取元素
        elements = self.extractor._get_elements(page)
        
        # 获取表单信息
        forms = self.extractor._get_forms(page)
        
        # 获取导航信息
        navigation = self.extractor._get_navigation(page)
        
        return PageInfo(
            url=url,
            title=title,
            page_type=page_type,
            elements=elements,
            forms=forms,
            navigation=navigation
        )
    
    def _detect_page_type(self, page: Page, url: str) -> str:
        """
        识别页面类型
        
        Args:
            page: Playwright页面对象
            url: 页面URL
            
        Returns:
            str: 页面类型
        """
        scores = {page_type: 0 for page_type in self.PAGE_TYPE_RULES}
        
        for page_type, rules in self.PAGE_TYPE_RULES.items():
            # URL匹配
            for pattern in rules["url_patterns"]:
                if re.search(pattern, url, re.IGNORECASE):
                    scores[page_type] += 2
            
            # 元素匹配
            for selector in rules["element_patterns"]:
                try:
                    if page.locator(selector).count() > 0:
                        scores[page_type] += 1
                except:
                    pass
        
        # 返回得分最高的类型
        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else "FORM"
    

    def to_dict(self, page_info: PageInfo) -> Dict:
        """转换为字典"""
        return {
            "url": page_info.url,
            "title": page_info.title,
            "page_type": page_info.page_type,
            "elements": [asdict(e) for e in page_info.elements],
            "forms": page_info.forms,
            "navigation": page_info.navigation,
        }
    
    def to_json(self, page_info: PageInfo, file_path: str = None) -> str:
        """
        转换为JSON
        
        Args:
            page_info: 页面信息
            file_path: 保存路径（可选）
            
        Returns:
            str: JSON字符串
        """
        data = self.to_dict(page_info)
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            logger.info(f"页面分析结果已保存: {file_path}")
        
        return json_str

