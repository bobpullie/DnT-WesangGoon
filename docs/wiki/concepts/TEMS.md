---
date: 2026-04-20
status: Active
phase: Phase-0-3
scope: wesang-all-agents
tags: [tems, memory, llm-behavior, sqlite, bm25, cuda-dense, rule-health]
---

# Concept — TEMS (Topological Evolving Memory System)

## 정의

TEMS는 LLM 에이전트의 행동을 교정·진화시키는 메모리 시스템이다.  
핵심 원리: 과거 실수와 명시적 지시를 규칙으로 구조화하여, 이후 세션에서 동일 실수가 반복되지 않도록 preflight 단계에 자동 주입한다.

**기술 스택:**
- 저장소: SQLite + FTS5 (BM25 랭킹)
- 검색: HybridRetriever (BM25 1차 + CUDA dense fallback)
- 발화 임계값: score ≥ 0.55 (quiet TEMS 정책, 무차별 주입 금지)
- 진화 추적: `rule_health` 테이블 (fire_count / compliance_count / violation_count)

## 출처 문헌

경험적 도출 — 위상군 2026-Q1~Q2 개발 (Session 29~33).  
외부 레퍼런스 없음. 내부 아키텍처 상세: `.claude/references/tems-architecture.md`

## 이 프로젝트 내 적용처

**운영 Hook 구성 (위상군 기준):**

| Hook 시점 | 모듈 | 역할 |
|-----------|------|------|
| UserPromptSubmit | preflight_hook | BM25+dense 규칙 주입 |
| PostToolUse Write\|Edit | memory_bridge | 파일 변경 → 자동 학습 |
| PostToolUse Bash | tool_failure_hook | 실패 시그니처 탐지 |
| PostToolUse (전체) | compliance_tracker | 위반/준수 카운팅 |
| PreToolUse (전체) | tool_gate_hook | TGL-T 도구 차단 [Phase 3] |
| Stop | retrospective_hook | 세션 종료 후 교훈 추출 |

**Phase 개발 이력 (S29~S33):**

- **Phase 0** (S31): self-contained 원복 + 자기관찰 (BM25 preflight)
- **Phase 0.5/0.6**: 조용한 TEMS (score gate 도입) + dense 복원
- **Phase 1** (S31): 자가진화 (pattern_detector, 자동 TGL 등록)
- **Phase 2** (S31): 게이트 검증 (A~E 게이트, 분류 체계)
- **Phase 3** (S32): tool_gate_hook + compliance_tracker + decay.py
- **Migration** (S33): 31개 레거시 TGL 자동 분류 (7-카테고리)
- **P1-a-follow + stale eviction** (S33): had_violation 보존 + 24h TTL

**에이전트 배포 현황:**

| 에이전트 | TEMS 버전 | 상태 |
|---------|-----------|------|
| 위상군 | Phase 0-3 (원조) | 운영 중 |
| 코드군 | Wave 1 (Phase 0-2) | 운영 중 (S33 이식) |
| 리얼군/디니군 | Wave 1 | 이식 예정 |
| 어플군/기록군/빌드군 | 구버전 (tems_core) | 전환 대기 |

## 주의점

**DVC ≠ TEMS TCL — 절대 혼동 금지:**

| 구분 | 식별자 형식 | 위치 | 목적 |
|------|------------|------|------|
| DVC case | `DISPLAY_HUMANIZE_001` (도메인_동사_ID) | `src/checklist/cases.json` | 결정론적 빌드 검증 |
| TEMS TCL | `#N` (정수) | `memory/error_logs.db` | LLM 행동 교정 |

preflight 자동 발동 시 **매 prompt 무차별 주입 금지** — score ≥ 0.55인 경우에만 컨텍스트에 주입.

## 관련 개념

[[TCL_vs_TGL]] [[../patterns/Classification_7_Category]] [[../decisions/2026-04-20_wave1-standardization]]

## 참조

- [[TCL_vs_TGL]] — 좁은 규칙 vs 넓은 위상 패턴 분류 기준
- [[../patterns/Classification_7_Category]] — TGL 7-카테고리 분류 체계
- [[../decisions/2026-04-20_wave1-standardization]] — Wave 1 표준화 결정
- [[Self_Containment(TEMS 자기완결성)]] — 외부 패키지 의존 금지 원리
- [[DVC_vs_TEMS]] — DVC(빌드 검증)와의 분리 기준 (혼동 방지)
