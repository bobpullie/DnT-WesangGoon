# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-19 Session 32

## TEMS 호출 매뉴얼 (조용한 TEMS 아키텍처)
**기본 정책:** 매 prompt 무차별 주입 금지. 키워드 강매칭(score≥0.55) 시에만 자동 발동.
**등록 (수동 호출):**
```bash
python memory/tems_commit.py --type {TCL|TGL} --rule "..." --triggers "키워드들" --tags "..."
```
**검색 (필요 시):**
```bash
sqlite3 memory/error_logs.db "SELECT id,category,correction_rule FROM memory_logs WHERE keyword_trigger LIKE '%X%' OR correction_rule LIKE '%X%' LIMIT 5"
```
**자동 발동 트리거:**
- 사용자 프롬프트에 TCL 패턴(`이제부터/앞으로/항상/반드시`) → `<rule-detected type="TCL">` 힌트
- 사용자 프롬프트에 TGL 패턴(`하지마/금지/절대/never/don't`) → `<rule-detected type="TGL">` 힌트
- Bash 도구 실패 시그니처 → `<tool-failure-detected>` 알림
- preflight 자체 실패 → `<preflight-degraded>` 알림
- **[Phase 3]** TGL-T 도구 패턴 매칭 (PreToolUse) → `<tgl-tool-alert>` 경고 또는 deny JSON 차단
- **[Phase 3]** active guard 활성 중 이후 도구 호출이 FORBIDDEN 위반 시 → `<compliance-violation>` + violation_count++

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **메타 프로젝트:** Atlas /atlas 명령체계 구현 완료 (7/7 Tasks, 88 tests)
- **TEMS 독립 패키지:** v0.1.0 구현 완료 — 단, **위상군 자체는 self-contained 모드로 원복 (S31)**
- **독립 위상군:** 구축 완료 — bobpullie/wesangAgent (03d6638)
- **ANKR 토큰 효율화:** Phase 1 (디니군 진행 중)

