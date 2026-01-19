# GodGPT Login UI 自动化测试计划（待证据链补齐）

## 0. 生成信息（用于可追溯）
- **入口 URL（未登录访问首页）**: `https://godgpt-ui-testnet.aelf.dev/`
- **登录页 URL**: `https://godgpt-ui-testnet.aelf.dev/`（同 URL 的登录视图渲染分支）
- **证据链目录**: `docs/test-plans/artifacts/godgpt_ui_testnet_aelf_dev_login/`
- **账号来源（脱敏）**:
  - **测试账号邮箱**: 执行期由账号池提供（不在文档中写死具体邮箱）
  - **密码/凭证**: 执行期通过账号池或环境变量提供（不写入计划/证据链）

> 说明：当前 CLI headless 证据链未能稳定捕获“登录页/登录弹窗”（可能存在风控/渲染差异）。  
> 请用 Cursor Playwright MCP（headed）在未登录态打开首页，出现登录页后导出：`visible.html/visible.txt/page.png`，再把本计划的 TBD 全部落地。

## 0.1 自动化脚本（精简整合后的唯一入口）
- **Page Object**: `pages/godgpt_ui_testnet_aelf_dev_login_page.py`
- **Test Suite（唯一保留套件）**: `tests/ext/godgpt_ui_testnet_aelf_dev_login/`
  - `test_godgpt_ui_testnet_aelf_dev_login_p0.py`
  - `test_godgpt_ui_testnet_aelf_dev_login_p1.py`
  - `test_godgpt_ui_testnet_aelf_dev_login_p2.py`
  - `test_godgpt_ui_testnet_aelf_dev_login_security.py`

> 备注：历史生成的 `tests/ext/godgpt_ui_testnet_aelf_dev/`（把首页误判为 FORM 页）已弃用并删除，避免误导与无意义 skip。

## 1. 页面概述
- **页面目标**: 让未登录用户通过邮箱+密码完成登录，并进入受保护页面/完成会话建立
- **风险点**:
  - 鉴权绕过：未登录不应访问受保护内容
  - 错误提示泄露：错误提示不应泄露账号是否存在/策略细节
  - 防自动化/验证码：Captcha/风控导致流程不稳定，需明确策略（测试环境白名单/关闭强验证/使用测试开关）

## 2. 页面元素映射（基于登录视图截图补齐）
> 定位优先级：role/name（最稳） > placeholder/label > aria > CSS。

> **代码证据（登录流）**：
> - 邮箱页：`custom-gpt-frontend/app/(auth)/index.tsx`
>   - 点击 Email Continue 前会调用 `POST /api/account/check-email-registered`
>   - 若已注册：`router.push({ pathname: '/email-login', params: { email } })`
> - 密码页：`custom-gpt-frontend/app/(auth)/email-login.tsx`
>   - 提交前校验：`validateEmail(email)` + `validateRegisterPassword(password)`
>   - 登录：`getAevatarToken({ username: email, password }, 'password')`
> - 密码规则真理源：`custom-gpt-frontend/utils/validation.ts`
> - 登录接口（token）：`custom-gpt-frontend/utils/authService.ts`（`POST <authAPIPrefix>/connect/token`，`grant_type=password`）

> 备注（重要）：该页的“按钮”在实际 DOM 中可能不是标准 `<button>`，若 `get_by_role("button", ...)` 不稳定，
> 允许使用证据链兜底定位（来自 `docs/test-plans/artifacts/godgpt_ui_testnet_aelf_dev/visible.txt`）：
> - `page.locator("div:has-text('Continue with Apple')").first`
> - `page.locator("div:has-text('Continue with Google')").first`
> - `page.locator("div:has-text('Continue with Email')").first`
> - `page.locator("div:has-text('Skip')").first`
> - `page.locator("div:has-text('Get App')").first`
> - `page.locator("div:has-text('Contact Us')").first`

