# Aevatar Management Test - SubscriptionFeatures（功能特性）测试计划（Step1 / MCP-first）

## 基本信息

- **目标页面**: `https://management-test.aevatar.ai/SubscriptionFeatures`
- **是否需要登录态**: 是（未登录访问会进入登录页流程）
- **登录页证据（可见内容）**：访问该 URL 会出现 `Login / Username or email address / Password / Remember me` 等字段  
  参考页面：[`https://management-test.aevatar.ai/SubscriptionFeatures`](https://management-test.aevatar.ai/SubscriptionFeatures)

## 账号来源（强制）

- **账号池文件**: `config/project.yaml -> test_data.accounts.path`
- **账号**: `developer`
- **密码**: **禁止写入任何计划/文件**；执行期由账号池/fixture 读取

## 证据链（必须落盘）

- **证据目录**: `docs/test-plans/artifacts/aevatar_management_test_subscription_features/`
- **必须文件**（由 Cursor Playwright MCP 导出并覆盖写入）：
  - `visible.html`
  - `visible.txt`
  - `metadata.json`
  - `page.png`（建议仅本地保存，不提交仓库）

## 页面功能点（以 ABP 后端为真理源，避免猜阈值）

> 本模块为 ABP 管理端 Razor Pages：`/SubscriptionFeatures`。

### 列表页能力（待 MCP 证据链补齐具体控件映射）

- **筛选**：按 FeatureType（TypeFilter）
- **列表展示**：NameKey / DescriptionKey / FeatureType / DisplayOrder
- **操作**：Create / Edit / Delete
- **重排序（条件）**：具备权限时支持拖拽并调用 reorder API

### 创建功能（字段与校验：真理源）

- **Feature.NameKey**（NameKey）
  - `[Required]`
  - `[MaxLength(256)]`
- **Feature.DescriptionKey**（DescriptionKey）
  - `[MaxLength(256)]`
- **Feature.Type**（FeatureType）
  - `[Required]`
- **Feature.DisplayOrder**（DisplayOrder）
  - int（默认 0）

## 用例设计

### P0 - 核心

- **TC-P0-FEAT-001 页面加载**
  - 前置：已登录
  - 步骤：进入 `/SubscriptionFeatures`
  - 断言：页面标题/列表区域可见；存在 Create 入口

- **TC-P0-FEAT-002 创建功能成功 + 删除回滚（可重复执行）**
  - 数据：`qa_feature_<ts>`（满足校验）
  - 断言：列表出现该条；删除后列表不再存在

### P1 - 校验矩阵 / 异常

- **TC-P1-FEAT-001 必填：NameKey 为空应失败**
  - 断言：可见错误证据（aria-invalid/inline error/toast 任一）
  - 断言：列表不应新增记录

- **TC-P1-FEAT-002 必填：Type 为空应失败**

- **TC-P1-FEAT-003 边界：NameKey 长度 257 应失败，256 可接受**

- **TC-P1-FEAT-004 创建后取消不保存**
  - 步骤：打开创建弹窗→填写→Cancel
  - 断言：列表不新增该条

- **TC-P1-FEAT-005 API 失败处理（网络失败/超时）**
  - 断言：用户得到可见反馈；页面不崩溃；不产生脏数据

### P2 - 体验/可用性

- **TC-P2-FEAT-001 键盘 Tab 可用性（筛选→表格→操作）**
- **TC-P2-FEAT-002 基础 a11y（label/role/错误提示可感知）**

### Security（P1 + security）

- **TC-SEC-FEAT-001 未登录访问应进入登录流程**
  - 断言：URL 命中 `/Account/Login`（或等价登录路由）

- **TC-SEC-FEAT-002 XSS/SQLi 载荷不执行**
  - 范围：可编辑输入框（NameKey/DescriptionKey）
  - 断言：不弹 dialog、不异常跳转、若触发请求不应为 5xx

## Step2 自动化落盘建议（对齐本仓库）

```
tests/
└── aevatar/
    └── management/
        └── subscription_features/
            ├── test_subscription_features_p0.py
            ├── test_subscription_features_p1.py
            └── test_subscription_features_security.py
```
