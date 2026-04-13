---
title: Atlas — 동적 계층 문서 시스템 스킬 (v1.0 설계)
date: 2026-04-11
status: design-approved
authors: 종일군, 위상군
atlas_version: 1.0
---

# Atlas — 동적 계층 문서 시스템 스킬 (v1.0 설계)

## 0. Executive Summary

**Atlas**는 프로젝트 규모가 커질수록 에이전트의 컨텍스트 윈도우가 포화되는 구조적 문제를 해결하기 위한 **계층 문서 시스템 구축/유지 스킬**이다.

핵심 아이디어 6가지:

1. **2축 직교 모델** — 문서의 좌표를 `(추상화 레벨, 시간축)`으로 분리. 레벨은 `L0~LN` 동적 확장, 시간축은 `present | history` 이진. 포폴군의 "L3=history" 혼선을 제거.
2. **동적 위상 연산 3가지** — `split-vertical` (수직 증식, L_k→L_{k+1}), `split-horizontal` (수평 증식, L_k 내 분화), `collapse` (역연산). OVERFLOW 감지 자동, 분할 모드 결정은 에이전트.
3. **위상 불변량 I1~I8** — 어떤 깊이로 확장되든 유지되어야 할 성질 8개. 매 세션 부트/shutdown/훅에서 검증.
4. **Drill-down 그래프 크롤 (하이브리드)** — L0 skeleton_index로 첫 hop 가속 + frontmatter bidirectional 링크로 수직/수평/상승 탐색 통일. 예산 기반 확장.
5. **3-Stage 백필 + TEMS 크로스 체크** — 기존 대형 프로젝트에 도입할 때 Shell→Spine→History 단계별 게이트. Stage 3는 기존 TEMS TGL과 교차 링크만 하고 중복 기록 금지.
6. **L-history → TGL 승격** — Rule 1(local ≥3회), Rule 2(cross-functional ≥2회), Rule 3(명시 플래그) 기반 자동 탐지 + 사용자 승인 기반 등록.

**목표 지표:**
- 1000노드/수천 줄 프로젝트 세션 부트 시 컨텍스트 사용 ≤ 10KB
- L0 + 평균 3~5개 L_k 파일 = 전형적 working set
- 동적 레벨 확장으로 인한 에이전트 개입 ≤ 세션당 2회

---

## 1. 목적과 배경

### 1.1 문제

규모가 일정 이상인 프로젝트에서 에이전트는 다음 고통을 반복한다:

- **전수 탐색 폭주** — 세션마다 구조 재파악, 38K+ 토큰이 한 번에 소모되어 메인 컨텍스트 즉시 포화 (리얼군 S1 hip 파일 검증 사례)
- **문서-빌드 drift** — "동기화하라" 규칙만으로는 반복 실수 발생, 문서가 구 버전에 정체
- **히스토리 기억 상실** — 과거 버그/패치의 교훈이 커밋 메시지에만 잔류, 같은 실수 재발
- **횡단 맥락 부재** — 기능 A를 수정할 때 어떤 다른 기능이 연관되어 있는지 파악 불가
- **도입 비용 장벽** — 계층 문서를 구축하려고 해도 전수 읽기가 필요해서 결국 미룸

### 1.2 목표

- **어떤 프로젝트에나 적용 가능**한 범용 스킬 (SPA / backend API / 파이프라인 / 노드 그래프 / 라이브러리)
- 에이전트가 **필요한 만큼만 계층적으로 로드** — drill-down/횡단/상승 모두 지원
- **도입 비용 최소화** — 단계별 게이트로 사용자가 원하는 깊이에서 멈출 수 있음
- **drift 방지 3중 방어** — Edit/Write 훅 + TEMS TCL + 세션 종료 체크
- **위상군 소유** — 구현 완료 시 독립 git 레포로 분리하여 발전 가능

### 1.3 비목표 (Non-goals)

- 사람 독자 전용 레퍼런스 매뉴얼 자동 생성
- 코드 API 레퍼런스 자동 생성 (JSDoc/타입 스크립트 기반 정적 분석 아님)
- 실시간 소스 파일 감시 (Edit/Write 도구 경유만, 파일 시스템 watcher 없음)
- 멀티 프로젝트 간 atlas 상호 참조 (단일 프로젝트 범위)
- atlas 자체의 자동 버저닝/마이그레이션 (v1.0 고정, v1.1 이후 설계)

### 1.4 레퍼런스

이 설계는 2개의 선행 구현을 일반화한 결과이다:

- **포폴군** (`E:/KJI_Portfolio/docs/architecture/`) — L0~L3 고정 계층, 3중 방어 동기화, 12개 L2 파일, git log 기반 백필
- **리얼군** (`E:/01_houdiniAgent/docs/houdini-graph/`) — 2단계 청킹 (skeleton + segments), 엔드노드 앵커, lazy 확장, manifest 기반 역인덱스

두 접근법의 공통 DNA를 추출하고, 각각의 한계(포폴군: 레벨 고정, 리얼군: 수동 동기화)를 **동적 레벨 확장 + 선언적 sync_watch**로 해결한다.

---

## 2. 핵심 결정 요약

