# TEMS — Topological Evolving Memory System

> LLM 에이전트의 행동을 규칙으로 구조화하여 반복 실수를 자동 차단·교정하는 자기진화 메모리 시스템.

---

## TL;DR

TEMS 는 다음 세 가지를 한꺼번에 해결하는 경량 SQLite 기반 프레임워크다.

1. **행동 규칙을 영속화** — 사용자 지시와 누적 실수를 구조화된 규칙(TCL/TGL)으로 DB 에 저장
2. **매 대화마다 관련 규칙을 자동 주입** — `UserPromptSubmit` hook 에서 BM25 + dense semantic 매칭으로 현재 맥락에 맞는 규칙만 LLM 컨텍스트에 삽입
3. **준수/위반을 자동 측정하고 진화** — `PostToolUse` 에서 위반을 감지해 카운팅, 반복 위반 규칙은 hook 레벨로 승격 또는 archive

CLAUDE.md / system prompt 에 자연어 지시를 쌓아올리는 방식과 다르게, TEMS 는 **규칙을 데이터로 취급**하여 검색·카운팅·decay 가 가능하다.

---

## 왜 필요한가

CLAUDE.md 같은 정적 지시 파일의 한계:

| 문제 | 정적 지시 | TEMS |
|------|----------|------|
| 컨텍스트 희석 | 모든 지시가 매 turn 주입 → 길어지면 무시됨 | 관련 규칙만 score ≥ 0.55 강매칭 시 주입 |
| 효용도 측정 불가 | 어느 지시가 실효인지 알 수 없음 | `fire_count` / `compliance_count` / `violation_count` 자동 누적 |
| 누적 실수 학습 불가 | 같은 실수를 세션마다 반복 | `pattern_detector` 로 N≥5회 반복 패턴 자동 TGL 등록 |
| 강제력 없음 | LLM 순응에만 의존 | TGL-T 는 `PreToolUse` 에서 도구 호출 자체를 harness 차단 |
| 검색 불가 | 키워드로 찾을 수 없음 | FTS5 BM25 + CUDA dense hybrid retrieval |

---

## 핵심 개념

### TCL vs TGL

규칙은 일반화 수준에 따라 두 타입으로 분리된다. 혼용 등록 금지.

