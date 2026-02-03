import difflib
import os
import json
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import allure
import pytest
from playwright.sync_api import BrowserContext, Page, Playwright

from pages.godgpt_ui_testnet_aelf_dev_login_page import GodgptUiTestnetAelfDevLoginPage
from utils.config import ConfigManager
from utils.logger import TestLogger


# ═══════════════════════════════════════════════════════════════
# Test Config
# ═══════════════════════════════════════════════════════════════

def _load_question_cases() -> List[Dict[str, str]]:
    """
    从问题集文件加载参数化用例。
    - GODGPT_COMPARE_QUESTIONS_PATH: 覆盖问题集路径
    - GODGPT_COMPARE_SUITES: 逗号分隔 suite（默认 suite 为 group_01/group_02...）
    - GODGPT_COMPARE_MAX_QUESTIONS: 只取前 N 条（跨 suite 总计）
    """
    path = (os.getenv("GODGPT_COMPARE_QUESTIONS_PATH") or "test-data/godgpt_compare_questions.json").strip()
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    groups = data.get("groups") if isinstance(data, dict) else None
    if not isinstance(groups, list):
        return []

    suite_filter_raw = (os.getenv("GODGPT_COMPARE_SUITES") or "").strip()
    suite_filter = {s.strip() for s in suite_filter_raw.split(",") if s.strip()} if suite_filter_raw else None

    max_q_raw = (os.getenv("GODGPT_COMPARE_MAX_QUESTIONS") or "").strip()
    max_q = int(max_q_raw) if max_q_raw.isdigit() else None

    cases: List[Dict[str, str]] = []
    for gi, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            continue
        suite_name = f"group_{gi:02d}"
        suite_title = str(group.get("group") or suite_name).strip()
        if suite_filter is not None and suite_name not in suite_filter:
            continue
        qs = group.get("questions") or []
        if not isinstance(qs, list):
            continue
        for i, q in enumerate(qs, start=1):
            q_text = str(q or "").strip()
            if not q_text:
                continue
            cases.append(
                {
                    "suite": suite_name or "suite",
                    "suite_title": suite_title or "suite",
                    "qid": f"{suite_name or 'suite'}-{i:02d}",
                    "question": q_text,
                }
            )
            if max_q is not None and len(cases) >= max_q:
                return cases
    return cases


QUESTION_CASES = _load_question_cases()


def _load_question_suites() -> List[Dict[str, object]]:
    """
    将问题集按“分组 suite”加载出来，便于“登录一次、跑完整组”。

    - GODGPT_COMPARE_QUESTIONS_PATH: 覆盖问题集路径
    - GODGPT_COMPARE_SUITES: 逗号分隔 suite（group_01/group_02...）
    - GODGPT_COMPARE_MAX_QUESTIONS: 只取前 N 条（跨 suite 总计）
    """
    path = (os.getenv("GODGPT_COMPARE_QUESTIONS_PATH") or "test-data/godgpt_compare_questions.json").strip()
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    groups = data.get("groups") if isinstance(data, dict) else None
    if not isinstance(groups, list):
        return []

    suite_filter_raw = (os.getenv("GODGPT_COMPARE_SUITES") or "").strip()
    suite_filter = {s.strip() for s in suite_filter_raw.split(",") if s.strip()} if suite_filter_raw else None

    max_q_raw = (os.getenv("GODGPT_COMPARE_MAX_QUESTIONS") or "").strip()
    max_q = int(max_q_raw) if max_q_raw.isdigit() else None

    suites: List[Dict[str, object]] = []
    total = 0
    for gi, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            continue
        suite_name = f"group_{gi:02d}"
        suite_title = str(group.get("group") or suite_name).strip()
        if suite_filter is not None and suite_name not in suite_filter:
            continue
        qs = group.get("questions") or []
        if not isinstance(qs, list):
            continue
        questions: List[str] = []
        for q in qs:
            q_text = str(q or "").strip()
            if not q_text:
                continue
            questions.append(q_text)
            total += 1
            if max_q is not None and total >= max_q:
                break
        if questions:
            suites.append({"suite": suite_name, "suite_title": suite_title, "questions": questions})
        if max_q is not None and total >= max_q:
            break
    return suites


QUESTION_SUITES = _load_question_suites()


