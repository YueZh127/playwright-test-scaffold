# Playwright Test Scaffold - Architecture

> AI 驱动的自动化测试脚手架 - 架构文档

## 使用方式

**本项目只通过 AI 对话交互**，用自然语言描述需求，AI 自动完成：
- 检查服务状态
- **分析 GitHub 代码** - 根据页面 URL 查找对应代码，提取功能点
- 生成 Page Object
- 生成测试用例（覆盖所有分析出的功能点）
- 执行测试
- 查看报告

## 页面功能分析流程

```
页面 URL → 推断代码位置 → DeepWiki 查询代码 → 提取功能点 → 生成测试
```

| 分析维度 | 关注点 |
|----------|--------|
| 表单字段 | 输入框、下拉框、必填/可选 |
| 验证规则 | 正则、长度限制、格式要求 |
| API 接口 | 请求方法、参数、响应 |
| 业务逻辑 | 条件判断、流程分支 |

## 目录结构

```
playwright-test-scaffold/
├── conftest.py                   # pytest 根配置
├── pytest.ini                    # pytest 配置
├── requirements.txt              # 依赖清单
│
├── config/
│   └── project.yaml              # 项目配置中心（仓库/服务/数据）
│
├── core/                         # 核心框架层
│   ├── __init__.py
│   ├── base_page.py              # Page Object 基类
│   ├── fixtures.py               # pytest fixtures
│   └── page_utils.py             # 页面工具函数
│
├── generators/                   # 代码生成引擎
│   ├── __init__.py
│   ├── utils.py                  # 公共工具
│   ├── page_analyzer.py          # 页面分析器
│   ├── test_plan_generator.py    # 测试计划生成
│   └── test_code_generator.py    # 代码生成
│
├── utils/                        # 工具模块
│   ├── __init__.py
│   ├── config.py                 # 配置管理器
│   ├── logger.py                 # 日志系统
│   └── service_checker.py        # 🆕 服务健康检查
│
├── pages/                        # Page Object 实现层
│   └── *.py
│
├── tests/                        # 测试用例层
│   ├── test_*.py
│   └── ext/                      # 外部站点/集成类测试（按站点与页面分目录）
│       ├── godgpt_ui_testnet_aelf_dev_login/
│       ├── godgpt_ui_testnet_aelf_dev_home/
│       └── godgpt_compare/       # 🆕 生产 vs 测试环境对比测试（同问题对比 AI 回复）
│
├── test-data/                    # 测试数据
│   └── test_account_pool.json    # 测试账号池
│
├── docs/                         # 文档
│   ├── architecture.md           # 本文档
│   └── test-plans/               # 生成的测试计划
│
├── reports/                      # 测试报告
├── screenshots/                  # 截图
└── allure-results/               # Allure 数据
```

## 模块职责

### `config/project.yaml` (项目配置中心)

统一管理所有项目配置：

| 配置项 | 用途 |
|--------|------|
| `repositories` | GitHub 仓库地址（前端/后端） |
| `environments` | 多环境服务地址配置 |
| `test_data` | 测试数据文件路径 |
| `health_check` | 服务健康检查配置 |
| `browser` | 浏览器配置 |

### `utils/config.py` (配置管理器)

| 方法 | 功能 |
|------|------|
| `get_repository(name)` | 获取仓库配置 |
| `get_service_url(name)` | 获取当前环境的服务 URL |
| `get_health_check_url(name)` | 获取健康检查 URL |
| `get_test_data_path(name)` | 获取测试数据路径 |
| `load_test_data(name)` | 加载测试数据 |
| `get_all_services()` | 获取所有服务配置 |

### `utils/service_checker.py` (服务健康检查)

| 方法 | 功能 |
|------|------|
| `check_service(name)` | 检查单个服务 |
| `check_all_services()` | 检查所有服务 |
| `wait_for_service(name)` | 等待服务启动 |
| `get_status_report()` | 获取格式化状态报告 |

### `core/fixtures.py` (Pytest Fixtures)

| Fixture | 功能 |
|---------|------|
| `frontend_url` | 前端服务 URL |
| `backend_url` | 后端服务 URL |
| `test_account` | 测试账号 |
| `test_data` | 通用测试数据加载器 |
| `service_checker` | 服务检查器 |
| `ensure_services_running` | 确保服务运行 |

### `generators/page_analyzer.py` (页面分析器)

- 使用 Playwright 获取页面快照
- 自动识别页面类型 (LOGIN, FORM, LIST...)
- 提取可交互元素

### `generators/test_code_generator.py` (代码生成)

- 输入: `PageInfo`
- 输出: Page Object + 测试用例 + 测试数据

### `core/base_page.py` (Page Object 基类)

- 模板方法模式
- 强制子类实现 `navigate()` 和 `is_loaded()`

## 设计原则

1. **AI 优先** - 所有操作通过自然语言对话完成
2. **配置集中** - 所有配置统一在 `project.yaml`
3. **服务感知** - 测试前自动检查服务状态
4. **多环境支持** - 支持 dev/staging/production 多套配置
5. **DRY** - 公共逻辑提取复用

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-01-29 | 新增 `tests/ext/godgpt_compare/`：生产 vs 测试环境对比测试（双浏览器登录与回复差分产物） |
| 2025-12-15 | 新增服务健康检查模块 |
| 2025-12-15 | 扩展配置结构（仓库/多环境/测试数据） |
| 2025-12-15 | 移除 CLI，改为纯 AI 对话驱动 |
| 2025-12-09 | 创建 `generators/utils.py`，重构生成器 |
