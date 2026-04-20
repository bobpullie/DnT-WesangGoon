"""SDC Auto-Dispatch Check gate 테스트 (TCL #120)

check_sdc_gate 함수를 직접 단위 테스트.
tool_gate_hook.py 에서 import — DB / active_guards.json 미사용.
"""
import sys
from pathlib import Path

# memory/ 디렉토리를 sys.path 에 추가 (패키지가 아닌 스크립트 import 지원)
MEMORY_DIR = Path(__file__).parent.parent
if str(MEMORY_DIR) not in sys.path:
    sys.path.insert(0, str(MEMORY_DIR))

import pytest
from tool_gate_hook import check_sdc_gate


# ---------------------------------------------------------------------------
# 테스트 케이스
# ---------------------------------------------------------------------------


def test_non_trigger_bypass():
    """git status 같은 읽기 전용 명령은 게이트를 통과(None)해야 한다."""
    result = check_sdc_gate(
        tool_name="Bash",
        tool_input={"command": "git status"},
        active_guards_data={},
    )
    assert result is None, f"예상 None, 실제: {result!r}"


def test_trigger_no_brief():
    """git commit 호출 + brief 미제출 → <sdc-gate-alert> 포함 문자열 반환."""
    result = check_sdc_gate(
        tool_name="Bash",
        tool_input={"command": 'git commit -m "foo"'},
        active_guards_data={},
    )
    assert result is not None, "경고 문자열이 반환되어야 함"
    assert "<sdc-gate-alert>" in result, f"<sdc-gate-alert> 태그 없음: {result!r}"
    assert "TCL #120" in result, f"TCL #120 언급 없음: {result!r}"
    assert "sdc_brief_submitted=false" in result, f"sdc_brief_submitted=false 없음: {result!r}"


def test_trigger_with_brief():
    """git push + sdc_brief_submitted=True → gate clear (None 반환)."""
    result = check_sdc_gate(
        tool_name="Bash",
        tool_input={"command": "git push origin main"},
        active_guards_data={"sdc_brief_submitted": True},
    )
    assert result is None, f"brief 제출 완료 시 None 이어야 함, 실제: {result!r}"


def test_self_invocation_bypass():
    """TEMS 자체 호출(tems_commit.py 등)은 self-invocation으로 간주, None 반환."""
    result = check_sdc_gate(
        tool_name="Bash",
        tool_input={"command": "python memory/tems_commit.py --type TGL --summary test"},
        active_guards_data={},
    )
    assert result is None, f"self-invocation 은 None 이어야 함, 실제: {result!r}"


def test_non_bash_bypass():
    """Bash 이외 도구(Read 등)는 게이트 적용 안 함 → None 반환."""
    result = check_sdc_gate(
        tool_name="Read",
        tool_input={"file_path": "/some/file.md"},
        active_guards_data={},
    )
    assert result is None, f"Bash 이외 도구는 None 이어야 함, 실제: {result!r}"
