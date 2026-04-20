---
date: 2026-04-20
status: Active
phase: S35-introduced
scope: all-agents
tags: [qmd, local-data, principle, per-agent, data-locality, session-storage]
---

# Principle — Per-Agent Local QMD Data

## 원리

**모든 에이전트는 QMD 데이터를 자기 프로젝트 로컬 폴더에서 관리한다.**

QMD 전역 인덱스(`C:/Users/bluei/.cache/qmd/index.sqlite`)는 공유되지만, **embedding의 source 파일은 반드시 각 에이전트 프로젝트 로컬**에 위치해야 한다.

## 근거

S35 (2026-04-20) 종일군 지시 + 위상군 QMD 데이터 산개 실태 발견:

**사고 패턴 (반면교사):**
- `wesanggoon-sessions` collection이 `E:/AgentInterface/wesanggoon-sessions/` 를 가리키는데 해당 경로 미존재 → 0 files, 조용히 실패
- `jaemi-sessions` collection이 `G:/내 드라이브/JEAMIGOON_Memory/...` 를 가리킴 — 외부 동기화 경로
- `sessions` collection이 `C:\Users\bluei\.claude\qmd_sessions` — 사용자 전역 경로, 어느 에이전트 것인지 불분명
- 위상군 세션 데이터가 **3곳**에 산개: `QMD_drive/sessions/` (43) + `Claude-Sessions/` (2) + `qmd_sessions/` (46)

**문제:**
1. **경로 fragility** — 외부 경로는 드라이브 마운트/네트워크 드라이브/사용자 프로필 이동에 취약
2. **에이전트 간 혼선** — 전역 경로는 어느 에이전트 데이터인지 식별 어려움
3. **백업·버전관리 이탈** — 프로젝트 git 스냅샷에 포함되지 않음
4. **Stale collection 누적** — 참조 끊긴 collection이 조용히 0 files 반환

## 표준 구조 (모든 에이전트 공통)

```
<AGENT_PROJECT_ROOT>/
├── qmd_drive/
│   ├── sessions/     # Claude Code 세션 export (sync-claude-sessions 출력)
│   └── recaps/       # 세션 종료 recap (session-lifecycle Step 3)
├── memory/
│   └── qmd_rules/    # TEMS 규칙 embedding source (tems_engine.py 하드코딩)
```

## 표준 Collection 네이밍

| 용도 | 이름 패턴 | 예시 (위상군) |
|-----|----------|-------------|
| 세션 + recap | `<agent>-qmd-drive` | `wesanggoon-qmd-drive` |
| TEMS 규칙 | `tems-<agent>` | `tems-wesanggoon` |

## 예외 (프로젝트 외부 허용)

- **`~/.claude/projects/<project-id>/*.jsonl`** — Claude Code native raw JSONL. Claude Code가 관리, 이동 불가. `/recall`이 native JSONL 타임라인으로 직접 조회. QMD collection에 등록하지 않는다 (중복).

## 금지 사항

- `C:\Users\...\`, `E:/AgentInterface/*`, `G:/내 드라이브/...` 등 **에이전트 프로젝트 루트 밖** 경로를 QMD collection source로 등록 금지
- `Claude-Sessions/`, `qmd_sessions/` 등 **과거 파편 이름**의 폴더 신규 사용 금지 — 단일 `qmd_drive/` 구조로 통합

## 배포 현황 (S35~)

| 에이전트 | 이관 완료 | 비고 |
|---------|---------|------|
| 위상군 (DnT) | ✓ S35 | 91 파일 이관, `wesanggoon-qmd-drive` 등록 |
| 위상군 (독립) | 대기 | `E:\WesangGoon` — S36+ |
| 리얼군 | 대기 | `E:\00_unrealAgent` |
| 코드군 | 대기 | `E:\QuantProject\DnT_Fermion` |
| 디니군 | 대기 | `E:\01_houdiniAgent` |
| 어플군/기록군/빌드군 | 대기 | |

## 관련

[[../concepts/TEMS]] [[../concepts/SDC]]

- TCL #116 — QMD 로컬 관리 규칙
- `.claude/rules/session-lifecycle.md` Step 3 (경로)
- `qmd_drive/README.md` (프로젝트별 상세)
