# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Base Page
# ═══════════════════════════════════════════════════════════════
"""
BasePage - 所有页面对象的抽象基类
提供统一的页面操作接口，子类只需关注业务逻辑
"""

from playwright.sync_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from core.page_utils import PageUtils
from utils.logger import get_logger
from utils.config import ConfigManager

logger = get_logger(__name__)


class BasePage(ABC):
    """
    页面对象基类 - 模板方法模式
    
    使用方式:
        class LoginPage(BasePage):
            URL = "/login"
            
            # 元素选择器
            USERNAME_INPUT = "#username"
            PASSWORD_INPUT = "#password"
            SUBMIT_BUTTON = "button[type='submit']"
            
            def navigate(self):
                self.goto(self.URL)
            
            def is_loaded(self) -> bool:
                return self.is_visible(self.USERNAME_INPUT)
            
            def login(self, username: str, password: str):
                self.fill(self.USERNAME_INPUT, username)
                self.fill(self.PASSWORD_INPUT, password)
                self.click(self.SUBMIT_BUTTON)
    """
    
    # 子类可覆盖的类属性
    URL: str = "/"
    page_loaded_indicator: str = "body"
    
    def __init__(self, page: Page):
        """
        初始化页面对象
        
        Args:
            page: Playwright Page对象
        """
        self.page = page
        self.utils = PageUtils(page)
        self.config = ConfigManager()
        self.base_url = self.config.get_base_url()
        
        logger.debug(f"初始化页面对象: {self.__class__.__name__}")
    
    # ═══════════════════════════════════════════════════════════════
    # ABSTRACT METHODS - 子类必须实现
    # ═══════════════════════════════════════════════════════════════
    
    @abstractmethod
    def navigate(self) -> None:
        """导航到页面 - 子类必须实现"""
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """检查页面是否加载完成 - 子类必须实现"""
        pass
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def goto(self, path: str = "", wait_for_load: bool = True) -> None:
        """
        导航到指定路径
        
        Args:
            path: 相对路径或完整URL
            wait_for_load: 是否等待页面加载完成
        """
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        logger.info(f"导航到: {url}")
        # 外部站点偶发 load 事件迟迟不触发，默认 30s 容易超时；这里更稳地等待 domcontentloaded，
        # 并使用更保守的 timeout（>=60s）。
        try:
            cfg_timeout = int(self.config.get("browser.timeout", 30000) or 30000)
        except Exception:
            cfg_timeout = 30000
        timeout_ms = max(cfg_timeout, 60000)
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except PlaywrightTimeoutError:
            # 某些 SPA/风控场景下 domcontentloaded 可能迟迟不触发；降级到更早的导航阶段再继续后续等待。
            logger.warning(f"goto domcontentloaded 超时，降级到 wait_until=commit 重试: {url}")
            self.page.goto(url, wait_until="commit", timeout=timeout_ms)
        
        if wait_for_load:
            self.wait_for_page_load()
    
    def wait_for_page_load(self, timeout: int = 30000) -> None:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待页面加载: {self.__class__.__name__}")
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        
        # 等待页面标识元素
        if self.page_loaded_indicator:
            try:
                self.page.wait_for_selector(
                    self.page_loaded_indicator, 
                    state="visible", 
                    timeout=timeout
                )
            except Exception as e:
                logger.warning(f"页面加载指示器未找到: {self.page_loaded_indicator}")
    
    def refresh(self) -> None:
        """刷新页面"""
        logger.info("刷新页面")
        self.page.reload(wait_until='networkidle')
        self.wait_for_page_load()
    
    def go_back(self) -> None:
        """返回上一页"""
        logger.info("返回上一页")
        self.page.go_back()
        self.wait_for_page_load()
    
    def go_forward(self) -> None:
        """前进到下一页"""
        logger.info("前进到下一页")
        self.page.go_forward()
        self.wait_for_page_load()
    
    # ═══════════════════════════════════════════════════════════════
    # ELEMENT INTERACTION METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def click(self, selector: str, timeout: int = 10000) -> None:
        """
        点击元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"点击元素: {selector}")
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 10000) -> None:
        """
        填写输入框
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"填写输入框: {selector} = {value}")
        self.page.wait_for_selector(selector, state="visible", timeout=timeout)
        self.page.fill(selector, value, timeout=timeout)
    
    def clear_and_fill(self, selector: str, value: str, timeout: int = 10000) -> None:
        """
        清空并填写输入框
        
        Args:
            selector: 元素选择器
            value: 要填写的值
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"清空并填写: {selector} = {value}")
        element = self.page.locator(selector)
        element.clear()
        element.fill(value)
    
    def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """
        逐字符输入文本（模拟真实输入）
        
        Args:
            selector: 元素选择器
            text: 要输入的文本
            delay: 字符间延迟(毫秒)
        """
        logger.debug(f"逐字符输入: {selector}")
        self.page.locator(selector).type(text, delay=delay)
    
    def select_option(self, selector: str, value: str) -> None:
        """
        选择下拉框选项
        
        Args:
            selector: 元素选择器
            value: 选项值
        """
        logger.debug(f"选择选项: {selector} = {value}")
        self.page.select_option(selector, value)
    
    def check(self, selector: str) -> None:
        """勾选复选框"""
        logger.debug(f"勾选: {selector}")
        self.page.check(selector)
    
    def uncheck(self, selector: str) -> None:
        """取消勾选复选框"""
        logger.debug(f"取消勾选: {selector}")
        self.page.uncheck(selector)
    
    # ═══════════════════════════════════════════════════════════════
    # ELEMENT STATE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def is_visible(self, selector: str, timeout: int = 5000) -> bool:
        """
        检查元素是否可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 元素是否可见
        """
        try:
            return self.page.is_visible(selector, timeout=timeout)
        except Exception:
            return False
    
    def is_enabled(self, selector: str) -> bool:
        """检查元素是否启用"""
        return self.page.is_enabled(selector)
    
    def is_checked(self, selector: str) -> bool:
        """检查复选框是否被勾选"""
        return self.page.is_checked(selector)
    
    def get_text(self, selector: str, timeout: int = 10000) -> Optional[str]:
        """
        获取元素文本
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            str: 元素文本
        """
        try:
            return self.page.text_content(selector, timeout=timeout)
        except Exception:
            return None
    
    def get_input_value(self, selector: str) -> str:
        """
        获取输入框的值
        
        Args:
            selector: 元素选择器
            
        Returns:
            str: 输入框的值
        """
        return self.page.input_value(selector)
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            selector: 元素选择器
            attribute: 属性名
            
        Returns:
            str: 属性值
        """
        return self.page.get_attribute(selector, attribute)
    
    # ═══════════════════════════════════════════════════════════════
    # WAIT METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def wait_for_element(self, selector: str, state: str = "visible", timeout: int = 10000) -> None:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            state: 状态（visible, attached, detached, hidden）
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待元素: {selector} ({state})")
        self.page.wait_for_selector(selector, state=state, timeout=timeout)
    
    def wait_for_url(self, url_pattern: str, timeout: int = 10000) -> None:
        """
        等待URL匹配
        
        Args:
            url_pattern: URL模式（支持正则）
            timeout: 超时时间(毫秒)
        """
        logger.debug(f"等待URL匹配: {url_pattern}")
        self.page.wait_for_url(url_pattern, timeout=timeout)
    
    def wait(self, milliseconds: int) -> None:
        """
        等待指定时间
        
        Args:
            milliseconds: 等待时间(毫秒)
        """
        self.page.wait_for_timeout(milliseconds)
    
    # ═══════════════════════════════════════════════════════════════
    # PAGE INFO METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_url(self) -> str:
        """获取当前URL"""
        return self.page.url
    
    def get_title(self) -> str:
        """获取页面标题"""
        return self.page.title()
    
    # ═══════════════════════════════════════════════════════════════
    # SCREENSHOT METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def take_screenshot(self, name: str, full_page: bool = False) -> bytes:
        """
        截取屏幕截图
        
        Args:
            name: 截图名称（无需扩展名）
            full_page: 是否截取整页
            
        Returns:
            bytes: 截图数据
        """
        return self.utils.take_screenshot(
            file_path=f"screenshots/{name}.png",
            full_page=full_page,
            attach_to_allure=True,
            step_name=name
        )
    
    # ═══════════════════════════════════════════════════════════════
    # ASSERTION HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def assert_visible(self, selector: str, message: str = None) -> None:
        """断言元素可见"""
        expect(self.page.locator(selector)).to_be_visible()
        logger.info(f"✓ 断言通过: 元素可见 - {selector}")
    
    def assert_text(self, selector: str, expected_text: str) -> None:
        """断言元素文本"""
        expect(self.page.locator(selector)).to_have_text(expected_text)
        logger.info(f"✓ 断言通过: 文本匹配 - {expected_text}")
    
    def assert_url_contains(self, text: str) -> None:
        """断言URL包含指定文本"""
        expect(self.page).to_have_url(f"*{text}*")
        logger.info(f"✓ 断言通过: URL包含 - {text}")