| # | 결정 | 선택 | 근거 |
|---|------|------|------|
| 1 | 스킬 형태 | **B) 가이드 + 스캐폴딩 자동화** | 재현성 + 시작 비용 최소화 |
| 2 | 앵커 전략 | **C) 프리셋 + 보편 알고리즘 + frontmatter 기록** | 흔한 유형 가속 + 어떤 유형에도 대응 |
| 3 | 레벨 구조 | **L0~LN 동적 × (present, history) 2축 직교** | 고정 L0~L3의 경직성 해소 |
| 4 | Drill-down | **D) 하이브리드 (L0 skeleton_index + frontmatter 그래프 크롤)** | 첫 hop 가속 + 수직/수평/상승 통일 |
| 5 | 백필 전략 | **D) 3-Stage 점진 백필 + D-3 TEMS 크로스 체크** | 단계별 게이트 + TEMS 단일 진실원 원칙 |
| 6 | 동기화 | **sync_watch frontmatter + 3중 방어 (Hook+TCL+Shutdown)** | 자기기술적, 프로젝트 유형 독립 |
| 7 | TEMS 승격 | **Y) 자동 탐지 + 수동 승인** (Rule 1/2/3) | false positive 방지 + 승격 누락 방지 |
| 8 | 스킬 이름 | **atlas** | 위상수학 atlas와 수학적 동형 (manifold/chart/transition map) |

### 2.1 보충 결정 (검증 질문 답변)

| 질문 | 결정 |
|------|------|
| A1 — Stage 1 T=4 모듈 판별 확인 게이트 | **추가** (I4 위반 downstream 비용 회피) |
| B1 — Stage 3 diff 요약 주체 | **Haiku 서브콜 우선, 폴백=메인 에이전트** |
| B2 — TEMS 크로스 체크 유사도 임계값 | **Jaccard ≥ 0.5 AND 공통 키워드 ≥ 2개** (이중 조건), config.yaml override |
| C1 — Drill-down 우선순위 공식 | **SKILL.md에 고정 공식 + 명시적 justification으로 deviate 허용** |
| C2 — drift clear 3-옵션 | **규칙화 — {본문수정, 히스토리추가, no-op 명시} 3가지로만 clear** |

---

## 3. 아키텍처

### 3.1 3개 공간 배치

스킬 설치/운용 시 파일은 서로 다른 3개 공간에 존재한다. 각 공간의 책임이 다르므로 혼동 금지.

#### 공간 A — 스킬 패키지 원본 (단일 설치, 공유)

```
E:/AgentInterface/skills/atlas/
├── SKILL.md                          # 에이전트가 읽는 가이드 (진입점)
├── references/
│   ├── topology-invariants.md        # I1~I8 상세 정의 + 검증 로직
│   ├── drill-down-protocol.md        # NAV 프로토콜 + 우선순위 공식
│   ├── backfill-staged.md            # Stage 1~4 절차 상세
│   ├── sync-watch-schema.md          # frontmatter 스키마 권위 정의
│   ├── promotion-rules.md            # Rule 1/2/3 + 승격 프로토콜
│   └── anchor-presets.md             # spa / backend-api / pipeline 프리셋
├── templates/
│   ├── L0.template.md
│   ├── Lk.template.md                # level 파라미터화 템플릿 (k≥1)
│   ├── Lk.history.template.md
│   ├── README.template.md
│   └── CHANGELOG.template.md
├── scripts/
│   ├── atlas_setup.py                # Stage 1 (shell)
│   ├── atlas_backfill.py             # Stage 2~3 (spine + history)
│   ├── atlas_check.py                # 불변량 검증 + drift 스캔
│   ├── atlas_split.py                # 수직/수평 증식 실행
│   ├── atlas_collapse.py             # 역연산
│   ├── atlas_promote_check.py        # TGL 승격 후보 탐지
│   ├── atlas_rebuild_cache.py        # .hdocs/ 캐시 재빌드 (F5 복구)
│   └── topology.py                   # 공통 라이브러리
└── hook_templates/
    ├── post_tool_use_sync.py.tmpl
    └── session_end_check.py.tmpl
```

**책임:** 원본 보관. 각 프로젝트 설치 시 템플릿 렌더링하여 공간 B로 복제.

**배치 이유:** `E:/AgentInterface/`는 이미 TEMS 인프라의 중앙이고, atlas 역시 범용 에이전트 스킬이므로 같은 위치가 자연스러움.

#### 공간 B — 프로젝트 내부 설치물 (프로젝트별 복제)

```
<PROJECT>/
├── .claude/
│   ├── references/
│   │   └── L0-architecture.md        # L0 (SessionStart 훅 자동 주입)
│   └── hooks/
│       ├── post_tool_use_sync.py     # 공간 A 템플릿에서 렌더링
│       └── session_end_check.py
├── docs/
│   └── architecture/                 # L1 이하 전체
│       ├── README.md
│       ├── CHANGELOG.md
│       └── <module>/
│           ├── README.md             # L1 (모듈)
│           ├── <feature>.md          # L2
│           ├── <feature>.history.md
│           └── <feature>/            # L3 (동적 생성)
│               ├── <subcomponent>.md
│               └── <subcomponent>.history.md
└── .hdocs/                           # git ignored (옵션 E 원칙)
    ├── manifest.json                 # topology 엔진 in-memory 캐시
    ├── sync_index.json               # sync_watch 역인덱스 (path → L파일 목록)
    └── config.yaml                   # 프로젝트별 설정
```

**책임:** 실제 문서 + 훅 + 캐시. `.hdocs/`는 git ignored이며 훅이 maintain함 (TEMS 옵션 E 교훈 적용 — 런타임 생성물은 머신별 축적이 본질).

#### 공간 C — TEMS (프로젝트별, 이미 존재)

```
<PROJECT>/memory/
├── tems_db.db                        # gitignored
└── qmd_rules/
    └── rule_*.md                     # git tracked (rebuild 가능)
```

**책임:** 승격된 TGL의 최종 저장소. Atlas는 공간 C에 쓰기만 수행 (`tems_commit.py` 경유). 읽기는 TEMS의 기존 preflight 메커니즘이 담당.

### 3.2 4개 엔진 + 공통 라이브러리

