# GodGPT - Upgrade（订阅策略/升级方案页）- Step1 测试计划

> 规则：`.cursor/rules/ui-test-plan-generator.mdc`  
> 环境真理源：`config/project.yaml` → `environments.godgpt_ui_testnet.frontend.url`  
> 目标页面：`/upgrade`

## 1. 安全约束（必须）

- **禁止**在计划/产物中写入密码、Token、Cookie、storageState。
- 本计划仅写明测试账号 **email** 用于可读性：`testaaaa@drmail.in`
- 自动化执行（Step2）必须从账号池/环境变量读取密码；**不得写死到代码**。

## 2. 证据链（本次可获取）

目录：`docs/test-plans/artifacts/godgpt_upgrade_subscription_strategy/`

- `visible.html` / `visible.txt` / `page.png`：本次在**无凭证**状态下抓取到的页面证据
- 关键观察（来自证据）：直接访问 `/upgrade` 被重定向到 `/`，并出现登录入口（Apple/Google/Email）

结论：
- **订阅升级页需要登录态**：`requires_auth = true`
- 登录后页面内容（价格/方案/CTA）本次无法证据化 → 计划中标注 `TBD(需登录态证据)`

## 3. 页面功能概述（推断 + 证据）

### 3.1 未登录态（已证据化）
- 访问 `/upgrade` → 重定向至首页/登录入口
- 登录入口包含：
  - `Continue with Apple`
  - `Continue with Google`
  - `Continue with Email`

### 3.2 登录后（TBD，需补证据）
> 需要通过 MCP 或“已登录态 Playwright 采集”补充：方案卡片、价格、计费周期、购买/升级 CTA、支付/Checkout 行为。

## 4. 用例设计

### P0（核心主链路）

#### TC-P0-001 未登录访问 upgrade 必须被引导登录（已证据化）
- **步骤**：未登录打开 `GET {frontend}/upgrade`
- **期望**：
  - URL 重定向到 `{frontend}/` 或登录页（以实际为准）
  - 页面存在 Email/Google/Apple 登录入口
  - 不出现 5xx/白屏

#### TC-P0-002 Email 登录成功后可进入 upgrade（TBD）
- **前置**：账号池中存在可用账号（email：`testaaaa@drmail.in`；密码不落盘）
- **步骤**：
  - 通过 Email 登录
  - 登录成功后访问 `{frontend}/upgrade`
- **期望（TBD）**：
  - upgrade 页面加载成功
  - 能看到至少 1 个方案与 CTA

#### TC-P0-003 选择一个方案并进入下一步（支付/确认）（TBD）
- **步骤**：在 upgrade 页面点击默认推荐方案 CTA（或任一方案）
- **期望（TBD）**：
  - 若为跳转式 checkout：URL 变为支付页且包含方案标识
  - 若为弹窗式 checkout：出现支付弹窗/确认页关键元素
  - 返回/取消行为可回到 upgrade 或 account 页

### P1（校验/一致性）

#### TC-P1-001 upgrade 价格/计费周期展示一致性（TBD）
- **断言**：每个方案卡片显示价格与计费周期文案
- **TBD**：价格/折扣真理源（需要后端契约/配置/或 UI 证据链）

#### TC-P1-002 推荐标签与折扣文案（TBD）
- **断言**：如存在 “Most popular / Best value / Save xx” 等标签，需与产品策略一致且不冲突

#### TC-P1-003 方案权益列表完整性（TBD）
- **断言**：每档权益列表不为空；关键权益文案存在且无乱码

### Security（最小集）

#### TC-SEC-001 未登录不可直接购买/升级（已部分证据化）
- **断言**：未登录访问 `/upgrade` 会被引导登录，不应直接进入支付完成页

#### TC-SEC-002 购买请求不可被前端篡改（TBD）
- **断言（TBD）**：即使篡改前端参数/请求体，也不能以低价购买高档（需后端校验证据）

## 5. 数据设计（Step2 建议）

```json
{
  \"account\": { \"email\": \"testaaaa@drmail.in\", \"password\": \"(FROM_POOL_OR_ENV)\" },
  \"tbd\": {
    \"plan_catalog\": \"TBD(登录后证据)\",
    \"checkout_flow\": \"TBD(登录后证据)\"
  }
}
```

## 6. 自动化建议（对齐本仓库）

- 使用 `auth_page` fixture（账号从账号池获取；密码用 `secret_fill`）
- 先做未登录态断言（TC-P0-001），再用登录态采集 upgrade 页面证据补齐 P0/P1
- 写操作（若有“升级”导致状态变化）必须可回滚/可清理

