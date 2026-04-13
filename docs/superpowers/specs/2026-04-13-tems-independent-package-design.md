# TEMS Independent Package Design

**Date:** 2026-04-13 (Session 26)
**Author:** 위상군
**Status:** Approved
**Supersedes:** tems-tier2-s3-design.md (packaging aspects only)

## 1. Goal

TEMS (Topological Evolving Memory System)를 `E:/AgentInterface/tems_core/`에서 분리하여 독립 git 레포(`bobpullie/TEMS`) + PyPI 패키지(`tems`) + Claude Code 스킬로 배포한다.

### Success Criteria
- `pip install tems` 후 `from tems.fts5_memory import MemoryDB` 동작
- `tems scaffold` CLI로 새 에이전트 초기화 가능
- `tems init-skill`로 Claude Code 스킬 배포 가능
- `atlas-docs[tems]` optional dependency 연결 동작
- 기존 12 에이전트의 AgentInterface 경로 참조는 점진 전환 중 깨지지 않음

## 2. Package Structure

```
bobpullie/TEMS/
├── pyproject.toml
├── src/
│   └── tems/
│       ├── __init__.py              # Public API exports
│       ├── fts5_memory.py           # FTS5+BM25 retrieval (← tems_core/)
│       ├── tems_engine.py           # 4-Phase orchestrator (← tems_core/)
│       ├── rebuild_from_qmd.py      # DB restoration from QMD (← tems_core/)
│       ├── scaffold.py              # Agent initialization (← tems_scaffold.py)
│       ├── cli.py                   # CLI entry: tems scaffold / tems init-skill
│       ├── templates/               # package_data (importlib.resources)
│       │   ├── preflight_hook.py    # ← tems_templates/
│       │   ├── tems_commit.py       # ← tems_templates/
│       │   └── gitignore.template   # ← tems_templates/
│       ├── skill/                   # init-skill deployment source
│       │   ├── SKILL.md             # Claude Code skill definition
│       │   └── references/
│       │       └── tems-architecture.md
│       └── py.typed                 # PEP 561 marker
├── tests/                           # Migrated + new tests
│   ├── test_fts5_memory.py
│   ├── test_tems_engine.py
│   ├── test_scaffold.py
│   ├── test_cli.py
│   └── conftest.py
├── LICENSE
└── README.md
```

## 3. pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tems"
version = "0.1.0"
description = "Topological Evolving Memory System"
requires-python = ">=3.10"
dependencies = []  # sqlite3 is stdlib, no external deps for core

[project.optional-dependencies]
qmd = []  # placeholder: QMD dense vector integration (subprocess-based)
dev = ["pytest>=7.0", "pytest-cov"]

[project.scripts]
tems = "tems.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/tems"]
```

**Zero external dependencies** for core — sqlite3 is stdlib, QMD is subprocess-based.

## 4. CLI Commands

### 4.1 `tems scaffold`
```bash
tems scaffold --agent-id <id> --agent-name "Display Name" --project <project> --cwd <path> [--force]
```

**Actions:**
1. Create `.claude/tems_agent_id` marker file
2. Create `memory/` + `memory/qmd_rules/` directories
3. Initialize `error_logs.db` with full 10-table schema
4. Copy templates (preflight_hook.py, tems_commit.py) from package_data via `importlib.resources`
5. Update `tems_registry.json` at `TEMS_REGISTRY_PATH`

### 4.2 `tems init-skill`
```bash
tems init-skill [--target <path>]  # default: ~/.claude/skills/tems/
```

**Actions:**
1. Copy `skill/SKILL.md` → `<target>/SKILL.md`
2. Copy `skill/references/` → `<target>/references/`

## 5. Registry Strategy

| Item | Location | Rationale |
|------|----------|-----------|
| `tems_registry.json` | `E:/AgentInterface/` (외부) | 머신 상태 = 패키지 외부. 설치 위치 분산 방지 |
| 경로 결정 | `TEMS_REGISTRY_PATH` 환경변수 | 기본값: `E:/AgentInterface/tems_registry.json` |
| 폴백 | registry 없으면 scaffold만 로컬 동작 | registry 미발견 시 warning, 등록 skip |

### Registry Path Resolution (scaffold.py)
```python
def get_registry_path() -> Path:
    env = os.environ.get("TEMS_REGISTRY_PATH")
    if env:
        return Path(env)
    default = Path("E:/AgentInterface/tems_registry.json")
    if default.exists():
        return default
    return None  # registry unavailable, skip registration
