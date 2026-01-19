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
import allure
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
        # 与 PageAnalyzer 保持一致：固定 UA/locale，避免 i18n 文案/渲染分支不一致导致断言不稳定
        "user_agent": browser_config.get("user_agent") or browser_context_args.get("user_agent"),
        "locale": browser_config.get("locale") or browser_context_args.get("locale"),
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
# COMPAT FIXTURES (GENERATED SUITES)
# ═══════════════════════════════════════════════════════════════
#
# 说明：
# - 新版生成器/规则文件会建议使用 `auth_page` / `unauth_page`。
# - 但本仓库历史上存在 `logged_in_page` 等命名差异，导致生成用例在部分环境中找不到 fixture。
# - 这里提供兼容层，保证“现有测试用例能跑通”。
#
# 安全约束：
# - 这里不落盘、不硬编码任何密码/凭证。
# - 若后续需要真正的登录态，应实现专用 LoginPage + storage_state 方案（再替换此兼容实现）。


@pytest.fixture(scope="function")
def unauth_page(page: Page) -> Page:
    """未登录页面（兼容 fixture）"""
    return page


@pytest.fixture(scope="function")
def auth_page(page: Page) -> Page:
    """
    已登录页面（兼容 fixture）。

    当前默认返回 `page`，用于让 suite 至少可执行并暴露真实 UI/定位问题。
    若目标页面确实需要登录态，请改用：
    - `logged_in_page`（前提：实现并维护 `pages/login_page.py`）
    - 或引入 storage_state（推荐）
    """
    return page


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
# ALLURE - AUTO SCREENSHOT
# ═══════════════════════════════════════════════════════════════
#
# 说明：
# - 用户希望 Allure 报告中每个用例都有截图。
# - 仅依赖测试代码手动调用 take_screenshot() 往往会导致“全绿但没截图”的体验。
# - 因此这里提供 function 级 autouse：每条用例结束都截一张并 attach 到 Allure。
#
# 控制开关：
# - ALLURE_AUTO_SCREENSHOT=0 可关闭（默认开启）


@pytest.fixture(scope="function", autouse=True)
def allure_auto_screenshot(request, page: Page):
    """每个用例结束自动截图并附加到 Allure。"""
    yield

    if os.getenv("ALLURE_AUTO_SCREENSHOT", "1").strip() == "0":
        return

    try:
        screenshot_bytes = page.screenshot(full_page=True)
        name = request.node.nodeid.replace("/", "_").replace("::", "_")
        allure.attach(
            screenshot_bytes,
            name=f"{name}_final",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as e:
        logger.warning(f"Allure 自动截图失败（忽略，不影响用例结果）: {e}")


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