class BaseDialog(BasePage):
    """
    对话框基类
    
    使用方式:
        class ConfirmDialog(BaseDialog):
            DIALOG_SELECTOR = ".modal-dialog"
            CONFIRM_BUTTON = "button.confirm"
            CANCEL_BUTTON = "button.cancel"
            
            def confirm(self):
                self.click(self.CONFIRM_BUTTON)
            
            def cancel(self):
                self.click(self.CANCEL_BUTTON)
    """
    
    DIALOG_SELECTOR: str = ".dialog"
    
    def navigate(self) -> None:
        """对话框不需要导航"""
        pass
    
    def is_loaded(self) -> bool:
        """检查对话框是否显示"""
        return self.is_visible(self.DIALOG_SELECTOR)
    
    def close(self) -> None:
        """关闭对话框"""
        # 尝试点击关闭按钮
        close_selectors = [
            f"{self.DIALOG_SELECTOR} .close",
            f"{self.DIALOG_SELECTOR} [aria-label='close']",
            f"{self.DIALOG_SELECTOR} button:has-text('Close')",
            f"{self.DIALOG_SELECTOR} button:has-text('Cancel')",
        ]
        
        for selector in close_selectors:
            if self.is_visible(selector, timeout=1000):
                self.click(selector)
                return
        
        # 按ESC键关闭
        self.page.keyboard.press("Escape")

