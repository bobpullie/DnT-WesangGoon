---
description: TEMS 메모리 커밋, TCL/TGL 규칙 생성, preflight 검색 시 적용 (v2026.4 — Phase 2 재정의)
globs:
  - "memory/**"
alwaysApply: false
---

# TEMS — Topological Evolving Memory System 프로토콜 (v2026.4)

## 메모리 기록 (Memory Commit)
모든 등록은 `python memory/tems_commit.py`로 수행. 분류·게이트 통과 후에만 DB 적재.

## 작업 전 자가 검색 (Pre-flight)
preflight_hook이 UserPromptSubmit마다 자동 발동(BM25 + CUDA dense fallback). 주입된 규칙을
컨텍스트에 통합 후 **"과거 메모리에 따라 A 대신 B 방법 사용"**을 명시적으로 선언.

---

## TCL (Topological Checklist Loop) — 좁은 규칙
**본질:** 사용자가 직접 정한 명시적·국지적 케이스 한정 규칙. 체크리스트처럼 작동.

**예시:** 종일군 명명규칙(#47), 세션종료 핸드오버(#4), GitHub repo 보존(#91)

**등록 트리거:**
- 사용자가 "앞으로/이제부터/항상/반드시" 등 명시적 미래 지시
- 또는 좁은 케이스에 대한 명확한 규약 정의

**일반화 수준:** L1 (Concrete Pattern) — 변수만 추출. 위상화 X.

**필수 슬롯:**
- `correction_rule` (200자 이하 권장)
- `keyword_trigger` — 본문 핵심 명사의 80% 이상 명시 + 동의어 5개 이상 권장
- `tags` (`project:*`, 도메인 태그)

**발동 메커니즘:** BM25 키워드 매칭(1차). dense는 백업.

**검증 게이트:** A(schema) + 키워드 다양성 검사. B/C/D/E 미적용 (좁아서 불필요).

---

## TGL (Topological Guard Loop) — 넓은 위상 패턴
**본질:** 누적 실수/심각 사고에서 추출한 일반화 가능한 카테고리 차원의 가드.
유사 사례 다수를 함께 차단.

**예시:** 외부 패키지 검증(#92), useEffect deps 패턴(#54), negative knowledge(#88)

**등록 트리거:**
- pattern_detector가 동일 시그니처 N≥5회 자동 감지
- 또는 종일군이 명시한 광범위 가드

**일반화 수준:** L2 (Topological Case) sweet spot 강제. L0/L4 거부.

**7-카테고리 분류 (`classification` 슬롯):**

| 코드 | 본질 | 트리거 시점 |
|------|------|------------|
| TGL-T | Tool Action — 도구 호출 자체가 위험 | tool_input |
| TGL-S | System State — 사전조건 깨짐 | startup |
| TGL-D | Dependency — 외부 의존성 부재/변경 | runtime exception |
| TGL-P | Pattern Reuse — 코드 패턴 반복 버그 | 코드 작성 |
| TGL-W | Workflow — 작업 흐름/순서 위반 | 단계 전환 |
| TGL-C | Communication — 정보 전달 결함 | 위임/보고 |
| TGL-M | Meta-system — TEMS/hook 자체 변경 | 시스템 변경 |

**필수 슬롯:**
- `classification` (위 7개 중 1)
- `abstraction_level` (L1~L3, L2 권장)
- `topological_case` (L2 위상 케이스 본문)
- `forbidden_action` (NOT TO DO)
- `required_action` (TO DO INSTEAD)
- `verification.success_signal` + `verification.compliance_check`
- `keyword_anchors` (BM25용) + `semantic_intent` (dense용)
- 카테고리별 추가 슬롯 (TGL-T면 `tool_patterns`, TGL-D면 `failure_signatures` 등)

**발동 메커니즘:** dense vector 의미 매칭(1차) + BM25(보강) + 카테고리별 hook (Phase 3에서 PreToolUse 등 도입 예정).

**검증 게이트:** A(schema) + B(abstraction) **거부형**. C(duplication) + D(replay) + E(verifiability) **경고형**.

---

## 트리거 카운팅 (Phase 2A 도입)
모든 규칙 매칭 시 `rule_health.fire_count++` 자동 갱신:
- 30일 0회 발동 → `status='cold'` 자동 전환
- 90일 0회 → `archive` 후보
- `compliance_count`/`violation_count`로 효용도 측정

## 자동 등록 모드 (Phase 1)
TCL "TEMS 자동등록 활성화" 등록 시: pattern_detector가 N≥5 반복 패턴을 자동 TGL 등록 (L1 + `needs_review` 태그).

## 상세 참조
DB 스키마, 자동 트리거, 4-Phase 아키텍처: `.claude/references/tems-architecture.md`
