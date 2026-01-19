# ═══════════════════════════════════════════════════════════════
# Example Test Cases
# ═══════════════════════════════════════════════════════════════
"""
示例测试用例
展示如何编写测试用例的最佳实践

运行命令:
    pytest tests/test_example.py -v
    pytest tests/test_example.py -v -m P0
"""

import os
import pytest
import allure
from playwright.sync_api import Page
from pages.example_page import ExamplePage
from utils.logger import TestLogger

# 示例用例用于展示框架写法，不保证对齐真实业务站点。
# 如需运行示例用例，请显式设置环境变量：RUN_EXAMPLE_TESTS=1
if os.getenv("RUN_EXAMPLE_TESTS") != "1":
    pytest.skip("Skip scaffold example tests (set RUN_EXAMPLE_TESTS=1 to enable).", allow_module_level=True)

logger = TestLogger("test_example")


@allure.feature("Example Feature")
class TestExample:
    """
    示例测试类
    
    展示测试类的标准结构
    """
    
    # ═══════════════════════════════════════════════════════════════
    # FIXTURES
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """
        测试 setup
        
        每个测试方法执行前自动运行
        """
        self.page = page
        self.example_page = ExamplePage(page)
    
    # ═══════════════════════════════════════════════════════════════
    # P0 TESTS - 核心功能测试
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P0
    @pytest.mark.functional
    @allure.story("页面加载")
    @allure.title("TC-EX-001: 页面加载验证")
    def test_p0_page_load(self):
        """
        TC-EX-001: 页面加载验证测试
        
        测试目标: 验证示例页面能够正常加载
        测试区域: 整个页面
        测试步骤:
        1. 导航到示例页面
        2. 验证页面加载完成
        3. 验证核心元素可见
        
        预期结果:
        - 页面成功加载
        - 标题元素可见
        """
        logger.start()
        
        # 步骤1: 导航到页面
        logger.step("导航到示例页面", "Navigation")
        self.example_page.navigate()
        
        # 截图: 初始状态
        logger.screenshot("页面初始状态")
        self.example_page.take_screenshot("tc_ex_001_initial")
        
        # 步骤2: 验证页面加载
        logger.step("验证页面加载完成", "Verification")
        is_loaded = self.example_page.is_loaded()
        logger.checkpoint("页面加载完成", is_loaded)
        assert is_loaded, "页面未能正常加载"
        
        # 步骤3: 验证标题
        logger.step("验证页面标题", "Verification")
        title = self.example_page.get_page_title()
        logger.checkpoint(f"页面标题: {title}", bool(title))
        
        # 截图: 加载完成
        logger.screenshot("页面加载完成")
        self.example_page.take_screenshot("tc_ex_001_loaded")
        
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P1 TESTS - 重要功能测试
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P1
    @pytest.mark.validation
    @allure.story("输入验证")
    @allure.title("TC-EX-101: 空值输入验证")
    def test_p1_empty_input_validation(self):
        """
        TC-EX-101: 空值输入验证测试
        
        测试目标: 验证空值输入时的错误处理
        测试区域: 表单区域
        """
        logger.start()
        
        # 步骤1: 导航到页面
        logger.step("导航到示例页面", "Navigation")
        self.example_page.navigate()
        
        # 步骤2: 不填写任何内容，直接提交
        logger.step("点击登录按钮（不填写任何内容）", "Form区域")
        self.example_page.click_login()
        
        # 步骤3: 验证错误提示
        logger.step("验证错误提示显示", "Verification")
        # 注: 实际测试需要根据页面实现调整
        # has_error = self.example_page.is_error_displayed()
        # logger.checkpoint("显示错误提示", has_error)
        
        logger.screenshot("验证结果")
        self.example_page.take_screenshot("tc_ex_101_result")
        
        logger.end(success=True)
    
    @pytest.mark.P1
    @pytest.mark.boundary
    @allure.story("边界测试")
    @allure.title("TC-EX-102: 超长输入测试")
    def test_p1_long_input(self):
        """
        TC-EX-102: 超长输入测试
        
        测试目标: 验证超长输入的处理
        """
        logger.start()
        
        # 步骤1: 导航到页面
        logger.step("导航到示例页面", "Navigation")
        self.example_page.navigate()
        
        # 步骤2: 输入超长字符
        logger.step("输入超长用户名", "Form区域")
        long_username = "a" * 256
        self.example_page.fill_username(long_username)
        
        # 步骤3: 验证处理
        logger.step("验证超长输入处理", "Verification")
        # 注: 根据实际实现验证截断或错误提示
        
        logger.screenshot("超长输入结果")
        self.example_page.take_screenshot("tc_ex_102_result")
        
        logger.end(success=True)
    
    # ═══════════════════════════════════════════════════════════════
    # P2 TESTS - 一般功能测试
    # ═══════════════════════════════════════════════════════════════
    
    @pytest.mark.P2
    @pytest.mark.ui
    @allure.story("UI验证")
    @allure.title("TC-EX-201: UI样式验证")
    def test_p2_ui_styling(self):
        """
        TC-EX-201: UI样式验证测试
        
        测试目标: 验证页面UI元素的样式和布局
        """
        logger.start()
        
        # 步骤1: 导航到页面
        logger.step("导航到示例页面", "Navigation")
        self.example_page.navigate()
        
        # 步骤2: 截取完整页面
        logger.step("截取完整页面", "Screenshot")
        self.example_page.take_screenshot("tc_ex_201_fullpage", full_page=True)
        
        # 步骤3: 验证元素可见性
        logger.step("验证核心元素可见", "Verification")
        is_loaded = self.example_page.is_loaded()
        logger.checkpoint("页面元素可见", is_loaded)
        
        logger.end(success=True)
    
    @pytest.mark.P2
    @pytest.mark.ui
    @allure.story("UI验证")
    @allure.title("TC-EX-202: 键盘导航测试")
    def test_p2_keyboard_navigation(self):
        """
        TC-EX-202: 键盘导航测试
        
        测试目标: 验证Tab键导航功能
        """
        logger.start()
        
        # 步骤1: 导航到页面
        logger.step("导航到示例页面", "Navigation")
        self.example_page.navigate()
        
        # 步骤2: 使用Tab键导航
        logger.step("使用Tab键导航", "Keyboard")
        self.example_page.utils.press_key("Tab")
        self.example_page.wait(500)
        
        self.example_page.utils.press_key("Tab")
        self.example_page.wait(500)
        
        # 步骤3: 截图
        logger.screenshot("Tab导航后")
        self.example_page.take_screenshot("tc_ex_202_tab")
        
        logger.end(success=True)

