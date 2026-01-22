# Aevatar Management Test - Login 测试计划（Step1 / MCP-first）

## 基本信息

- **目标页面**: `https://management-test.aevatar.ai/`
- **页面类型**: Public landing + Login（疑似需要登录态进入受保护功能，待证据链确认）
- **环境真理源**: `config/project.yaml -> environments.aevatar_test.frontend.url`
- **环境选择**: `TEST_ENV=aevatar_test`

## 账号来源（强制）

- **账号池文件**: `config/project.yaml -> test_data.accounts.path`
- **账号**: `developer`
- **密码**: **禁止写入任何计划/文件**；执行期由账号池/fixture 读取

## 证据链（必须落盘）

> 本文件只做 Step1。请用 Cursor Playwright MCP 访问页面并导出证据到本文指定目录。

- **证据目录**: `docs/test-plans/artifacts/aevatar_management_test_login/`
- **必须文件**:
  - `visible.html`: 页面可见 HTML（脱敏；不得包含 token/cookie）
  - `visible.txt`: 可见文本 + 核心控件摘要（role/name 优先）
  - `metadata.json`: slug/url/title/元素映射/证据文件列表（不得包含任何密码/凭证）
  - `page.png`: 页面截图（建议不提交到仓库；仅本地保存）

### 当前已知页面信息（来自网页可见内容快照，非 MCP 证据）

> 仅用于先行设计用例骨架；阈值/规则一律以 ABP/Swagger/代码推导为准，无法证明则标 `TBD`。

- 顶部存在语言切换：`English / EN`、`简体中文 / ZH`、`繁體中文 / ZH`、`Español / ES`
- 页面有入口：`Login`
- 主页文案：`Welcome to Aevatar`、`AI-Powered Intelligent Assistant Platform`

参考: `https://management-test.aevatar.ai/`

## 元素映射（定位优先级：role/name > label > aria > 语义 CSS > 结构 CSS）

> 以下为“计划级映射”。完成 MCP 证据链后，把可稳定定位器补齐到 `metadata.json`，并在 Step2 自动化里优先使用 role/name。

| 区域 | 目标控件 | 推荐定位（计划） | 备注 |
|------|----------|------------------|------|
| Header | 语言切换 | `role=button/menu` + 可见文本（EN/ZH/ES） | 需确认是否为 dropdown |
| Header/Body | Login 入口 | `role=link/button` name=`Login` | 需要确认是跳转还是弹窗 |
| Login 表单 | Username | `role=textbox` + label/name TBD | 需 MCP 证据确定字段名 |
| Login 表单 | Password | `role=textbox` + type=password | 不记录输入值 |
| Login 表单 | Submit | `role=button` name TBD（可能是 Login/Sign in） | |
| 通知 | 错误提示 | `role=alert` / toast region | 文案避免硬绑 |

## 风险与优先级依据

- **P0**: 入口可达 + 登录成功（阻塞用户使用）
- **P1**: 账号/输入校验 + 错误处理（安全与体验高风险）
- **P2**: i18n、键盘可用性、基础 a11y（质量与覆盖）
- **Security（P1 + security）**: 未登录访问控制、XSS/SQLi 不执行、不 5xx

## 规则真理源（ABP 优先）

> 若能获取 ABP/Swagger，则以其为真理源；否则按规则降级到“代码识别”；两者皆不可得则 `TBD`，禁止硬猜。

### 规则快照（条件触发，推荐）

- ABP Application Configuration（若可访问）：
  - `GET <frontend_base>/api/abp/application-configuration`
  - 产物：`docs/test-plans/artifacts/aevatar_management_test_login/abp_app_config.json`
- Swagger/OpenAPI（若可访问）：
  - `GET <backend_base>/swagger/v1/swagger.json`（优先后端直连；若未知先跳过）
  - 或 `GET <frontend_base>/swagger/v1/swagger.json`
  - 产物：`docs/test-plans/artifacts/aevatar_management_test_login/abp_swagger.json`
- 规则摘要（仅结构化规则，不含任何用户输入/凭证）：
  - `docs/test-plans/artifacts/aevatar_management_test_login/abp_rules_extract.json`

## 用例设计（Step2 将据此生成自动化）

### P0 - 核心主链路