## 이번 세션 성과 (Session 32) — TEMS Phase 3 Enforcement
- **Phase 3A — PreToolUse tool_gate_hook.py 신규:** DB에서 classification=TGL-T + tool_pattern 슬롯 규칙 로드, 도구 호출 payload(tool_name + command/file_path/url 등)에 정규식 매칭. severity=critical → deny JSON 차단, info/warning → `<tgl-tool-alert>` 경고. self-invocation은 Bash가 hook 자체를 실행할 때만 제외 (Edit/Write file_path가 memory/*.py인 경우는 측정 대상).
- **Phase 3B — compliance_tracker.py 신규:** PostToolUse matcher=''. active_guards.json 순회하여 매 도구 호출마다 (1) tool_pattern (2) failure_signature (3) FORBIDDEN 본문 키워드≥3개 매칭 중 하나라도 걸리면 violation_count++ + `<compliance-violation>` 알림. remaining_checks 0 도달 시 위반 이력 없으면 compliance_count++. preflight_hook.record_fire가 TGL 발동 시 active_guards에 push하도록 확장 (remaining_checks=8).
- **Phase 3C — decay.py 신규:** 30일 미발동+warm → cold, 90일 미발동 → archive. effective_last_activity는 last_fired > last_activated > memory_logs.timestamp > status_changed_at 순. `rule_health.created_at`은 백필 시점이라 제외. `--dry-run` / `--json` 지원. Windows Task Scheduler 또는 cron 등록 권장.
- **settings.local.json 배선:** PreToolUse matcher='' → tool_gate_hook, PostToolUse matcher='' → compliance_tracker 추가.
- **TGL #102 등록 (Phase 3 시범 TGL-T):** "TEMS 자기 수정 시 백업 없이 hook 편집 금지" — tool_pattern으로 memory/*_hook.py 편집 감지. E2E 검증 완료: preflight 발동 → active_guards push → violation 감지 → 깨끗한 window 만료 시 compliance 증가까지 전체 사이클 작동.
- **TCL #103, #104 등록:** Phase 3 구현 기록 + decay.py cron 운영 정책.
- **검증 완료:** `python memory/decay.py --dry-run` 정상 (현재 규칙 모두 27일 이내라 0 transitions, 이는 정상). hook 3종 empty/minimal stdin smoke test 통과. 시뮬레이션: fire=2, violation=1, compliance=1 정상 집계.
- **독립 code-reviewer agent audit 수행:** Ship-with-fixes 판정. P0 1건 + P1 3건 + P2 3건 발견.
- **audit P0/P1 4건 즉시 패치 완료 (종일군 지시):**
  - **P0**: compliance_tracker `check_violation` FORBIDDEN 키워드 휴리스틱을 fallback 전용으로 격하. 조건: `tool_pattern` + `failure_signature` 둘 다 없음 + `MUTATING_TOOLS`(Edit/Write/Bash/NotebookEdit)일 때만 동작. distinct 토큰 dedup + `FORBIDDEN_NOISE_TOKENS`에 memory/hook/preflight/compliance/tool 등 인프라 명사 추가. → Read/Glob/Grep으로 memory 파일 조회 시 false-positive 0.
  - **P1-a**: `tool_gate_hook.record_active_guard` rule_id 기준 dedup 추가. 이미 active 시 remaining_checks 리셋 + 슬롯 보충만. 이중 카운팅 제거.
  - **P1-b**: `build_match_target`에서 `\\` → `/` 정규화. Windows 경로가 자동으로 정규식 매칭. TGL-T 작성자는 `/` 한 가지만 고려하면 됨.
  - **P1-c**: scope-aware `remaining_checks` 감소. 관찰형 도구(Read/Glob/Grep/WebFetch/NotebookRead 등)는 guard window를 건드리지 않고 통과. 변형 도구만 window 틱 소비 + compliance 적립 대상. "공짜 compliance++" 제거.
- **스냅샷 보존 (#102 REQUIRED 준수):** `memory/_post_S32_phase3_preP0_patch/`에 패치 직전 4개 파일 저장.
- **#102 오염 카운터 리셋:** audit 과정에서 누적된 violation_count 초기화 후 clean-start. 패치 후 재검증: Read 5회 → remaining_checks 변화 없음, Bash 8회 clean → compliance=1 정상.
- **TCL #105 등록:** P0/P1 패치 기록.
- **누적 규칙:** TCL/TGL #1~#105, archive: #64, #98

## S32 결정 — Phase 3 P2 및 audit 재검증은 S33으로 이월
- P2 3건 (단위 테스트 추가, `update_counts`의 `created_at` 보호 `INSERT OR IGNORE`, `.claude/rules/tems-protocol.md`에 FORBIDDEN 휴리스틱 설명) 미처리.
- S33 세션 첫 태스크: code-reviewer agent 재호출하여 P0/P1 패치가 실제로 감사 지적을 해소했는지 독립 재검증.

## 이전 세션 성과 (Session 31)
- **위상군 자체 TEMS 표준화 원복:** 외부 `tems` 패키지 미배포로 preflight/tems_commit 무력화 → `_backup_tier1/`에서 self-contained 복원
- **복원 파일:** `memory/{fts5_memory,tems_engine,tems_commit,preflight_hook}.py` + `__init__.py` + `backfill_triggers.py` 로컬 import 전환
- **post-S29 표준화 버전 보존:** `memory/_post_S29_standardization/`
- **TGL #92 등록:** 외부 패키지 마이그레이션 시 import 검증 + self-contained 백업 보존 필수
- **TEMS 구조적 결함 진단:** 4개 자동 등록 채널 모두 사각지대 — TGL truncation, 강제 메커니즘 부재, subagent 무관찰, except:pass silent failure
- **개선안 4티어 아키텍처 제안:** 관찰(T1) → 충실도(T2) → 강제(T3) → 메타학습(T4)
- **TCL #93 등록 (종일군 결정):** TEMS 개선은 위상군에서 먼저 검증 → 타 에이전트 전파. 동시 마이그레이션 금지.
- **TCL #64 폐기 (종일군 지시):** "설계와 구현 별도 세션" 규칙 → archive
- **TEMS Phase 0 구현 완료 (자기관찰 + 충실도):**
  - T1.1: `preflight_hook.py` `except:pass` 제거 → `<preflight-degraded>` 출력 + `memory/tems_diagnostics.jsonl` 영속화
  - T1.2: `memory/tool_failure_hook.py` 신규 — Bash PostToolUse에서 11개 실패 시그니처 감지 → `<tool-failure-detected>` 출력 + `memory/tool_failures.jsonl`
  - T2.2: TGL 풀텍스트 주입 (truncation 제거). TCL은 summary 유지.
  - settings.local.json PostToolUse Bash matcher 추가
- **TCL #94 등록:** Phase 0 완료 기록
- **검증 통과:** TGL #92 풀텍스트 주입 확인, ModuleNotFoundError 자동 감지 확인, 잘못된 stdin → degraded 신호 + 진단 로그 확인
- **TEMS Phase 0.5 적용 (조용한 TEMS, 종일군 지시):**
  - SCORE_THRESHOLD=0.55 도입 — 약매칭 자동 차단
  - stopwords 확장: 테스트/확인/진행/시작 등 generic noise 차단
  - CURRENT_STATE.md 상단에 TEMS 호출 매뉴얼 1회 주입 (SessionStart)
  - 토큰 절감 추정: 360 tok/prompt → 100~200 tok/prompt (60~70% 절감)
- **TCL #95 등록:** Phase 0.5 아키텍처 전환 기록
- **종일군 정정 — Phase 0.6 (Dense semantic 부활):**
  - 위상군이 이미 구축한 CUDA QMD dense + HybridRetriever를 잊고 reinvent했음
  - SEMANTIC_FALLBACK_ENABLED=True 복원 + qmd embed 4개 신규 규칙 임베딩
  - 검증: "패키지 디펜던시 사라지면" 같이 trigger 키워드 0개 매칭이어도 의미적으로 #92 정확 발동
- **TGL #96 등록:** "위상군이 이미 구축한 시스템 잊고 reinvent 금지" — self-awareness 가드
- **TEMS Phase 1 (자가진화) 구현 완료:**
  - T1.3 `memory/pattern_detector.py` 신규 — jsonl 스캔, 정규화, 그룹화, 반복 임계 이상 후보 추출, TGL 텍스트 일반화
  - T4.1 `memory/retrospective_hook.py` 신규 — Claude Code Stop event hook, RATE_LIMIT_SEC=600 throttle
  - 모드 토글: `is_auto_register_enabled()` — TCL "자동등록 활성화" 존재 여부로 결정
  - 중복 방지: `is_already_registered_pattern()` — auto-detected 태그 + signature
  - settings.local.json Stop hook 등록
- **TCL #97 등록 (종일군 활성화):** TEMS 자동등록 활성화 — pattern_detector가 count≥5 패턴을 자동 등록
- **TGL #98 자동등록 (Phase 1 첫 자율 산출물):** python_traceback ×7회 반복 패턴 자동 감지·일반화·등록 — TEMS의 'Evolving' 부분 첫 가동
- **TCL #99 등록:** Phase 1 완료 기록
- **TEMS Phase 2 (분류·템플릿·게이트·카운팅) 완료 — Systematizing 단계:**
  - **2A** rule_health 스키마 확장: fire_count, last_fired, compliance_count, violation_count, classification, abstraction_level, needs_review, created_at. preflight_hook이 cap 후 실제 주입 ID만 fire_count++.
  - **2B** TCL/TGL 재정의 (CLAUDE.md, tems-protocol.md): TCL=좁은규칙 BM25, TGL=넓은위상패턴 dense+7카테고리(T/S/D/P/W/C/M)
  - **2C/D/E** tems_commit.py 통합 재작성: 자동 분류 추론, 게이트 A(schema 거부) B(abstraction L0/L4 거부) C(duplication 경고) D(replay 시뮬 경고) E(verifiability 경고). --dry-run, --classification, --abstraction, --topological-case, --forbidden, --required, --semantic-intent, --failure-signature, --tool-pattern, --success-signal, --compliance-check 슬롯
  - **TGL #98 → archive, TGL #100 보강 재등록:** TGL-M/L2 첫 시범 사례 — "관찰 시스템 self-trigger 루프 방지"
  - **TCL #101 등록:** Phase 2 완료
- **누적 규칙:** TCL/TGL #1~#101, archive 처리: #64(설계-구현 분리 폐기), #98(보강 대체)

## 이전 세션 성과 (Session 30)
- 독립 위상군 11/11 Tasks 구축 완료 (E:\WesangGoon, bobpullie/wesangAgent @ 03d6638)
- TEMS 28개 범용 규칙 이식, 스킬 7개, Rules 4개, TGL #91 등록

## 다음 세션 부트 (S33)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (DnT 위상군)
HEAD (DnT-WesangGoon): 4c9b468 (S31+S32 변경분 모두 미커밋)
HEAD (wesangAgent): 03d6638
HEAD (TEMS bobpullie): 변경 없음 (S27 이월 미커밋분 잔존)

위상군 TEMS: self-contained + Enforcement (Phase 3 완료 + P0/P1 패치 완료)
  - memory/ 로컬 모듈 (fts5_memory, tems_engine, tems_commit, preflight_hook, backfill_triggers)
  - 신규 S31: tool_failure_hook.py, pattern_detector.py, retrospective_hook.py
  - 신규 S32: tool_gate_hook.py, compliance_tracker.py, decay.py
  - 상태 파일: active_guards.json (PreToolUse ↔ PostToolUse 간 guard 상태 전달)
  - 로그: tems_diagnostics.jsonl, tool_failures.jsonl, compliance_events.jsonl
  - 스냅샷: _post_S29_standardization/ (S31), _post_S32_phase3_preP0_patch/ (S32)
  - DB: memory/error_logs.db
  - 규칙: #1~#105 (archive: #64, #98)
  - 자동등록 모드: ON (TCL #97 활성)

Hooks 구성:
  - SessionStart (matcher: startup|resume|clear): CURRENT_STATE 자동 주입
  - UserPromptSubmit: preflight_hook (BM25 + CUDA dense, threshold 0.55, TGL 발동 시 active_guards push)
  - PreToolUse (matcher ''): tool_gate_hook (TGL-T tool_pattern 매칭)
  - PostToolUse Write|Edit: changelog + memory_bridge
  - PostToolUse Bash: tool_failure_hook
  - PostToolUse (matcher ''): compliance_tracker (active_guards 순회 + violation/compliance 카운트)
  - Stop: retrospective_hook (rate limit 10분)

QMD 상태:
  - 백엔드: CUDA, embeddinggemma 모델
  - tems-wesanggoon 컬렉션: 72 files indexed (Phase 3 신규 규칙은 embed 재실행 권장)
  - 전체: 4414 vectors, 686 files

상태: 종일군 지시 대기 (S33 Phase 3 운영 관찰 + 보강 또는 다른 에이전트 전파)
```

## S33 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **Phase3-Audit-Reverify** | P0 | S32 말미 P0/P1 패치(FORBIDDEN fallback-only, dedup, path normalize, scope-aware)가 실제로 audit 지적을 해소했는지 code-reviewer agent 재호출하여 독립 재검증 |
| **Phase3-P2-Tests** | P1 | memory/tests/에 test_tool_gate_hook.py, test_compliance_tracker.py, test_decay.py 추가 (S32 audit P2-1) |
| **Phase3-P2-CreatedAt** | P1 | compliance_tracker.update_counts에서 INSERT OR IGNORE + UPDATE로 분리해 created_at 오염 방지 (S32 audit P2-2) |
| **Phase3-P2-ProtocolDoc** | P2 | .claude/rules/tems-protocol.md에 FORBIDDEN 휴리스틱 fallback 조건 + MUTATING_TOOLS 개념 문서화 (S32 audit P2-3) |
| **Phase3-Observation** | P1 | Phase 3 운영 관찰 1~2 세션. false-positive/미발동 기록 후 `compliance_events.jsonl` 분석 |
| **Phase3-Decay-Cron** | P1 | Windows Task Scheduler 등록: 매일 09:00 `python memory/decay.py` 실행 |
| **Phase3-QMD-Embed** | P1 | #102~#105 신규 규칙 qmd embed 실행 (semantic 매칭 풀 확장) |
| **FalsePositive-IgnorePatterns** | P1 | tool_failure_hook의 IGNORE_PATTERNS에 jsonl cat, hook.py 실행, 테스트 echo 추가 |
| **Migration-Classification** | P1 | 기존 규칙의 classification/abstraction 자동 채우기 (현재 65+개 분류 NULL) |
| **NeedsReview-Notify** | P1 | retrospective_hook이 needs_review=1 규칙도 함께 알림 |
| **Phase2-Tuning** | P3 | Gate B 휴리스틱 한국어 specific 토큰 인식, preflight 비용 최적화 (QMD daemon 모드) |
| **Other-agents-rollback** | P2 | 디니/기록/빌드 등 self-contained 원복 + Phase 0~3 적용 (TCL #93 정책 준수, 위상군 N세션 가동 후 종일군 승인 시) |

## 대기 태스크 (우선순위)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| **TEMS-패키지커밋** | 위상군 | bobpullie/TEMS tems_commit.py 업데이트분 커밋 | **P0** |
| **Atlas-피드백** | 종일군 | 기록군 L2 키워드 보강 후 hint 품질 재테스트 | P0 |
| **ANKR-Phase1** | 디니군 | extract_and_dump + 하드코딩 제거 (진행 중) | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| **TEMS-마이그레이션** | 위상군 | 나머지 에이전트 import 전환 | P1 |
| **KH-Phase2** | 위상군 | Phase 2 brainstorming | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **독립 위상군 → bobpullie/wesangAgent** | 종일군 지정 URL | 4/13 S30 |
| **settings.local.json git tracked** | 이식성 우선 (종일군 요청) | 4/13 S30 |
| **bobpullie/WesangGoon 유지** | 종일군 삭제 거부 | 4/13 S30 |
| **Atlas → bobpullie/atlas push** | 미니PC 배포용 | 4/13 S28 |

## 팀 현황
| 에이전트 | 위치 | TEMS 상태 | 현재 태스크 |
|---------|------|-----------|------------|
| 위상군 (DnT) | E:\DnT\DnT_WesangGoon | **self-contained 원복 (S31)** | 대기 |
| 위상군 (독립) | E:\WesangGoon | **신규 구축 완료** | 대기 |
| 기록군 | E:\KnowledgeHub | 구버전 (tems_core) | L2 키워드 보강 대기 |
| 디니군 | E:\01_houdiniAgent | 구버전 (tems_core) | ANKR Phase 1 |
| 빌드군 | E:\DnT\MRV_DnT | 구버전 (tems_core) | 대기 (Q-002) |
