"""TEMS scaffold 서브커맨드 테스트"""
import json
import tempfile
import shutil
from pathlib import Path

from tems.scaffold import add_project_to_agent, load_registry, save_registry, rename_project, retire_agent, reactivate_agent

SAMPLE_REGISTRY = {
    "version": 1,
    "registry_path": "",
    "projects": {
        "DnT": {"aliases": ["DnT", "MRV"], "status": "active"},
        "MysticIsland": {"aliases": ["MysticIsland"], "status": "active"},
    },
    "agents": {
        "wesanggoon": {
            "name": "위상군",
            "projects": ["DnT"],
            "db_path": "E:/DnT/DnT_WesangGoon/memory/error_logs.db",
            "status": "active",
            "last_verified": "2026-04-09",
        }
    },
}


def make_registry(tmp_dir: Path) -> Path:
    reg_path = tmp_dir / "tems_registry.json"
    data = SAMPLE_REGISTRY.copy()
    data["registry_path"] = str(reg_path)
    reg_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return reg_path


def test_add_project_to_agent():
    """add 서브커맨드: 기존 에이전트에 프로젝트 추가"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = add_project_to_agent("wesanggoon", "MysticIsland", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "project_added"

        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        assert "MysticIsland" in reg["agents"]["wesanggoon"]["projects"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_add_project_already_member():
    """add: 이미 소속된 프로젝트 → 중복 아님, 무해"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = add_project_to_agent("wesanggoon", "DnT", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "already_member"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_add_project_agent_not_found():
    """add: 존재하지 않는 에이전트 → 에러"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = add_project_to_agent("nonexistent", "DnT", registry_path=reg_path)
        assert result["ok"] is False
        assert "not found" in result["error"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_rename_project():
    """rename: 프로젝트명 변경 → 전 에이전트 자동 갱신"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = rename_project("DnT", "DnT_v3", registry_path=reg_path)
        assert result["ok"] is True
        assert result["affected_agents"] == ["wesanggoon"]

        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        assert "DnT_v3" in reg["projects"]
        assert "DnT" not in reg["projects"]
        assert "DnT_v3" in reg["agents"]["wesanggoon"]["projects"]
        assert "DnT" not in reg["agents"]["wesanggoon"]["projects"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_rename_project_not_found():
    """rename: 존재하지 않는 프로젝트 → 에러"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = rename_project("NonExistent", "NewName", registry_path=reg_path)
        assert result["ok"] is False
        assert "not found" in result["error"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_rename_project_target_exists():
    """rename: 대상 이름이 이미 존재 → 에러"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = rename_project("DnT", "MysticIsland", registry_path=reg_path)
        assert result["ok"] is False
        assert "already exists" in result["error"]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retire_agent():
    """retire: 에이전트 은퇴"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = retire_agent("wesanggoon", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "agent_retired"

        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        assert reg["agents"]["wesanggoon"]["status"] == "retired"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retire_agent_not_found():
    """retire: 존재하지 않는 에이전트 → 에러"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = retire_agent("nonexistent", registry_path=reg_path)
        assert result["ok"] is False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retire_already_retired():
    """retire: 이미 은퇴 → 무해"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        retire_agent("wesanggoon", registry_path=reg_path)
        result = retire_agent("wesanggoon", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "already_retired"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_reactivate_agent():
    """reactivate: 은퇴 에이전트 재활성화"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        retire_agent("wesanggoon", registry_path=reg_path)
        result = reactivate_agent("wesanggoon", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "agent_reactivated"

        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        assert reg["agents"]["wesanggoon"]["status"] == "active"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_reactivate_already_active():
    """reactivate: 이미 active → 무해"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        reg_path = make_registry(tmp_dir)
        result = reactivate_agent("wesanggoon", registry_path=reg_path)
        assert result["ok"] is True
        assert result["action"] == "already_active"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_add_project_to_agent()
    print("PASS: test_add_project_to_agent")
    test_add_project_already_member()
    print("PASS: test_add_project_already_member")
    test_add_project_agent_not_found()
    print("PASS: test_add_project_agent_not_found")
    test_rename_project()
    print("PASS: test_rename_project")
    test_rename_project_not_found()
    print("PASS: test_rename_project_not_found")
    test_rename_project_target_exists()
    print("PASS: test_rename_project_target_exists")
    test_retire_agent()
    print("PASS: test_retire_agent")
    test_retire_agent_not_found()
    print("PASS: test_retire_agent_not_found")
    test_retire_already_retired()
    print("PASS: test_retire_already_retired")
    test_reactivate_agent()
    print("PASS: test_reactivate_agent")
    test_reactivate_already_active()
    print("PASS: test_reactivate_already_active")
