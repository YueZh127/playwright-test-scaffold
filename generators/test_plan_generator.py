# ═══════════════════════════════════════════════════════════════
# Playwright Test Scaffold - Test Plan Generator (Coordinator)
# ═══════════════════════════════════════════════════════════════
"""
测试计划生成器 - 协调器

说明：
- 本仓库的 `.cursor/rules/ui-test-plan-generator.mdc` 约束了测试计划的结构与落盘路径；
- 这里输出的 Markdown 以“可落地、可追溯、可执行”为目标，优先写清楚：证据链、定位策略、用例优先级与风险。
"""

from __future__ import annotations

import json
from datetime import datetime

from generators.page_types import PageInfo, PageElement
from generators.utils import (
    get_page_name_from_url,
    get_file_name_from_url,
    to_class_name,
    requires_auth,
)
from generators.test_plan_formatter import TestPlanFormatter
from generators.test_plan_scenarios import TestPlanScenarios
from utils.logger import get_logger

logger = get_logger(__name__)


class TestPlanGenerator:
    """测试计划生成器 - 协调器"""
    
    def __init__(self):
        """初始化子生成器"""
        self.formatter = TestPlanFormatter()
        self.scenarios = TestPlanScenarios()
    
    def generate(self, page_info: PageInfo) -> str:
        """
        生成测试计划（对齐 ui-test-plan-generator.mdc）。

        注意：
        - 证据链目录按约定计算：docs/test-plans/artifacts/<slug>/
          实际写入由调用方负责（当前推荐手动流程，不依赖历史一键入口）。
        """
        logger.info(f"生成测试计划: {page_info.url}")
        return self._generate_rule_compliant(page_info)

    # ═══════════════════════════════════════════════════════════════
    # Rule-compliant generator (ui-test-plan-generator.mdc)
    # ═══════════════════════════════════════════════════════════════

    def _generate_rule_compliant(self, page_info: PageInfo) -> str:
        slug = get_file_name_from_url(page_info.url)
        page_name = get_page_name_from_url(page_info.url)
        class_name = f"{to_class_name(page_name)}Page"
        need_auth = "是" if requires_auth(page_info.page_type) else "否"

        overview = self._overview_lines(page_info)
        risk = self._risk_lines(page_info)
        mapping = self._element_mapping_table(page_info)
        pom = self._pom_skeleton(page_info, class_name=class_name)
        cases = self._cases_block(page_info)
        data = self._test_data_json(page_info)
        impl = self._implementation_suggestions(page_info, slug=slug, class_name=class_name)

        return "\n".join(
            [
                f"# {page_name} UI 自动化测试计划",
                "",
                "## 0. 生成信息（用于可追溯）",
                f"- **URL**: `{page_info.url}`",
                f"- **slug**: `{slug}`",
                f"- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **是否需要登录态**: {need_auth}",
                f"- **证据链目录**: `docs/test-plans/artifacts/{slug}/`",
                "",
                "## 1. 页面概述",
                f"- **页面类型**: {page_info.page_type}",
                "- **主要功能（用户任务流）**:",
                *[f"  - {x}" for x in overview],
                "- **风险点**:",
                *[f"  - {x}" for x in risk],
                "- **测试优先级**: 高（涉及权限/敏感操作/不可逆风险的页面默认 P0 覆盖）",
                "",
                "## 2. 页面元素映射",
                "### 2.1 关键元素识别",
                mapping,
                "",
                "### 2.2 页面对象设计（骨架）",
                "```python",
                *pom.splitlines(),
                "```",
                "",
                "## 3. 测试用例设计",
                cases,
                "",
                "## 4. 测试数据设计（JSON）",
                "```json",
                json.dumps(data, indent=2, ensure_ascii=False),
                "```",
                "",
                "## 5. 自动化实现建议（对齐本仓库）",
                impl,
                "",
                "## 6. 执行计划",
                "- **开发阶段**: 先补齐 PageObject 定位与关键动作 → 再补 P0 用例 → 最后补 P1/P2/安全类用例",
                "- **测试阶段**: 本地稳定跑通（含重试与截图）→ CI 分层执行（smoke/p0/regression）",
                "- **验收标准**: P0 全绿 + 失败有截图/日志证据链 + 关键断言不脆弱（避免写死易变文案）",
            ]
        ).strip() + "\n"

    def _overview_lines(self, page_info: PageInfo) -> list[str]:
        url = (page_info.url or "").lower()
        if "change-password" in url or "password" in url:
            return [
                "进入页面并确认关键表单可见",
                "输入当前密码 / 新密码 / 确认新密码",
                "提交修改并观察成功/失败反馈（toast/表单错误/跳转）",
            ]
        if page_info.page_type == "SETTINGS":
            return ["进入设置页", "修改配置项", "保存并验证结果"]
        return ["进入页面", "完成主要交互", "验证可观察结果（UI 状态/业务结果）"]

    def _risk_lines(self, page_info: PageInfo) -> list[str]:
        url = (page_info.url or "").lower()
        risks = []
        if requires_auth(page_info.page_type):
            risks.append("鉴权/权限：未登录或权限不足时的跳转与提示必须正确")
        if "password" in url:
            risks.extend(
                [
                    "敏感信息：密码输入/错误提示不能泄露策略细节",
                    "安全性：防 XSS/注入，避免把用户输入当作 HTML 执行",
                    "不可逆/影响面：修改密码可能导致会话失效、影响后续登录",
                ]
            )
        if not risks:
            risks.append("稳定性：定位器漂移/异步加载导致 flaky")
        return risks

    def _locator_suggestion(self, e: PageElement) -> tuple[str, str]:
        """
        输出：定位策略、定位器（优先 role/name，其次 css 兜底）
        """
        txt = (e.text or "").strip()
        # 自定义按钮（div tabindex=0 + :has-text）用 role/name 往往拿不到；强制用 css
        sel = (e.selector or "").strip()
        if sel and ":has-text(" in sel:
            return "css", f'page.locator("{sel}").first'
        if e.type == "button" and txt:
            # 文本太长会导致 get_by_role(name=...) 不可用；此时仍用 css 更稳
            if len(txt) > 40 and sel:
                return "css", f'page.locator("{sel}").first'
            return "role/name", f'page.get_by_role("button", name="{txt}")'
        if e.type == "link" and txt:
            return "role/linkText", f'page.get_by_role("link", name="{txt}")'
        if e.role:
            return "role", f'page.get_by_role("{e.role}")'
        return "css", f'page.locator("{e.selector}")'

    def _semantic_hint(self, e: PageElement) -> str:
        """
        粗略给出业务语义（用于计划，不参与执行）。
        """
        key = " ".join([(e.name or ""), (e.id or ""), (e.placeholder or ""), (e.text or "")]).lower()
        if e.type == "input" and (e.attributes.get("type") or "").lower() == "password":
            if "current" in key or "old" in key:
                return "当前密码"
            if "confirm" in key or "repeat" in key:
                return "确认新密码"
            if "new" in key:
                return "新密码"
            return "密码输入"
        if e.type == "button":
            if "save" in key or "submit" in key or "confirm" in key:
                return "提交/保存"
            return "按钮操作"
        if e.type == "link":
            return "导航/跳转"
        return "表单字段/交互"

    def _checkpoints(self, e: PageElement) -> str:
        if e.type == "input":
            pts = ["可输入", "可清空", "校验提示（必填/格式/长度）"]
            if (e.attributes.get("type") or "").lower() == "password":
                pts.append("mask 显示/不回显明文")
            return " / ".join(pts)
        if e.type == "button":
            pts = ["可点击", "loading/禁用态", "触发结果（toast/错误提示/跳转）"]
            return " / ".join(pts)
        return "可见 / 可交互 / 行为正确"

    def _element_mapping_table(self, page_info: PageInfo) -> str:
        rows = []
        for e in (page_info.elements or []):
            strategy, locator = self._locator_suggestion(e)
            desc = self._semantic_hint(e)
            rows.append(
                "| {t} | {d} | {biz} | {st} | `{loc}` | {chk} | {dep} |".format(
                    t=e.type or "-",
                    d=(e.text or e.placeholder or e.name or e.id or "-").strip()[:60] or "-",
                    biz=desc,
                    st=strategy,
                    loc=locator,
                    chk=self._checkpoints(e),
                    dep="需要登录态" if requires_auth(page_info.page_type) else "无",
                )
            )
        if not rows:
            rows.append("| - | - | - | - | - | - | - |")
        return "\n".join(
            [
                "| 元素类型 | 元素描述 | 业务语义 | 定位策略 | 定位器 | 可校验点 | 依赖前置 |",
                "|---------|----------|----------|----------|--------|----------|----------|",
                *rows,
            ]
        )

    def _pom_skeleton(self, page_info: PageInfo, *, class_name: str) -> str:
        # 只给骨架：避免把执行细节塞进计划
        return "\n".join(
            [
                "from core.base_page import BasePage",
                "",
                "# ============================================================",
                f"# 页面对象：{class_name}",
                "# - 目标：封装稳定定位器与业务操作",
                "# - 原则：短小、直白、少分支",
                "# ============================================================",
                f"class {class_name}(BasePage):",
                "    # 元素定位器（优先 role/label/testid；必要时给 2 套策略）",
                "    # CURRENT_PASSWORD_INPUT = ...",
                "    # NEW_PASSWORD_INPUT = ...",
                "    # CONFIRM_PASSWORD_INPUT = ...",
                "    # SUBMIT_BUTTON = ...",
                "",
                "    def navigate(self) -> None:",
                f"        self.goto(\"{page_info.url}\")",
                "",
                "    def is_loaded(self) -> bool:",
                "        # 以关键元素作为“已加载”判定",
                "        return True",
                "",
                "    # --------------------------------------------------------",
                "    # 业务动作（示例）",
                "    # --------------------------------------------------------",
                "    def submit_change_password(self, current_pwd: str, new_pwd: str, confirm_pwd: str) -> None:",
                "        # TODO: 填写并提交；失败时保留截图与上下文（证据链）",
                "        pass",
            ]
        )

    def _cases_block(self, page_info: PageInfo) -> str:
        # 对齐模板，给出可执行的用例骨架；内容尽量贴合 password change
        url = (page_info.url or "").lower()
        is_pwd = "password" in url

        base = [
            "- **TC001**: 页面加载",
            "  - **标签**: [@smoke @p0]",
            "  - **前置条件**: 已登录（若需要）",
            "  - **测试步骤**: 打开页面 → 等待稳定 → 关键元素可见",
            "  - **预期结果**: 页面可用且无阻塞错误",
            "  - **断言层级**: UI 状态",
            "  - **优先级**: 高",
        ]

        if not is_pwd:
            return "\n".join(["### 3.1 功能测试用例", *base, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例"])

        pwd_cases = [
            "- **TC002**: 必填校验（未填当前密码）",
            "  - **标签**: [@p0 @validation]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 仅填写新密码/确认密码 → 提交",
            "  - **预期结果**: 当前密码出现必填提示；提交被阻止",
            "  - **断言层级**: UI 状态",
            "  - **优先级**: 高",
            "",
            "- **TC003**: 新密码与确认密码不一致",
            "  - **标签**: [@p0 @validation]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 填写当前密码 → 新密码/确认密码填不一致 → 提交",
            "  - **预期结果**: 提示不一致；不调用提交或提交失败可观测",
            "  - **断言层级**: UI 状态/可观察性（toast/接口）",
            "  - **优先级**: 高",
            "",
            "- **TC004**: 当前密码错误",
            "  - **标签**: [@p0 @exception]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 输入错误当前密码 → 输入合法新密码/确认 → 提交",
            "  - **预期结果**: 显示错误提示；密码不被修改",
            "  - **断言层级**: 业务结果（仍可用旧密码登录）/UI 提示",
            "  - **优先级**: 高",
            "",
            "- **TC005**: 修改成功",
            "  - **标签**: [@p0]",
            "  - **前置条件**: 已登录；账号可用于修改密码",
            "  - **测试步骤**: 输入正确当前密码 → 输入合法新密码/确认 → 提交",
            "  - **预期结果**: 成功提示；必要时要求重新登录/会话更新符合预期",
            "  - **断言层级**: 业务结果 + UI 状态",
            "  - **优先级**: 高",
        ]

        sec = [
            "- **TC006**: 未登录访问重定向/拦截",
            "  - **标签**: [@p1 @auth]",
            "  - **前置条件**: 未登录",
            "  - **测试步骤**: 直接访问 URL",
            "  - **预期结果**: 跳转到登录页或显示未授权提示",
            "  - **断言层级**: UI 状态/可观察性",
            "  - **优先级**: 中",
            "",
            "- **TC007**: XSS 输入不执行",
            "  - **标签**: [@p1 @security]",
            "  - **前置条件**: 已登录",
            "  - **测试步骤**: 在输入框填入 `<script>alert(1)</script>` 等 payload → 提交",
            "  - **预期结果**: 不弹窗；输入被当作普通字符串处理",
            "  - **断言层级**: 可观察性（无 dialog）",
            "  - **优先级**: 中",
        ]

        return "\n".join(["### 3.1 功能测试用例", *base, "", *pwd_cases, "", "### 3.2 边界测试用例", "", "### 3.3 异常测试用例", "", *sec])

    def _test_data_json(self, page_info: PageInfo) -> dict:
        url = (page_info.url or "").lower()
        if "password" in url:
            return {
                "valid": [
                    {
                        "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                        "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                        "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    }
                ],
                "invalid": [
                    {
                        "case": "missing_current_password",
                        "currentPassword": "",
                        "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                        "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    },
                    {
                        "case": "wrong_current_password",
                        "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD_WRONG",
                        "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                        "confirmNewPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                    },
                    {
                        "case": "mismatch_confirm_password",
                        "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                        "newPasswordEnv": "TEST_NEW_PASSWORD_VALID",
                        "confirmNewPasswordLiteral": "__DIFFERENT_FROM_NEW__",
                    },
                ],
                "boundary": [
                    {
                        "case": "new_password_min_minus_1",
                        "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                        "newPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                        "confirmNewPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                    },
                    {
                        "case": "new_password_max_plus_1",
                        "currentPasswordEnv": "TEST_ACCOUNT_PASSWORD",
                        "newPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                        "confirmNewPasswordLiteral": "__TBD_BY_ABP_POLICY__",
                    },
                ],
            }
        return {
            "valid": [{"field1": "value1", "field2": "value2"}],
            "invalid": [{"field1": "", "field2": "invalid"}],
            "boundary": [{"field1": "min", "field2": "max"}],
        }

    def _implementation_suggestions(self, page_info: PageInfo, *, slug: str, class_name: str) -> str:
        # 对齐仓库目录结构与命名惯例
        module = (slug.split("_")[0] or "admin").strip()
        return "\n".join(
            [
                "### 5.1 页面类实现",
                f"- 建议 PageObject：`pages/{slug}_page.py`（类名 `{class_name}`，继承 `core/base_page.py:BasePage`）",
                "- 把“业务动作”封装成方法（不要在测试里散落 click/fill）",
                "- 定位器优先级：role/name、label、data-testid；必要时提供 CSS 兜底（两套策略）",
                "",
                "### 5.2 测试类实现",
                f"- 建议测试目录：`tests/{module}/{slug}/` 或对齐现有 suite 目录",
                "- 用 pytest 标记分层（@smoke/@p0/@p1/@security）",
                "- 数据驱动（valid/invalid/boundary）减少重复代码",
                "",
                "### 5.3 配置建议",
                "- 若需要：在 `config/project.yaml` 补充 base_url/账号策略",
                "- 若涉及账号：复用 `test-data/test_account_pool.json`，并在用例前做账号可用性预检",
            ]
        )

    def _test_cases(self, page_info: PageInfo) -> str:
        """
        测试用例章节（来自 TestPlanScenarios）。
        
        说明：
        - formatter 负责“文档结构/排版”
        - scenarios 负责“具体用例内容”
        - 这里显式组合，避免 formatter 误持有 scenarios 的内部方法
        """
        cases = []

        cases.append("### 3.1 P0 - Critical Tests (核心功能)")
        cases.extend(self.scenarios._p0_tests(page_info))

        cases.append("\n### 3.2 P1 - High Priority Tests (重要功能)")
        cases.extend(self.scenarios._p1_tests(page_info))

        cases.append("\n### 3.3 P2 - Medium Priority Tests (一般功能)")
        cases.extend(self.scenarios._p2_tests(page_info))

        return f"""## 3. Test Cases

{chr(10).join(cases)}"""
    
    # ═══════════════════════════════════════════════════════════════
    # SECTION GENERATORS
    # ═══════════════════════════════════════════════════════════════
    