```
                 ┌──────────────────┐
                 │   topology.py    │ (공통 라이브러리)
                 │  - 불변량 I1~I8  │
                 │  - 그래프 조작    │
                 │  - sync_watch    │
                 │  - skeleton_idx  │
                 └────────┬─────────┘
                          │
     ┌────────────┬───────┴───────┬────────────┐
     ▼            ▼               ▼            ▼
  ┌──────┐   ┌────────┐   ┌───────────┐  ┌──────────┐
  │SETUP │   │ SYNC   │   │  NAV      │  │ PROMOTE  │
  │엔진  │   │ 엔진   │   │ 프로토콜   │  │ 엔진     │
  │      │   │        │   │(에이전트  │  │          │
  │Stage │   │PostTool│   │ 수행)     │  │Rule 1/2  │
  │1/2/3 │   │Use 훅  │   │           │  │ 탐지     │
  │백필  │   │Shutdown│   │drill-down │  │세션종료  │
  │      │   │체크    │   │graph crawl│  │후보 제시 │
  └──────┘   └────────┘   └───────────┘  └──────────┘
```

**책임 구분:**

1. **SETUP 엔진** (결정론적) — 1회성, 프로젝트 도입 시 실행. `atlas setup` / `atlas backfill`로 호출.
2. **SYNC 엔진** (결정론적) — 매 Edit/Write마다 훅으로 실행. drift 탐지 + 리마인더 주입. 세션 종료 시 shutdown 체크.
3. **NAV 프로토콜** (에이전트 수행) — 엔진이 아니라 **SKILL.md가 기술하는 알고리즘**. 에이전트가 의미 해석이 필요한 부분을 담당. topology.py는 skeleton_index lookup, 그래프 탐색 유틸리티만 지원.
4. **PROMOTE 엔진** (결정론적 탐지 + 사용자 승인) — 세션 종료 시 실행. L-history 스캔 → 후보 → 사용자 승인 → TEMS 커밋.

**NAV를 엔진이 아니라 프로토콜로 분리한 이유:** "어떤 depends_on을 더 따라갈지"는 의미 해석이 필요하여 자동화가 부적절. 다른 3개는 결정론 알고리즘으로 충분. 이 분리가 atlas의 핵심 철학이며, "결정론 + 판단력 혼합"을 깔끔하게 나누는 축.

---

## 4. 데이터 모델

### 4.1 파일의 2축 좌표

```
모든 파일은 정확히 두 개의 축 좌표를 가진다:
  - level: 0, 1, 2, ... (정수, 동적 확장)
  - time:  present | history  (이진)
```

**파일명 규약:**
- `(level=k, time=present)` → `<name>.md`
- `(level=k, time=history)` → `<name>.history.md`
- 두 파일은 반드시 페어 (I8)

### 4.2 Frontmatter 스키마 (Present)

```yaml
---
# 필수 — 위상 좌표
atlas_version: 1.0
level: 2
parent: docs/architecture/gallery/README.md  # L_{k-1} present 파일 경로
children: []                                  # L_{k+1} 있으면 경로 목록

# 필수 — 링크 (bidirectional invariant I6)
depends_on: [worker/endpoints.md, worker/cloudinary-integration.md]
used_by:    [admin-panel.md, group-management.md]

# 필수 — 탐색/동기화
keywords: [crop, coordinate, cloudinary-transform, 좌표]
sync_watch:
  - path: gallery.html
    range: [1680, 1944]
  - path: gallery.html
    range: [2183, 2201]
last_synced_commit: 902259c

# 선택 — 메타
owner: <agent-name>                    # "primary" agent. 타 에이전트 편집은 L-history에 서명
anchor_strategy: preset:spa            # preset:<type> | derived | manual
status: active                          # active | stub | deprecated
history_of: null                        # present는 항상 null
---
```

**멀티 에이전트 협업:** `owner`는 해당 L 파일의 **1차 소유자**를 지정한다. 다른 에이전트(예: 빌드군)가 같은 L 파일을 편집해야 할 때는 `owner`를 바꾸지 않고, L-history 엔트리에 서명(`by: <agent-name>`) 필드를 포함하여 출처를 남긴다. 단일 진실원 원칙 — owner는 문서의 책임자이지 독점자가 아니다.

### 4.3 Frontmatter 스키마 (History)

```yaml
---
atlas_version: 1.0
level: 2                                # 짝 present와 동일
history_of: gallery/crop-editor.md      # 짝 present 경로 (필수)
append_only: true
owner: <agent-name>
---
```

History는 `parent`/`children`/`depends_on`/`used_by`/`keywords`/`sync_watch`를 갖지 않는다. 모든 구조 정보는 짝 present에서 상속. 2축 직교의 핵심 — "L3=history" 혼선 제거.

### 4.4 L0 특수 — Skeleton Index

L0는 drill-down 1-hop 가속용 인라인 인덱스를 갖는다. **topology 엔진이 자동 생성/재빌드**하며, 수동 유지 금지.

```yaml
---
atlas_version: 1.0
level: 0
anchor_strategy: preset:spa
budget:
  drill_files: 8
  history_per_file: 1
  tokens_soft_cap: 20000
max_lines:
  0: 200
  1: 300
  default: 500                          # k≥2
promotion:
  similarity_threshold: 0.5             # Jaccard
  min_shared_keywords: 2
  rule1_min_occurrences: 3
  rule2_min_occurrences: 2
skeleton_index:
  - keywords: [crop, 좌표, coordinate]
    entry: docs/architecture/gallery/crop-editor.md
  - keywords: [upload, 업로드]
    entry: docs/architecture/gallery/upload.md
---
```

### 4.5 L-history 엔트리 스키마

