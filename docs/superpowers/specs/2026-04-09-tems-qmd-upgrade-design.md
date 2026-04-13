# TEMS + QMD Dense Vector Upgrade — Design Spec
> Author: 위상군 | Date: 2026-04-09 Session 11 | Status: Draft

## 1. Problem Statement

TEMS Phase 1의 `HybridRetriever`는 FTS5 BM25(sparse) + QMD(dense) RRF를 설계했으나, dense 검색이 **규칙 DB가 아닌 세션 문서(`wesanggoon-sessions`)를 검색**하고 있어 Hybrid의 진짜 위력이 발휘되지 않는다.

가우스군이 CUDA 백엔드를 해결하여 `qmd embed`가 ~50초에 전체 재임베딩 가능해졌으므로, 이제 규칙 수백 개 수준에서 실시간 dense 검색이 실용적이다.

추가로, 에이전트가 10개 이상으로 증가하면서 cross-agent 규칙 검색 수요가 발생했으나, 프로젝트 간 규칙 혼선과 컨텍스트 윈도우 오염 위험이 있다.

## 2. Goals

1. TEMS 규칙 자체를 dense vector로 검색하여 BM25 어휘 불일치 문제 해결
2. 전 에이전트에 TEMS를 배포하고 프로젝트 단위로 묶는 인프라 구축
3. Local → Project → Global 3단계 폴백 cross-agent 검색 구현
4. 신규 프로젝트/에이전트 온보딩을 `/TEMS:project` 스킬 한 줄로 완료

## 3. Non-Goals

- TEMS Phase 2~4 (THS, TAC, MetaRule) 자체의 로직 변경
- QMD 엔진 자체 개선 (가우스군 영역)
- 에이전트 간 실시간 메시징 (Agent Teams 영역)

## 4. Architecture

### 4.1 3단계 폴백 검색

```
Preflight Query
    │
    ▼
[Level 1: Local]
    자기 error_logs.db (FTS5 + QMD dense)
    confidence ≥ threshold? → 결과 반환
    │ no
    ▼
[Level 2: Project]
    tems_registry.json에서 동일 프로젝트 에이전트 DB 목록 조회
    각 DB에 대해 dense 검색 (QMD 컬렉션 기반)
    결과에 [프로젝트: 에이전트명] 라벨
    confidence ≥ threshold? → 결과 반환
    │ no
    ▼
[Level 3: Global]
    전체 active 에이전트 DB 대상 dense 검색
    결과에 [외부: 에이전트명] 라벨
    → 결과 반환
```

### 4.2 TEMS Registry (`tems_registry.json`)

중앙 레지스트리 — 에이전트 ID는 불변, 경로는 가변.

```json
{
  "version": 1,
  "registry_path": "E:/AgentInterface/tems_registry.json",
  "projects": {
    "DnT": {
      "aliases": ["DnT", "MRV"],
      "status": "active"
    },
    "FermionQuant": {
      "aliases": ["FermionQuant", "Fermion"],
      "status": "active"
    },
    "MysticIsland": {
      "aliases": ["MysticIsland"],
      "status": "active"
    },
    "ChildSchedule": {
      "aliases": ["아이의하루", "ChildSchedule"],
      "status": "active"
    },
    "GCE": {
      "aliases": ["GCE"],
      "status": "active"
    },
    "TCAS": {
      "aliases": ["TCAS"],
      "status": "active"
    }
  },
  "agents": {
    "wesanggoon": {
      "name": "위상군",
      "projects": ["DnT"],
      "db_path": "E:/DnT/DnT_WesangGoon/memory/error_logs.db",
      "status": "active",
      "last_verified": "2026-04-09"
    },
    "buildgoon": {
      "name": "빌드군",
      "projects": ["DnT"],
      "db_path": "E:/MRV_DnT/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "artgoon": {
      "name": "아트군",
      "projects": ["DnT"],
      "db_path": "E:/DnT/DnT_ArtGoon/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "codegoon": {
      "name": "코드군",
      "projects": ["FermionQuant"],
      "db_path": "E:/QuantProject/DnT_Fermion/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "jaemigoon": {
      "name": "재미군",
      "projects": ["FermionQuant"],
      "db_path": "E:/QuantProject/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "gihakgoon": {
      "name": "기획군",
      "projects": ["FermionQuant"],
      "db_path": "E:/QuantProject/DNT_GihakGoon/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "realgoon": {
      "name": "리얼군",
      "projects": ["MysticIsland"],
      "db_path": "E:/00_unrealAgent/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "dinigoon": {
      "name": "디니군",
      "projects": ["MysticIsland"],
      "db_path": "E:/01_houdiniAgent/tems/tems_db.db",
      "status": "active",
      "last_verified": "2026-04-09"
    },
    "appgoon": {
      "name": "어플군",
      "projects": ["ChildSchedule"],
      "db_path": "E:/ChildSchedule/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "gaussgoon": {
      "name": "가우스군",
      "projects": ["GCE"],
      "db_path": "E:/GCE/GCE_Engineer/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    },
    "managegoon": {
      "name": "관리군",
      "projects": ["TCAS"],
      "db_path": "E:/TCAS_BUILDER/memory/error_logs.db",
      "status": "active",
      "last_verified": null
    }
  }
}
```

