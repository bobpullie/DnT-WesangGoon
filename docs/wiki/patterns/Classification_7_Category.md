---
date: 2026-04-20
status: Active
phase: Phase-2-Migration
scope: wesang-all-agents
tags: [tems, tgl, classification, 7-category, hook-trigger, migration]
---

# Pattern — TGL 7-Category 분류 체계

## ID

PAT-TGL-7CAT

## 정의

TGL(Topological Guard Loop) 규칙을 7개 카테고리로 분류하는 체계.  
각 카테고리는 가드가 발동해야 할 Hook 시점과 도메인 특성이 다르며,  
동일 카테고리 내 규칙끼리 semantic 유사도가 높아 dense retrieval 효율이 향상된다.

**7-카테고리 정의:**

| 코드 | 본질 | 발동 Hook | 핵심 질문 |
|------|------|-----------|----------|
| **TGL-T** | Tool Action — 도구 호출 자체가 위험 | PreToolUse | "이 도구를 호출하면 안 되는가?" |
| **TGL-S** | System State — 사전 조건 깨짐 | SessionStart | "시스템 상태가 전제 조건을 만족하는가?" |
| **TGL-D** | Dependency — 외부 의존성 부재/변경 | runtime exception | "이 패키지/서비스가 실제 존재하는가?" |
| **TGL-P** | Pattern Reuse — 코드 패턴 반복 버그 | 코드 작성 | "이 패턴을 전에 잘못 쓴 적 있는가?" |
| **TGL-W** | Workflow — 작업 흐름/순서 위반 | 단계 전환 | "이 단계를 건너뛰면 어떤 오류가 발생하는가?" |
| **TGL-C** | Communication — 정보 전달 결함 | 위임/보고 | "이 정보가 올바른 에이전트에게 전달되는가?" |
| **TGL-M** | Meta-system — TEMS/hook 자체 변경 | 시스템 변경 | "TEMS 자체를 변경하는 작업인가?" |

## 데이터 소스 / 의존성

- 저장소: `memory/error_logs.db` (TEMS SQLite)
- 분류 실행: `python memory/tems_commit.py --type TGL --classification TGL-X ...`
- Migration: `memory/migrate_classification.py` (레거시 TGL 자동 분류)

## 현재 상태

Active — S33 Migration 실행 결과:

| 카테고리 | 건수 | 비고 |
|---------|------|------|
| TGL-M | 21 | TEMS 자체 변경 관련 (최다) |
| TGL-T | 3 | 도구 호출 위험 |
| TGL-P | 3 | 코드 패턴 버그 |
| TGL-S | 2 | 시스템 상태 전제조건 |
| TGL-C | 2 | 커뮤니케이션 결함 |
| TGL-W | 1 | 워크플로우 순서 |
| TGL-D | 1 | 의존성 (#92 외부 패키지 검증) |
| **합계** | **33** | 22건 needs_review (수동 재분류 대기) |

## 관련 실험·결과

카테고리별 추가 필수 슬롯 (tems_commit.py 스키마):

| 카테고리 | 추가 슬롯 |
|---------|----------|
| TGL-T | `tool_patterns` (차단 대상 도구 이름/패턴 목록) |
| TGL-S | `precondition_checks` (상태 검증 항목) |
| TGL-D | `failure_signatures` (런타임 예외 시그니처) |
| TGL-P | `code_pattern` (버그 패턴 정규식 또는 예시) |
| TGL-W | `workflow_step` (위반 발생 단계명) |
| TGL-C | `communication_channel` (위임 경로 명시) |
| TGL-M | `meta_target` (변경 대상 TEMS 컴포넌트) |

**Migration 원칙:**
1. 레거시 TGL은 `migrate_classification.py` → 자동 분류 + `needs_review` 태그 부여
2. `needs_review` 건은 수동 재분류 (종일군 또는 위상군이 컨텍스트 파악 후 결정)
3. `TGL-M fallback` 패턴 주의: 분류 불명확 시 TGL-M으로 기본 배정됨

**Phase 3 hook 연계 계획:**
- TGL-T: `PreToolUse` hook에서 `tool_gate_hook.py`가 자동 차단/경고
- 나머지 카테고리: Phase 3 이후 hook 확장 예정

## 주의점

- L2 Topological Case가 아닌 L0/L4 등록 시 Gate B가 거부 — 추상화 수준 조정 필요
- TGL-M이 과도하게 많은 경우 (21/33) TEMS 자체 변경 빈도 높음을 의미 — 수동 재분류로 실제 카테고리 확인 필요
- 카테고리 분류는 "발동 Hook 시점"을 기준으로 판단 (본질이 아닌 발동 맥락 우선)

## 관련 엔티티

[[../concepts/TEMS]] [[../concepts/TCL_vs_TGL]]

## 참조

- [[../concepts/TEMS]] — TEMS 전체 아키텍처
- [[../concepts/TCL_vs_TGL]] — TCL/TGL 분류 기준 및 게이트
- [[../decisions/2026-04-20_wave1-standardization]] — Wave 1 표준화 (분류 포함)
