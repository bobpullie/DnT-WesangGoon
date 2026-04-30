import importlib
import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest


gate = importlib.import_module("memory.self_cognition_gate")


@pytest.fixture()
def tmp_path():
    base = Path(__file__).resolve().parents[1] / "memory" / "_test_self_cognition_tmp"
    path = base / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def isolated_gate(tmp_path, monkeypatch):
    pending = tmp_path / "pending_self_cognition"
    templates = tmp_path / "templates"
    templates.mkdir()
    for signal in gate.SIGNAL_CLASSIFICATION:
        (templates / f"self_cognition_{signal}.txt").write_text(
            "signal={matched_tokens}\nuser={user_excerpt}\nassistant={assistant_excerpt}\n"
            "turn={turn_index}\nmissing={missing_failures}\n",
            encoding="utf-8",
        )
    monkeypatch.setattr(gate, "PENDING_DIR", pending)
    monkeypatch.setattr(gate, "TEMPLATE_DIR", templates)
    monkeypatch.setattr(gate, "DIAG_PATH", tmp_path / "tems_diagnostics.jsonl")
    monkeypatch.setattr(gate, "STATE_PATH", tmp_path / ".self_cognition_state.json")
    return pending


def line(role, content):
    return json.dumps({"type": role, "message": {"role": role, "content": content}}, ensure_ascii=False)


def write_transcript(tmp_path, *lines):
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_fixture(tmp_path, *lines):
    path = write_transcript(tmp_path, *lines)
    return gate.run_gate(json.dumps({"session_id": "s", "transcript_path": str(path)}))


def draft_files(pending):
    return sorted(pending.glob("*.json"))


def read_draft(pending):
    files = draft_files(pending)
    assert len(files) == 1
    return json.loads(files[0].read_text(encoding="utf-8"))


def write_failure(diag_path, event="example_failure"):
    ts = (datetime.now() - timedelta(minutes=5)).isoformat()
    diag_path.write_text(
        json.dumps({"timestamp": ts, "event": event, "exc_type": "RuntimeError"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ts


def test_empty_stdin_exits_silent(isolated_gate):
    assert gate.main([], "") == 0
    assert draft_files(isolated_gate) == []


def test_invalid_json_stdin_logs_parse_failure(isolated_gate):
    assert gate.main([], "{not json") == 0
    events = (gate.DIAG_PATH).read_text(encoding="utf-8")
    assert "self_cognition_gate_stdin_parse_failure" in events


def test_missing_transcript_path_logs_read_failure(isolated_gate):
    assert gate.main([], json.dumps({"session_id": "s"})) == 0
    events = gate.DIAG_PATH.read_text(encoding="utf-8")
    assert "self_cognition_gate_transcript_read_failure" in events


def test_layer_b_detects_self_praise(isolated_gate, tmp_path):
    run_fixture(tmp_path, line("user", "작업 결과 알려줘"), line("assistant", [{"type": "text", "text": "처리했습니다 ㅋㅋ"}]))
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "self_praise"
    assert draft["priority"] == "normal"


def test_layer_a_detects_user_rebuke(isolated_gate, tmp_path):
    run_fixture(tmp_path, line("user", "또 실패했네. 정정해"), line("assistant", [{"type": "text", "text": "정정하겠습니다."}]))
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "user_rebuke"
    assert draft["priority"] == "normal"


def test_user_echo_self_praise_is_skipped(isolated_gate, tmp_path):
    run_fixture(tmp_path, line("user", "ㅋㅋ 이 표현으로 답해"), line("assistant", [{"type": "text", "text": "ㅋㅋ 알겠습니다"}]))
    assert draft_files(isolated_gate) == []


@pytest.mark.parametrize(
    "assistant_text",
    [
        "인라인 `완벽합니다` 예시입니다.",
        "```\n완벽합니다\n```",
        "> 완벽합니다\n인용입니다.",
    ],
)
def test_code_and_quote_context_self_praise_is_skipped(isolated_gate, tmp_path, assistant_text):
    run_fixture(tmp_path, line("user", "검토해"), line("assistant", [{"type": "text", "text": assistant_text}]))
    assert draft_files(isolated_gate) == []


def test_negated_self_praise_is_skipped(isolated_gate, tmp_path):
    run_fixture(tmp_path, line("user", "검토해"), line("assistant", [{"type": "text", "text": "이 방식은 완벽하지 않다."}]))
    assert draft_files(isolated_gate) == []


def test_retrospective_self_praise_is_skipped(isolated_gate, tmp_path):
    run_fixture(tmp_path, line("user", "회고해"), line("assistant", [{"type": "text", "text": "S50에서 ㅋㅋ 자축했다는 점이 문제였습니다."}]))
    assert draft_files(isolated_gate) == []


def test_layer_c_detects_missing_failure_timestamp_in_edit_payload(isolated_gate, tmp_path):
    write_failure(gate.DIAG_PATH)
    run_fixture(
        tmp_path,
        line("user", "핸드오버 써"),
        line("assistant", [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "handover_doc/test.md", "new_string": "failure 요약만 있음"}},
            {"type": "text", "text": "작성했습니다."},
        ]),
    )
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "failure_citation_skip"
    assert draft["priority"] == "high"


def test_layer_e_detects_numeric_self_audit_falsification(isolated_gate, tmp_path):
    write_failure(gate.DIAG_PATH)
    run_fixture(tmp_path, line("user", "상태는?"), line("assistant", [{"type": "text", "text": "errors=0, alive"}]))
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "numeric_self_audit_falsification"
    assert draft["priority"] == "high"


def test_layer_f_escalates_hook_author_self_praise(isolated_gate, tmp_path):
    run_fixture(
        tmp_path,
        line("user", "hook 고쳐"),
        line("assistant", [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "memory/foo_hook.py", "new_string": "x"}},
            {"type": "text", "text": "완벽합니다"},
        ]),
    )
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "self_praise"
    assert draft["priority"] == "critical"


