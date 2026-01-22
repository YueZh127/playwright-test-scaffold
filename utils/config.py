# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Configuration Manager
# ═══════════════════════════════════════════════════════════════
"""
配置管理器 - 统一管理项目配置
支持 YAML 配置文件、环境变量、多环境服务地址、测试数据
"""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()


class ConfigManager:
    """
    配置管理器 - 单例模式
    
    配置优先级（从高到低）:
    1. 环境变量
    2. config/project.yaml
    3. 默认值
    """
    
    _instance = None
    _config_data = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "config/project.yaml"):
        if ConfigManager._config_data is None:
            ConfigManager._config_data = self._load_config(config_file)
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"⚠️ 配置文件不存在: {config_file}，使用默认配置")
            return self._get_default_config()
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "project": {"name": "Test Project", "version": "1.0.0"},
            "repositories": {"frontend": {"url": ""}, "backend": {"url": ""}},
            "environments": {
                "default": "dev",
                "dev": {
                    "frontend": {"url": "http://localhost:3000", "health_check": "/"},
                    "backend": {"url": "http://localhost:8080", "health_check": "/api/health"}
                }
            },
            "test_data": {"accounts": {"path": "test-data/test_account_pool.json"}},
            "health_check": {"enabled": True, "timeout": 10, "retry_count": 3, "retry_interval": 2},
            "browser": {"headless": True, "slow_mo": 0, "timeout": 30000, "viewport": {"width": 1920, "height": 1080}},
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        keys = key.split('.')
        value = self._config_data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def _convert_value(self, value: str) -> Any:
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        elif value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value
    
    # ═══════════════════════════════════════════════════════════════
    # ENVIRONMENT METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_environment(self) -> str:
        """获取当前环境名称"""
        return os.getenv("TEST_ENV", self.get("environments.default", "dev"))
    
    def get_available_environments(self) -> List[str]:
        """获取所有可用环境列表"""
        envs = self.get("environments", {})
        return [k for k in envs.keys() if k != "default"]
    
    # ═══════════════════════════════════════════════════════════════
    # REPOSITORY METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_repository(self, name: str) -> Dict[str, str]:
        """
        获取仓库配置
        
        Args:
            name: 仓库名称 (frontend/backend)
        """
        return self.get(f"repositories.{name}", {"url": "", "branch": "main"})
    
    def get_repository_url(self, name: str) -> str:
        """获取仓库 URL"""
        return self.get_repository(name).get("url", "")
    
    # ═══════════════════════════════════════════════════════════════
    # SERVICE METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_service_url(self, name: str) -> str:
        """
        获取当前环境的服务 URL
        
        Args:
            name: 服务名称 (frontend/backend)
        """
        env = self.get_environment()
        return self.get(f"environments.{env}.{name}.url", "")
    
    def get_health_check_path(self, name: str) -> str:
        """获取服务的健康检查路径"""
        env = self.get_environment()
        return self.get(f"environments.{env}.{name}.health_check", "/")
    
    def get_health_check_url(self, name: str) -> str:
        """获取完整的健康检查 URL"""
        base_url = self.get_service_url(name)
        path = self.get_health_check_path(name)
        if not base_url:
            return ""
        return f"{base_url.rstrip('/')}{path}"
    
    def get_all_services(self) -> Dict[str, Dict[str, str]]:
        """获取当前环境的所有服务配置"""
        env = self.get_environment()
        env_config = self.get(f"environments.{env}", {})
        services = {}
        for key, value in env_config.items():
            if isinstance(value, dict) and "url" in value:
                services[key] = value
        return services
    
    # ═══════════════════════════════════════════════════════════════
    # TEST DATA METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_test_data_path(self, name: str) -> str:
        """
        获取测试数据文件路径
        
        Args:
            name: 数据类型名称 (accounts/orders/products...)
        """
        return self.get(f"test_data.{name}.path", "")
    
    def load_test_data(self, name: str) -> Any:
        """
        加载测试数据
        
        Args:
            name: 数据类型名称
        """
        path = self.get_test_data_path(name)
        if not path:
            return None
        
        file_path = Path(path)
        if not file_path.exists():
            print(f"⚠️ 测试数据文件不存在: {path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载测试数据失败: {e}")
            return None
    
    def get_available_test_data(self) -> List[str]:
        """获取所有可用的测试数据类型"""
        test_data = self.get("test_data", {})
        return list(test_data.keys())
    
    # ═══════════════════════════════════════════════════════════════
    # HEALTH CHECK CONFIG
    # ═══════════════════════════════════════════════════════════════
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """获取健康检查配置"""
        return {
            "enabled": self.get("health_check.enabled", True),
            "timeout": self.get("health_check.timeout", 10),
            "retry_count": self.get("health_check.retry_count", 3),
            "retry_interval": self.get("health_check.retry_interval", 2),
        }
    
    # ═══════════════════════════════════════════════════════════════
    # LEGACY METHODS (保持兼容)
    # ═══════════════════════════════════════════════════════════════
    
    def get_base_url(self) -> str:
        """获取前端 URL（兼容旧接口）"""
        return self.get_service_url("frontend") or "http://localhost:3000"
    
    def get_api_url(self) -> str:
        """获取后端 API URL（兼容旧接口）"""
        return self.get_service_url("backend") or "http://localhost:8080"
    
    def get_browser_config(self) -> Dict[str, Any]:
        """获取浏览器配置"""
        return {
            "headless": self.get("browser.headless", True),
            "slow_mo": self.get("browser.slow_mo", 0),
            "timeout": self.get("browser.timeout", 30000),
            "viewport_width": self.get("browser.viewport.width", 1920),
            "viewport_height": self.get("browser.viewport.height", 1080),
            "type": self.get("browser.type", "chromium"),
        }
    
    def get_test_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return {
            "retry_count": self.get("test.retry_count", 2),
            "implicit_wait": self.get("test.implicit_wait", 10),
            "screenshot_on_failure": self.get("test.screenshot_on_failure", True),
            "video_recording": self.get("test.video_recording", False),
        }
    
    def get_test_account(self, account_type: str = "default") -> Dict[str, str]:
        """获取测试账号（兼容旧接口）"""
        # 支持固定账号选择（不把密码写入任何代码/文件；仅选择账号池中的记录）
        preferred_username = (os.getenv("TEST_ACCOUNT_USERNAME") or "").strip()
        preferred_email = (os.getenv("TEST_ACCOUNT_EMAIL") or "").strip()
        # 环境级默认：Aevatar 管理台测试环境优先使用 developer 账号（避免随机拿到不可登录账号）
        if not preferred_username and not preferred_email:
            try:
                if self.get_environment() == "aevatar_test":
                    preferred_username = "developer"
            except Exception:
                pass

        # 优先从账号池加载
        accounts_data = self.load_test_data("accounts")
        if accounts_data and "test_account_pool" in accounts_data:
            pool = accounts_data["test_account_pool"]
            # 1) 若指定了 preferred username/email：优先命中该账号（且必须可用）
            if preferred_username or preferred_email:
                for account in pool:
                    if account.get("is_locked", False) or account.get("in_use", False):
                        continue
                    if preferred_username and str(account.get("username", "")).strip() == preferred_username:
                        return account
                    if preferred_email and str(account.get("email", "")).strip() == preferred_email:
                        return account
            # 返回第一个未锁定且未使用的账号
            for account in pool:
                if not account.get("is_locked", False) and not account.get("in_use", False):
                    return account
            # 如果没有可用账号，返回第一个未锁定的
            for account in pool:
                if not account.get("is_locked", False):
                    return account
        
        return {"username": "testuser", "email": "test@example.com", "password": "TestPass123!"}
