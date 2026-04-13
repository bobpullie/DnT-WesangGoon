# TEMS Tier 2 S3 — Registry + Scaffold + Migration Design
> Author: 위상군 | Date: 2026-04-09 Session 12 | Status: Approved
> Parent Spec: `2026-04-09-tems-qmd-upgrade-design.md` §5 Tier 2 S3

## 1. Scope

Tier 2 S3의 범위:
1. `tems_core/` 공유 코어 구축 (위상군 코드 → 범용화)
2. `tems_templates/` 진입점 템플릿
3. `tems_scaffold.py` — 결정론적 에이전트 scaffold 스크립트
4. `tems_registry.json` — 중앙 레지스트리 생성
5. `/TEMS:project` 글로벌 스킬 (scaffold + register + status)
6. 위상군 마이그레이션 (기존 코드 → 코어 사용)

S4 범위(add/rename/retire/reactivate)는 포함하지 않음.

## 2. Design Decisions (Brainstorming에서 확정)

| 결정 | 선택 | 근거 |
|------|------|------|
| 스킬 위치 | `~/.claude/skills/tems-project.md` (유저 글로벌) | scaffold 전에는 대상 에이전트에 `.claude/skills/`가 없을 수 있음 |
| 에이전트 식별 | `.claude/tems_agent_id` 마커 파일 | CWD 하위 디렉토리에서도 상위 순회로 확실하게 식별 |
| 코드 공유 | 하이브리드 — 코어 공유 + 진입점 템플릿 | 코어 업데이트 전파 + 진입점은 가볍고 잘 안 바뀜 |
| scaffold 메커니즘 | 스킬(.md) + Python 스크립트 | 결정론적 파일 생성, Claude 해석 의존 제거 |
| 마이그레이션 | 전체 마이그레이션 + 백업 | 모든 에이전트 동일 코드, 백업으로 롤백 가능 |
| 디니군 | S3에서 미포함 | 1주일 판정 대기 상태, S5 일괄 온보딩에서 처리 |

## 3. File Layout

```
E:/AgentInterface/
  tems_registry.json                  ← 중앙 레지스트리
  tems_scaffold.py                    ← scaffold 스크립트
  tems_core/
    __init__.py                       ← 빈 파일 (패키지 마커)
    fts5_memory.py                    ← 공유 코어 (위상군에서 이동)
    tems_engine.py                    ← 공유 코어 (위상군에서 이동)
  tems_templates/
    preflight_hook.py                 ← 범용 진입점 템플릿
    tems_commit.py                    ← 범용 진입점 템플릿

~/.claude/skills/
  tems-project.md                     ← 글로벌 스킬

E:/DnT/DnT_WesangGoon/ (마이그레이션 후)
  .claude/
    tems_agent_id                     ← "wesanggoon"
  memory/
    _backup_tier1/
      fts5_memory.py                  ← 백업
      tems_engine.py                  ← 백업
      preflight_hook.py               ← 백업
      tems_commit.py                  ← 백업
    preflight_hook.py                 ← 템플릿 기반 (tems_core import)
    tems_commit.py                    ← 템플릿 기반 (tems_core import)
    error_logs.db                     ← 그대로
    qmd_rules/                        ← 그대로
```

## 4. Component Details

### 4.1 tems_core/ — 공유 코어

위상군의 `fts5_memory.py`와 `tems_engine.py`를 이동. 변경점:

- **import 경로 정리**: `from memory.fts5_memory import` → `from fts5_memory import` (패키지 내부 상대 import)
- **DB_PATH 파라미터화**: 하드코딩된 `Path(__file__).parent / "error_logs.db"` → 생성자 인자로 받음
- **QMD 컬렉션명 파라미터화**: `HybridRetriever.__init__(self, db, collection="tems-wesanggoon")` → `tems-{agent_id}` 동적
- **MemoryDB 생성자**: `MemoryDB(db_path=None)` → db_path 인자 추가, None이면 기존 기본값

로직(HybridRetriever, RuleGraph, PredictiveTGL, HealthScorer, EnhancedPreflight 등)은 전부 그대로 유지. 하드코딩만 파라미터화.

### 4.2 tems_templates/ — 진입점 템플릿

**preflight_hook.py 템플릿:**