# --- S56 P0(A) regression: false-positive 회귀 차단 ---

def test_numeric_in_retro_violation_list_skipped(isolated_gate, tmp_path):
    """S55 false-positive 재현: '자기 위반 4건' 헤더 + numbered list 안의 '문제없습니다' 인용 → fire 금지"""
    write_failure(gate.DIAG_PATH)
    text = (
        "## 자기 위반 4건 (TGL/TCL 으로 일반화 정착)\n"
        "1. 'PC/사용자 문제없습니다' + 4건 부채 동시 출현 → TGL #132 직접 출처\n"
        "2. SDC canonical push 누락 직전 → 종일군 지적으로 회수 (TCL #119)\n"
    )
    run_fixture(tmp_path, line("user", "보고해"), line("assistant", [{"type": "text", "text": text}]))
    assert draft_files(isolated_gate) == [], "회고 인용 문맥에서 numeric_self_audit_falsification 가 발동됨"


def test_numeric_in_postmortem_section_skipped(isolated_gate, tmp_path):
    write_failure(gate.DIAG_PATH)
    text = (
        "### 회고\n"
        "S50 에서 '문제없음' 으로 단언했다가 잘못 보고된 사례.\n"
    )
    run_fixture(tmp_path, line("user", "회고"), line("assistant", [{"type": "text", "text": text}]))
    assert draft_files(isolated_gate) == [], "회고 헤더 하 인용에서 fire 금지"


def test_numeric_audit_context_still_fires(isolated_gate, tmp_path):
    """회귀 가드: 진짜 audit 단언 (회고 마커 없음) 은 그대로 fire 해야 함"""
    write_failure(gate.DIAG_PATH)
    run_fixture(
        tmp_path,
        line("user", "상태"),
        line("assistant", [{"type": "text", "text": "전체 점검 결과: errors=0, all pass"}]),
    )
    draft = read_draft(isolated_gate)
    assert draft["signal_type"] == "numeric_self_audit_falsification"


def test_cross_turn_dedup_downgrades_priority(isolated_gate, tmp_path):
    """동일 signal+tokens 가 2턴 이내 재발 시 priority='low' + dedup_suppressed 마커"""
    write_failure(gate.DIAG_PATH)
    # 1회차: 정상 fire
    run_fixture(
        tmp_path,
        line("user", "상태"),
        line("assistant", [{"type": "text", "text": "errors=0"}]),
    )
    files1 = draft_files(isolated_gate)
    assert len(files1) == 1
    d1 = json.loads(files1[0].read_text(encoding="utf-8"))
    assert d1["priority"] == "high"
    # 2회차: 동일 signal+tokens → dedup
    run_fixture(
        tmp_path,
        line("user", "상태"),
        line("assistant", [{"type": "text", "text": "errors=0"}]),
    )
    files2 = sorted(draft_files(isolated_gate))
    assert len(files2) == 2
    d2 = json.loads(files2[-1].read_text(encoding="utf-8"))
    assert d2["priority"] == "low"
    assert "dedup_suppressed" in d2["matched_tokens"]


def test_cross_turn_different_signal_independent(isolated_gate, tmp_path):
    """서로 다른 signal_type 은 dedup 영향 없음"""
    write_failure(gate.DIAG_PATH)
    run_fixture(
        tmp_path,
        line("user", "상태"),
        line("assistant", [{"type": "text", "text": "errors=0"}]),
    )
    run_fixture(
        tmp_path,
        line("user", "또 실패했네"),
        line("assistant", [{"type": "text", "text": "정정하겠습니다."}]),
    )
    files = sorted(draft_files(isolated_gate))
    assert len(files) == 2
    types = {json.loads(f.read_text(encoding="utf-8"))["signal_type"] for f in files}
    assert types == {"numeric_self_audit_falsification", "user_rebuke"}
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["priority"] != "low" or "dedup_suppressed" not in d.get("matched_tokens", [])
