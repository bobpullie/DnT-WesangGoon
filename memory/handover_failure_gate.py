"""
TEMS Handover Failure Gate (S50 — TGL #128 hook-level enforcement, β layer)
=============================================================================
PreToolUse hook. Edit/Write 가 `handover_doc/` 또는 `Claude-Sessions/` 산출물
대상이면 24h 내 `*_failure` 이벤트를 도구 호출 직전 위상군 컨텍스트에 강제 첨부.

자기보고 (핸드오버) 작성 시 production failure 누락을 차단:
- failure 0건 → silent (오버헤드 0)
- failure ≥1건 → <handover-failure-warn>...</handover-failure-warn> stdout
- deny 안 함 — warning only. 위상군이 인용/누락 결정. 단 "못 봤다" 핑계 차단.

신규 모듈 — TGL #102 백업 의무 비대상. 자기 자신 (memory/*.py) 호출은 스킵.

stdin: { "tool_name": "...", "tool_input": {...}, ... }
stdout: <handover-failure-warn>...</handover-failure-warn> 또는 빈 출력
exit: 0 (항상 — 차단 없음)
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent
DIAG_PATH = MEMORY_DIR / "tems_diagnostics.jsonl"

# 핸드오버/자기보고 산출물 경로 — 백슬래시 정규화 후 매칭
HANDOVER_PATH_MARKERS = (
    "handover_doc/",
    "Claude-Sessions/",
    "qmd_drive/recaps/",
    "docs/session_archive/",
)

# 자기 자신 (TEMS 인프라) 편집은 매칭 제외 — self-trigger 루프 방지
SELF_INVOCATION_MARKERS = (
    "memory/preflight_hook.py",
    "memory/tool_failure_hook.py",
    "memory/tool_gate_hook.py",
    "memory/tems_commit.py",
    "memory/retrospective_hook.py",
    "memory/pattern_detector.py",
    "memory/decay.py",
    "memory/compliance_tracker.py",
    "memory/sdc_commit.py",
    "memory/audit_diagnostics_recent.py",
    "memory/handover_failure_gate.py",
    "memory/self_cognition_gate.py",
    "memory/pending_self_cognition/",
    "memory/templates/self_cognition_",
    "docs/superpowers/plans/2026-04-29-self-cognition-auto-register.md",
)

LOOKBACK_HOURS = 24
MAX_FAILURES_TO_SHOW = 5
FAILURE_SUFFIX = "_failure"


def _log_diagnostic(event: str, exc: Exception) -> None:
    try:
        with open(DIAG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "exc_type": type(exc).__name__,
                "exc_msg": str(exc)[:300],
                "traceback": traceback.format_exc()[-800:],
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _is_handover_target(file_path: str) -> bool:
    if not file_path:
        return False
    norm = file_path.replace("\\", "/")
    if any(marker in norm for marker in SELF_INVOCATION_MARKERS):
        return False
    return any(marker in norm for marker in HANDOVER_PATH_MARKERS)


def _collect_recent_failures() -> list[dict]:
    if not DIAG_PATH.exists():
        return []
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=LOOKBACK_HOURS)
    out: list[dict] = []
    try:
        with open(DIAG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return []

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_name = evt.get("event") or ""
        if not event_name.endswith(FAILURE_SUFFIX):
            continue
        ts_str = evt.get("timestamp") or ""
        try:
            ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue
        if ts < cutoff:
            break
        out.append(evt)
    out.reverse()
    return out


def _format_alert(failures: list[dict]) -> str:
    lines = [
        "<handover-failure-warn>",
        f"  ⚠ TGL #128 hook-level — {LOOKBACK_HOURS}h 내 TEMS failure {len(failures)}건 감지.",
        "  자기보고 (핸드오버/recap) 작성 시 아래 failure 의 후속 처치/원인 분석을 반드시 포함.",
    ]
    for evt in failures[-MAX_FAILURES_TO_SHOW:]:
        ts = evt.get("timestamp", "?")
        ev = evt.get("event", "?")
        exc_type = evt.get("exc_type", "") or ""
        exc_msg = (evt.get("exc_msg") or "").replace("\n", " ")[:160]
        line = f"    [{ts}] {ev}"
        if exc_type:
            line += f"  ({exc_type})"
        lines.append(line)
        if exc_msg:
            lines.append(f"      msg: {exc_msg}")
    if len(failures) > MAX_FAILURES_TO_SHOW:
        lines.append(f"  ... +{len(failures) - MAX_FAILURES_TO_SHOW}건 더 (전수: memory/tems_diagnostics.jsonl)")
    lines.append("  → 누락하면 S48/S49-style 메타-결함 재발. 인용 또는 명시적 'no follow-up needed' 사유 필수.")
    lines.append("</handover-failure-warn>")
    return "\n".join(lines)


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        data = json.loads(raw)
    except Exception as e:
        _log_diagnostic("handover_gate_stdin_parse_failure", e)
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        return 0

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""

    if not _is_handover_target(file_path):
        return 0

    try:
        failures = _collect_recent_failures()
    except Exception as e:
        _log_diagnostic("handover_gate_collect_failure", e)
        return 0

    if not failures:
        return 0

    sys.stdout.write(_format_alert(failures) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