| 축 | **TCL** (Topological Checklist Loop) | **TGL** (Topological Guard Loop) |
|----|--------------------------------------|----------------------------------|
| 본질 | 명시적 사용자 지시 · 국지적 규약 | 누적 실수에서 추출한 카테고리 가드 |
| 트리거 | "앞으로/이제부터/항상/반드시" 명시 | 동일 시그니처 N≥5회 자동 감지 또는 명시 지시 |
| 일반화 | L1 Concrete Pattern | L2 Topological Case (sweet spot 강제) |
| 매칭 | BM25 키워드(1차) | dense semantic(1차) + BM25(보강) |
| 예시 | "세션 종료 시 핸드오버 작성"(#4) | "외부 패키지는 `pip show` 로 존재 검증 후 import"(#92) |

**L2 Topological Case** 가 왜 sweet spot 인가 — L0 는 1회성이라 재사용 불가, L1 은 여전히 구체적, L3 이상은 도메인 초월이라 과잉 적용. L2 는 "여러 도메인에 걸쳐 같은 구조의 실수가 재발하는 경우" 를 잡는 추상화 수준.

### TGL 7-카테고리

TGL 은 **발동 Hook 시점** 기준으로 7개 카테고리로 분류된다. 같은 카테고리끼리 semantic 유사도가 높아 dense retrieval 효율이 올라간다.

| 코드 | 본질 | 발동 시점 | 핵심 질문 |
|------|------|-----------|----------|
| **TGL-T** | Tool Action — 도구 호출 자체가 위험 | PreToolUse | 이 도구를 호출하면 안 되는가? |
| **TGL-S** | System State — 사전조건 깨짐 | SessionStart | 시스템이 전제조건을 만족하는가? |
| **TGL-D** | Dependency — 외부 의존성 부재/변경 | runtime exception | 이 패키지가 실제 존재하는가? |
| **TGL-P** | Pattern Reuse — 코드 패턴 반복 버그 | 코드 작성 | 이 패턴을 전에 잘못 쓴 적 있는가? |
| **TGL-W** | Workflow — 작업 흐름/순서 위반 | 단계 전환 | 이 단계를 건너뛰면 무슨 오류가? |
| **TGL-C** | Communication — 정보 전달 결함 | 위임/보고 | 올바른 에이전트에게 전달되는가? |
| **TGL-M** | Meta-system — TEMS/hook 자체 변경 | 시스템 변경 | TEMS 자체를 건드리는가? |

---

## 아키텍처 개요

```
사용자 프롬프트
      │
      ▼
┌─────────────────────┐
│ UserPromptSubmit    │  preflight_hook.py
│ ─ BM25 검색         │  → <preflight-memory-check>
│ ─ dense fallback    │    TGL/TCL 규칙 주입
│ ─ score ≥ 0.55 gate │    + violation_count 노출
└──────────┬──────────┘
           │
           ▼
    LLM (Claude)
           │
           ▼
┌─────────────────────┐
│ PreToolUse          │  tool_gate_hook.py
│ ─ TGL-T tool_pattern│  → severity=critical 매칭 시
│   regex 매칭        │    deny JSON 반환 (hard block)
│ ─ self-invocation   │    → severity=warning 은 경고만
│   제외              │
└──────────┬──────────┘
           │ (deny 아니면 통과)
           ▼
     도구 실행
           │
           ▼
┌─────────────────────┐
│ PostToolUse         │  compliance_tracker.py
│ ─ forbidden/        │  → window 내 위반 없으면 compliance++
│   failure_signature │  → 위반 감지 시 violation++
│   매칭              │  → window 만료 후 guard 제거
│ ─ TTL 만료 guard    │
│   청소              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stop (session end)  │  retrospective_hook.py
│ ─ 세션 교훈 추출    │  → 자동 학습, 핸드오버 작성
└─────────────────────┘
```

### 저장소 구조

```
memory/
├── error_logs.db              SQLite 본체 (git tracked 금지 — TGL #74)
├── qmd_rules/                 규칙 정규 소스 (tems_commit.py 자동 생성 md)
│                              → DB 손상 시 rebuild_from_qmd.py 로 복원
├── active_guards.json         현재 활성 guard (compliance window 추적)
├── compliance_events.jsonl    위반/준수 이벤트 로그 (append-only)
├── tems_diagnostics.jsonl     hook 실패 진단 로그
├── sdc_briefs.jsonl           SDC 계약 제출 로그
├── preflight_hook.py          UserPromptSubmit — 규칙 주입
├── tool_gate_hook.py          PreToolUse — TGL-T 도구 차단
├── compliance_tracker.py      PostToolUse — 위반/준수 측정
├── tool_failure_hook.py       PostToolUse Bash — 실패 시그니처 탐지
├── retrospective_hook.py      Stop — 세션 종료 교훈 추출
├── pattern_detector.py        반복 패턴 자동 TGL 등록
├── memory_bridge.py           PostToolUse Write|Edit — 파일 변경 학습
├── tems_engine.py             HybridRetriever, RuleGraph, PredictiveTGL
├── fts5_memory.py             MemoryDB (BM25 전문검색)
├── tems_commit.py             규칙 등록 CLI (분류·게이트 자동)
├── sdc_commit.py              SDC 3-question gate brief 제출 CLI
└── decay.py                   cold 전환 / archive 후보 처리 (cron)
```

### DB 스키마 (핵심 테이블)

| 테이블 | 용도 |
|--------|------|
| `memory_logs` | 규칙 본문 (category, correction_rule, context_tags, severity) |
| `memory_fts` | FTS5 전문검색 가상 테이블 |
| `rule_health` | `ths_score`, `fire_count`, `compliance_count`, `violation_count`, `status` (hot/warm/cold/archive) |
| `exceptions` | 예외 케이스 (승격 이력, persistence_score) |
| `meta_rules` | 메타 규칙 조절 이력 (가중치 변경 근거) |

상세는 [.claude/references/tems-architecture.md](../.claude/references/tems-architecture.md).

---

## 런타임 라이프사이클 (실제 예시)

### Step 1 — 프롬프트 도착

```
사용자: "useEffect deps 에 currentPrice 넣어서 interval 재생성 문제 있는데"
```

### Step 2 — preflight 키워드 추출 + BM25 검색

```python
keywords = ["useEffect", "deps", "currentPrice", "interval", "재생성"]
fts_query = '"useEffect"* OR "deps"* OR "currentPrice"* OR ...'
→ TGL #54 매칭 (final_score=0.73, THRESHOLD=0.55)
```

### Step 3 — 컨텍스트 주입

```
<preflight-memory-check>
[TGL] 필수 준수 — 위반 시 rule_health.violation_count 자동 증가
  #54 (v:0 c:11): useEffect deps 에 매 틱 변하는 값(currentPrice 등)을
    넣으면 interval/timer 가 매번 재생성되어 모션 재생이 끊긴다.
    useRef 로 최신값을 래핑하고 deps 에서 제외하여 stale closure 를 방지할 것.
→ 위 TGL 중 해당되는 규칙을 응답에 명시하세요.
  예: "TGL #54 에 따라 X 대신 Y 사용". 주입된 TGL: #54
</preflight-memory-check>
```

`(v:0 c:11)` = 이 규칙은 지금까지 위반 0회, 준수 11회 — LLM 은 "잘 지켜지는 규칙" 으로 인지. 반대로 `(v:14 c:1)` 이면 반복 위반 경고 신호.

### Step 4 — LLM 응답

```
TGL #54 에 따라 currentPrice 를 useRef 로 래핑하고 deps 에서 제외...
```

### Step 5 — 도구 호출 (Edit)

`PreToolUse` → `tool_gate_hook` 가 TGL-T tool_pattern 검사. 매칭 없으면 통과.

### Step 6 — 도구 완료 후

`PostToolUse` → `compliance_tracker` 가 `active_guards.json` 의 #54 guard 를 검사. `forbidden`/`failure_signature` 미매칭, window 만료 시 `compliance_count++`.

---

## 강제력 계층 (Enforcement Layers)

TEMS 는 규칙 강제력을 4층으로 분리해 적용한다. 강할수록 구현·유지보수 비용이 크므로 필요에 따라 승격한다.

| Layer | 수단 | 강제력 | 구현 위치 | 적용 대상 |
|-------|------|--------|-----------|----------|
| **L1** | 자연어 주입 강화 + violation_count 노출 | 소프트 (LLM 순응 의존) | `preflight_hook.py` `format_rules` | 모든 TGL |
| **L2** | PreToolUse `permissionDecision: "deny"` JSON | 하드 (harness 가 도구 호출 차단) | `tool_gate_hook.py` | TGL-T `tool_pattern` + `severity=critical` |
| **L3** | PostToolUse compliance 측정 + violation_count 누적 | 사후 적발 + 데이터화 | `compliance_tracker.py` | 모든 TGL (`forbidden`/`failure_signature` 슬롯 보유) |
| **L4** | DVC case 승격 (결정론적 빌드 검증) | CI/cron 차단 | `src/checklist/cases.json` (DVC 별도 시스템) | 빌드 산출물 기반 체크 가능한 규칙 |

**설계 원칙:**
- 자연어 주입은 근본적으로 소프트 — 컨텍스트 길어지면 희석됨.
- 정규식/패턴 매칭 가능한 TGL-T → L2 하드 차단 승격.
- 사후 적발로 충분한 규칙 → L3 (violation_count 누적으로 반복 위반 자동 식별).
- 빌드 산출물로 검증 가능 → L4 (런타임 비용 0, CI 에서만 실행).

**Layer 2 deny JSON 스펙:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "TGL #N (TGL-T) — 도구 호출 차단\n패턴: ...\n..."
  }
}
```
이 JSON 을 hook 이 stdout 으로 출력하면 Claude Code harness 가 도구 호출 자체를 취소한다 (stdout 텍스트 경고보다 훨씬 강함).

---

## 조용한 TEMS (Quiet TEMS) 정책

매 prompt 무차별 주입은 "banner blindness" 를 일으켜 모든 규칙이 무시된다. TEMS 는 다음 임계값 gate 를 적용한다.

```python
SCORE_THRESHOLD = 0.55   # final_score < 이 값이면 주입 안 함
MAX_TCL = 2              # TCL 최대 주입 수
MAX_TGL = 2              # TGL 최대 주입 수
MAX_CASCADE = 1          # 이웃 규칙 최대
MAX_PREDICT = 1          # 예측 최대