| 元素类型 | 业务语义 | 定位策略 | 定位器 | 备注 |
|---------|----------|----------|--------|------|
| button | Apple 登录 | role/name | `page.get_by_role("button", name="Continue with Apple")` | 第三方登录 |
| button | Google 登录 | role/name | `page.get_by_role("button", name="Continue with Google")` | 第三方登录 |
| input | 邮箱 | placeholder | `page.get_by_placeholder("Enter your email")` | 登录入口字段 |
| button | Continue with Email | role/name | `page.get_by_role("button", name="Continue with Email")` | 进入邮箱登录下一步 |
| input | 密码（登录页） | css/placeholder | `page.locator("input[type='password']").first` | 密码页 `/email-login`；placeholder=`Enter password` |
| button | Continue（提交密码） | role/name | `page.get_by_role("button", name="Continue")` | 密码页提交 |
| link/button | Edit（修改邮箱） | text/css | `page.get_by_text("Edit", exact=True)` | 密码页中邮箱只读，需 Edit 返回 |
| link/button | Forget Password? | text/css | `page.get_by_text("Forget Password?", exact=True)` | 忘记密码弹窗/流程 |
| link | Terms of Service | role/name 或 link text | `page.get_by_role("link", name="Terms of Service")` | 合规链接 |
| link | Privacy Policy | role/name 或 link text | `page.get_by_role("link", name="Privacy Policy")` | 合规链接 |

## 3. 测试用例设计（补充登录页）

### 3.1 P0 - 核心功能
- **TC-LOGIN-001**: 登录页/登录弹窗可达
  - **前置条件**: 未登录
  - **步骤**: 打开首页 `https://godgpt-ui-testnet.aelf.dev/`
  - **预期**: **URL 不变**，但登录视图核心控件可见：
    - Continue with Apple / Continue with Google
    - Enter your email
    - Continue with Email

- **TC-LOGIN-002**: 正常登录（happy path）
  - **前置条件**: 未登录；账号可用
  - **步骤**:
    - 输入邮箱（例如：`automationtest@drmail.in`，执行期由账号池分配）→ 点击 “Continue with Email”
    - 预期进入密码页（`/email-login` 视图）：出现 `input[type=password]`（placeholder=`Enter password`）
    - 输入正确密码（执行期注入；不落盘）→ 点击 “Continue”
  - **预期**（满足任一即可，优先选“可观测且稳定”的）:
    - 路由进入 `/(app)`（或出现“已登录态”顶部入口/用户信息）
    - 会话建立可观测（例如：可发送消息且不再出现登录提示）
  - **证据**: 截图 + 关键断言（避免写死易变文案）

### 3.2 P0/P1 - 校验与错误处理
- **TC-LOGIN-010**: 邮箱必填
  - **步骤**: 不填邮箱 → 点击 “Continue with Email”
  - **预期**: 前端拦截（validationMessage/错误 UI）；不应进入下一步

- **TC-LOGIN-012**: 邮箱格式非法（如 `aaa`）
  - **步骤**: 输入非法邮箱 → 点击 “Continue with Email”
  - **预期**: 显示格式错误（不应进入下一步）

- **TC-LOGIN-013**: 第三方登录按钮可点击（最小可用性）
  - **步骤**: 点击 “Continue with Apple/Google”
  - **预期**: 打开第三方 OAuth 流程（新页面/弹窗/跳转）；可回退；不应卡死在 loading

- **TC-LOGIN-014**: 不正确的邮箱地址（格式正确但账号不存在/不可用）
  - **步骤**: 输入格式正确但不可用邮箱（如 `not-exists+qa@drmail.in`）→ 点击 “Continue with Email”
  - **预期**:
    - 错误提示不泄露“账号是否存在”（避免账号枚举）
    - 与“错误密码/账号不存在”行为一致（同类提示/同类状态码/同类 UI）
  - **备注**: 若产品走“验证码/魔法链接”，此用例验证：不会提示“邮箱不存在”（若产品要求提示则需产品确认并记录）。

- **TC-LOGIN-015**: 邮箱首尾空格处理（Trim）
  - **步骤**: 输入 `  test@example.com  `（首尾空格）→ 点击 “Continue with Email”
  - **预期**: 系统按 Trim 后处理邮箱；不应因空格导致格式校验误判

