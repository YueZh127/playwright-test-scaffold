# Aevatar Management Test - SubscriptionLabels（商品标签）测试计划（Step1 / MCP-first）

## 基本信息

- **目标页面**: `https://management-test.aevatar.ai/SubscriptionLabels`
- **是否需要登录态**: 是（未登录访问会进入登录页流程）
- **登录页证据（可见内容）**：访问该 URL 会出现 `Login / Username or email address / Password / Remember me` 等字段  
  参考页面：[`https://management-test.aevatar.ai/SubscriptionLabels`](https://management-test.aevatar.ai/SubscriptionLabels)

## 账号来源（强制）

- **账号池文件**: `config/project.yaml -> test_data.accounts.path`
- **账号**: `developer`
- **密码**: **禁止写入任何计划/文件**；执行期由账号池/fixture 读取

## 证据链（必须落盘）

- **证据目录**: `docs/test-plans/artifacts/aevatar_management_test_subscription_labels/`
- **必须文件**（由 Cursor Playwright MCP 导出并覆盖写入）：
  - `visible.html`
  - `visible.txt`
  - `metadata.json`
  - `page.png`（建议仅本地保存，不提交仓库）

## 功能概述（根据后端代码推导，作为真理源）

> 该模块为 ABP 管理端 Razor Pages：`/SubscriptionLabels`。

### 创建标签表单字段（真理源：后端 DataAnnotations）

- **Label.Key**（LabelKey）
  - `[Required]`
  - `[MaxLength(128)]`
  - `[RegularExpression(@"^[a-z][a-z0-9_]*$")]`（snake_case，小写字母开头，仅允许小写/数字/下划线）

## 用例设计（创建标签为主）

### P0 - 核心

- **TC-P0-LABEL-001 页面加载**
  - 前置：已登录
  - 步骤：进入 `/SubscriptionLabels`
  - 断言：页面标题/列表区域可见；存在“CreateLabel”按钮（或等价入口）

- **TC-P0-LABEL-002 创建标签成功 + 删除回滚**
  - 数据：`qa_label_<ts>`（符合 regex）
  - 断言：列表出现该 key；删除后列表不再存在该 key（保证可重复执行）

### P1 - 校验矩阵 / 异常

- **TC-P1-LABEL-001 必填：Key 为空应失败**
  - 断言：可见错误证据（aria-invalid/inline error/toast 任一）
  - 断言：列表不应新增记录

- **TC-P1-LABEL-002 格式：Key 非 snake_case（如 `Bad-KEY`）应失败**
  - 断言：可见错误证据；不新增

- **TC-P1-LABEL-003 边界：Key 长度 129 应失败，128 可接受**
  - 断言：129 失败且有证据；128 输入可接受（必要时不提交，避免污染）

- **TC-P1-LABEL-004 创建后取消不保存**
  - 步骤：打开创建弹窗→填写 key→Cancel
  - 断言：列表不新增该 key

### Security（P1 + security）

- **TC-SEC-LABEL-001 未登录访问应进入登录流程**
  - 断言：URL 命中 `/Account/Login`（或等价登录路由）；不暴露受保护数据

## Step2 自动化落盘建议（对齐本仓库）

```
tests/
└── aevatar/
    └── management/
        └── subscription_labels/
            ├── test_subscription_labels_p0_p1.py
            └── test_subscription_labels_security.py
```

