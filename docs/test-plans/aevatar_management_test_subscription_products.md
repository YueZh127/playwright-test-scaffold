# Aevatar Management Test - SubscriptionProducts（订阅商品）测试计划（Step1 / MCP-first）

## 基本信息

- **目标页面**: `https://management-test.aevatar.ai/SubscriptionProducts`
- **是否需要登录态**: 是（未登录访问会进入登录页流程）
- **登录页证据（可见内容）**：访问该 URL 会出现 `Login / Username or email address / Password / Remember me` 等字段  
  参考页面：[`https://management-test.aevatar.ai/SubscriptionProducts`](https://management-test.aevatar.ai/SubscriptionProducts)

## 账号来源（强制）

- **账号池文件**: `config/project.yaml -> test_data.accounts.path`
- **账号**: `developer`
- **密码**: **禁止写入任何计划/文件**；执行期由账号池/fixture 读取

## 证据链（必须落盘）

- **证据目录**: `docs/test-plans/artifacts/aevatar_management_test_subscription_products/`
- **必须文件**（由 Cursor Playwright MCP 导出并覆盖写入）：
  - `visible.html`
  - `visible.txt`
  - `metadata.json`
  - `page.png`（建议仅本地保存，不提交仓库）

## 页面功能点（结合后端代码推导，作为真理源）

> 本模块为 ABP 管理端 Razor Pages：`/SubscriptionProducts`。

### 列表页（能力概览）

- **筛选**：
  - PlatformFilter（平台）
  - IsListedFilter（上架状态）
- **列表字段（核心）**：
  - Name/NameKey
  - PlanType
  - Description/DescriptionKey
  - Highlight/HighlightKey
  - Platform
  - PlatformProductId
  - Prices（含 last synced time）
  - Label
  - IsUltimate
  - IsListed（Listed/Delisted/NotListed）
  - Features（按钮打开 Features Modal）

### 操作与接口（真理源：后端页面脚本里的 abp.ajax）

- **创建/编辑**：Modal（CreateModal/EditModal），成功后 `location.reload()`
- **删除**：`DELETE /api/admin/subscription/products/{id}`
- **上架/下架**：`POST /api/admin/subscription/products/{id}/list|unlist`
- **同步价格（仅 Stripe 平台出现按钮）**：`POST /api/admin/subscription/products/{id}/sync-prices`

### 创建商品字段与校验（真理源：CreateProductInput DataAnnotations）

- `Product.NameKey`：`[Required]` + `MaxLength(256)`
- `Product.PlanType`：`[Required]`
- `Product.DescriptionKey`：`[Required]` + `MaxLength(256)`
- `Product.HighlightKey`：`MaxLength(256)`
- `Product.Platform`：`[Required]`
- `Product.PlatformProductId`：`[Required]` + `MaxLength(256)`
- `Product.FeatureIds`：可选（多选）
- `Product.LabelId`：可选
- `Product.IsUltimate`：bool

## 用例设计

### P0 - 核心

- **TC-P0-PROD-001 页面加载**
  - 前置：已登录
  - 断言：页面标题/列表区域可见；存在 Create 入口；筛选控件可见

- **TC-P0-PROD-002 创建商品成功 + 删除回滚（可重复执行）**
  - 数据：最小必填字段集 + 随机唯一 NameKey/PlatformProductId
  - 断言：列表出现该条；删除后列表不再出现

- **TC-P0-PROD-003 创建 Stripe 商品（指定 prodId）并验证联动能力**
  - 数据：`Platform=Stripe` + `PlatformProductId=prod_TnlJvBax2vcxRu` + PlanType=weekly
  - 断言：
    - 列表字段与创建选择一致
    - Features 弹窗包含所选功能
    - **仅 Stripe 行存在同步价格按钮**；Apple/Google 行不应出现
    - 点击上架后 IsListed 状态变化为 Listed
    - 同步价格后 Price 与时间（last synced）更新
    - 删除回滚

### P1 - 校验矩阵 / 异常

- **TC-P1-PROD-001 必填缺失矩阵（逐字段）**
  - 缺失：NameKey / PlanType / DescriptionKey / Platform / PlatformProductId
  - 断言：可见错误证据（aria-invalid/inline error/toast 任一）+ 不新增记录

- **TC-P1-PROD-002 边界：NameKey MaxLength(256) / DescriptionKey MaxLength(256) / PlatformProductId MaxLength(256)**
  - 断言：257 失败且有证据；256 输入可接受（必要时不提交，避免污染）

- **TC-P1-PROD-003 创建后取消不保存**
  - 步骤：打开创建弹窗→填写→Cancel
  - 断言：列表不新增该条

- **TC-P1-PROD-004 API 异常处理（网络失败/超时/4xx）**
  - 断言：用户得到可见反馈；页面不崩溃；不产生脏数据

### P2 - 体验/可用性

- **TC-P2-PROD-001 键盘 Tab 可用性（筛选→表格→操作）**
- **TC-P2-PROD-002 i18n 切换后页面可用（EN/ZH）**

### Security（P1 + security）

- **TC-SEC-PROD-001 未登录访问应进入登录流程**
  - 断言：URL 命中 `/Account/Login`（或等价登录路由）

- **TC-SEC-PROD-002 XSS/SQLi 载荷不执行（输入字段）**
  - 范围：NameKey/DescriptionKey/HighlightKey/PlatformProductId
  - 断言：不弹 dialog、不异常跳转、若触发请求不应为 5xx

## Step2 自动化落盘建议（对齐本仓库）

```
tests/
└── aevatar/
    └── management/
        └── subscription_products/
            ├── test_subscription_products_p0.py
            ├── test_subscription_products_p1.py
            ├── test_subscription_products_create_full_p0.py
            └── test_subscription_products_security.py
```