```markdown
### #N — YYYY-MM-DD `<SHA>` <유형 이모지> <한 줄 제목>

**증상:** …
**재현:** … (버그만)
**원인:** …
**패치:** 파일:라인 …
**교훈:** …
**관련 파일:** …
**promote_candidate:** true | false    <!-- Rule 3용, 기본 false -->
**tgl_ref:** TGL#2                      <!-- 역링크, 없으면 생략 -->
**keywords_for_promotion:** [coordinate, single-source-of-truth, cloudinary-transform]
```

`keywords_for_promotion` 필드가 Rule 1/2 탐지기의 입력이 된다.

### 4.6 MAX_LINES 공식

```
MAX_LINES[0] = 200
MAX_LINES[1] = 300
MAX_LINES[k] = 500   for k >= 2
```

`config.yaml`에서 레벨별 override 가능. 초과 시 I5(OVERFLOW) 플래그 → 분할 제안.

---

## 5. 위상 불변량 I1~I8

| # | 불변량 | 검증 주체 | 위반 레벨 | 대응 |
|---|------|---------|---------|------|
| I1 | L0 파일 정확히 1개 존재 | check_invariants | 치명 | 에러, 복구 절차 안내 |
| I2 | 모든 파일은 유일한 parent (트리 구조) | check_invariants | 치명 | 에러, DAG 탐지 시 수동 개입 |
| I3 | `avg_size(L_k) / avg_size(L_{k-1}) ∈ [0.1, 0.5]` | check_invariants | 경고 | 분할 또는 축소 제안 |
| I4 | `fan_out(L_{k-1} entry) ∈ [2, 12]` | check_invariants | 경고 | 단일 자식 → collapse, 12+ → 추가 분할 |
| I5 | `lines(file) ≤ MAX_LINES[level]` | PostToolUse 훅 + check | OVERFLOW | 분할 제안 |
| I6 | `depends_on` ↔ `used_by` 양방향 일관성 | SYNC 엔진 | 자동 보정 | topology.update_bidirectional_links() |
| I7 | 파일명 = 상위 인덱스의 stable identifier | check_invariants | 경고 | rename 시 상위 인덱스 자동 업데이트 |
| I8 | `.history.md`는 짝 `present.md` 필수 | check_invariants | 치명 | dangling history 감지 → 수동 개입 |

**검증 시점:**
- **매 Edit/Write 후** (PostToolUse 훅): I5, I6
- **세션 부트 시**: I1, I2, I8 (치명 우선)
- **세션 종료 시** (shutdown 체크): I3, I4, I7 (경고 포함 전수)
- **atlas 명령 실행 전후** (setup/backfill/split/collapse): 전수

---

## 6. 런타임 플로우 — 3개 시나리오

### 6.1 시나리오 A — 새 프로젝트 shell 설치

**상황:** 종일군이 새 프로젝트에서 에이전트에게 "atlas 도입"을 지시.

```
[T=0] 사용자: "atlas 스킬 도입"

[T=1] 에이전트: SKILL.md 읽음 → Stage 1 절차 시작

[T=2] atlas_setup.py 실행
      ├─ 프로젝트 루트 Glob (src/**, package.json, pyproject.toml 등)
      ├─ anchor_strategy 프리셋 판별 (예: package.json+react → preset:spa)
      └─ 사용자 확인 게이트: "앵커 전략 'preset:spa' 맞나요? (y/n/manual)"

[T=3] L0 생성 (.claude/references/L0-architecture.md)
      ├─ 템플릿 렌더링
      ├─ skeleton_index: 빈 배열
      └─ budget/max_lines/promotion 기본값

[T=4] L1 모듈 판별 — ★ 확인 게이트 (A1 결정)
      ├─ 에이전트가 3~5개 모듈 추정 (예: [frontend, api, shared])
      ├─ 사용자 확인 게이트: "모듈 이 3개로 괜찮나요?"
      └─ 승인 후 L1 생성
          - docs/architecture/<module>/README.md 각각 (최소: 진입점+요약)

[T=5] topology.rebuild_skeleton_index() → L0 업데이트

[T=6] 훅 설치 (.claude/hooks/)
      ├─ post_tool_use_sync.py (템플릿 렌더링)
      └─ session_end_check.py

[T=7] TEMS TCL 규칙 등록
      └─ "atlas sync drift 발생 시 해당 L 파일 업데이트"

[T=8] .hdocs/ 생성 (config.yaml, manifest.json, sync_index.json, .gitignore)

[T=9] 에이전트 → 사용자:
      "Stage 1 완료. L0 1, L1 N, 훅 2, TCL 1 등록.
       Stage 2 (spine, git log Top-K) 진행? 또는 종료?"
```

**이 시점의 드릴다운:** L1만 있어도 작동. 기능 요청 시 에이전트는 L0 skeleton_index → 가장 가까운 L1 entry → "L2 없음" 확인 → on-demand 생성 제안 → 사용자 승인 → lazy expansion.

### 6.2 시나리오 B — 기존 대형 프로젝트 백필 (Stage 3 + 3)

**상황:** Stage 1 완료 상태. 사용자가 Stage 2 진행 선택.