- **TC-LOGIN-016**: 错误的密码（若存在密码输入步骤）
  - **前置条件**: 点击 “Continue with Email” 后进入密码页（`/email-login` 视图）
  - **步骤**: 输入有效邮箱（来自账号池）→ 输入错误密码（执行期提供，不落盘）→ 点击 “Continue”
  - **预期**:
    - 登录失败；不进入已登录态
    - 错误提示出现（来自后端 `error_description` 或 fallback `Login failed`）
    - 与“邮箱不存在/不可用”行为尽量一致（防枚举）

- **TC-LOGIN-017**: 失败节流/锁定/验证码升级（若有）
  - **步骤**: 对同一邮箱连续触发失败 N 次（N=`TBD(产品策略/后端规则)`）
  - **预期**: 出现节流/锁定提示或验证码升级；不会无限制尝试

#### 3.2.1 密码页校验矩阵（来自代码真理源）
> 规则证据：`custom-gpt-frontend/utils/validation.ts:validateRegisterPassword()`
> - 必填：空密码 → `signin_password_toast`（英文：`Please enter a password`）
> - 长度：`len(password) >= 6` → `password_min_length`
> - 复杂度：
>   - 必须包含大写：`/[A-Z]/` → `password_uppercase_required`
>   - 必须包含小写：`/[a-z]/` → `password_lowercase_required`
>   - 必须包含数字：`/[0-9]/` → `password_digit_required`
>   - 必须包含特殊字符：`/[.!@#$%^&*]/` → `password_special_required`

- **TC-LOGIN-PW-001**: 密码必填拦截
  - **步骤**: 进入密码页 → 密码为空 → 点击 “Continue”
  - **预期**: 显示 `Please enter a password`；不发送登录请求；停留在密码页

- **TC-LOGIN-PW-002**: 密码太短（<6）
  - **测试数据**: `A1!a`（示例）
  - **步骤**: 输入短密码 → 点击 “Continue”
  - **预期**: 显示 `Password should be at least 6 characters`；不发送登录请求

- **TC-LOGIN-PW-003**: 缺少大写
  - **测试数据**: `abcdef1!`
  - **预期**: 显示 `password_uppercase_required` 对应文案；不发送登录请求

- **TC-LOGIN-PW-004**: 缺少小写
  - **测试数据**: `ABCDEF1!`
  - **预期**: 显示 `password_lowercase_required` 对应文案；不发送登录请求

- **TC-LOGIN-PW-005**: 缺少数字
  - **测试数据**: `Abcdef!@`
  - **预期**: 显示 `password_digit_required` 对应文案；不发送登录请求

- **TC-LOGIN-PW-006**: 缺少特殊字符
  - **测试数据**: `Abcdef12`
  - **预期**: 显示 `password_special_required` 对应文案；不发送登录请求

### 3.4 页面专项/特殊用例（基于截图控件）
- **TC-S-01 [Skip 逻辑]**: 点击 “Skip”
  - **步骤**: 点击右上角 “Skip”
  - **预期**（二选一）:
    - 进入 Guest/受限模式（可见部分内容，但关键受保护功能仍需登录）
    - 或仍停留登录视图但给出明确提示（按产品设计）

#### 3.4.1 Skip → 游客(非登录)页面：交互限制验证（核心）
> 目标：验证“游客模式”下的交互次数限制、UI 限制与会话行为。
>
> 说明：以下用例需要在 Skip 后进入游客页面才能执行；定位器若证据链未覆盖，统一标记 `TBD(需证据链)`。
>
> **代码证据（前端/后端真理源）**：
> - 前端游客态数据结构：`custom-gpt-frontend/utils/state/sessionId.ts`（`TGuestSessionInfo.remainingChats` / `totalAllowed`）
> - 前端计数递减：`custom-gpt-frontend/utils/hooks/useSessionInfo.ts`（`useUpdateSessionInfo()` 每次发送后 `remainingChats - 1`）
> - 前端第 4 次拦截：`custom-gpt-frontend/app/chat/[sessionId]/index.tsx`（`remainingChats <= 0` 时 `Toast.show({ text1: t('signup_continue_alert') })` 并 return）
> - 提示文案来源：`custom-gpt-frontend/i18n/locales/en.json`（`signup_continue_alert`: “Sign up to continue and receive 320 FREE credits.”）
> - 后端硬限制：`godgpt/src/GodGPT.GAgents/Anonymous/AnonymousUserGAgent.cs`
>   - `GetMaxChatCount()` 默认 `MaxChatCount ?? 3`
>   - 超限抛 `InvalidOperationException("Daily chat limit exceeded for guest users")`