final_score = 0.6 * BM25_rank_score + 0.4 * THS_score
```

- `BM25_rank_score = 1 / (1 + rank)` — 키워드 매칭 순위
- `THS_score` — 규칙 효용도 (0~1, `rule_health.ths_score`)
- 강매칭 (키워드 1위 + THS 0.5 이상) ≈ 0.8, 약매칭 = 주입 차단

결과: 매 turn 평균 2~4개 규칙만 주입, 무관한 규칙은 침묵.

---

## 규칙 진화 (Self-Evolution)

### Trigger Counting

preflight 주입 시 `fire_count++` 자동 갱신. 매칭만이 아니라 **실제 주입된** 규칙만 카운트.

### Health States

| 상태 | 조건 | 효과 |
|------|------|------|
| `hot` | 최근 빈번히 발동 | 주입 우선순위 상승 |
| `warm` | 정상 | 기본 |
| `cold` | 30일 0회 발동 | 자동 전환, 주입 감점 |
| `archive` | 90일 0회 | 주입 대상에서 제외 |

`python memory/decay.py` 를 cron 으로 돌려 상태 전환 (기본 미활성).

### Pattern Detection (자동 TGL 등록)

`pattern_detector.py` 는 `compliance_events.jsonl` 과 실패 로그를 스캔하여 N≥5회 반복된 동일 시그니처를 자동 TGL 로 등록. `needs_review=1` 태그 부여 → 나중에 수동 재분류 필요.

활성화 조건: `TEMS 자동등록 활성화` TCL 이 등록되어 있어야 함.

---

## 규칙 등록 (Rule Registration)

### TCL 등록

```bash
python memory/tems_commit.py --type TCL \
  --rule "세션 종료 트리거(퇴근|종료|마무리) 감지 시 핸드오버 문서 작성" \
  --triggers "퇴근,종료,마무리,끝,핸드오버,session-end" \
  --tags "project:wesang,domain:lifecycle"