```
[Stage 2 — Spine, T=0]
      사용자: "Stage 2 진행"

[T=1] atlas_backfill.py --stage 2
      ├─ git log --name-only -50 → 파일 수정 빈도 집계
      └─ Top-K=8 파일 추출

[T=2] 각 파일을 L1 모듈과 매칭 (경로 규칙) → L2 stub 생성
      ├─ 최소 템플릿: 목적 / 코드 위치 / 핵심 동작 (TODO) / depends_on (빈)
      ├─ sync_watch 자동 등록
      └─ status: stub

[T=3] 에이전트가 각 L2 stub의 sync_watch 범위만 읽음 (전수 탐색 금지)
      ├─ 핵심 동작 3~5줄 작성
      ├─ 명백한 depends_on 추출 (import/require)
      └─ topology.update_bidirectional_links() → used_by 자동

[T=4] check_invariants() 전수
      ├─ I3 (압축비) 통과 확인
      ├─ I4 (팬아웃) 통과 확인
      └─ stub 파일 수 기록

[T=5] L0 skeleton_index 재빌드

[T=6] 사용자 게이트: "Stage 3 진행? 또는 종료?"

─────────────────────────────────────

[Stage 3 — History, T=0]
      사용자: "Stage 3 진행"

[T=1] atlas_backfill.py --stage 3
      └─ Stage 2에서 생성된 L2만 대상

[T=2] 각 L2마다:
      ├─ git log --follow <sync_watch.path> -L <range> → fix/revert 추출
      ├─ 커밋당 diff 요약 — ★ Haiku 서브콜 (B1 결정)
      │   폴백: Haiku 미사용 환경이면 메인 에이전트가 직접
      ├─ (증상/원인/패치/교훈/keywords_for_promotion) 템플릿 변환
      └─ L_k.history.md에 append

[T=3] ★ D-3 TEMS 크로스 체크 ★
      ├─ 각 교훈의 keywords_for_promotion으로 TEMS DB BM25 검색
      ├─ Jaccard ≥ 0.5 AND 공통 키워드 ≥ 2개 (B2 결정) 만족 시:
      │   → L-history 엔트리에 tgl_ref: TGL#N 역링크
      │   → 중복 텍스트 금지 (단일 진실원 — TCL#75 원칙 존중)
      └─ 매칭 없으면:
          → promote_candidate 필드 설정 (PROMOTE 엔진이 나중 탐지)

[T=4] check_invariants() 전수
[T=5] 사용자에게 보고: history 엔트리 수, 역링크 수, 승격 후보 수
```

### 6.3 시나리오 C — 일반 개발 세션 (drill-down + 동기화 + 승격, 메인 유스케이스)

**상황:** Stage 2까지 완료된 포폴군 프로젝트. 사용자가 "크롭 에디터에서 좌표가 또 틀어지는 것 같다"고 요청.

```
[T=0] 세션 부트
      └─ SessionStart 훅: L0-architecture.md 자동 주입 (200줄 이내)

[T=1] 사용자 요청 수신

[T=2] 에이전트 — Drill-down 시작 (NAV 프로토콜)
      ├─ L0.skeleton_index 스캔 (이미 주입됨)
      ├─ keywords=[crop, 좌표] 매칭 → entry=crop-editor.md
      └─ working_set = [L0, crop-editor.md]

[T=3] crop-editor.md 읽기
      ├─ frontmatter 파싱:
      │   depends_on=[worker/endpoints.md, worker/cloudinary-integration.md]
      │   used_by=[admin-panel.md, group-management.md]
      │   sync_watch=gallery.html:1680-1944, 2183-2201
      └─ 본문 읽기 → "원본 픽셀 단일 진실원 (TGL#2)" 제약 확인

[T=4] 사용자 의도 = 디버깅 → history 로드 판단
      └─ crop-editor.history.md 읽기
          → 과거 #1 (c_limit,w_1920), #2 (applyCrop 누락) 확인

[T=5] 횡단 확장 — 우선순위 큐 (C1 결정, 고정 공식)
      priority(file) = 0.5 × keyword_match
                     + 0.3 × link_weight[link_type]
                     + 0.2 × (1 / distance_from_current)
      link_weight: depends_on=1.0, used_by=0.8, parent=0.6, children=0.5

      ├─ 큐 계산:
      │   cloudinary-integration → 0.5×0.6 + 0.3×1.0 + 0.2×1.0 = 0.80
      │   endpoints             → 0.5×0.2 + 0.3×1.0 + 0.2×1.0 = 0.60
      │   admin-panel           → 0.5×0.1 + 0.3×0.8 + 0.2×1.0 = 0.49
      │   group-management      → 0.5×0.1 + 0.3×0.8 + 0.2×1.0 = 0.49
      │   gallery/README(parent) → 0.5×0.3 + 0.3×0.6 + 0.2×1.0 = 0.53
      ├─ 예산 drill_files=8, 현재 2 → 남은 6
      └─ 상위 3개 로드: cloudinary-integration(0.80), endpoints(0.60), parent(0.53)

[T=6] 에이전트 → 사용자: 분석 보고
      "1. 과거 동일 증상 2건 (TGL#2 등록됨)
       2. crop-editor 제약: 원본 URL에 c_limit 금지
       3. gallery.html:1695 확인 필요"

[T=7] gallery.html:1695 읽기 (sync_watch 범위 내 필요 부분만)
      → 발견: c_limit,w_1920 재추가 (회귀)

[T=8] 수정 제안 → 사용자 승인 → Edit 도구로 수정

[T=9] ★ PostToolUse 훅 (SYNC 엔진) ★
      ├─ sync_index.json 조회: gallery.html:1695 → [crop-editor.md (L2)]
      ├─ last_synced_commit < HEAD → STALE 플래그
      └─ 리마인더 주입:
         <doc-sync-reminder>
         [drift 감지] gallery.html:1695 수정 (sync_watch 범위)
         대응 L: docs/architecture/gallery/crop-editor.md
         → 다음 3가지 중 1개로 clear (C2 결정):
           (a) 본문 수정
           (b) 히스토리 추가
           (c) "docs: no-op" 명시
         </doc-sync-reminder>

[T=10] 에이전트 판단: 코드 위치/핵심 동작 라인 번호 불변 → 본문 수정 불필요
       → L-history에 append (clear 옵션 b):
          "#3 — 2026-04-11 회귀 — c_limit 재추가 → 제거
           원인: 다른 PR에서 잘못된 patch
           교훈: 주기적 회귀 체크 필요
           promote_candidate: true
           keywords_for_promotion: [coordinate, c_limit, cloudinary-transform, regression]"

[T=11] 세션 종료 → session_end_check.py

[T=12] ★ PROMOTE 엔진 실행 ★
       ├─ topology.detect_promotion_candidates()
       │   Rule 1: crop-editor.history #1,#2,#3 → 유사도 0.6 (모두 좌표 단일 진실원)
       │         → 이미 TGL#2 등록 (tgl_ref 있음) → skip
       │   Rule 2: 다른 L-history 파일 (upload/admin-panel/endpoints 등) 전수 스캔
       │         → [coordinate, c_limit, cloudinary-transform, regression] 키워드와
       │           Jaccard ≥ 0.5 AND 공통 키워드 ≥ 2 매칭 없음 → 없음
       │   Rule 3: promote_candidate 플래그 있음 but TGL#2 매핑됨 → skip
       └─ 후보 0건 → 사용자 개입 없이 통과

[T=13] check_invariants() 전수 통과

[T=14] 핸드오버 문서 작성 → 세션 종료

─────────────────────────────────────

[다음 세션 부트]
      └─ L0 자동 주입 + TEMS preflight
         (preflight에 TGL#2 자동 노출 → "c_limit 금지")
         → 같은 실수 반복 방지
```