- **TC-GUEST-001**: Skip 后进入游客页面（非登录态标识正确）
  - **标签**: [@p0 @guest]
  - **步骤**: 点击 “Skip”
  - **预期结果**:
    - 页面进入游客模式（无登录态标识/无用户信息）
    - **左侧菜单栏不展示**（`TBD(需证据链：侧边栏容器 selector)`）

- **TC-GUEST-002**: 游客模式允许进行 3 次交互（算命流程/灵魂控制台）
  - **标签**: [@p0 @guest]
  - **步骤**:
    - 在游客模式下分别触发 3 次交互（覆盖：算命流程、灵魂控制台、任意一次普通对话）
  - **预期结果**:
    - 每次交互后 **AI 回复正常出现**（`TBD(需证据链：message bubble selector)`）
    - **交互计数准确递增**，且不超过 3 次限制（`TBD(需证据链：计数器 UI)`）

- **TC-GUEST-003**: 发送消息后保持顶部导航栏，并进入会话页面
  - **标签**: [@p0 @guest]
  - **步骤**: 在游客模式发送一条消息
  - **预期结果**:
    - 顶部导航栏保持可见（`TBD(需证据链：顶部导航 selector)`）
    - 页面进入/停留在会话页面（URL 变化或会话容器出现，二选一；`TBD(需证据链：会话页容器)`）

- **TC-GUEST-004**: 第 4 次交互被阻止并提示登录
  - **标签**: [@p0 @guest]
  - **前置条件**: 已完成 3 次交互，计数达到上限
  - **步骤**: 尝试第 4 次发送/触发交互
  - **预期结果**:
    - 弹出提示：`signup_continue_alert`（英文环境下为 “Sign up to continue and receive 320 FREE credits.”，避免硬编码其它文案）
    - 发送按钮置灰（disabled）
    - 输入框清除（内容被清空）
  - **备注**: 以上 3 个断言缺一不可（限制必须生效且用户得到明确反馈）。

- **TC-GUEST-005**: 会话页面动作限制：仅有复制按钮（Report/重新生成不显示）
  - **标签**: [@p1 @guest]
  - **步骤**: 在会话页面查看 GodGPT 的对话项
  - **预期结果**:
    - 仅展示“复制”按钮
    - “Report”“重新生成/Regenerate”按钮不展示
  - **代码证据**: Web 对话气泡操作区 `custom-gpt-frontend/components/Chat/WebChatContent.tsx`
    - AI 回复完成后仅渲染 `CopyComponent`
    - `Report`/`Regenerate` 未在该组件中渲染（按需求应保持不出现）
  - **定位**: `TBD(需证据链：消息操作区 selector + Copy 按钮可点击点)`

- **TC-GUEST-006**: 游客模式不能修改会话名称
  - **标签**: [@p1 @guest]
  - **步骤**: 尝试修改会话名称（点击标题/编辑入口）
  - **预期结果**: 不允许修改（入口不可见或操作被阻止且有提示）
  - **代码证据**: 前端改名弹窗 `custom-gpt-frontend/components/ModalsComponent/RenameChatModal/index.tsx`（通过 `renameItem({sessionId,title})` 调用后端；游客态应禁用入口或拦截）
  - **定位**: `TBD(需证据链：会话标题/编辑入口 selector)`（需在 Skip 后游客页导出证据链补齐）

