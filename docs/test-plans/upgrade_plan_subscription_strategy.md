# Upgrade Plan（订阅策略页面）- Step1 测试计划（基于快照）

> 规则：`.cursor/rules/ui-test-plan-generator.mdc`  
> 证据来源：`file:///Users/zy/Downloads/upgrade-plan.mhtml`（离线快照）  
> 说明：本计划仅基于快照可见信息生成；**无法从快照确认的内容一律标注 TBD**，禁止硬猜阈值/后端规则。

## 1. 配置真理源（来自 `config/project.yaml`）

- **环境地址**：当前 `config/project.yaml` 为模板占位（`https://localhost:3000` 等）；本页面真实线上 URL **TBD(需要在 project.yaml 配置实际环境)**  
- **账号池**：`test-data/test_account_pool.json`（Step2 自动化必须从账号池取账号；Step1 不写入任何密码/Token）

## 2. 证据链（已落盘）

目录：`docs/test-plans/artifacts/upgrade_plan_subscription_strategy/`

- **visible.html**：从 `.mhtml` 提取的 HTML（快照）
- **visible.txt**：可见文本与控件摘要（快照）
- **page.png**：占位空文件（需要 MCP 才能截图）
- **metadata.json**：slug/url/title + 元素定位建议

> 若要补全可执行 UI 证据（截图/真实可见 HTML）：请用 MCP 打开真实环境页面并覆盖 `page.png/visible.*`。

## 3. 页面功能概述（从快照提取）

页面主题：**Upgrade your plan**（升级订阅方案/订阅策略）

从快照可见的核心元素：
- **方案卡片**：Weekly / Monthly / Annual
- **定价与计费周期**：
  - Weekly：`$5 / week` + `Billed weekly`
  - Monthly：`$15 / month` + `Billed monthly`（含 `Most Popular` 与 `25% cheaper than weekly` 文案）
  - Annual：`$120 / year` + `Billed annually`（含 `Best Value`、`Go Annual & Save`、`Save $60 / year`、`Lock in this price forever.`）
- **CTA**：`Try It` / `Get Started` / `Go Annual & Save`
- **对比入口**：`Compare plans`
- **承诺与限制文案**（示例）：`cancel anytime`、`Rate limit applies`、`Priority responses`、`Multi-device sync` 等

## 4. 风险点（为什么要测）

- **价格/折扣一致性**：UI 显示价格、折扣和“节省金额”必须数学一致且不误导。
- **CTA 链路**：升级按钮可能跳转登录、跳转支付、或触发内嵌弹窗；任何断链会直接影响转化。
- **多方案差异**：各档权益列表必须与产品策略一致（避免“展示承诺”与实际开通不一致）。
- **可用性**：对比区、按钮可点击性、移动端布局可能影响转化。

## 5. 元素映射（定位建议，Step2 会用）

优先级：role/name > aria/label > 语义 CSS > 结构 CSS

- **页面标题**：`role=heading`，name 包含 `Upgrade your plan`
- **方案卡片**：按文本 `Weekly/Monthly/Annual` 定位卡片容器（TBD：是否存在稳定的 data-testid）
- **CTA**
  - Weekly CTA：`role=button[name="Try It"]`
  - Monthly CTA：`role=button[name="Get Started"]`
  - Annual CTA：`role=button[name="Go Annual & Save"]`
- **对比入口**：`text=Compare plans`

## 6. 测试用例设计

### P0（核心链路）

#### TC-P0-001 页面加载与基础内容
- **步骤**：打开订阅策略页（真实环境 URL TBD）
- **断言**：
  - 页面标题包含 `Upgrade your plan`
  - 三个方案卡片（Weekly/Monthly/Annual）可见
  - 每个卡片至少包含：价格 + 计费周期（Billed xxx）+ CTA
- **证据**：见快照 `visible.txt`