**시나리오 C의 핵심 포인트 (3가지):**

1. **토큰 소비:** L0 (200줄) + crop-editor.md (50줄) + crop-editor.history.md + 3개 depends_on/parent 파일 + 해당 소스 범위만 ≈ 총 ~15KB. 전수 탐색 대비 60~80% 절감.
2. **drift clear 3-옵션 (C2):** 훅이 리마인더를 줬다고 무조건 본문을 수정해야 하는 것이 아니다. `{본문수정, 히스토리추가, no-op 명시}` 중 1가지로만 clear 가능. 이 규칙이 없으면 drift = open loop.
3. **TEMS 단일 진실원:** 과거 #1이 이미 TGL#2로 승격되어 있으므로 새 L-history 엔트리 #3도 자동으로 같은 TGL에 흡수되고 중복 승격 시도하지 않음. TCL#75의 "DB가 source of truth" 원칙과 일치.

---

## 7. 백필 전략 — 3-Stage 점진 백필

### 7.1 Stage 진행 개요

| Stage | 산출물 | 예상 토큰 | 게이트 |
|-------|-------|---------|-------|
| 1 (Shell) | L0 + L1 N개 + 훅 + TEMS TCL + .hdocs/ | ~5K | 앵커 프리셋 확인, 모듈 판별 확인 |
| 2 (Spine) | Top-K L2 stub → 본문 작성 | ~15K | 진행 여부 확인 |
| 3 (History) | L-history 엔트리 + TEMS 크로스 체크 | ~25K+ (프로젝트 크기 비례) | 진행 여부 확인 |
| 4+ (Lazy) | 이후 작업 중 자동 확장 | 작업별 | 없음 (자율) |

### 7.2 Stage 1 — Shell

§6.1 시나리오 A와 동일.

**사용자 확인 게이트 2개:**
1. T=2: 앵커 프리셋 확인 (`preset:spa` 맞는지)
2. T=4: L1 모듈 판별 확인 (제안 모듈 N개 괜찮은지)

### 7.3 Stage 2 — Spine

§6.2 시나리오 B Stage 2와 동일.

**핵심 원칙:**
- 전수 탐색 금지 — `git log` 기반 Top-K 파일만 대상
- 각 stub의 `sync_watch` 라인 범위만 소스 읽기
- 불변량 I3/I4 post-check 필수

### 7.4 Stage 3 — History + TEMS 크로스 체크 (D-3)

§6.2 시나리오 B Stage 3와 동일.

**핵심 원칙:**
- **Haiku 서브콜로 diff 요약** (B1) — 메인 컨텍스트 보호
- **Jaccard ≥ 0.5 AND 공통 키워드 ≥ 2개** (B2) — false positive 방지
- **TEMS 단일 진실원** — 기존 TGL 매칭 시 역링크만, 중복 텍스트 금지

### 7.5 Stage 4+ — Lazy Expansion

이후 작업 중 OVERFLOW 감지 또는 새 기능 접촉 시 위상 연산으로 자라남.

**Trigger 흐름 (자동 vs 수동 분리):**
1. **OVERFLOW 감지는 자동** — PostToolUse 훅이 I5 플래그만 걸고 **리마인더 주입**. 분할 자체는 실행하지 않음.
2. **분할 모드 결정은 에이전트** — 해당 L 파일을 읽고 vertical vs horizontal 휴리스틱 적용.
3. **분할 실행은 수동 명령** — 에이전트가 `atlas split <file> --mode vertical|horizontal` 호출. 자동 실행 금지 (F2 위험 — 오탐지 시 잘못된 구조 고착).
4. **분할 후 불변량 재검증 자동** — split 명령이 내부에서 `check_invariants()` 실행. 실패 시 롤백.

사용자가 "지금 stub인 X도 본문 채워줘" 요청 시에만 능동 expansion.

---

## 8. 동기화 — sync_watch + 3중 방어

### 8.1 sync_watch 메커니즘

각 L_k present 파일의 frontmatter에 **이 문서가 감시할 소스 변경 범위**를 선언:

```yaml
sync_watch:
  - path: gallery.html
    range: [1680, 1944]        # 특정 라인 범위 (선택, 없으면 파일 전체)
# 리얼군 스타일 예시:
# sync_watch:
#   - type: manual
#     command: "sync OUT_houses"
```

