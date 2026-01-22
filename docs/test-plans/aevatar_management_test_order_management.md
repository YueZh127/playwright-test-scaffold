 # Aevatar Management Test - 订单管理 测试计划（Step1 / MCP-first）

## 基本信息

- **环境**: `aevatar_test`
- **前端地址**: `config/project.yaml -> environments.aevatar_test.frontend.url`
- **入口页面**: `https://management-test.aevatar.ai/`
- **前置条件**: 需要登录态（基于“管理端侧边栏”截图推断；待 MCP 证据链确认）

## 账号来源（强制）

- **账号池文件**: `config/project.yaml -> test_data.accounts.path`
- **账号**: `developer`
- **密码**: **禁止写入任何计划/文件**；执行期由账号池/fixture 读取（你提供的密码仅用于当次 MCP 登录）

## 范围（来自你提供的 UI 证据：侧边栏“订单管理”）

> 你给的截图显示“订单管理”下有 3 个子页面；具体 URL/路由以 MCP 证据链为准。

- **订单管理 / 订阅商品**
- **订单管理 / 功能特性**
- **订单管理 / 商品标签**

## 证据链（必须落盘）

- **证据目录**: `docs/test-plans/artifacts/aevatar_management_test_order_management/`
- **每个子页面都要导出**（建议每页一个子目录，或在 metadata.json 里做 page_key 区分）：
  - `visible.html`：页面可见 HTML（脱敏）
  - `visible.txt`：页面标题 + 核心控件摘要（role/name 优先）+ 是否需要登录态
  - `metadata.json`：slug/url/title/元素映射/证据文件列表（脱敏）
  - `page.png`：页面截图（建议仅本地保存，不提交仓库）

## 元素映射（计划级，占位，待 MCP 补齐）

### 全局（侧边栏/导航）

| 区域 | 目标控件 | 推荐定位（计划） | 备注 |
|------|----------|------------------|------|
| Sidebar | “订单管理”分组 | `role=button`/`role=link` name=`订单管理` | 展开/折叠 |
| Sidebar | 订阅商品 | `role=link` name=`订阅商品` | |
| Sidebar | 功能特性 | `role=link` name=`功能特性` | |
| Sidebar | 商品标签 | `role=link` name=`商品标签` | |

### 页面级（通用 CRUD 列表页模板：TBD）

> 未拿到 MCP 证据前，不硬猜控件结构；以下为常见“管理台列表页”风险点清单。

- 列表容器（table/grid）
- 搜索框/筛选条件（input/select）
- 分页（上一页/下一页/页码/每页条数）
- 新增按钮（Create/Add）
- 编辑入口（row action）
- 删除入口（row action + confirm）
- 状态切换（enable/disable/publish）
- Toast/Alert（错误与成功提示）

## 风险与优先级依据

- **P0**：菜单可达 + 页面可加载 + 列表可读（管理端不可用即阻塞运营/配置）
- **P1**：新增/编辑/删除/校验矩阵 + 关键异常处理（数据一致性与运维风险）
- **P2**：Tab/键盘可用性、基础 a11y、i18n（体验与覆盖）
- **Security（P1 + security）**：鉴权/越权、注入载荷不执行、不 5xx

## 规则真理源（ABP/Swagger 优先；否则代码识别）

> 本项目规范：后端为真理源；拿不到就降级；都拿不到就 `TBD`，禁止硬猜阈值。

### 条件触发：规则快照采集

- `GET <frontend_base>/api/abp/application-configuration`（若 200）
  - 产物：`abp_app_config.json`
- `GET <backend_base>/swagger/v1/swagger.json`（若已知 backend_base 且可访问）
  - 产物：`backend_swagger.json`
- 规则摘要（字段约束/错误体结构/接口契约）：`abp_rules_extract.json`

## 用例设计（Step2 将据此生成自动化）

> 说明：本计划先把“可证据化的行为断言”写清楚；字段阈值/正则/DTO 约束待 ABP/Swagger/代码推导补齐。

### P0 - 核心

- **TC-P0-OM-001 登录后侧边栏可见“订单管理”**
  - 断言：侧边栏存在“订单管理”分组与 3 个子菜单项

- **TC-P0-OM-002 订阅商品页可打开并稳定渲染**
  - 步骤：点击“订阅商品”
  - 断言：页面标题可见；主列表区域可见（table/grid 任一）

- **TC-P0-OM-003 功能特性页可打开并稳定渲染**

- **TC-P0-OM-004 商品标签页可打开并稳定渲染**

### P1 - CRUD + 校验 + 异常（每页一套最小闭环）

#### 订阅商品（TBD：实体字段与规则）

- **TC-P1-OM-PROD-001 新增订阅商品（最小字段集）**
  - 断言：保存成功（toast/列表出现/详情页展示）
  - 回滚：删除该条目或恢复 baseline（可重复执行）

- **TC-P1-OM-PROD-002 必填/格式校验矩阵（TBD(真理源))**
  - 断言：前端可见错误证据（validationMessage/aria-invalid/inline error）且（推荐）不发写请求

- **TC-P1-OM-PROD-003 API 失败处理（网络失败/4xx/5xx）**
  - 断言：用户得到可见反馈；页面不崩；不产生脏数据

#### 功能特性（TBD：字段与规则）

- **TC-P1-OM-FEAT-001 新增功能特性**
- **TC-P1-OM-FEAT-002 编辑功能特性**
- **TC-P1-OM-FEAT-003 删除功能特性（含确认弹窗）**
- **TC-P1-OM-FEAT-004 校验矩阵（TBD(真理源))**

#### 商品标签（TBD：字段与规则）

- **TC-P1-OM-TAG-001 新增标签**
- **TC-P1-OM-TAG-002 重名标签处理（TBD：是否允许）**
- **TC-P1-OM-TAG-003 删除标签**
- **TC-P1-OM-TAG-004 校验矩阵（TBD(真理源))**

### P2 - UI/可用性

- **TC-P2-OM-001 列表页 Tab/键盘可用性（搜索→列表→分页→操作）**
- **TC-P2-OM-002 i18n 切换后菜单与页面标题仍可用（EN/ZH）**

### Security（P1 + security）

- **TC-SEC-OM-001 未登录访问订单管理路由应进入登录流程**
  - 路由：TBD(从 MCP/metadata 获取)
  - 断言：跳转登录或未授权提示

- **TC-SEC-OM-002 越权/角色不足访问应被拒绝（若存在权限系统）**
  - 数据：TBD(账号角色)

- **TC-SEC-OM-003 XSS/SQLi payload 不得触发 dialog**
  - 范围：所有可编辑 input/select/textarea（由 MCP 映射决定）

## Step2 自动化落盘建议（对齐本仓库）

```
tests/
└── aevatar/
    └── management/
        └── order_management/
            ├── test_order_management_p0.py
            ├── test_order_management_p1.py
            ├── test_order_management_p2.py
            └── test_order_management_security.py
```