#### TC-P0-002 三档价格展示一致性（快照可证据化）
- **断言**（以快照为准；线上若变化需更新证据）：
  - Weekly 显示 `$5 / week` 且出现 `Billed weekly`
  - Monthly 显示 `$15 / month` 且出现 `Billed monthly`
  - Annual 显示 `$120 / year` 且出现 `Billed annually`

#### TC-P0-003 折扣与节省金额一致性（快照可证据化）
- **断言**：
  - Monthly 出现 `25% cheaper than weekly`（文案存在即可；百分比计算 **TBD(需后端/配置真理源)**）
  - Annual 出现 `Save $60 / year`
  - 数学一致性（基于快照价格）：\(15\\times12-120=60\)  
    - 若线上价格不同：此断言应随真理源更新（禁止硬猜）

#### TC-P0-004 CTA 可点击与跳转/弹窗行为（需 MCP/真实环境）
- **步骤**：点击三档 CTA（Try It / Get Started / Go Annual & Save）
- **断言（TBD，需实测确认）**：
  - 若需要登录：应跳转登录且回跳到 upgrade 流程
  - 若进入支付：应进入对应的 checkout 页面/弹窗（提供方案标识与价格）
  - 不应出现 5xx/白屏/无限 loading

### P1（重要：一致性/边界/可用性）

#### TC-P1-001 Compare plans 行为
- **步骤**：点击 `Compare plans`
- **断言**：滚动到对比区域或打开对比弹窗（TBD：具体行为）

#### TC-P1-002 文案一致性与可读性
- **断言**：
  - `cancel anytime` / `Rate limit applies` 等关键限制/承诺文案可见且无乱码（快照里存在替换字符 `���`，线上需验证）

#### TC-P1-003 价格格式与货币符号
- **断言**：价格格式一致（货币符号、分隔符、小数位数）  
- **TBD**：货币/本地化策略来源（需要后端/配置真理源）

#### TC-P1-004 方案标签正确性
- **断言**：`Most Popular` 只标在指定方案、`Best Value` 只标在指定方案（快照：Monthly/Annual）

### P2（一般：UI/兼容性）

#### TC-P2-001 响应式布局（移动端）
- **断言**：三档卡片在窄屏不重叠、CTA 可点击、对比区可访问

#### TC-P2-002 可访问性（A11y）
- **断言**：
  - CTA 可通过键盘 focus/Enter 触发
  - 主要信息（标题/价格）对屏幕阅读器可读（role/name）

### Security（最小集）

#### TC-SEC-001 未登录访问策略（若该页需要登录）
- **断言**：未登录访问时行为明确：要么可访问营销页，要么重定向登录（TBD：产品策略）

#### TC-SEC-002 价格/方案参数不可被前端篡改（需真实环境）
- **断言（TBD）**：通过修改前端参数/URL/query 不能以低价购买高档（需要后端校验证据）

## 7. 数据设计（Step2 生成建议）

本页主要是展示与跳转，数据以“方案配置”为主：

```json
{
  "plans": {
    "weekly": { "price_text": "$5 / week", "billing_text": "Billed weekly", "cta": "Try It" },
    "monthly": { "price_text": "$15 / month", "billing_text": "Billed monthly", "cta": "Get Started", "badge": "Most Popular" },
    "annual": { "price_text": "$120 / year", "billing_text": "Billed annually", "cta": "Go Annual & Save", "badge": "Best Value", "save_text": "Save $60 / year" }
  },
  "tbd": {
    "real_env_url": "TBD(config/project.yaml)",
    "checkout_flow": "TBD(MCP 观察/后端契约)",
    "currency_policy": "TBD(后端/配置真理源)"
  }
}
```

## 8. Step2 自动化建议（不生成代码，仅说明）

- **页面对象**：建议 `pages/subscription_strategy_page.py`（命名 TBD）  
- **用例目录**：`tests/<domain>/subscription_strategy/`  
- **证据优先**：对价格/折扣/标签用 **文本断言 + 截图**（避免依赖 DOM 结构）  
- **跳转链路**：点击 CTA 后用 `expect(page).to_have_url(...)` 或等待 `checkout` 特征元素（TBD）