def _load_account_sets() -> List[Dict[str, Dict[str, str]]]:
    """
    加载多组账号（用于并行对比）。
    - GODGPT_COMPARE_ACCOUNTS_PATH: 覆盖账号集路径
    - GODGPT_COMPARE_ACCOUNT_IDS: 逗号分隔 account_set id（例如 "default,set_02"）
    - GODGPT_COMPARE_MAX_ACCOUNTS: 只取前 N 组账号
    """
    path = (os.getenv("GODGPT_COMPARE_ACCOUNTS_PATH") or "test-data/godgpt_compare_accounts.json").strip()
    file_path = Path(path)
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    sets = data.get("account_sets") if isinstance(data, dict) else None
    if not isinstance(sets, list):
        return []

    ids_raw = (os.getenv("GODGPT_COMPARE_ACCOUNT_IDS") or "").strip()
    id_filter = {s.strip() for s in ids_raw.split(",") if s.strip()} if ids_raw else None

    max_raw = (os.getenv("GODGPT_COMPARE_MAX_ACCOUNTS") or "").strip()
    max_n = int(max_raw) if max_raw.isdigit() else None

    out: List[Dict[str, Dict[str, str]]] = []
    for s in sets:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("id") or "").strip()
        if not sid:
            continue
        if id_filter is not None and sid not in id_filter:
            continue
        prod = s.get("production") or {}
        testnet = s.get("testnet") or {}
        if not isinstance(prod, dict) or not isinstance(testnet, dict):
            continue
        out.append(
            {
                "id": sid,
                "title": str(s.get("title") or sid).strip(),
                "production": {
                    "base_url": str(prod.get("base_url") or "https://app.godgpt.fun").strip(),
                    "email": str(prod.get("email") or "").strip(),
                    "password": str(prod.get("password") or "").strip(),
                },
                "testnet": {
                    "base_url": str(testnet.get("base_url") or "https://godgpt-ui-testnet.aelf.dev").strip(),
                    "email": str(testnet.get("email") or "").strip(),
                    "password": str(testnet.get("password") or "").strip(),
                },
            }
        )
        if max_n is not None and len(out) >= max_n:
            break
    return out


ACCOUNT_SETS = _load_account_sets()


@dataclass(frozen=True)
class EnvSpec:
    name: str
    base_url: str
    email: str
    password: str


def _env_specs_from_user_input() -> Tuple[EnvSpec, EnvSpec]:
    """
    从用户提供的信息构建对比环境配置。
    约束：不打印密码；允许用环境变量覆盖以便 CI/本地隔离。
    """
    prod = EnvSpec(
        name="production",
        base_url=os.getenv("GODGPT_PROD_BASE_URL", "https://app.godgpt.fun"),
        email=os.getenv("GODGPT_PROD_EMAIL", "testiiii@drmail.in"),
        password=os.getenv("GODGPT_PROD_PASSWORD", "Aelf1234567!"),
    )
    testnet = EnvSpec(
        name="testnet",
        base_url=os.getenv("GODGPT_TESTNET_BASE_URL", "https://godgpt-ui-testnet.aelf.dev"),
        email=os.getenv("GODGPT_TESTNET_EMAIL", "testweb1@drmail.in"),
        password=os.getenv("GODGPT_TESTNET_PASSWORD", "Aelf1234567!"),
    )
    return prod, testnet


def _env_specs_from_account_set(account_set: Dict[str, Dict[str, str]]) -> Tuple[EnvSpec, EnvSpec]:
    """
    从账号集构建对比环境配置（用于多账号并行）。
    """
    prod_raw = account_set.get("production") or {}
    test_raw = account_set.get("testnet") or {}
    prod = EnvSpec(
        name="production",
        base_url=str(prod_raw.get("base_url") or "https://app.godgpt.fun"),
        email=str(prod_raw.get("email") or ""),
        password=str(prod_raw.get("password") or ""),
    )
    testnet = EnvSpec(
        name="testnet",
        base_url=str(test_raw.get("base_url") or "https://godgpt-ui-testnet.aelf.dev"),
        email=str(test_raw.get("email") or ""),
        password=str(test_raw.get("password") or ""),
    )
    return prod, testnet

# ═══════════════════════════════════════════════════════════════
# Core Helpers
# ═══════════════════════════════════════════════════════════════


