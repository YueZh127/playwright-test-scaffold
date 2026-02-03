# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Logger
# ═══════════════════════════════════════════════════════════════
"""
日志系统 - 提供统一的日志记录功能
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def get_logger(name: str = __name__) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_dir = Path("reports")
    log_dir.mkdir(exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = log_dir / f"test_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


class TestLogger:
    """
    测试日志类 - 提供结构化的测试日志记录
    
    使用方式:
        logger = TestLogger("test_login")
        logger.step("点击登录按钮")
        logger.checkpoint("验证登录成功")
    """
    
    def __init__(self, test_name: str):
        """
        初始化测试日志
        
        Args:
            test_name: 测试名称
        """
        self.logger = get_logger(test_name)
        self.test_name = test_name
        self.step_count = 0

    # pytest 发现规则：以 Test* 命名且带 __init__ 的类会触发收集警告；
    # 这里显式标记为“非测试类”，避免污染测试输出。
    __test__ = False
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(f"❌ {message}")
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(f"⚠️ {message}")
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)
    
    def step(self, description: str, region: str = None) -> None:
        """
        记录测试步骤
        
        Args:
            description: 步骤描述
            region: 页面区域（可选）
        """
        self.step_count += 1
        region_str = f"[{region}] " if region else ""
        self.logger.info(f"步骤{self.step_count}: {region_str}{description}")
    
    def checkpoint(self, description: str, passed: bool = True) -> None:
        """
        记录检查点
        
        Args:
            description: 检查点描述
            passed: 是否通过
        """
        status = "✓" if passed else "✗"
        self.logger.info(f"   {status} 检查点: {description}")
    
    def screenshot(self, description: str) -> None:
        """
        记录截图操作
        
        Args:
            description: 截图描述
        """
        self.logger.info(f"📸 截图: {description}")
    
    def start(self) -> None:
        """记录测试开始"""
        self.logger.info("=" * 60)
        self.logger.info(f"开始执行: {self.test_name}")
        self.logger.info("=" * 60)
    
    def end(self, success: bool = True) -> None:
        """
        记录测试结束
        
        Args:
            success: 测试是否成功
        """
        status = "✅ 通过" if success else "❌ 失败"
        self.logger.info(f"{status} - {self.test_name}")
        self.logger.info("=" * 60)