**자기기술적(self-describing):** 매핑이 각 L 파일 frontmatter에 있으므로 훅 코드는 범용. 프로젝트별 매핑 코드 작성 불필요.

**SYNC 엔진 초기화:** 세션 부트 시 모든 L_k 파일의 `sync_watch`를 훑어 `.hdocs/sync_index.json`에 역인덱스 구축. 이후 Edit/Write마다 O(log N) 조회.

### 8.2 3중 방어

| 층 | 시점 | 메커니즘 | 강제력 | 구현 |
|----|------|---------|-------|------|
| 1 | Edit/Write 직후 | PostToolUse 훅이 sync_index 조회 → 리마인더 | 즉시 경고 | post_tool_use_sync.py |
| 2 | 세션 부트 | TEMS TCL 규칙 자동 주입 (atlas 설치 시 등록) | 매 세션 의식 | tems_commit.py |
| 3 | 세션 종료 직전 | shutdown 체크 — drift 있으면 강제 대화 게이트 | 최후 방어 | session_end_check.py |

### 8.3 drift clear 3-옵션 (C2)

훅 리마인더는 다음 3가지 중 **정확히 1가지**로만 clear 가능:

1. **본문 수정** — L_k present 파일의 해당 섹션 업데이트
2. **히스토리 추가** — L_k.history.md에 append (+`last_synced_commit` 업데이트)
3. **no-op 명시** — 주석/포맷팅/리팩토링만인 경우 명시적 `docs: no-op` 응답

이 규칙이 없으면 drift = open loop가 된다.

### 8.4 shutdown 체크 — 강제 대화 게이트 (F1 핵심)

포폴군 8.1 실패 모드 "훅 피로도"를 정면 대응. session_end_check.py는 단순 리마인더가 아니라 **명시적 응답 요구 게이트**:

```
[세션 종료 직전]
1. check_invariants() 전수 실행
2. drift 상태 스캔 (STALE 플래그 있는 L 파일 목록)
3. drift가 있으면:
   "세션 종료 직전 drift 감지 N건. 다음 선택:
    (a) 지금 업데이트
    (b) 전체 'docs: no-op' 명시
    (c) 다음 세션 이월 (TEMS에 경고 엔트리 기록)"
4. 사용자 응답 대기. 응답 없으면 세션 종료 보류.
```

---

## 9. TEMS 승격 프로토콜

### 9.1 승격 트리거 — 3가지 Rule

**Rule 1: Local pattern repetition**
- 동일 L-history 파일에 유사 교훈이 ≥3회 누적
- 유사 조건: Jaccard(keywords_for_promotion) ≥ 0.5 AND 공통 키워드 ≥ 2개
- → 승격 후보

**Rule 2: Cross-functional invariant**
- 서로 다른 L-history 파일에 유사 교훈이 ≥2회 누적
- → 승격 후보 (더 강한 신호)

**Rule 3: Agent intuition**
- L-history 엔트리 작성 시 `promote_candidate: true` 플래그
- → 승격 후보 (주관적)

### 9.2 승격 실행 — 자동 탐지 + 수동 승인 (Y)

```
[세션 종료 직전, PROMOTE 엔진]

1. atlas_promote_check.py 실행
   ├─ 모든 L-history 파일 스캔
   ├─ keywords_for_promotion 집계
   ├─ Rule 1/2/3 각각 탐지
   └─ 후보 목록 생성

2. 각 후보에 대해 TEMS DB 사전 조회
   ├─ BM25 검색으로 유사 TGL 탐색
   ├─ 이미 매칭 TGL 있으면:
   │   → 해당 L-history 엔트리에 tgl_ref 자동 추가
   │   → 후보에서 제거 (이미 있는 규칙은 재등록 X)
   └─ 매칭 없으면:
       → 사용자 승인 단계로 유지

3. 사용자에게 후보 제시
   "[승격 후보 M건]
    #1 crop-editor.history × 3 — 좌표 단일 진실원
        제안 TGL: '크롭/좌표 변환 시 원본 픽셀 단일 진실원 유지'
        triggers: crop coordinate 좌표 transform
        ... "

4. 각 후보에 대해 사용자 선택:
   (a) 승인 → tems_commit.py --type TGL --rule ... 실행
   (b) 수정 → 규칙 문구 편집 후 등록
   (c) 거부 → blacklist + 유사도 임계값 자동 0.05 상향 (F3 대응)

5. 등록된 TGL에 대해:
   ├─ 관련 L-history 엔트리에 tgl_ref 역링크 추가 (append-only)
   └─ .hdocs/manifest.json에 승격 기록
```

### 9.3 단일 진실원 원칙 (TCL#75 존중)

- **TGL = 권위** (1줄 금지 규칙 + triggers, TEMS DB가 source of truth)
- **L-history = 맥락** (왜 그 규칙이 생겼는가의 서사)
- **중복 저장 금지** — L-history는 `tgl_ref` 링크만 유지, 규칙 문구 자체를 복제하지 않음

TCL#75의 "DB가 source of truth, qmd_rules/*.md는 단방향 출력물" 원칙과 정합.

---

## 10. 실패 모드 & 회복