```

## 6. Migration Strategy (Gradual Transition)

### Phase 1: Repository Creation
- `bobpullie/TEMS` git 레포 생성
- src-layout으로 tems_core/ 코드 이식
- 기존 테스트 이식 + CLI 테스트 추가
- `pip install -e .` 로컬 개발 설치

### Phase 2: Validation (위상군 먼저)
- 위상군 에이전트에서 `pip install -e .` 후 import 경로 전환
- preflight_hook.py 템플릿의 `sys.path.insert` → `from tems import ...` 변경
- 기존 DB, QMD rules, hook 동작 전부 검증

### Phase 3: Sequential Agent Migration
- 각 에이전트 세션에서 순차 전환 (빌드군 → 코드군 → 관리군 → ...)
- 전환 체크리스트:
  1. `pip install tems`
  2. `memory/preflight_hook.py` 교체 (새 import 경로)
  3. `memory/tems_commit.py` 교체
  4. `.claude/tems_agent_id` 확인
  5. preflight 동작 검증

### Phase 4: Deprecation
- 전 에이전트 전환 완료 후 `E:/AgentInterface/tems_core/` deprecated
- `tems_templates/`, `tems_scaffold.py` 제거
- `E:/AgentInterface/tems_registry.json`은 유지 (외부 상태)

### Backward Compatibility During Transition
기존 templates의 `sys.path.insert(0, "E:/AgentInterface")` + `from tems_core import ...`는 AgentInterface에 코드가 남아있는 한 계속 동작. 전환 중 양쪽 모두 유효.

## 7. Atlas Integration

### atlas-docs pyproject.toml 변경
```toml
[project.optional-dependencies]
tems = ["tems"]
```

### atlas/tems_query.py 변경
```python
# Before: subprocess call to memory/tems_query.py
# After: direct import with graceful fallback
try:
    from tems.fts5_memory import MemoryDB
    from tems.tems_engine import HybridRetriever
    TEMS_AVAILABLE = True
except ImportError:
    TEMS_AVAILABLE = False

def query_tems_rules(keywords: list[str], rule_type: str = "TGL") -> list[dict]:
    if not TEMS_AVAILABLE:
        return []
    # ... direct DB query instead of subprocess
```

## 8. Import Path Changes

| Component | Before | After |
|-----------|--------|-------|
| Core library | `from tems_core.fts5_memory import MemoryDB` | `from tems.fts5_memory import MemoryDB` |
| Engine | `from tems_core.tems_engine import HybridRetriever` | `from tems.tems_engine import HybridRetriever` |
| Rebuild | `from tems_core.rebuild_from_qmd import rebuild_db_from_qmd` | `from tems.rebuild_from_qmd import rebuild_db_from_qmd` |
| sys.path hack | `sys.path.insert(0, "E:/AgentInterface")` | (제거) |

## 9. Template Updates

패키지화 후 templates 내부의 import 경로를 변경해야 한다:

### preflight_hook.py (new version)
```python
# Old: sys.path.insert(0, "E:/AgentInterface")
# Old: from tems_core.fts5_memory import MemoryDB
# New:
from tems.fts5_memory import MemoryDB
from tems.tems_engine import HybridRetriever, EnhancedPreflight, RuleGraph
```

### tems_commit.py (new version)
```python
# Old: from tems_core.tems_engine import sync_single_rule_to_qmd
# New:
from tems.tems_engine import sync_single_rule_to_qmd
from tems.fts5_memory import MemoryDB
```

**Note:** 전환 기간 동안 구버전 templates(AgentInterface 경로)와 신버전(tems 패키지)이 공존한다. scaffold가 배포하는 것은 항상 신버전.

## 10. SKILL.md Scope

Claude Code 스킬로 배포되는 SKILL.md는 다음을 포함:
- TEMS 개요 (4-Phase architecture)
- TCL/TGL 규칙 등록 방법
- Preflight retrieval 동작 원리
- DB 스키마 요약
- 트러블슈팅 가이드 (DB 복원, QMD 재빌드)

## 11. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Import 경로 변경으로 기존 preflight 깨짐 | 에이전트 메모리 검색 중단 | 점진 전환 + AgentInterface 코드 유지 |
| registry.json 경로 하드코딩 | 다른 머신에서 동작 불가 | TEMS_REGISTRY_PATH 환경변수 |
| tems_engine.py 2040 LOC 단일 파일 | 유지보수 어려움 | v0.1.0에서는 그대로, 추후 모듈 분할 |
| QMD subprocess 의존성 | qmd.cmd 없는 환경에서 HybridRetriever 실패 | Dense search graceful fallback (기존 구현) |
| PyPI name `tems` 충돌 | pip install 실패 | 내부 전용, PyPI 미공개. --index-url 또는 direct git install |

## 12. Out of Scope (This Spec)

- tems_engine.py 모듈 분할 (v0.2.0+)
- Godel Agent / TemporalGraph 실전 활성화
- TEMS S4 (rule add/rename/retire/reactivate CLI)
- PyPI 공개 배포
- CI/CD 파이프라인 (GitHub Actions)
