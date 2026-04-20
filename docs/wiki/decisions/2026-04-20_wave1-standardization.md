---
date: 2026-04-20
status: Accepted
phase: Wave-1-Standard
scope: all-agents
tags: [tems, wave-1, standard, self-contained, phase-0-2]
---

# TEMS Wave 1 (Phase 0-2) 전 에이전트 표준 승격

## TL;DR

위상군 TEMS Phase 0-2 (self-contained, 외부 패키지 의존 없음)를 모든 에이전트의 공통 기반으로 채택.  
TEMS 코드 자체는 고정하고, 각 에이전트는 도메인 가드(`.claude/rules/`)에만 집중한다.

## 배경

코드군이 S33에서 위상군 Wave 1을 이식하여 8세션 실전 운영하면서 안정성을 검증.  
이전에는 에이전트마다 tems_core 구버전을 개별 유지하여 버전 drift와 외부 패키지 의존 문제가 반복됨.  
(참고: TGL #92 외부 패키지 검증 규칙 도출 배경이기도 함)

Phase 3 기능(tool_gate, compliance_tracker, decay)은 위상군 단독 관찰 중 — 이번 표준에 포함하지 않음.

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| (α) 코드군 구현을 표준으로 | 코드군 도메인 가드 포함 | 실질적으로 위상군 Wave 1 복사본 — 이득 없음 |
| **(β) 위상군 Wave 1 표준 승격 + minimal hook** | 검증된 원본, self-contained, 이식 용이 | Phase 3 제외로 기능 제한적 |
| (γ) Phase 3까지 기본 포함 | 기능 완전성 | 관찰 데이터 부족, 안정성 미검증 |

채택: **(β)** — 8세션 안정성 데이터 + 이식 용이성 우선.

## 결정

**Wave 1 표준 정의:**
- Phase 0 (preflight_hook: BM25+dense 규칙 주입)
- Phase 0.5/0.6 (조용한 TEMS: score ≥ 0.55 gate)
- Phase 1 (memory_bridge: 자가진화 + pattern_detector)
- Phase 2 (검증 게이트: A~E, 7-카테고리 분류)
- tool_failure_hook (Bash 실패 탐지)
- retrospective_hook (세션 종료 교훈 추출)

**이식 절차 (최소):**
1. `memory/` 디렉토리 전체 복사
2. 외부 `tems` 패키지 참조 제거 (`grep -rn "^import tems\|^from tems" memory/` → 0건)
3. `.claude/rules/tems-protocol.md` + `.claude/references/tems-architecture.md` 복사
4. `settings.json` hook 6종 등록

**배포 현황 (2026-04-20):**

| 에이전트 | 상태 | 커밋 |
|---------|------|------|
| 위상군 (원조) | Phase 0-3 운영 | eec891e |
| 코드군 | Wave 1 이식 완료 | 52f8dff |
| 디니군 | Wave 1 이식 완료 | 확인 필요 |
| 리얼군 | Wave 1 이식 완료 | 확인 필요 |
| 어플군 | 구버전, 대기 | — |
| 기록군 | 구버전, 대기 | — |
| 빌드군 | 구버전, 대기 | — |

## 위험 및 제약

- Phase 3 미포함으로 tool_gate 차단 기능 없음 — TGL-T 가드는 등록되지만 자동 차단 불가
- 에이전트별 도메인 가드 품질 편차 — 이식 후 needs_review 수동 처리 필요
- 코드군 14건, 위상군 22건 needs_review 대기

## 참조

- [[../concepts/TEMS]] — TEMS 전체 아키텍처
- [[2026-04-20_tems-phase3-deployment]] — Phase 3 관찰 유보 결정
- [[Self_Containment(TEMS 자기완결성)]] — self-contained 이식 원리