| ID | 실패 모드 | 원인 | 탐지 | 회복 |
|----|---------|-----|-----|-----|
| F1 | Drift 누적 | 훅 리마인더 반복 무시 | check_invariants에서 N회 stale | shutdown 체크 강제 대화 게이트 (§8.4) |
| F2 | 분할 오탐지 (vertical↔horizontal) | 휴리스틱 실패 | I3 post-check | `atlas collapse` 역연산 |
| F3 | 승격 false positive | 임계값 부적절 | 사용자 거부 기록 | blacklist + 자동 0.05 상향 |
| F4 | Drill-down 확장 폭주 | 예산 미준수 | drill_files 초과 감지 | 강제 중단 + 현재 working set 유지 |
| F5 | manifest.json 오염 | 동시 세션 쓰기 | 로드 시 schema 검증 | `atlas rebuild-cache` (모든 .md frontmatter에서 재구축) |
| F6 | 앵커 프리셋 부적합 | 하이브리드 프로젝트 | scaffold 후 I4 이상 | `config.yaml`에서 `anchor_strategy: manual` + L1 재구성 |
| F7 | TEMS 역링크 dangling | TGL 삭제/rename | 세션 부트 시 L-history 스캔 | 역링크 "(삭제됨)" 마킹, append-only 유지 |
| F8 | history 파일이 present 없이 존재 | 파일 수동 삭제 | I8 위반 | 치명 — 사용자 개입 요구 |

---

## 11. 구현 범위 경계

### 11.1 In-Scope (이번 spec에서 정의)

- ✅ §1~§10 전체 설계
- ✅ Frontmatter 스키마 (present, history, L0 skeleton_index)
- ✅ 위상 불변량 I1~I8 정의 + 검증 시점
- ✅ 3개 엔진 (SETUP/SYNC/PROMOTE) + NAV 프로토콜
- ✅ 3개 시나리오 기반 런타임 플로우 (A/B/C)
- ✅ 3-Stage 백필 전략 + D-3 TEMS 크로스 체크
- ✅ sync_watch + 3중 방어 + drift clear 3-옵션
- ✅ TEMS 승격 Rule 1/2/3 + 단일 진실원 원칙
- ✅ 실패 모드 F1~F8 + 회복 절차
- ✅ anchor_strategy 프리셋 3종 최소 (spa / backend-api / pipeline)

### 11.2 Out-of-Scope (다음 phase 또는 별건)

- ❌ 실제 Python 스크립트 작성 (→ writing-plans 단계)
- ❌ 훅 템플릿 실제 파일 작성 (→ writing-plans 단계)
- ❌ 포폴군/리얼군 회귀 테스트 실행 (→ 구현 완료 후 별 세션)
- ❌ 추가 anchor_strategy 프리셋 (game/lib/monorepo 등)은 v1.1 이후
- ❌ atlas git 레포 구축 (구현 완료 후 — 종일군이 레포 제공 예정)
- ❌ TEMS 독립 스킬 분화 (별건, 별도 기획)
- ❌ atlas 자체 CHANGELOG / 버저닝 정책 상세 (v1.0 고정)
- ❌ 멀티 프로젝트 간 atlas 상호 참조 (단일 프로젝트만)
- ❌ 파일 시스템 watcher (Edit/Write 도구 경유만)
- ❌ 자동 코드 리뷰 / API 레퍼런스 생성

---

## 12. 테스트/검증 계획

### 12.1 정의만 (실행은 구현 후 별 세션)

1. **포폴군 회귀 테스트**
   - 포폴군의 기존 L0~L3 구조를 atlas로 "재구축" 시 같은 결과 확인
   - 특히 skeleton_index 자동 생성, sync_watch 라인 범위, L-history 매핑 정합성

2. **리얼군 회귀 테스트**
   - 리얼군 `docs/houdini-graph/` 구조를 atlas로 표현 가능성 확인
   - 앵커 전략: manual, sync_watch: manual 모드
   - 2단계 청킹(L1 skeleton + L2 segments)이 atlas의 동적 L_k에 매핑되는지

3. **시나리오 C dogfood**
   - 포폴군에서 발생했던 `c_limit` 회귀를 재현
   - atlas가 올바른 경고와 drift 리마인더를 주는지 확인

4. **토큰 벤치마크**
   - 같은 작업을 (a) atlas 없음, (b) 포폴군 기존 방식, (c) atlas로 3회 비교
   - 메인 컨텍스트 사용량 측정
   - 목표: atlas가 (a) 대비 60% 이상 절감, (b) 대비 10% 이상 절감

### 12.2 자동화된 테스트

없음. 휴먼 루프 검증만. atlas 자체가 "에이전트의 컨텍스트 보호"가 목적이므로 자동 테스트 가치가 낮고, 실사용 시나리오 기반 검증이 핵심.

---

## 13. 참고 자료

### 13.1 레퍼런스 구현
- `E:/KJI_Portfolio/docs/architecture/` — 포폴군 L0~L3 고정 계층
- `E:/KJI_Portfolio/docs/superpowers/specs/2026-04-11-portfolio-docs-hierarchy-design.md` — 포폴군 설계 원문
- `E:/01_houdiniAgent/docs/superpowers/specs/2026-04-08-houdini-graph-knowledge-design.md` — 리얼군 그래프 지식 시스템 원문

### 13.2 관련 TEMS 규칙
- TCL#24 — 프로젝트 규모 확장 시 컨텍스트 분할/스코핑/점진적 로딩 파이프라인 필요
- TCL#75 — TEMS DB가 source of truth, md는 단방향 출력물 원칙
- TCL#64 — brainstorming→spec→plan과 구현은 반드시 다른 세션에서 진행
- TGL#63 — 모호한 동의는 텍스트 명세 대신 end-to-end 시나리오로 재검증

### 13.3 예상 후속 산출물
- `docs/superpowers/plans/2026-04-11-atlas-implementation.md` (writing-plans 스킬로 작성)
- `E:/AgentInterface/skills/atlas/**` (공간 A 실제 구현)
- atlas git 레포 (구현 완료 후 종일군이 제공)

---

**승인 상태:** 설계 초안 작성 완료 (2026-04-11, 위상군)
**다음 단계:** 사용자 검토 → 수정 반영 → `writing-plans` 스킬로 전환하여 구현 계획 작성