```python
TEMS_CORE = "E:/AgentInterface/tems_core"
sys.path.insert(0, TEMS_CORE)
from fts5_memory import MemoryDB
from tems_engine import EnhancedPreflight, RuleGraph

def find_agent_root(start: Path) -> Path:
    """상위 순회하며 .claude/tems_agent_id 찾기"""
    cur = start
    while cur != cur.parent:
        if (cur / ".claude" / "tems_agent_id").exists():
            return cur
        cur = cur.parent
    raise FileNotFoundError("tems_agent_id not found")

AGENT_ROOT = find_agent_root(Path(__file__).parent)
AGENT_ID = (AGENT_ROOT / ".claude" / "tems_agent_id").read_text().strip()
DB_PATH = AGENT_ROOT / "memory" / "error_logs.db"
```

키워드 추출, 한국어 어미 처리, THS 가중치, context budget, 규칙성 패턴 감지 — 현재 위상군 코드 그대로 유지.

`detect_project_scope` 변경:
```python
def detect_project_scope(agent_id: str) -> list[str]:
    """tems_registry.json에서 에이전트의 프로젝트 조회"""
    REGISTRY_PATH = Path("E:/AgentInterface/tems_registry.json")
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    projects = registry["agents"].get(agent_id, {}).get("projects", [])
    scopes = ["project:meta", "project:all", ""]
    for p in projects:
        scopes.append(f"project:{p.lower()}")
    return scopes
```

**tems_commit.py 템플릿:**

동일한 마커 기반 `DB_PATH` 해석. `sync_single_rule_to_qmd`는 `tems_core`에서 import. QMD 컬렉션명을 `tems-{agent_id}`로 동적 결정.

### 4.3 tems_scaffold.py — Scaffold 스크립트

**CLI:**
```bash
python tems_scaffold.py \
  --agent-id realgoon \
  --agent-name "리얼군" \
  --project MysticIsland \
  --cwd "E:/00_unrealAgent" \
  [--force]
```

**실행 순서:**
1. `{cwd}/.claude/` 디렉토리 확인/생성
2. `{cwd}/.claude/tems_agent_id` 생성 → agent-id 기록
3. `{cwd}/memory/` 디렉토리 생성
4. `{cwd}/memory/qmd_rules/` 디렉토리 생성
5. `{cwd}/memory/error_logs.db` 생성 — 전체 스키마:
   - `memory_logs` (id, timestamp, category, context_tags, keyword_trigger, correction_rule, action_taken, result, severity, summary)
   - `memory_fts` (FTS5 가상 테이블, content=memory_logs)
   - `rule_health` (rule_id, ths_score, status, last_activated, activation_count, modification_count)
   - `exceptions` (id, rule_id, type, description, persistence_score, promoted_to_rule_id)
   - `meta_rules` (id, rule_id, field_changed, old_value, new_value, reason, health_before, health_after)
   - `rule_edges` (source_id, target_id, edge_type, weight)
   - `co_activations` (rule_a_id, rule_b_id, prompt_hash, timestamp)
   - `tgl_sequences` (antecedent_id, consequent_id, count, avg_gap_hours, confidence)
   - `trigger_misses` (id, query, expected_rule_id, timestamp)
   - `rule_versions` (id, rule_id, field_changed, old_value, new_value, timestamp)