### 4.3 Agent Status Lifecycle

```
active ──→ stale (경로 깨짐, 자동 감지)
  │            │
  │            └──→ active (/TEMS:project 재실행 시 경로 갱신)
  │
  └──→ retired (/TEMS:project retire)
           │
           └──→ active (/TEMS:project reactivate, 필요 시)
```

- `active`: 검색 대상
- `stale`: 경로 접근 실패, cross-agent 검색에서 자동 제외, 경고 표시
- `retired`: 명시적 은퇴, cross-agent 검색 제외 (`--include-retired`로 명시적 포함 가능)

### 4.4 `/TEMS:project` 글로벌 스킬

단일 진입점으로 모든 TEMS 인프라 관리:

```bash
# 신규 에이전트 온보딩 (DB 생성 + preflight hook + settings 등록)
/TEMS:project MysticIsland

# 프로젝트 추가 소속
/TEMS:project add DnT

# 프로젝트 이름 변경 (전 에이전트 자동 갱신)
/TEMS:project rename OldName NewName

# 에이전트 은퇴
/TEMS:project retire 에이전트ID

# 에이전트 재활성화
/TEMS:project reactivate 에이전트ID
```

스킬 실행 시:
1. `tems_registry.json` 로드
2. 현재 CWD + 에이전트 ID로 해당 에이전트 식별
3. 지정된 작업 수행 (scaffold / register / rename / retire)
4. 레지스트리 갱신 + `last_verified` 타임스탬프 업데이트

신규 scaffold 시 자동 생성:
- `memory/error_logs.db` (전체 스키마: memory_logs, memory_fts, rule_health, exceptions, meta_rules, rule_edges, co_activations, tgl_sequences, trigger_misses, rule_versions)
- `memory/preflight_hook.py` (위상군 패턴 이식)
- `memory/tems_commit.py` (CLI)
- `.claude/settings.local.json`에 UserPromptSubmit hook 등록

### 4.5 TEMS 전용 QMD 컬렉션

각 에이전트의 규칙을 개별 QMD 컬렉션으로 임베딩:

```
qmd://tems-wesanggoon/     → 위상군 규칙 벡터
qmd://tems-buildgoon/      → 빌드군 규칙 벡터
qmd://tems-all/            → 전체 에이전트 규칙 통합 (Global 검색용)
```

- `tems_commit` 시 → 해당 에이전트 컬렉션 + `tems-all` 컬렉션 동시 갱신
- `_dense_search()` Level 1 → `tems-{agent_id}` 컬렉션 검색
- `_dense_search()` Level 2 → 동일 프로젝트 에이전트 컬렉션들 검색
- `_dense_search()` Level 3 → `tems-all` 컬렉션 검색

## 5. Tier Roadmap

### Tier 1 — 구조 교정 (세션 1~2)
> 방식: `autoresearch:plan` → `writing-plans` → 구현

위상군 단독. 기존 코드 수정, 측정 가능한 목표.

