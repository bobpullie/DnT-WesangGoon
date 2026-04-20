# wesang Wiki — Index

> 마지막 갱신: 2026-04-21 (S37 — handover 독립 스킬 packaging decision)

```dataview
TABLE date, status, scope
FROM "docs/wiki"
WHERE file.name != "index" AND file.name != "log"
SORT date DESC
LIMIT 20
```


---

## Decisions

- [[decisions/2026-04-21_handover-skill-packaging]] — 핸드오버 시스템 독립 스킬(`bobpullie/handover`) 패키징 결정 (Implemented, S37)
- [[decisions/2026-04-20_wave1-standardization]] — TEMS Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (Accepted)
- [[decisions/2026-04-20_tems-phase3-deployment]] — Phase 3 (tool_gate + compliance_tracker) 위상군 단독 관찰 유보 (Observation)
- [[decisions/2026-04-20_dvc-skill-promotion]] — DVC 글로벌 스킬 승격 + 위상군 dogfood 설치 (Accepted)
- [[decisions/2026-04-20_plugin-remote-repos]] — 4개 플러그인 원격 레포 체계 확립 (bobpullie/{TEMS,TWK,DVC,SDC}) (Accepted)
- [[decisions/2026-04-20_sdc-gate-phase3-integration]] — SDC Auto-Dispatch gate 를 Phase 3 tool_gate_hook 에 편입 (TCL #120 자동 강제) (Implemented, S36)

## Patterns

- [[patterns/Classification_7_Category]] — TGL 7-카테고리 분류 체계 (TGL-T/S/D/P/W/C/M) + 발동 Hook 시점
- [[patterns/DVC_Case_Lifecycle]] — 버그 발견 → case 일반화 → 영구 회귀 방지 6단계 순환

## Concepts

- [[concepts/TEMS]] — Topological Evolving Memory System 정의 + 아키텍처 개요
- [[concepts/TCL_vs_TGL]] — 좁은 규칙(TCL) vs 넓은 위상 패턴(TGL) 분류 기준 비교
- [[concepts/DVC]] — Deterministic Verification Checklist: 결정론적 빌드 검증 프레임워크
- [[concepts/DVC_vs_TEMS]] — DVC vs TEMS TCL 혼동 방지 대조표 (S33 사고 기반)
- [[concepts/SDC]] — Subagent Delegation Contract: Opus→Sonnet 위임 계약 (Design by Contract 구조)
- [[concepts/System_vs_Skill]] — System/Skill/Hybrid 3-way 분류 체계 (TEMS/DVC/SDC/TWK 분류표)

## Postmortems

- [[postmortems/20260420_sdc-gate-violation]] — S36 본체 SDC Auto-Dispatch 위반 → gate 편입 트리거 (Confirmed, T1+T2)

## Principles

- [[Self_Containment(TEMS 자기완결성)]] — TEMS 자기완결성 원리: memory/ 만으로 완결, 외부 패키지 금지
- [[principles/Case_Generalization]] — 버그 수정 시 case 일반화 우선 원리 (DVC 핵심)
- [[principles/Per_Agent_Local_QMD]] — 에이전트별 프로젝트 로컬 QMD 데이터 관리 원리 (S35 전 에이전트 공통)


---
*관리: LLM (Ingest/Lint 시 자동 갱신), 큐레이션: 인간*
*이 파일은 wiki의 진입점. Obsidian에서 북마크 권장.*