6. `tems_templates/preflight_hook.py` → `{cwd}/memory/preflight_hook.py` 복사
7. `tems_templates/tems_commit.py` → `{cwd}/memory/tems_commit.py` 복사
8. `{cwd}/.claude/settings.local.json`에 UserPromptSubmit hook 등록 (기존 설정 병합)
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [{
         "type": "command",
         "command": "python \"{cwd}/memory/preflight_hook.py\""
       }]
     }
   }
   ```
9. `E:/AgentInterface/tems_registry.json` 갱신:
   - agents에 항목 추가/갱신
   - `db_path`, `projects`, `status: "active"`, `last_verified` 설정
   - 프로젝트가 없으면 projects에도 추가

**멱등성:**
- 파일이 이미 존재하면 스킵 (`--force`로 덮어쓰기)
- DB가 이미 존재하면 스키마 검증만 수행 (누락 테이블 생성)
- 레지스트리 항목이 이미 있으면 갱신 (projects 병합, last_verified 갱신)

**출력:** JSON stdout
```json
{"ok": true, "agent_id": "realgoon", "actions": ["marker_created", "db_created", ...]}
```

**종료 코드:** 0=성공, 1=에러

### 4.4 tems_registry.json — 초기 상태

스펙 §4.2의 구조 그대로. S3 완료 시점에서는 위상군만 `last_verified` 설정:

```json
{
  "version": 1,
  "registry_path": "E:/AgentInterface/tems_registry.json",
  "projects": { ... },
  "agents": {
    "wesanggoon": {
      "name": "위상군",
      "projects": ["DnT"],
      "db_path": "E:/DnT/DnT_WesangGoon/memory/error_logs.db",
      "status": "active",
      "last_verified": "2026-04-09"
    },
    ...나머지는 last_verified: null 유지...
  }
}
```

### 4.5 /TEMS:project 스킬 — `~/.claude/skills/tems-project.md`

**S3 범위 서브커맨드:**
- `(프로젝트명)` → scaffold + register (신규 에이전트)
- `status` → 레지스트리 현황 출력

**스킬 내부 로직:**
1. `.claude/tems_agent_id` 읽기 시도
2. 없으면 → 신규. agent-id, agent-name 질문
3. `python E:/AgentInterface/tems_scaffold.py --agent-id X --agent-name Y --project Z --cwd CWD` 실행
4. 사후 검증:
   - `sqlite3 {cwd}/memory/error_logs.db ".tables"` → 테이블 존재 확인
   - `.claude/tems_agent_id` 읽기 확인
   - `tems_registry.json`에서 해당 에이전트 항목 확인
5. 결과 리포트 출력

**S4에서 추가될 서브커맨드** (이번 S3에서는 미구현):
- `add`, `rename`, `retire`, `reactivate`

## 5. Migration Safety Plan

### Phase A — 코어 구축 (기존 코드 무변경)
1. `E:/AgentInterface/tems_core/` 생성
2. 위상군 `fts5_memory.py`, `tems_engine.py`를 코어에 **복사**
3. 코어 import 경로 수정 (상대 import 정리)
4. DB_PATH, QMD 컬렉션명 파라미터화
5. 코어 단독 테스트

### Phase B — 템플릿 + scaffold 구축
1. `tems_templates/` 진입점 작성
2. `tems_scaffold.py` 작성
3. 테스트 에이전트(임시 디렉토리)로 scaffold E2E 테스트

### Phase C — 위상군 마이그레이션
1. `memory/_backup_tier1/`에 기존 4개 파일 백업
2. 진입점을 템플릿 버전으로 교체
3. `.claude/tems_agent_id` → `wesanggoon` 생성
4. 검증: `python -m memory.tests.test_preflight_semantic` + `python -m memory.tests.test_qmd_sync`
5. 실패 시 → 백업에서 즉시 복원

### Phase D — 레지스트리 + 스킬 배포
1. `tems_registry.json` 생성
2. `~/.claude/skills/tems-project.md` 배포
3. 위상군에서 `/TEMS:project DnT` 실행 → 자기 자신 검증
4. 스킬 status 서브커맨드로 레지스트리 현황 확인

## 6. Verification Criteria

| 검증 항목 | 명령 | 기대 결과 |
|-----------|------|----------|
| 코어 import | `python -c "import sys; sys.path.insert(0,'E:/AgentInterface/tems_core'); from fts5_memory import MemoryDB; print('OK')"` | OK |
| scaffold E2E | `python tems_scaffold.py --agent-id testgoon --agent-name "테스트군" --project Test --cwd /tmp/test_agent` | JSON 성공 + 파일 생성 |
| 위상군 preflight | `python -m memory.tests.test_preflight_semantic` | PASS |
| 위상군 QMD sync | `python -m memory.tests.test_qmd_sync` | PASS |
| 레지스트리 정합성 | `/TEMS:project status` | 위상군 active, 나머지 에이전트 목록 표시 |

## 7. Out of Scope (→ S4, S5)

- `/TEMS:project add/rename/retire/reactivate` 서브커맨드
- scaffold 로직 완성 (settings.local.json 고급 병합 등)
- 10개 에이전트 일괄 온보딩
- 디니군 마이그레이션
- cross-agent 검색 (Tier 3)