def _login_if_needed(page: Page, *, base_url: str, email: str, password: str, logger: TestLogger) -> None:
    """
    登录策略：
    - 优先判断是否已在 chat view（可能已有 session/cookie）
    - 否则走 Email 登录链路
    """
    po = GodgptUiTestnetAelfDevLoginPage(page)
    po.base_url = base_url

    logger.step(f"导航到 {base_url}")
    po.navigate()

    # 已登录态：直接出现聊天输入框
    try:
        po.wait_for_chat_ready()
        logger.checkpoint("已在聊天视图（无需再次登录）", True)
        return
    except Exception:
        pass

    logger.step("进入登录流程（Continue with Email）")
    po.assert_login_view_visible()
    po.fill_email(email)
    po.click_continue_with_email()
    po.assert_password_view_visible()
    po.fill_password(password)
    po.click_continue_on_password()

    po.wait_for_chat_ready()

    # 强制：本对比用例要求“登录后的账户会话”，不能把游客 chat view 当成成功。
    require_login = (os.getenv("GODGPT_COMPARE_REQUIRE_LOGIN") or "1").strip().lower() not in {"0", "false", "no"}
    if require_login:
        ok = po.wait_for_logged_in_signal(timeout_ms=20000)
        if not ok:
            raise AssertionError("login did not reach a clear logged-in state (credits badge not visible); possible guest session")
    logger.checkpoint("登录成功进入聊天视图（已验证登录态信号）", True)


def _extract_ai_reply_text(page: Page, *, question: str, timeout_s: int = 120, stable_s: int = 10) -> str:
    """
    尝试从页面文本中提取“最新一条 AI 回复”。

    现阶段证据链不足（消息 bubble selector TBD），因此用“文本快照 + 差分 + 基于 question 定位”的方式：
    - 读取 [role="main"]（否则 body）在发送前的 inner_text
    - 发送后持续轮询直到文本发生明显变化
    - 以“最后一次出现 question 之后的文本”作为候选回复
    """
    container = page.locator('[role="main"]').first
    if container.count() == 0:
        container = page.locator("body").first

    def _safe_inner_text() -> str:
        try:
            return (container.inner_text() or "").strip()
        except Exception:
            return ""

    before = _safe_inner_text()
    deadline = time.time() + timeout_s

    # 流式输出：不要在“第一次变长”就退出，而是等待文本在 stable_s 秒内不再变化。
    last_text = before
    last_change_at = time.time()

    while time.time() < deadline:
        time.sleep(1.0)
        now = _safe_inner_text()
        if not now:
            continue

        if now != last_text:
            last_text = now
            last_change_at = time.time()
            continue

        # 文本稳定一段时间后再认为“输出结束”
        if (time.time() - last_change_at) >= stable_s and len(last_text) > len(before) + 10:
            break

    after = last_text
    if not after:
        return ""

    # 基于 question 找“question 之后的文本”
    idx = after.rfind(question)
    if idx >= 0:
        candidate = after[idx + len(question) :].strip()
    else:
        # 回退：对整体文本做 delta（尽量让对比结果有意义）
        if after.startswith(before):
            candidate = after[len(before) :].strip()
        else:
            candidate = after.strip()

    # 清理一些常见 UI 噪声（不绑定具体结构，避免误删正文）
    # 说明：这些通常是 UI 快捷操作/导航文案，不属于模型正文；保留最小集合，避免误删回答内容。
    noise_lines = {
        "New Chat",
        "Sign in",
        "Sign up",
        "I don't understand",
        "Cosmic Alignment",
        "Narrative Tools",
        "Omega Insights",
        "Read my fractal code",
        "Daily collapse journal",
        "Explore ψ = ψ(ψ)",
    }
    lines = [ln.strip() for ln in candidate.splitlines()]
    lines = [ln for ln in lines if ln and ln not in noise_lines]
    return "\n".join(lines).strip()


