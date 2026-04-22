---
title: 위상군 — 세션 산출물
date: 2026-04-22
status: Active
cssclass: twk-timeline
tags: [index, session, artifacts]
---

# 세션 산출물 (Session Artifacts)

> [!abstract]+ 범위
> **L2 raw** + **핸드오버** + **QMD recap** + **L3 wiki** 의 통합 타임라인.
> 4개 폴더의 최근 작성/수정 문서를 한 눈에.

## 최근 작성 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  date as "작성일",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT date DESC
LIMIT 10
```

## 최근 수정 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") as "수정시각",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT file.mtime DESC
LIMIT 10
```

## 폴더별 네비게이션

- [[wiki/index|L3 Wiki Index]] — 큐레이션된 지식
- `docs/session_archive/` — L2 raw (기계 추출)
- `handover_doc/` — 세션 핸드오버
- `qmd_drive/recaps/` — QMD recap