- **TC-P0-001 页面加载**
  - 步骤：打开 `<frontend_base>/`
  - 断言：标题/关键文案可见；Login 入口可见且可点击
  - 证据：全页截图 + `visible.txt` 记录控件摘要

- **TC-P0-002 进入登录流程**
  - 步骤：点击 `Login`
  - 断言：出现登录表单（或跳转到登录页）；存在用户名/密码输入与提交按钮
  - 备注：定位器以 MCP 证据链补全；若为弹窗需考虑遮罩与 ESC 关闭行为

- **TC-P0-003 使用账号池登录成功（developer）**
  - 数据：账号 `developer`，密码从账号池读取（不落盘）
  - 断言（可观测）：登录后 URL/页面状态发生预期变化（例如出现用户菜单/退出按钮/受保护导航项）
  - 约束：**不得硬绑成功提示文案**（多语言/产品差异）
  - 回滚：若存在 logout，必须执行 logout（或清 cookie）以保证可重复

### P1 - 输入校验 / 异常处理（矩阵 + 少而精的后端探针）

> 未获得 ABP/Swagger/代码证据前，阈值/正则均标 `TBD`。

- **TC-P1-001 错误密码应失败（4xx 或可见错误）**
  - 数据：账号 `developer` + 错误密码（测试数据生成期构造；不落盘）
  - 断言：页面出现可见错误证据（toast/inline error/aria-invalid）；并且不会进入登录后状态

- **TC-P1-002 空用户名 / 空密码（必填）**
  - 断言：前端必须有可见错误证据（validationMessage/inline error）；必要时断言“不发登录请求”

- **TC-P1-003 多语言切换不影响登录成功**
  - 步骤：切换 EN/ZH/ES 任意两种语言后登录
  - 断言：登录结果一致；语言切换不导致登录控件丢失

- **TC-P1-004 会话保持（刷新/新开标签）**
  - 断言：刷新后仍为登录态（若产品要求）；或按产品策略重定向登录（TBD(需求))

- **TC-P1-005 API 异常处理（网络失败/超时）**
  - 方法：route abort / 超时模拟
  - 断言：用户得到可见错误反馈；页面不崩溃；不出现 5xx 导致的白屏

### P2 - UI/可用性/可访问性（最小集合）

- **TC-P2-001 键盘 Tab 顺序**
  - 断言：用户名 → 密码 → 提交按钮（顺序 TBD(证据))

- **TC-P2-002 基础 a11y**
  - 断言：输入框有可感知 label；错误提示可被屏幕阅读器感知（role=alert/aria-describedby）

### Security（建议 P1 + security 叠加）

- **TC-SEC-001 未登录访问受保护页面应进入登录流程**
  - 路径：TBD(从导航/路由证据推导)
  - 断言：被重定向到登录流程（或显示未授权提示）

- **TC-SEC-002 XSS payload 不得触发 dialog**
  - 输入：`<img src=x onerror=alert(1)>` 等最小载荷集
  - 断言：不弹窗、不异常跳转；若触发请求则不应为 5xx

- **TC-SEC-003 SQLi 风格字符串不应导致异常**
  - 输入：`' OR 1=1 --`
  - 断言：同上

## 测试数据设计（JSON 草案）

> Step2 生成 `test-data/aevatar_management_test_login_data.json` 时应遵循：

- **valid**
  - username: `developer`
  - password: 从账号池读取（运行期注入）
- **invalid**
  - wrong_password: `"wrong-password"`（示例；不落盘真实密码）
  - empty_username / empty_password
- **policy_matrix**
  - `TBD(ABP/Swagger/代码推导)`：若能抓到 ABP PasswordPolicy / DTO 约束，再补齐边界矩阵

## Step2 自动化建议（对齐本仓库）

- 使用 `auth_page` fixture（账号池分配 + 登录态管理）
- 选择器优先级：role/name > label > aria > 语义 CSS
- 截图：只截关键证据步骤（打开/填写/提交/结果），避免 Allure 噪声
- 严禁把密码写入代码/日志/Allure 附件

## 建议目录（Step2 输出）

> 仅建议命名，具体以生成器落盘为准。

```
tests/
└── aevatar/
    └── management/
        └── login/
            ├── test_login_p0.py
            ├── test_login_p1.py
            ├── test_login_p2.py
            └── test_login_security.py
```