```

- `--triggers` 는 BM25 매칭을 위한 동의어 (5개 이상 권장)
- 게이트 A (스키마) + 키워드 다양성 검사 통과 시 DB 적재

### TGL 등록

```bash
python memory/tems_commit.py --type TGL \
  --classification TGL-D \
  --topological_case "외부 패키지 import 전 실제 설치 여부 미검증 → ModuleNotFoundError" \
  --forbidden "pip show 없이 import 시도" \
  --required "pip show {package} + python -c 'import {package}' 선행 확인" \
  --failure_signatures "ModuleNotFoundError,ImportError: No module named" \
  --tags "project:all,domain:dependency"
```

- `--classification` 필수 (TGL-T/S/D/P/W/C/M 중 1)
- 카테고리별 추가 슬롯 (`tool_patterns` for TGL-T 등) 필수
- 게이트 A + B (거부형) + C/D/E (경고형) 통과 시 적재

### 게이트 요약

| 게이트 | 대상 | 내용 | 형태 |
|--------|------|------|------|
| A | TCL/TGL | 스키마 완성도 | 거부 |
| B | TGL | L0/L4 추상화 수준 거부 | 거부 |
| C | TGL | 중복 탐지 | 경고 |
| D | TGL | 재현성 검증 | 경고 |
| E | TGL | 검증 가능성 | 경고 |
| 키워드 다양성 | TCL | triggers 80% 이상 커버 | 거부 |

---

## 타 에이전트 배포 (Deployment)

TEMS 는 **self-contained** 로 설계되어 외부 패키지 의존 없이 복사만으로 이식 가능하다.

### 최소 이식 (Phase 0 — Self-contained 원복)

```bash
# 1. memory/ 디렉토리 전체 복사 (error_logs.db 제외)
rsync -av --exclude='error_logs.db*' --exclude='__pycache__' \
  source_agent/memory/ target_agent/memory/