#### 3.4.2 Skip → 对话保留机制验证
- **TC-GUEST-010**: 不刷新页面的情况下，切换到 login 后不再保留会话
  - **标签**: [@p1 @guest]
  - **步骤**:
    - 游客模式进行 1 次对话
    - 不刷新页面，切换到 login（点击登录入口或触发登录弹窗）
  - **预期结果**: 游客会话不再保留（回到会话区/历史区为空或不可见；`TBD(需证据链：会话列表/历史入口)`）

- **TC-GUEST-011**: 页面刷新后对话不保留
  - **标签**: [@p1 @guest]
  - **步骤**:
    - 游客模式进行 1 次对话
    - 刷新页面（F5/Reload）
  - **预期结果**: 刷新后没有会话记录（会话列表为空/不可见；`TBD(需证据链：会话列表/空态)`）

- **TC-GUEST-012**: 登录后不继承游客对话（不会进入会话历史）
  - **标签**: [@p1 @guest]
  - **步骤**:
    - 游客模式进行 1 次对话
    - 执行登录（账号来自账号池；不落盘密码）
    - 登录后进入会话历史/列表
  - **预期结果**: 历史中不出现游客对话内容（游客对话不会迁移到登录态账号下）
  - **定位**: `TBD(需证据链：会话历史入口 + 会话列表条目)`

- **TC-S-02 [Get App]**: 点击 “Get App (NEW)”
  - **步骤**: 点击右上角 “Get App”
  - **预期**: 打开下载页/应用商店/二维码页面（新标签或同页跳转均可）；页面不崩溃

- **TC-S-03 [法律条款]**: Terms / Privacy 可达
  - **步骤**: 点击 “Terms of Service” 和 “Privacy Policy”
  - **预期**: 链接可打开且内容可加载；建议新标签打开（若同页打开需可返回）

- **TC-S-04 [Contact Us]**: 联系我们入口可用
  - **步骤**: 点击底部 “Contact Us”
  - **预期**: 打开反馈页/邮件/表单入口（符合产品设计）；不应无响应

- **TC-S-05 [暗黑模式/可访问性]**: 文本对比度与可读性
  - **步骤**: 在默认深色背景下检查关键文本（按钮文案/输入 placeholder/条款链接）
  - **预期**: 对比度满足可读性要求（建议对齐 WCAG AA；若无法自动计算则记录为 `TBD(需工具评估)`）

- **TC-S-06 [响应式布局]**: 移动端尺寸不重叠
  - **步骤**: 切换 viewport 到移动端（如 390x844）与桌面端（1920x1080）
  - **预期**: 登录卡片居中/可滚动；“Get App/Skip”不遮挡主按钮；核心控件可点击

- **TC-S-07 [Placeholder 行为]**: 邮箱输入框占位符
  - **步骤**: 验证默认 placeholder 为 “Enter your email”；聚焦输入后 placeholder 行为正确（消失/不遮挡输入）
  - **预期**: placeholder 不影响输入与校验提示

### 3.3 P1 - 安全最小集
- **TC-LOGIN-020**: XSS payload 不执行
  - **步骤**: 在邮箱/密码字段输入 `<script>alert(1)</script>` 等 → 提交
  - **预期**: 不弹窗；页面不崩溃；错误提示不把 payload 当 HTML 渲染

- **TC-LOGIN-021**: 失败重试与节流（若有）
  - **预期**: 多次失败后提示/锁定策略符合预期（TBD：需后端规则/产品定义）

## 4. 证据链要求（按规则）
必须落盘到：`docs/test-plans/artifacts/godgpt_ui_testnet_aelf_dev_login/`
- `visible.html`
- `visible.txt`（必须包含：页面标题、核心控件摘要、是否疑似需要登录态）
- `page.png`
- `metadata.json`

## 5. 下一步（你需要给我一个“可审计真理源”）
请在 Cursor Playwright MCP（headed）中：
1. 清除登录态（新 profile 或清 cookie）
2. 打开首页：`https://godgpt-ui-testnet.aelf.dev/`（应直接渲染登录视图）
4. 导出证据链到：`docs/test-plans/artifacts/godgpt_ui_testnet_aelf_dev_login/`

我拿到证据链后会把本计划里的所有 `TBD` 变成确定的定位器与断言，并补齐对应的自动化代码生成入口。


