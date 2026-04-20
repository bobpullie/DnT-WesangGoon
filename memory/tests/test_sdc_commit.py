"""sdc_commit.py unit tests (TCL #120)

ACTIVE_GUARDS_PATH / SDC_LOG_PATH 를 monkeypatch 로 tmp_path 로 교체하여
prod 파일을 건드리지 않고 테스트한다.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# memory/ 디렉토리를 sys.path 에 추가
MEMORY_DIR = Path(__file__).parent.parent
if str(MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(MEMORY_DIR))

import sdc_commit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def patched_paths(tmp_path, monkeypatch):
    """ACTIVE_GUARDS_PATH / SDC_LOG_PATH 를 tmp_path 내 파일로 교체."""
    guards_path = tmp_path / "active_guards.json"
    log_path = tmp_path / "sdc_briefs.jsonl"
    monkeypatch.setattr(sdc_commit, "ACTIVE_GUARDS_PATH", guards_path)
    monkeypatch.setattr(sdc_commit, "SDC_LOG_PATH", log_path)
    return guards_path, log_path


@pytest.fixture()
def guards_with_list(patched_paths):
    """guards 리스트가 있는 초기 active_guards.json 을 미리 기록."""
    guards_path, log_path = patched_paths
    initial = {
        "sdc_brief_submitted": False,
        "guards": [
            {
                "rule_id": 54,
                "classification": "",
                "tool_pattern": "",
                "failure_signature": "",
                "source": "preflight",
                "fired_at": "2026-04-20T23:09:14.507596",
                "remaining_checks": 7,
            }
        ],
    }
    guards_path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")
    return guards_path, log_path


# ---------------------------------------------------------------------------
# Test 1: KEEP verdict → sdc_brief_submitted = True
# ---------------------------------------------------------------------------


def test_verdict_keep_sets_true(guards_with_list):
    """--verdict KEEP 후 active_guards.json 의 sdc_brief_submitted 가 True 이어야 한다."""
    guards_path, _ = guards_with_list

    sdc_commit.cmd_submit(
        verdict="KEEP",
        task="test-task",
        rationale="Q2: trivial edit",
        brief="",
        as_json=False,
    )

    data = json.loads(guards_path.read_text(encoding="utf-8"))
    assert data["sdc_brief_submitted"] is True, (
        f"sdc_brief_submitted 가 True 이어야 함, 실제: {data['sdc_brief_submitted']!r}"
    )
    assert data["sdc_brief_verdict"] == "KEEP"
    assert data["sdc_brief_task"] == "test-task"
    assert "sdc_brief_submitted_at" in data


# ---------------------------------------------------------------------------
# Test 2: reset → sdc_brief_submitted = False, verdict/at/task 키 제거
# ---------------------------------------------------------------------------


def test_reset_restores_false(guards_with_list):
    """먼저 true 로 세팅한 뒤 --reset → false, verdict/at/task 키 제거 확인."""
    guards_path, _ = guards_with_list

    # 먼저 submit
    sdc_commit.cmd_submit(
        verdict="DELEGATE",
        task="before-reset",
        rationale="",
        brief="",
        as_json=False,
    )
    data_before = json.loads(guards_path.read_text(encoding="utf-8"))
    assert data_before["sdc_brief_submitted"] is True

    # reset
    sdc_commit.cmd_reset(as_json=False)

    data_after = json.loads(guards_path.read_text(encoding="utf-8"))
    assert data_after["sdc_brief_submitted"] is False, (
        f"reset 후 sdc_brief_submitted 가 False 이어야 함, 실제: {data_after['sdc_brief_submitted']!r}"
    )
    assert "sdc_brief_verdict" not in data_after, "reset 후 sdc_brief_verdict 키가 제거되어야 함"
    assert "sdc_brief_submitted_at" not in data_after, "reset 후 sdc_brief_submitted_at 키가 제거되어야 함"
    assert "sdc_brief_task" not in data_after, "reset 후 sdc_brief_task 키가 제거되어야 함"


# ---------------------------------------------------------------------------
# Test 3: 유효하지 않은 verdict → returncode != 0, stderr 비어 있지 않음
# ---------------------------------------------------------------------------


def test_invalid_verdict_rejected():
    """--verdict FOO → exit 2, stderr 에 에러 메시지 포함."""
    result = subprocess.run(
        [sys.executable, str(MEMORY_DIR / "sdc_commit.py"), "--verdict", "FOO"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"유효하지 않은 verdict 는 non-zero exit 이어야 함, 실제: {result.returncode}"
    )
    assert result.stderr.strip() or result.stdout.strip(), (
        "stderr (또는 stdout) 에 에러 메시지가 있어야 함"
    )


# ---------------------------------------------------------------------------
# Test 4: 2회 호출 후 JSONL 에 2줄, verdict 필드 일치
# ---------------------------------------------------------------------------


def test_log_appended(guards_with_list):
    """2회 호출 후 sdc_briefs.jsonl 에 2줄, 각 줄의 verdict 필드가 일치해야 한다."""
    guards_path, log_path = guards_with_list

    sdc_commit.cmd_submit(
        verdict="KEEP",
        task="task-1",
        rationale="",
        brief="",
        as_json=False,
    )
    sdc_commit.cmd_submit(
        verdict="STAGING",
        task="task-2",
        rationale="",
        brief="long brief text",
        as_json=False,
    )

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2, f"JSONL 에 2줄이어야 함, 실제: {len(lines)}"

    entry0 = json.loads(lines[0])
    entry1 = json.loads(lines[1])

    assert entry0["verdict"] == "KEEP", f"첫 번째 줄 verdict=KEEP 이어야 함, 실제: {entry0['verdict']!r}"
    assert entry1["verdict"] == "STAGING", f"두 번째 줄 verdict=STAGING 이어야 함, 실제: {entry1['verdict']!r}"
    assert entry0["reset"] is False
    assert entry1["reset"] is False


# ---------------------------------------------------------------------------
# Test 5 (권장): 기존 guards 리스트 보존 확인
# ---------------------------------------------------------------------------


def test_existing_guards_preserved(guards_with_list):
    """submit 후에도 active_guards.json 의 기존 guards 리스트가 그대로 보존되어야 한다."""
    guards_path, _ = guards_with_list

    sdc_commit.cmd_submit(
        verdict="DELEGATE",
        task="preserve-test",
        rationale="",
        brief="",
        as_json=False,
    )

    data = json.loads(guards_path.read_text(encoding="utf-8"))

    assert "guards" in data, "guards 키가 존재해야 함"
    guards = data["guards"]
    assert len(guards) == 1, f"guards 리스트 길이 1 이어야 함, 실제: {len(guards)}"
    assert guards[0]["rule_id"] == 54, f"rule_id=54 이어야 함, 실제: {guards[0].get('rule_id')!r}"
    assert guards[0]["source"] == "preflight", "source=preflight 이어야 함"