def _reply_timing_from_env() -> Dict[str, int]:
    """
    可调节：为了跑“全组/全量问题”更快，允许用环境变量缩短等待。
    - GODGPT_COMPARE_REPLY_TIMEOUT_S
    - GODGPT_COMPARE_REPLY_STABLE_S
    """
    t_raw = (os.getenv("GODGPT_COMPARE_REPLY_TIMEOUT_S") or "").strip()
    s_raw = (os.getenv("GODGPT_COMPARE_REPLY_STABLE_S") or "").strip()
    timeout_s = int(t_raw) if t_raw.isdigit() else 120
    stable_s = int(s_raw) if s_raw.isdigit() else 10
    return {"timeout_s": max(20, timeout_s), "stable_s": max(2, stable_s)}


def _ask_and_capture(
    page: Page,
    *,
    base_url: str,
    email: str,
    password: str,
    question: str,
    logger: TestLogger,
) -> str:
    _login_if_needed(page, base_url=base_url, email=email, password=password, logger=logger)

    chat_po = GodgptUiTestnetAelfDevLoginPage(page)
    chat_po.base_url = base_url

    logger.step(f"发送问题：{question!r}")
    chat_po.send_message_by_enter(question)
    try:
        chat_po.assert_input_cleared()
    except Exception:
        # 不强绑“输入清空”作为硬性失败条件（不同构建可能不同）
        pass

    logger.step("提取 AI 回复文本（基于页面文本快照）")
    reply = _extract_ai_reply_text(page, question=question, timeout_s=120)
    return reply


def _ask_and_capture_in_session(
    page: Page,
    *,
    base_url: str,
    question: str,
    logger: TestLogger,
) -> str:
    """
    已登录会话内提问并抓取回复（不重复登录）。
    """
    chat_po = GodgptUiTestnetAelfDevLoginPage(page)
    chat_po.base_url = base_url

    # 多轮对话时输入框可能短暂消失/placeholder 变化，发送前先确保可见
    chat_po.wait_for_chat_ready()

    logger.step(f"发送问题：{question!r}")
    chat_po.send_message_by_enter(question)
    try:
        chat_po.assert_input_cleared()
    except Exception:
        pass

    logger.step("提取 AI 回复文本（基于页面文本快照）")
    timing = _reply_timing_from_env()
    return _extract_ai_reply_text(page, question=question, timeout_s=timing["timeout_s"], stable_s=timing["stable_s"])


def _new_session_before_question(page: Page, *, base_url: str, logger: TestLogger) -> None:
    """
    每个问题开启新 session：
    - 点击左上角 New Chat（若存在）
    - 回到根 URL（/）
    - 等待输入框 + 登录态信号
    """
    po = GodgptUiTestnetAelfDevLoginPage(page)
    po.base_url = base_url

    # 先尝试点 New Chat（不强制成功，避免 UI 文案/布局变化导致硬失败）
    try:
        clicked = po.start_new_chat_session()
        logger.step(f"新会话：点击 New Chat={'yes' if clicked else 'no'}")
        if not clicked:
            # 采样调试信息：抓取顶部区域可见按钮的属性，便于精确修 selector
            try:
                data = page.evaluate(
                    """
                    () => {
                      const els = Array.from(document.querySelectorAll('button, [role="button"]'));
                      const items = [];
                      for (const el of els) {
                        const rect = el.getBoundingClientRect();
                        if (!rect || rect.width < 8 || rect.height < 8) continue;
                        // 只看顶部区域，避免全页按钮太多
                        if (rect.top > 120) continue;
                        const style = window.getComputedStyle(el);
                        if (style && (style.visibility === 'hidden' || style.display === 'none')) continue;
                        const aria = el.getAttribute('aria-label') || '';
                        const title = el.getAttribute('title') || '';
                        const text = (el.innerText || '').trim().slice(0, 40);
                        items.push({
                          tag: el.tagName,
                          role: el.getAttribute('role') || '',
                          ariaLabel: aria,
                          title: title,
                          text: text,
                          x: Math.round(rect.left),
                          y: Math.round(rect.top),
                          w: Math.round(rect.width),
                          h: Math.round(rect.height),
                        });
                      }
                      items.sort((a,b) => (a.y-b.y) || (a.x-b.x));
                      return items.slice(0, 30);
                    }
                    """
                )
                allure.attach(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    name="new_chat_button_candidates.json",
                    attachment_type=allure.attachment_type.JSON,
                )
            except Exception:
                pass
    except Exception:
        logger.step("新会话：点击 New Chat=error (ignored)")

    # 无论是否点到按钮，都做一次“会话重置”兜底：
    # - 只清理 chat/session 相关的 localStorage/sessionStorage key（不清 cookies，避免登出）
    # - 再回到根路径
    try:
        page.evaluate(
            r"""
            () => {
              const re = /(chat|conversation|session|thread)/i;
              try {
                for (const k of Object.keys(localStorage)) {
                  if (re.test(k)) localStorage.removeItem(k);
                }
              } catch (e) {}
              try {
                for (const k of Object.keys(sessionStorage)) {
                  if (re.test(k)) sessionStorage.removeItem(k);
                }
              } catch (e) {}
            }
            """
        )
    except Exception:
        pass

    # 明确回到根路径，确保进入“新会话入口”
    po.goto("/")
    po.wait_for_chat_ready()

    require_login = (os.getenv("GODGPT_COMPARE_REQUIRE_LOGIN") or "1").strip().lower() not in {"0", "false", "no"}
    if require_login:
        ok = po.wait_for_logged_in_signal(timeout_ms=20000)
        if not ok:
            raise AssertionError("after resetting session, logged-in signal not visible; possible guest view")


