---
title: 위상군 Wiki
date: 2026-04-22
status: Active
updated: 2026-04-21
session: S38
cssclass: twk-index
tags: [wiki, index, wesanggoon]
---

# 위상군 Wiki

> [!abstract]+ Wesanggoon Knowledge Base
> **Triad Chord Studio — 위상군(位相群)** 의 지식 베이스.
>
> Karpathy **3-Layer Wiki 방법론** 의 L3 큐레이션 레이어 — 네 가지 위상 시스템의 결정 · 개념 · 패턴 · 원리 · 사후분석을 기록합니다.
>
> `TEMS` · `DVC` · `SDC` · `TWK`

> [!info] 메타
> - **마지막 갱신** — 2026-04-21 · Session 38 (SDC 선택적 발동)
> - **관리 주기** — Ingest 자동 · Lint 5세션마다 또는 20 페이지
> - **다음 Lint 주기** — Session 41
> - **변경 이력** — [[log|Wiki Change Log]]

---

## 세션 산출물 (통합)

> [!tip] 4폴더 통합 타임라인
> 아래는 [[../session_artifacts]] 의 embed 입니다. 독립 열람도 가능.

![[../session_artifacts]]

---

## 최근 변경

```dataview
TABLE WITHOUT ID
  file.link as "페이지",
  date as "날짜",
  status as "상태",
  scope as "범위"
FROM "docs/wiki"
WHERE file.name != "index" AND file.name != "log"
SORT date DESC
LIMIT 8
```

---

## 시스템 빠른 이동

> [!tip]+ 4개 위상 시스템
> | 시스템 | 정의 | 한 줄 설명 |
> |:------:|:-----|:----------|
> | **TEMS** | [[concepts/TEMS]] | LLM 행동 교정 메모리 (TCL / TGL) |
> | **DVC**  | [[concepts/DVC]]  | 결정론적 빌드 검증 프레임워크 |
> | **SDC**  | [[concepts/SDC]]  | Opus → Sonnet 서브에이전트 위임 계약 |
> | **TWK**  | *(이 위키 자체)* | Karpathy 3-Layer 위키 방법론 구현 |
>
> **분류 체계** — [[concepts/System_vs_Skill]] (System / Skill / Hybrid 3-way)

> [!question]+ 혼동 방지 대조표
> - [[concepts/TCL_vs_TGL]] — *좁은 규칙(TCL)* vs *넓은 위상 패턴(TGL)*
> - [[concepts/DVC_vs_TEMS]] — *빌드 검증(DVC)* vs *LLM 교정(TEMS TCL)*

---

## Decisions — 결정

> [!check] 아키텍처 · 정책 결정
> 구현되었거나 승인된 주요 결정. Status: `Implemented` · `Accepted` · `Observation`

```dataview
TABLE WITHOUT ID
  file.link as "Decision",
  status as "상태",
  phase as "Phase",
  date as "날짜"
FROM "docs/wiki/decisions"
SORT date DESC
```

---

## Concepts — 개념

> [!info] 시스템 · 용어의 정의
> 고유명사 · 시스템 이름 · 용어 차이의 기준선.

```dataview
TABLE WITHOUT ID
  file.link as "Concept",
  status as "상태",
  scope as "범위"
FROM "docs/wiki/concepts"
SORT file.name ASC
```

---

## Patterns — 패턴

> [!abstract] 반복되는 위상 패턴
> 카테고리 분류 체계 · 수명주기 등 일반화된 구조.

```dataview
TABLE WITHOUT ID
  file.link as "Pattern",
  status as "상태",
  scope as "범위"
FROM "docs/wiki/patterns"
SORT file.name ASC
```

---

## Principles — 원리

> [!quote] 설계 원리
> 판단 기준 · 금지 사항 · 시스템 운영 원칙.

```dataview
TABLE WITHOUT ID
  file.link as "Principle",
  status as "상태",
  scope as "범위"
FROM "docs/wiki/principles"
SORT file.name ASC
```

---

## Postmortems — 사후분석

> [!bug] 실제 사고 · 실수 기록
> 원인 분석 → 재발 방지 규칙으로 이어진 사건.

```dataview
TABLE WITHOUT ID
  file.link as "Postmortem",
  status as "상태",
  date as "날짜"
FROM "docs/wiki/postmortems"
SORT date DESC
```

---

> [!example]- 위키 전체 현황 (펼치기)
> ```dataview
> TABLE WITHOUT ID
>   file.link as "페이지",
>   date as "날짜",
>   status as "상태",
>   scope as "범위"
> FROM "docs/wiki"
> WHERE file.name != "index" AND file.name != "log"
> SORT date DESC
> ```

---

*관리 — LLM (Ingest / Lint 자동 갱신) · 큐레이션 — 인간*
*이 파일은 위키의 진입점. Obsidian 북마크 권장.*
