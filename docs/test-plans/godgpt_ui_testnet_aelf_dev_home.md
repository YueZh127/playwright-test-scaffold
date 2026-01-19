# Test Plan: GodGPT UI Testnet - Home Page (Chat Interface)

## 1. 页面概述
- **Slug**: `godgpt_ui_testnet_aelf_dev_home`
- **URL**: `https://godgpt-ui-testnet.aelf.dev/` (登录后进入 `/(app)` 路由)
- **描述**: GodGPT 的核心交互界面，用户在此处与 AI 进行对话、管理会话历史、上传附件及配置个人信息。
- **风险点**: 
  - 消息流式输出的稳定性。
  - 会话切换后的上下文隔离。
  - 附件（图片/PDF）上传与解析。
  - 余额/Credits 校验逻辑。

## 2. 元素映射 (Locators)
| 元素名称 | 定位器 (Priority) | 类型 | 说明 |
| :--- | :--- | :--- | :--- |
| **聊天输入框** | `textarea[placeholder="Ask anything"]` | `textarea` | 支持多行输入，Enter 发送 |
| **发送按钮** | `button:has(svg[name="SendIcon"])` | `button` | 输入框有内容且非加载中时可用 |
| **侧边栏开关** | `button:has(svg[name="Logo30"])` | `button` | 切换侧边栏展开/收起 |
| **新会话按钮** | `text="New Chat"` | `button` | 重置当前会话，进入空白页 |
| **会话历史项** | `[role="link"]:has-text("...")` | `link` | 侧边栏中的历史记录列表 |
| **附件上传按钮** | `button:has(svg[name="PlusIcon"])` | `button` | 弹出图片/文件选择菜单 |
| **用户头像/设置** | `button:has-text("A")` | `button` | 打开用户 Profile / 登出菜单 |
| **建议提问项** | `[role="button"]:has-text("...")` | `button` | 页面中间的建议问题卡片 |
| **追问建议（4 个 chip）** | `components/ChatSuggestions` 渲染的 `Pressable(Text)`（推荐：`get_by_text(<chip_text>).click()` 或 `get_by_role("button", name=<chip_text>)`） | `button` | 每次 AI 回复后在输入框上方出现 4 个追问，可点击继续对话 |

## 3. 测试用例设计

### P0: 核心交互 (Core Flows)
| ID | 测试标题 | 验证规则 |
| :--- | :--- | :--- |
| TC-HOME-001 | 成功发送单条消息并获得 AI 回复 | 1. 输入消息后按 Enter 2. 输入框清空 3. AI 消息出现在列表中 4. **收到 AI 回复后，用户 Credits 数量应减少 10（非订阅用户）** |
| TC-HOME-002 | 创建新会话 (New Chat) | 1. 点击 New Chat 2. 消息列表清空 3. URL 路由重置 |
| TC-HOME-003 | 侧边栏历史记录切换 | 1. 点击侧边栏任一历史项 2. 消息列表加载对应历史内容 |
| TC-HOME-004 | 追问建议展示与可点击继续对话 | 1. 发送一条对话并等待 AI 回复结束 2. **输入框上方出现 4 个追问 chip** 3. **追问中包含“我不理解 / I don't understand”（i18n key: `chat_i_dont_understand`）** 4. 追问文本应与当前会话内容相关（来源：后端 `SuggestedItems`，若无法判定相关性则至少断言非空且互不相同） 5. 点击任一追问，追问文本应作为用户消息发送并产生新的 AI 回复 6. 追问语言应与会话语言一致（例如：英文会话出现 `I don't understand`；中文会话出现 `我不理解`） |

> 证据（扣费规则）：前端存在本地扣费逻辑 `custom-gpt-frontend/utils/hooks/useConsumeCredits.ts`，会将 `credits` 扣减 10（订阅用户不扣，且下限为 0）。

> 证据（追问 SuggestedItems + 渲染）：  
> - `custom-gpt-frontend/components/getAIData.ts`：流式结束时读取 `dataObj.SuggestedItems` 并调用 `setSuggestedItems?.(...)`。  
> - `custom-gpt-frontend/utils/hooks/useSuggestedItems.ts`：通过 react-query `queryClient.setQueryData(['suggestedItems', id], items)` 存储追问列表。  
> - `custom-gpt-frontend/components/ChatSuggestions/index.tsx`：当 `items.length>0` 时渲染横向 `FlatList`，每个 item 为 `Pressable`（可点击）。  
> - i18n：`custom-gpt-frontend/i18n/locales/*` 中 `chat_i_dont_understand`（en: "I don't understand", zh/zh-TW: "我不理解"）。

### P1: 边界与功能 (Functional & Boundary)
| ID | 测试标题 | 验证规则 |
| :--- | :--- | :--- |
| TC-HOME-101 | 输入框最大字符限制 | 1. 输入超过 `maxLength` (推导: 2000+) 2. 字符被截断或禁止输入 |
| TC-HOME-102 | 图片附件上传 | 1. 上传合规图片 2. 图片在输入框预览 3. 发送后 AI 识别图片 |
| TC-HOME-103 | 余额不足拦截 (Credits Check) | 1. 使用 **0 credits** 测试账号登录（来源：`test-data/test_account_pool.json` 中描述为“GodGPT 0 credits测试账户”，如 `automationtest3@drmail.in`） 2. 输入消息并尝试发送 3. 弹出 **Credits 用尽** toast（i18n: `credits_exhausted`）4. 消息不会进入会话列表 |
| TC-HOME-104 | 消息发送防抖 (Throttle) | 1. 极短时间内多次点击发送 2. 仅第一条发送成功 |

### P2: UI 与 易用性 (UI & Usability)
| ID | 测试标题 | 验证规则 |
| :--- | :--- | :--- |
| TC-HOME-201 | 响应式布局：侧边栏自动收起 | 1. 调整窗口至移动端宽度 2. 侧边栏默认隐藏 |
| TC-HOME-202 | 消息 Markdown 渲染 | 1. 诱导 AI 返回表格/代码块 2. UI 正确解析并高亮展示 |

## 4. 测试数据设计
| 数据组 | 字段 | 内容示例 |
| :--- | :--- | :--- |
| `valid_chat` | `message` | "What is aelf blockchain?" |
| `long_chat` | `message` | (2000+ characters random string) |
| `image_payload` | `file` | `test-data/assets/sample_image.png` |

## 5. 自动化实现建议
- **Page Object**: `pages/godgpt_ui_testnet_aelf_dev_home_page.py`
- **Fixture**: 使用 `test_account` fixture 完成前置登录。
- **稳定性**: 针对 AI 流式回复，断言需使用 `to_have_text` 或等待 `is_done` 标志位的元素出现。
- **清理**: 每次测试后视情况点击 "New Chat" 或删除会话（若涉及后端存储）。
