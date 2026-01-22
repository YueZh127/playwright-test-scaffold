# Evidence Artifacts - aevatar_management_test_login

本目录用于 **Step1（MCP-first）** 的证据落盘，避免“凭空猜阈值/猜控件”。

## 规则（强制）

- **禁止**保存任何密码/Token/Cookie/storageState 到仓库
- 只允许保存：可见 HTML、可见文本、截图（建议仅本地）、规则快照 JSON（脱敏）

## 期望文件

- `visible.html`：页面可见 HTML（脱敏）
- `visible.txt`：可见文本 + 核心控件摘要（role/name 优先）
- `metadata.json`：slug/url/title/元素映射/证据文件列表（脱敏）
- `abp_app_config.json`（可选）：`GET /api/abp/application-configuration`
- `abp_swagger.json`（可选）：Swagger/OpenAPI JSON
- `abp_rules_extract.json`（可选）：从 ABP/Swagger 提取的规则摘要（仅结构化规则）

## 如何填充（建议）

使用 Cursor Playwright MCP：

1. 打开 `https://management-test.aevatar.ai/`
2. 等页面稳定（首屏内容/语言切换/登录入口出现）
3. 导出可见 HTML/文本/截图
4. 将导出物覆盖写入本目录对应文件