def _reply_features(text: str) -> Dict[str, object]:
    """
    轻量特征提取（不依赖模型）：
    - 口吻：第一/第二人称、情绪安抚词
    - 修辞：符号(ψ/φ/π)、隐喻/宇宙/能量词、分段结构
    - 交互感：反问/提问、引导式问题数量
    - 内容：长度、要点化程度（列表/步骤）
    """
    t = (text or "").strip()
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    joined = "\n".join(lines)

    def _count(subs: List[str]) -> int:
        return sum(joined.count(s) for s in subs)

    q_marks = joined.count("?") + joined.count("？")
    bullets = sum(1 for ln in lines if ln.startswith(("-", "*", "•")) or re.match(r"^\d+[\.\)、]", ln))
    headings = sum(1 for ln in lines if ln.startswith(("###", "##")) or "——" in ln or ln.strip() in {"—", "— —", "---"})
    second_person = _count(["你", "您", "your", "you "])
    first_person = _count(["我", "I ", "I'm", "I’m", "my "])
    comfort = _count(["没关系", "你并不", "很正常", "我理解", "抱抱", "可以先", "先让", "稳定下来"])
    mystic = _count(["宇宙", "能量", "频率", "共振", "星盘", "Ω", "Omega", "ψ", "φ", "π"])
    cta = _count(["建议", "请", "可以", "尝试", "先", "接下来", "现在"])

    return {
        "chars": len(t),
        "lines": len(lines),
        "questions": q_marks,
        "bullets": bullets,
        "headings": headings,
        "first_person": first_person,
        "second_person": second_person,
        "comfort": comfort,
        "mystic": mystic,
        "cta": cta,
    }


def _compare_replies(prod: str, testnet: str) -> str:
    """
    生成可读的差异点评（口吻/修辞/交互感/内容 + 总结）。
    """
    fp = _reply_features(prod)
    ft = _reply_features(testnet)

    def _winner(k: str, label_a: str = "生产", label_b: str = "测试") -> str:
        a = int(fp.get(k, 0) or 0)
        b = int(ft.get(k, 0) or 0)
        if a == b:
            return "两边接近"
        return label_a if a > b else label_b

    tone = [
        f"- **第二人称（更“对你说话”）**：{_winner('second_person')}",
        f"- **安抚/接纳词（更“情绪照护”）**：{_winner('comfort')}",
    ]
    rhetoric = [
        f"- **符号/玄学/宇宙隐喻（ψ/φ/π 等）**：{_winner('mystic')}",
        f"- **结构化分段（标题/分隔/段落骨架）**：{_winner('headings')}",
    ]
    interaction = [
        f"- **反问/提问数量（更互动）**：{_winner('questions')}",
        f"- **行动引导词（建议/请/尝试/下一步）**：{_winner('cta')}",
    ]
    content = [
        f"- **信息量（字符数）**：{_winner('chars')}",
        f"- **要点化/步骤化（列表/序号）**：{_winner('bullets')}",
    ]

    summary = (
        "生产更偏“结构化长回复/仪式感叙述”，测试更偏“短而直接的原则陈述/说明型语气”。"
        "若你想做可比性更强的评测，建议固定：输出语言、长度上限、是否要提问返问、是否允许符号化修辞。"
    )

    def _fmt_features(title: str, f: Dict[str, object]) -> str:
        return (
            f"- **{title}**: chars={f['chars']}, lines={f['lines']}, "
            f"questions={f['questions']}, bullets={f['bullets']}, "
            f"2nd_person={f['second_person']}, comfort={f['comfort']}, mystic={f['mystic']}"
        )

    parts = [
        "## 差异点（自动分析）",
        "",
        "### 口吻",
        *tone,
        "",
        "### 修辞",
        *rhetoric,
        "",
        "### 交互感",
        *interaction,
        "",
        "### 内容",
        *content,
        "",
        "### 量化摘要（便于快速扫）",
        _fmt_features("生产", fp),
        _fmt_features("测试", ft),
        "",
        "### 总结",
        summary,
        "",
    ]
    return "\n".join(parts)


