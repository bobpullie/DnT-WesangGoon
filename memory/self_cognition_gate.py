"""
TEMS Self-Cognition Auto-Register Gate (S51)
============================================
Stop hook. Reads the Claude transcript path from stdin, scans the last
user/assistant turn pair for self-cognition signals, and stages draft JSON files
under memory/pending_self_cognition for 위상군 review.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

MEMORY_DIR = Path(__file__).resolve().parent
DIAG_PATH = MEMORY_DIR / "tems_diagnostics.jsonl"
PENDING_DIR = MEMORY_DIR / "pending_self_cognition"
TEMPLATE_DIR = MEMORY_DIR / "templates"
STATE_PATH = MEMORY_DIR / ".self_cognition_state.json"
LOOKBACK_HOURS = 24
DEDUP_TURN_WINDOW = 2
KST = timezone(timedelta(hours=9))

REGEX_FLAGS = re.UNICODE | re.MULTILINE

HANDOVER_PATH_MARKERS = (
    "handover_doc/",
    "Claude-Sessions/",
    "qmd_drive/recaps/",
    "docs/session_archive/",
)

SELF_REFERENCE_WHITELIST = (
    "pending_self_cognition",
    "self_cognition_gate",
    "self_cognition/",
    "self_cognition\\",
    "audit reviewer",
    "audit findings",
    "docs/superpowers/plans/2026-04-29-self-cognition-auto-register.md",
)

HOOK_AUTHOR_PATTERNS = (
    re.compile(r"memory/.*hook.*\.py$", REGEX_FLAGS),
    re.compile(r"memory/.*gate.*\.py$", REGEX_FLAGS),
    re.compile(r"memory/audit.*\.py$", REGEX_FLAGS),
)


@dataclass
class Turn:
    role: str
    text_parts: list[str] = field(default_factory=list)
    tool_uses: list[dict[str, Any]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(part for part in self.text_parts if part)


@dataclass
class Signal:
    signal_type: str
    matched_tokens: list[str]
    priority: str
    missing_failures: list[dict[str, str]] = field(default_factory=list)


def _log_event(record: dict[str, Any]) -> None:
    try:
        with open(DIAG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _log_diagnostic(event: str, exc: Exception) -> None:
    _log_event({
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "exc_type": type(exc).__name__,
        "exc_msg": str(exc)[:300],
        "traceback": traceback.format_exc()[-800:],
    })


def _compile(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, REGEX_FLAGS)


USER_REBUKE_PATTERNS = [
    _compile(r"또\s*실패"),
    _compile(r"왜\s*[빼빠]"),
    _compile(r"(잘못|오류|실수)(을|를|이|가)"),
    _compile(r"안\s*했"),
    _compile(r"못\s*했"),
    _compile(r"정정해"),
    _compile(r"다시\s*해"),
    _compile(r"(니가|네가)\s*뭘"),
    _compile(r"왜\s*[가-힣A-Za-z]+\s*안"),
    _compile(r"전부\s*아니"),
    _compile(r"전혀\s*안"),
]

SELF_PRAISE_PATTERNS = [
    ("self_praise", _compile(r"ㅋㅋ|ㅎㅎ|🎉|🥳|완벽(?:하|함|입니다)?(?!\s*지\s*(?:않|못))|대단(?:하|함)(?!\s*지)|훌륭(?!\s*하지)|깔끔(?!\s*하지)")),
    ("absolutization", _compile(r"전면\s*강제|자율의존\s*종료|완전(?:히)?\s*[차해]|100%|절대\s*[안못](?!\s*[될하야])")),
    ("absolutization", _compile(r"해결됐습니다(?!\s*[?\?])|끝났습니다|(모두|전부)\s*통과")),
]

REVERSAL_PATTERNS = [
    _compile(r"정정합니다"),
    _compile(r"잘못\s*보고"),
    _compile(r"S4[89](?:/S5\d)?\s*동일"),
    _compile(r"메타[-\s]?결함"),
    _compile(r"재발"),
    _compile(r"자축\s*부적절"),
]

NUMERIC_AUDIT_PATTERNS = [
    _compile(r"errors?\s*[=:]\s*0"),
    _compile(r"failures?\s*[=:]\s*0"),
    _compile(r"failure\s*[=:]\s*0"),
    _compile(r"(?:문제|결함|오류|장애)\s*(?:없|0건)"),
    _compile(r"clear|alive|all\s*pass"),
]

NEGATION_RE = _compile(r"지\s*(?:않|못)|아니|없")
RETROSPECTIVE_RE = _compile(r"었어|었었|예전(?:에)?|과거(?:에)?|S\d{2}\s*(?:에서|의)|직전\s*세션|재발")
RETRO_SECTION_RE = _compile(
    r"자기\s*위반|위반\s*\d+\s*건|위반\s*사례|반성|회고|학습\s*자료|메타[-\s]?결함"
    r"|자기\s*인지|self.cognition|self.violation|postmortem|포스트모템"
)
RETRO_SECTION_LOOKBEHIND = 400


def _extract_content(message: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    content = message.get("content", "")
    text_parts: list[str] = []
    tool_uses: list[dict[str, Any]] = []
    if isinstance(content, str):
        text_parts.append(content)
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                text_parts.append(str(block.get("text", "")))
            elif block_type == "tool_use":
                tool_uses.append({
                    "name": block.get("name", ""),
                    "input": block.get("input") if isinstance(block.get("input"), dict) else {},
                })
    return text_parts, tool_uses


def parse_transcript(transcript_path: Path) -> tuple[list[Turn], int]:
    turns: list[Turn] = []
    parsed_lines = 0
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f):
            if line_no == 0:
                raw_line = raw_line.lstrip("\ufeff")
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            parsed_lines += 1
            msg = entry.get("message") if isinstance(entry.get("message"), dict) else {}
            role = msg.get("role") or entry.get("type")
            if role not in ("user", "assistant"):
                continue
            text_parts, tool_uses = _extract_content(msg)
            if role == "assistant" and turns and turns[-1].role == "assistant":
                turns[-1].text_parts.extend(text_parts)
                turns[-1].tool_uses.extend(tool_uses)
                continue
            turns.append(Turn(role=role, text_parts=text_parts, tool_uses=tool_uses))
    return turns, parsed_lines


def last_turn_pair(turns: list[Turn]) -> tuple[Turn | None, Turn | None, int]:
    last_assistant_idx = None
    for idx in range(len(turns) - 1, -1, -1):
        if turns[idx].role == "assistant":
            last_assistant_idx = idx
            break
    if last_assistant_idx is None:
        return None, None, 0
    for idx in range(last_assistant_idx - 1, -1, -1):
        if turns[idx].role == "user":
            turn_index = sum(1 for t in turns[: last_assistant_idx + 1] if t.role == "assistant")
            return turns[idx], turns[last_assistant_idx], turn_index
    return None, turns[last_assistant_idx], 0


def _is_self_reference_text(text: str) -> bool:
    low = text.lower().replace("\\", "/")
    return any(marker.lower() in low for marker in SELF_REFERENCE_WHITELIST)


def _line_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    pos = 0
    for line in text.splitlines(True):
        spans.append((pos, pos + len(line), line))
        pos += len(line)
    if not spans:
        spans.append((0, 0, text))
    return spans


def _masked_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"```.*?```", text, re.DOTALL | re.UNICODE):
        spans.append((match.start(), match.end()))
    for match in re.finditer(r"`[^`\n]+`", text, re.UNICODE):
        spans.append((match.start(), match.end()))
    for start, end, line in _line_spans(text):
        if re.match(r"^>\s?", line):
            spans.append((start, end))
    for marker in re.finditer(r"예시:|인용:|quote:|S\d{2}:", text, REGEX_FLAGS):
        spans.append((marker.start(), min(len(text), marker.end() + 60)))
    return spans


def _in_spans(index: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= index < end for start, end in spans)


def _is_user_echo(user_text: str, token: str) -> bool:
    return bool(token and token in user_text)


def _is_whitelisted_match(text: str, user_text: str, match: re.Match[str], masked: list[tuple[int, int]]) -> bool:
    token = match.group(0)
    if _is_user_echo(user_text, token):
        return True
    if _in_spans(match.start(), masked):
        return True
    after = text[match.end(): match.end() + 30]
    if NEGATION_RE.search(after):
        return True
    around = text[max(0, match.start() - 30): min(len(text), match.end() + 30)]
    if RETROSPECTIVE_RE.search(around):
        return True
    if _in_retrospective_section(text, match.start()):
        return True
    return False


def _in_retrospective_section(text: str, pos: int) -> bool:
    start = max(0, pos - RETRO_SECTION_LOOKBEHIND)
    return bool(RETRO_SECTION_RE.search(text[start:pos]))


def _summarize_tool_uses(tool_uses: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for tool in tool_uses:
        info = {"name": str(tool.get("name", ""))}
        inp = tool.get("input") if isinstance(tool.get("input"), dict) else {}
        if isinstance(inp.get("file_path"), str):
            info["file_path"] = inp["file_path"]
        out.append(info)
    return out


def _is_handover_path(file_path: str) -> bool:
    norm = file_path.replace("\\", "/")
    return any(marker in norm for marker in HANDOVER_PATH_MARKERS)


def _is_hook_author_edit(tool_uses: list[dict[str, Any]]) -> bool:
    for tool in tool_uses:
        if tool.get("name") not in ("Edit", "Write"):
            continue
        inp = tool.get("input") if isinstance(tool.get("input"), dict) else {}
        file_path = str(inp.get("file_path", "")).replace("\\", "/")
        if any(pattern.search(file_path) for pattern in HOOK_AUTHOR_PATTERNS):
            return True
    return False


def _parse_ts(ts_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts_str)
    except (TypeError, ValueError):
        return None


def collect_recent_failures(hours: int = LOOKBACK_HOURS) -> list[dict[str, str]]:
    if not DIAG_PATH.exists():
        return []
    cutoff = datetime.now() - timedelta(hours=hours)
    failures: list[dict[str, str]] = []
    try:
        with open(DIAG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        _log_diagnostic("self_cognition_gate_diagnostics_read_failure", e)
        return []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = str(evt.get("event") or "")
        if not event.endswith("_failure"):
            continue
        ts_str = str(evt.get("timestamp") or "")
        ts = _parse_ts(ts_str)
        if ts is not None and ts < cutoff:
            break
        failures.append({
            "timestamp": ts_str,
            "event": event,
        })
    failures.reverse()
    return failures


def detect_signals(user_turn: Turn, assistant_turn: Turn) -> list[Signal]:
    user_text = user_turn.text if user_turn else ""
    assistant_text = assistant_turn.text if assistant_turn else ""
    tool_uses = assistant_turn.tool_uses if assistant_turn else []
    signals: list[Signal] = []

    user_rebuke_tokens = []
    for pattern in USER_REBUKE_PATTERNS:
        user_rebuke_tokens.extend(m.group(0) for m in pattern.finditer(user_text))
    if user_rebuke_tokens:
        signals.append(Signal("user_rebuke", _unique(user_rebuke_tokens), "normal"))

    skip_self_ref = _is_self_reference_text(assistant_text)
    b_or_d_signal = False
    if not skip_self_ref:
        masked = _masked_spans(assistant_text)
        for signal_type, pattern in SELF_PRAISE_PATTERNS:
            tokens = []
            for match in pattern.finditer(assistant_text):
                if not _is_whitelisted_match(assistant_text, user_text, match, masked):
                    tokens.append(match.group(0))
            if tokens:
                b_or_d_signal = True
                signals.append(Signal(signal_type, _unique(tokens), "normal"))

        reversal_tokens = []
        for pattern in REVERSAL_PATTERNS:
            for match in pattern.finditer(assistant_text):
                if _is_whitelisted_match(assistant_text, user_text, match, masked):
                    continue
                reversal_tokens.append(match.group(0))
        has_tems_commit = any(
            tool.get("name") == "Bash"
            and "tems_commit.py" in str((tool.get("input") or {}).get("command", ""))
            for tool in tool_uses
        )
        if reversal_tokens and not has_tems_commit:
            b_or_d_signal = True
            signals.append(Signal("reversal_without_registration", _unique(reversal_tokens), "normal"))

    failures = collect_recent_failures()

    for tool in tool_uses:
        if tool.get("name") not in ("Edit", "Write"):
            continue
        inp = tool.get("input") if isinstance(tool.get("input"), dict) else {}
        file_path = str(inp.get("file_path", ""))
        if not _is_handover_path(file_path):
            continue
        body = str(inp.get("new_string", "") if tool.get("name") == "Edit" else inp.get("content", ""))
        if failures and not any(failure.get("timestamp", "")[:19] in body for failure in failures):
            signals.append(Signal("failure_citation_skip", ["missing_failure_timestamp"], "high", failures))
            break

    if not skip_self_ref and failures:
        masked = _masked_spans(assistant_text)
        numeric_tokens = []
        for pattern in NUMERIC_AUDIT_PATTERNS:
            for match in pattern.finditer(assistant_text):
                if _is_whitelisted_match(assistant_text, user_text, match, masked):
                    continue
                numeric_tokens.append(match.group(0))
        if numeric_tokens:
            signals.append(Signal("numeric_self_audit_falsification", _unique(numeric_tokens), "high", failures))

    if b_or_d_signal and _is_hook_author_edit(tool_uses):
        for signal in signals:
            if signal.signal_type in ("self_praise", "absolutization", "reversal_without_registration"):
                signal.priority = "critical"

    return signals


def _unique(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


SIGNAL_CLASSIFICATION = {
    "user_rebuke": ("TGL-C", "normal"),
    "self_praise": ("TGL-C", "normal"),
    "absolutization": ("TGL-C", "normal"),
    "failure_citation_skip": ("TGL-W", "high"),
    "reversal_without_registration": ("TGL-M", "normal"),
    "numeric_self_audit_falsification": ("TGL-W", "high"),
}


def _template_text(signal_type: str) -> str:
    path = TEMPLATE_DIR / f"self_cognition_{signal_type}.txt"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        _log_diagnostic("self_cognition_gate_template_read_failure", e)
        return (
            "자기-인지 시그널 검출 — TEMS 등록 후보.\n"
            "매칭 토큰: {matched_tokens}\n"
            "직전 사용자 발췌:\n  {user_excerpt}\n"
            "직전 응답 발췌:\n  {assistant_excerpt}\n"
            "누락 failure: {missing_failures}\n"
        )


def _render_template(signal: Signal, user_excerpt: str, assistant_excerpt: str, turn_index: int) -> str:
    values = {
        "matched_tokens": ", ".join(signal.matched_tokens),
        "user_excerpt": user_excerpt,
        "assistant_excerpt": assistant_excerpt,
        "turn_index": str(turn_index),
        "missing_failures": json.dumps(signal.missing_failures, ensure_ascii=False),
    }
    text = _template_text(signal.signal_type)
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    text = text.replace("{matched_tokens[0]}", signal.matched_tokens[0] if signal.matched_tokens else "")
    return text


def build_draft(signal: Signal, user_turn: Turn, assistant_turn: Turn, turn_index: int) -> dict[str, Any]:
    now = datetime.now(KST)
    draft_id = f"scd_{now.strftime('%Y%m%d_%H%M%S_%f')}_{signal.signal_type}"
    classification, default_priority = SIGNAL_CLASSIFICATION[signal.signal_type]
    priority = signal.priority or default_priority
    user_excerpt = (user_turn.text if user_turn else "")[:500]
    assistant_excerpt = (assistant_turn.text if assistant_turn else "")[:1000]
    rendered = _render_template(signal, user_excerpt, assistant_excerpt, turn_index)
    return {
        "draft_id": draft_id,
        "created_at": now.isoformat(),
        "signal_type": signal.signal_type,
        "matched_tokens": signal.matched_tokens,
        "priority": priority,
        "context": {
            "user_prompt_excerpt": user_excerpt,
            "assistant_response_excerpt": assistant_excerpt,
            "tool_uses_summary": _summarize_tool_uses(assistant_turn.tool_uses if assistant_turn else []),
            "missing_failures": signal.missing_failures,
        },
        "suggested_classification": classification,
        "suggested_abstraction": "L2",
        "suggested_topological_case": rendered,
        "suggested_forbidden": _suggested_forbidden(signal),
        "suggested_required": _suggested_required(signal),
        "suggested_triggers": ", ".join(signal.matched_tokens),
        "suggested_tags": "self-cognition,meta-defect",
        "draft_status": "pending",
    }


def _suggested_forbidden(signal: Signal) -> str:
    return {
        "user_rebuke": "사용자 질책/정정 신호를 받은 뒤 자기실수 등록 여부를 누락",
        "self_praise": "검증 미완료 또는 메타-결함 컨텍스트에서 자축어 사용",
        "absolutization": "검증 범위를 넘어선 절대화/완료 단언",
        "failure_citation_skip": "핸드오버/recap 작성 시 최근 failure timestamp 누락",
        "reversal_without_registration": "자기 정정/재발 인지 후 TEMS 등록 누락",
        "numeric_self_audit_falsification": "최근 failure가 있는데 errors=0 등으로 수치 자가감사 단언",
    }[signal.signal_type]


def _suggested_required(signal: Signal) -> str:
    return {
        "user_rebuke": "정정 전 실패 사실, 원인, TEMS 등록/기각 판단을 명시",
        "self_praise": "객관 수치와 한계만 보고하고 자축어를 사용하지 않음",
        "absolutization": "검증 범위와 미확인 영역을 함께 명시",
        "failure_citation_skip": "최근 failure timestamp와 후속 처치를 본문에 인용",
        "reversal_without_registration": "정정/재발 인지 시 pending draft 또는 수동 TEMS 등록으로 연결",
        "numeric_self_audit_falsification": "jsonl failure와 수치 보고를 대조한 뒤 불일치 시 정정",
    }[signal.signal_type]


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=PENDING_DIR, delete=False) as f:
            tmp_name = f.name
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        if tmp_name:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except Exception as cleanup_exc:
                _log_diagnostic("self_cognition_gate_temp_cleanup_failure", cleanup_exc)
        raise


def write_draft(draft: dict[str, Any]) -> Path:
    final_path = PENDING_DIR / f"{draft['draft_id']}.json"
    atomic_write_json(final_path, draft)
    _log_event({
        "timestamp": datetime.now().isoformat(),
        "event": "self_cognition_draft_created",
        "draft_id": draft["draft_id"],
        "signal_type": draft["signal_type"],
        "priority": draft["priority"],
    })
    return final_path


def _load_dedup_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        _log_diagnostic("self_cognition_state_read_failure", e)
        return {}


def _save_dedup_state(state: dict[str, Any]) -> None:
    try:
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        _log_diagnostic("self_cognition_state_write_failure", e)


def apply_dedup(signals: list[Signal], turn_index: int) -> list[Signal]:
    if not signals:
        return signals
    state = _load_dedup_state()
    new_state = dict(state)
    for sig in signals:
        prev = state.get(sig.signal_type) or {}
        prev_turn = int(prev.get("turn_index", -10))
        prev_tokens = set(prev.get("tokens") or [])
        cur_tokens = set(sig.matched_tokens)
        recent = (turn_index - prev_turn) <= DEDUP_TURN_WINDOW
        token_subset = bool(cur_tokens) and cur_tokens.issubset(prev_tokens)
        if recent and token_subset:
            sig.priority = "low"
            if "dedup_suppressed" not in sig.matched_tokens:
                sig.matched_tokens = sig.matched_tokens + ["dedup_suppressed"]
        new_state[sig.signal_type] = {
            "turn_index": turn_index,
            "tokens": sorted(cur_tokens),
            "ts": datetime.now().isoformat(),
        }
    _save_dedup_state(new_state)
    return signals


def run_gate(stdin_text: str | None = None) -> list[Path]:
    raw = sys.stdin.read() if stdin_text is None else stdin_text
    if not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except Exception as e:
        _log_diagnostic("self_cognition_gate_stdin_parse_failure", e)
        return []
    transcript_raw = data.get("transcript_path", "")
    if not transcript_raw:
        _log_diagnostic("self_cognition_gate_transcript_read_failure", FileNotFoundError("missing transcript_path"))
        return []
    try:
        transcript_path = Path(transcript_raw).resolve()
        turns, _ = parse_transcript(transcript_path)
        user_turn, assistant_turn, turn_index = last_turn_pair(turns)
        if user_turn is None or assistant_turn is None:
            return []
    except Exception as e:
        _log_diagnostic("self_cognition_gate_transcript_read_failure", e)
        return []
    try:
        signals = detect_signals(user_turn, assistant_turn)
        signals = apply_dedup(signals, turn_index)
        paths = []
        for signal in signals:
            paths.append(write_draft(build_draft(signal, user_turn, assistant_turn, turn_index)))
        return paths
    except Exception as e:
        _log_diagnostic("self_cognition_gate_detection_failure", e)
        return []


def reject_draft(draft_id: str, reason: str) -> int:
    if len((reason or "").strip()) < 10:
        print("--reason must be at least 10 characters", file=sys.stderr)
        return 1
    draft_path = PENDING_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"draft not found: {draft_id}", file=sys.stderr)
        return 1
    rejected_path = draft_path.with_suffix(draft_path.suffix + ".rejected")
    os.replace(draft_path, rejected_path)
    _log_event({
        "timestamp": datetime.now().isoformat(),
        "event": "self_cognition_rejected",
        "draft_id": draft_id,
        "reason": reason.strip(),
    })
    return 0


def resolve_draft(draft_id: str) -> int:
    draft_path = PENDING_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"draft not found: {draft_id}", file=sys.stderr)
        return 1
    committed_path = draft_path.with_suffix(draft_path.suffix + ".committed")
    os.replace(draft_path, committed_path)
    _log_event({
        "timestamp": datetime.now().isoformat(),
        "event": "self_cognition_resolved",
        "draft_id": draft_id,
    })
    return 0


def main(argv: list[str] | None = None, stdin_text: str | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reject", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--resolve", default="")
    args = parser.parse_args(argv)
    if args.resolve:
        return resolve_draft(args.resolve)
    if args.reject:
        return reject_draft(args.reject, args.reason)
    run_gate(stdin_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