| 세션 | 작업 | 산출물 | 검증 |
|------|------|--------|------|
| **S1** | `_dense_search()`를 `tems-wesanggoon` QMD 컬렉션으로 교정 + `tems_commit` 시 자동 임베딩 + `sync_rules_to_qmd()` 리팩터 | `tems_engine.py` 수정, QMD 컬렉션 생성 | BM25 miss 쿼리 → dense catch 비교 테스트 |
| **S2** | Preflight 시맨틱 폴백 통합 + Dynamic Weighted RRF 가중치 재튜닝 | `preflight_hook.py` 수정 | preflight 품질 A/B 비교 (동일 쿼리 10개) |

### Tier 2 — TEMS 확산 + 인프라 (세션 3~5)
> 방식: `brainstorming` (스킬 설계) → `writing-plans` → 구현

새로운 시스템/스킬 설계. 요구사항 정제 필요.

| 세션 | 작업 | 산출물 | 검증 |
|------|------|--------|------|
| **S3** | `tems_registry.json` 구현 + `/TEMS:project` 글로벌 스킬 코어 (scaffold + register) | 레지스트리 파일, 글로벌 스킬 | 위상군에서 `/TEMS:project DnT` 실행 성공 |
| **S4** | `/TEMS:project` 확장 (add, rename, retire, reactivate) + scaffold 로직 완성 | 스킬 완성, scaffold 스크립트 | 리얼군(DB 없음)에서 `/TEMS:project MysticIsland` → E2E |
| **S5** | 기존 10개 에이전트 일괄 온보딩 + 프로젝트 매핑 등록 + QMD 컬렉션 생성 | 전 에이전트 DB + 컬렉션 | 각 에이전트 `preflight` 작동 + `qmd status` 벡터 확인 |

### Tier 3 — Cross-Agent 검색 (세션 6~7)
> 방식: `autoresearch` (검색 알고리즘) → 구현 → `autoresearch:security`

알고리즘 최적화 + 반복 실험.

| 세션 | 작업 | 산출물 | 검증 |
|------|------|--------|------|
| **S6** | 3단계 폴백 구현 (Local → Project → Global) + confidence threshold 설계 + context budget 확장 | `tems_engine.py` HybridRetriever v2 | DnT 프로젝트 내 cross-검색 테스트 |
| **S7** | 시맨틱 중복 탐지 + 도메인 태그 필터 + `tems-all` 컬렉션 운용 + 보안 검토 | 중복 탐지 모듈, 보안 리포트 | 프로젝트 간 규칙 혼선 없음 확인 |

## 6. Key Design Decisions

| 결정 | 근거 |
|------|------|
| Local-First + 3단계 폴백 | 컨텍스트 윈도우 오염 방지 + 프로젝트 간 혼선 차단 |
| 에이전트 ID 불변 + 경로 가변 | 디니군 경로 깨짐 교훈 (S9~S10) |
| `/TEMS:project` 단일 스킬 | 온보딩 진입장벽 최소화 |
| 글로벌 레지스트리 (centralized) | cross-agent 검색 시 O(1) 프로젝트 매핑 조회 |
| 에이전트별 QMD 컬렉션 + `tems-all` 통합 | Level 1~3 검색 범위 자연 분리 |
| Tier 1 autoresearch / Tier 2 brainstorming / Tier 3 autoresearch | 코드 수정 vs 시스템 설계 vs 알고리즘 실험 — 각 성격에 맞는 방식 |

## 7. Risks & Mitigations

| 리스크 | 완화 |
|--------|------|
| QMD 임베딩 비용 (10개 에이전트 규칙) | CUDA ~50초/전체, 규칙 수백 개 수준에서 실용적 |
| 레지스트리 single point of failure | 레지스트리 접근 실패 시 Local-only 폴백 (graceful degradation) |
| 에이전트 DB 스키마 불일치 | scaffold가 표준 스키마를 강제, 버전 필드로 마이그레이션 관리 |
| Cross-agent에서 민감 규칙 노출 | 에이전트별 `private` 플래그 지원 (향후, 현재는 모든 규칙 공유 가능) |

## 8. Project-Agent Mapping (Initial)

| 프로젝트 | 에이전트 |
|---------|---------|
| DnT | 위상군, 빌드군, 아트군 |
| FermionQuant | 코드군, 재미군, 기획군 |
| MysticIsland | 리얼군, 디니군 |
| ChildSchedule | 어플군 |
| GCE | 가우스군 |
| TCAS | 관리군 |
