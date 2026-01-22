# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Pytest Fixtures
# ═══════════════════════════════════════════════════════════════
"""
通用测试 fixtures - 提供测试所需的各种资源
"""

import pytest
import os
from pathlib import Path
from playwright.sync_api import Page, BrowserContext
from utils.config import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)
config = ConfigManager()


# ═══════════════════════════════════════════════════════════════
# BROWSER CONFIGURATION
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """配置浏览器上下文参数"""
    browser_config = config.get_browser_config()
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "viewport": {
            "width": browser_config.get("viewport_width", 1920),
            "height": browser_config.get("viewport_height", 1080)
        },
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """配置浏览器启动参数"""
    browser_config = config.get_browser_config()
    args = config.get("browser.args", [])
    return {
        **browser_type_launch_args,
        "headless": browser_config.get("headless", True),
        "slow_mo": browser_config.get("slow_mo", 0),
        "timeout": 60000,
        "args": args if args else [
            "--disable-web-security",
            "--ignore-certificate-errors",
            "--allow-insecure-localhost",
            "--disable-gpu",
            "--no-sandbox",
        ],
    }


# ═══════════════════════════════════════════════════════════════
# PAGE FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def test_page(page: Page) -> Page:
    """测试页面 fixture - 每个测试独立的页面实例"""
    logger.info("创建测试页面")
    yield page
    logger.info("关闭测试页面")


@pytest.fixture(scope="class")
def shared_page(browser) -> Page:
    """共享页面 fixture - 测试类内共享"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    logger.info("创建共享页面")
    yield page
    logger.info("关闭共享页面")
    context.close()


# ═══════════════════════════════════════════════════════════════
# SERVICE URL FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def frontend_url() -> str:
    """获取前端服务 URL"""
    return config.get_service_url("frontend")


@pytest.fixture(scope="session")
def backend_url() -> str:
    """获取后端服务 URL"""
    return config.get_service_url("backend")


@pytest.fixture(scope="session")
def current_environment() -> str:
    """获取当前环境名称"""
    return config.get_environment()


# ═══════════════════════════════════════════════════════════════
# TEST DATA FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def test_config():
    """测试配置 fixture"""
    return config


@pytest.fixture(scope="session")
def test_account():
    """测试账号 fixture - 从账号池获取可用账号"""
    return config.get_test_account()


@pytest.fixture(scope="session")
def accounts_pool():
    """测试账号池 fixture - 获取完整账号池"""
    data = config.load_test_data("accounts")
    if data and "test_account_pool" in data:
        return data["test_account_pool"]
    return []


@pytest.fixture(scope="function")
def test_data():
    """
    通用测试数据加载器 fixture
    
    使用方式:
        def test_xxx(test_data):
            orders = test_data("orders")
            products = test_data("products")
    """
    def _load_data(name: str):
        return config.load_test_data(name)
    return _load_data


# ═══════════════════════════════════════════════════════════════
# LOGIN FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def logged_in_page(page: Page, test_account) -> Page:
    """已登录的页面 fixture - 自动执行登录流程"""
    from pages.login_page import LoginPage
    
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(
        username=test_account["username"],
        password=test_account["password"]
    )
    logger.info(f"已登录账号: {test_account['username']}")
    yield page


# ═══════════════════════════════════════════════════════════════
# Step2 preferred fixtures (rule-compatible aliases)
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
def auth_page(logged_in_page: Page) -> Page:
    """规则推荐：已登录页面（与生成器一致命名）"""
    return logged_in_page


@pytest.fixture(scope="function")
def unauth_page(browser) -> Page:
    """未登录页面：用于鉴权/跳转登录等 security 用例"""
    context: BrowserContext = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    page = context.new_page()
    yield page
    context.close()


# ═══════════════════════════════════════════════════════════════
# SERVICE CHECK FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def service_checker():
    """服务检查器 fixture"""
    from utils.service_checker import ServiceChecker
    return ServiceChecker()


@pytest.fixture(scope="session", autouse=False)
def ensure_services_running(service_checker):
    """
    确保服务运行 fixture（非自动）
    
    使用方式:
        @pytest.mark.usefixtures("ensure_services_running")
        class TestXxx:
            pass
    """
    if not service_checker.is_enabled():
        logger.info("服务健康检查已禁用")
        return
    
    report = service_checker.get_status_report()
    print(report)
    
    results = service_checker.check_all_services()
    failed = [name for name, (ok, _) in results.items() if not ok]
    
    if failed:
        pytest.skip(f"服务不可用: {', '.join(failed)}")


# ═══════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """设置测试环境 - session 级别"""
    directories = ["reports", "screenshots", "allure-results"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("🚀 测试环境初始化完成")
    logger.info(f"   环境: {config.get_environment()}")
    logger.info(f"   前端: {config.get_service_url('frontend')}")
    logger.info(f"   后端: {config.get_service_url('backend')}")
    logger.info("=" * 60)
    
    yield
    
    logger.info("=" * 60)
    logger.info("🏁 测试执行完成")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# TEST LOGGING
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(scope="function", autouse=True)
def log_test_info(request):
    """自动记录测试信息"""
    test_name = request.node.name
    test_file = request.node.fspath.basename if hasattr(request.node, 'fspath') else ""
    
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"▶️  开始测试: {test_file}::{test_name}")
    logger.info("=" * 60)
    
    yield
    
    logger.info(f"⏹️  结束测试: {test_name}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# SCREENSHOT ON FAILURE
# ═══════════════════════════════════════════════════════════════

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """测试报告钩子 - 失败时自动截图"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="function")
def screenshot_on_failure(request, page: Page):
    """失败时自动截图 fixture"""
    yield
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)
        
        test_name = request.node.nodeid.replace("/", "_").replace("::", "_")
        screenshot_path = screenshot_dir / f"{test_name}_failure.png"
        
        try:
            page.screenshot(path=str(screenshot_path))
            logger.info(f"📸 失败截图已保存: {screenshot_path}")
        except Exception as e:
            logger.error(f"截图失败: {e}")
