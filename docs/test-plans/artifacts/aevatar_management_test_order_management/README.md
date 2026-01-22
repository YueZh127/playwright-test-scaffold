# Evidence Artifacts - aevatar_management_test_order_management

本目录用于 **Step1（MCP-first）** 的证据落盘，支持“订单管理”模块三页：

- 订阅商品
- 功能特性
- 商品标签

## 安全规则（强制）

- **禁止**保存任何密码/Token/Cookie/storageState 到仓库
- 只允许保存：可见 HTML、可见文本、截图（建议仅本地）、规则快照 JSON（脱敏）

## 推荐组织（避免三页相互覆盖）

```
docs/test-plans/artifacts/aevatar_management_test_order_management/
├── subscription_products/
│   ├── visible.html
│   ├── visible.txt
│   ├── metadata.json
│   └── page.png   (建议仅本地)
├── feature_flags/
│   ├── visible.html
│   ├── visible.txt
│   ├── metadata.json
│   └── page.png
└── product_tags/
    ├── visible.html
    ├── visible.txt
    ├── metadata.json
    └── page.png
```

## 规则快照（可选，若可获取）

- `abp_app_config.json`：`GET <frontend_base>/api/abp/application-configuration`
- `backend_swagger.json`：`GET <backend_base>/swagger/v1/swagger.json`（若已知后端地址）
- `abp_rules_extract.json`：从上述 JSON 提取的规则摘要（仅结构化规则）