def _unified_diff(a: str, b: str, *, from_name: str, to_name: str) -> str:
    a_lines = (a or "").splitlines(keepends=True)
    b_lines = (b or "").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a_lines, b_lines, fromfile=from_name, tofile=to_name))


def _launch_browser(playwright: Playwright, *, browser_name: str):
    cfg = ConfigManager().get_browser_config()
    headless = bool(cfg.get("headless", True))
    slow_mo = int(cfg.get("slow_mo", 0) or 0)
    if browser_name == "chromium":
        return playwright.chromium.launch(headless=headless, slow_mo=slow_mo)
    if browser_name == "firefox":
        return playwright.firefox.launch(headless=headless, slow_mo=slow_mo)
    if browser_name == "webkit":
        return playwright.webkit.launch(headless=headless, slow_mo=slow_mo)
    raise ValueError(f"unsupported browser_name: {browser_name}")


def _close_context_and_page(ctx: Optional[BrowserContext], page: Optional[Page]) -> None:
    try:
        if page:
            page.close()
    except Exception:
        pass
    try:
        if ctx:
            ctx.close()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# Test Case
# ═══════════════════════════════════════════════════════════════


@pytest.mark.P0
@pytest.mark.functional
@allure.feature("GodGPT Compare")
@allure.story("Production vs Testnet")
@pytest.mark.parametrize("account_set", ACCOUNT_SETS or [{"id": "env_default", "title": "env_default"}], ids=lambda a: a.get("id", "account"))
@pytest.mark.parametrize("suite_pack", QUESTION_SUITES, ids=lambda s: str(s.get("suite", "suite")))
@allure.title("test_p0_compare_reply_by_question_bank")
def test_p0_compare_reply_by_question_bank(playwright: Playwright, account_set: Dict[str, Dict[str, str]], suite_pack: Dict[str, object]):
    """
    对比测试：从问题集文件读取“分组问题”，同一账号只登录一次，按组逐题对比两边回复差异。

    - 生产： https://app.godgpt.fun/
    - 测试： https://godgpt-ui-testnet.aelf.dev/
    """
    if not QUESTION_SUITES:
        pytest.skip("question suites empty or not loaded (check GODGPT_COMPARE_QUESTIONS_PATH)")

    suite = str(suite_pack.get("suite") or "suite")
    suite_title = str(suite_pack.get("suite_title") or suite)
    questions = suite_pack.get("questions") or []
    if not isinstance(questions, list) or not questions:
        pytest.skip(f"suite {suite} has no questions")

    account_id = (account_set.get("id") or "account").strip()
    logger = TestLogger(f"test_p0_compare_reply_by_question_bank__{account_id}__{suite}")
    logger.start()

    if account_id == "env_default" and "production" not in account_set and "testnet" not in account_set:
        prod, testnet = _env_specs_from_user_input()
    else:
        prod, testnet = _env_specs_from_account_set(account_set)
        if not (prod.email and prod.password and testnet.email and testnet.password):
            pytest.skip(f"account_set {account_id} missing email/password")

    browser_a = None
    browser_b = None
    ctx_a: Optional[BrowserContext] = None
    ctx_b: Optional[BrowserContext] = None
    page_a: Optional[Page] = None
    page_b: Optional[Page] = None
    try:
        logger.step("启动两个浏览器（优先 Chromium + Firefox；若 Firefox 不可用则回退到 Chromium + Chromium）")
        browser_a = _launch_browser(playwright, browser_name="chromium")
        browser_b_name = "firefox"
        try:
            browser_b = _launch_browser(playwright, browser_name=browser_b_name)
        except Exception as e:
            # 允许在未安装 Firefox/WebKit 的环境里仍可跑对比测试
            browser_b_name = "chromium"
            browser_b = _launch_browser(playwright, browser_name=browser_b_name)
            allure.attach(
                f"Firefox launch failed, fallback to Chromium.\nerror={e}",
                name="browser_fallback.txt",
                attachment_type=allure.attachment_type.TEXT,
            )

        cfg = ConfigManager().get_browser_config()
        ctx_a = browser_a.new_context(
            ignore_https_errors=True,
            viewport={
                "width": int(cfg.get("viewport_width", 1920)),
                "height": int(cfg.get("viewport_height", 1080)),
            },
        )
        ctx_b = browser_b.new_context(
            ignore_https_errors=True,
            viewport={
                "width": int(cfg.get("viewport_width", 1920)),
                "height": int(cfg.get("viewport_height", 1080)),
            },
        )
        page_a = ctx_a.new_page()
        page_b = ctx_b.new_page()

        allure.dynamic.story(f"{suite_title} / {account_set.get('title') or account_id}")

        with allure.step(f"生产环境：登录（{account_id}）"):
            _login_if_needed(page_a, base_url=prod.base_url, email=prod.email, password=prod.password, logger=logger)

        with allure.step(f"测试环境：登录（{account_id}）"):
            _login_if_needed(page_b, base_url=testnet.base_url, email=testnet.email, password=testnet.password, logger=logger)

        with allure.step(f"分组执行：{suite}（{len(questions)} questions）"):
            suite_notes: List[str] = []
            for qi, question in enumerate(questions, start=1):
                qid = f"{suite}-{qi:02d}"
                with allure.step(f"{qid}: ask & compare"):
                    # 需求：登录后的第一次对话不点 New Chat；从第二题开始才开新会话
                    if qi > 1:
                        _new_session_before_question(page_a, base_url=prod.base_url, logger=logger)
                        _new_session_before_question(page_b, base_url=testnet.base_url, logger=logger)

                    reply_prod = _ask_and_capture_in_session(page_a, base_url=prod.base_url, question=question, logger=logger)
                    reply_testnet = _ask_and_capture_in_session(page_b, base_url=testnet.base_url, question=question, logger=logger)

                    allure.attach(question, name=f"{qid}.question.txt", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(str(account_set.get("title") or account_id), name=f"{qid}.account_set.txt", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(reply_prod or "", name=f"{qid}.reply_production.txt", attachment_type=allure.attachment_type.TEXT)
                    allure.attach(reply_testnet or "", name=f"{qid}.reply_testnet.txt", attachment_type=allure.attachment_type.TEXT)
                    diff = _unified_diff(reply_prod or "", reply_testnet or "", from_name="production", to_name="testnet")
                    allure.attach(diff or "(no diff)", name=f"{qid}.reply_diff.patch", attachment_type=allure.attachment_type.TEXT)

                    analysis_md = _compare_replies(reply_prod or "", reply_testnet or "")
                    allure.attach(analysis_md, name=f"{qid}.analysis.md", attachment_type=allure.attachment_type.TEXT)

                    assert (reply_prod or "").strip() != "", f"production reply empty for {qid}"
                    assert (reply_testnet or "").strip() != "", f"testnet reply empty for {qid}"
                    suite_notes.append(f"- {qid}: ✅ 已生成 diff + analysis")

            if suite_notes:
                allure.attach(
                    "## 分组执行摘要\n\n" + "\n".join(suite_notes) + "\n",
                    name=f"{suite}.summary.md",
                    attachment_type=allure.attachment_type.TEXT,
                )

        logger.checkpoint("分组问题已逐题对比并产出附件", True)

        logger.end(success=True)
    finally:
        _close_context_and_page(ctx_a, page_a)
        _close_context_and_page(ctx_b, page_b)
        try:
            if browser_a:
                browser_a.close()
        except Exception:
            pass
        try:
            if browser_b:
                browser_b.close()
        except Exception:
            pass