# 2. DB 스키마 초기화
cd target_agent
python -c "from memory.fts5_memory import MemoryDB; MemoryDB()"

# 3. settings.local.json hook 등록 (Claude Code 기준)
# .claude/settings.local.json 에 아래 hook 추가:
{
  "hooks": {
    "UserPromptSubmit": [
      {"matcher": "", "hooks": [{"type": "command", "command": "python memory/preflight_hook.py"}]}
    ],
    "PreToolUse": [
      {"matcher": "", "hooks": [{"type": "command", "command": "python memory/tool_gate_hook.py"}]}
    ],
    "PostToolUse": [
      {"matcher": "", "hooks": [{"type": "command", "command": "python memory/compliance_tracker.py"}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python memory/tool_failure_hook.py"}]}
    ]
  }
}

# 4. 초기 규칙 씨앗
python memory/tems_commit.py --type TCL --rule "..." --triggers "..." --tags "project:myagent"
```

### Wave 1 표준 이식 (Phase 0-2)

검증된 Phase 2 까지 포함한 표준 이식. 현재 코드군·리얼군·디니군 적용.
- self-contained + hybrid retrieval + 게이트 A~E + 분류 체계

### Wave 2 표준 이식 (Phase 0-3) — 계획 중

Phase 3 (Enforcement) 포함.
- `tool_gate_hook.py` (L2 deny path)
- `compliance_tracker.py` (L3 violation 측정)
- `decay.py` (health 진화)

### 이식 시 주의

- `memory/error_logs.db` 는 **git tracked 금지** (TGL #74) — WAL/journal/shm 포함. 바이너리 런타임 상태로 매 세션 dirty, 머지 불가.
- 정규 소스는 `memory/qmd_rules/*.md` (tems_commit 자동 생성) — 이것만 tracked.
- DB 복원: `E:/AgentInterface/tems_core/rebuild_from_qmd.py` (외부 도구, 별도 설치).

---

## 관련 시스템과의 분리

TEMS 는 다른 레이어와 명확히 구분된다. 혼동 금지.

| 시스템 | 목적 | 식별자 | 위치 | 계층 |
|--------|------|--------|------|------|
| **TEMS** | LLM 행동 교정 | `#N` 정수 | `memory/error_logs.db` | 런타임 (매 prompt) |
| **DVC** | 결정론적 빌드 검증 | `DOMAIN_VERB_NNN` | `src/checklist/cases.json` | CI/cron (빌드 시) |
| **SDC** | 서브에이전트 위임 계약 | Q1/Q2/Q3 gate | `memory/sdc_briefs.jsonl` | 세션 내 결정 |
| **TWK** | 위키 L3 큐레이션 | 개념 페이지 | `docs/wiki/**` | 지식 베이스 |

---

## 자기 관찰 (Diagnostics)

실패는 조용히 먹지 않는다 (Phase 0 T1.1 원칙):

- hook 전반 예외: `memory/tems_diagnostics.jsonl` 구조화 로그
- preflight 실패 시: `<preflight-degraded reason="..."/>` 컨텍스트 주입 (silent fail 금지)
- 모든 hook 은 **절대 blocking 되지 않음** — 진단 로그 남기고 exit 0

### 건강 확인 쿼리

```bash
# 가장 자주 위반되는 규칙
sqlite3 memory/error_logs.db "
  SELECT m.id, rh.violation_count, substr(m.correction_rule, 1, 60)
  FROM memory_logs m JOIN rule_health rh ON rh.rule_id = m.id
  ORDER BY rh.violation_count DESC LIMIT 10
"

# 발동 없는 cold 후보
sqlite3 memory/error_logs.db "
  SELECT m.id, m.category, rh.last_fired
  FROM memory_logs m JOIN rule_health rh ON rh.rule_id = m.id
  WHERE rh.status = 'cold' OR rh.fire_count = 0
"

# 최근 위반/준수 이벤트
tail -20 memory/compliance_events.jsonl | jq .
```

---

## 한계와 진행 중 과제

| 한계 | 현재 상태 | 대응 |
|------|----------|------|
| L1 자연어 주입은 여전히 LLM 순응 의존 | Layer 1 강화 (violation_count 노출, 2026-04-22) | L2 승격 가능한 규칙 식별 후 이관 |
| TGL-T 외 카테고리는 hook 레벨 강제 미구현 | TGL-S/W/M 은 PreToolUse 로 일부 확장 가능 | Phase 4 계획 단계 |
| `pattern_detector` 자동 등록은 품질 편차 | `needs_review=1` 태그로 수동 검토 | 주기적 재분류 필요 |
| Windows 경로 정규화 일부 예외 | build_match_target 에서 `\` → `/` 변환 | 추가 케이스 발견 시 패치 |
| DB 복원 도구가 외부 경로 의존 | `E:/AgentInterface/tems_core/rebuild_from_qmd.py` | 향후 `memory/` 내부로 자체 포함 예정 |

---

## Phase 개발 이력

| Phase | 세션 | 내용 |
|-------|------|------|
| 0 | S31 | Self-contained 원복 + 자기관찰 (BM25 preflight) |
| 0.5/0.6 | S31 | 조용한 TEMS (score gate) + dense 복원 |
| 1 | S31 | 자가진화 (pattern_detector, 자동 TGL 등록) |
| 2 | S31 | 게이트 검증 (A~E 게이트, 분류 체계) |
| 3 | S32 | Enforcement (tool_gate_hook + compliance_tracker + decay) |
| Migration | S33 | 31개 레거시 TGL 자동 분류 (7-카테고리) |
| SDC Gate | S36 | git 쓰기 명령 3-question gate 도입 |
| SDC 선택화 | S38 | 자동 발동 deprecated, 태그 기반 선택적 발동 |
| L1 강화 | S42 (2026-04-22) | violation_count 노출 + 필수 준수 헤더 |

---

## 참조

- [.claude/rules/tems-protocol.md](../.claude/rules/tems-protocol.md) — 위상군 운영 규약
- [.claude/references/tems-architecture.md](../.claude/references/tems-architecture.md) — 아키텍처 상세
- [docs/wiki/concepts/TEMS.md](../docs/wiki/concepts/TEMS.md) — 개념 페이지
- [docs/wiki/concepts/TCL_vs_TGL.md](../docs/wiki/concepts/TCL_vs_TGL.md) — TCL/TGL 분류 기준
- [docs/wiki/patterns/Classification_7_Category.md](../docs/wiki/patterns/Classification_7_Category.md) — 7-카테고리 상세
- [docs/wiki/concepts/DVC_vs_TEMS.md](../docs/wiki/concepts/DVC_vs_TEMS.md) — DVC 와의 분리 기준
- [docs/wiki/concepts/SDC.md](../docs/wiki/concepts/SDC.md) — 서브에이전트 위임 계약

---

## 라이선스

저장소 루트의 라이선스를 따른다. TEMS 자체는 Triad Chord Studio 위상군이 S29~S42 세션 중 경험적으로 도출한 구조로, 외부 레퍼런스 없이 자체 개발되었다.
