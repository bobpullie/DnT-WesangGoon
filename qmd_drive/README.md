---
date: 2026-04-20
status: Active
scope: wesang-qmd-local-root
tags: [qmd, local-data, sessions, recaps, per-agent-policy]
---

# qmd_drive/ — 위상군 로컬 QMD 데이터 루트

> 정책 (S35 도입): 모든 에이전트는 QMD 데이터를 자기 프로젝트 로컬 폴더에서 관리한다.

## 구조

```
qmd_drive/
├── sessions/      # Claude Code 세션 export (sync-claude-sessions 포맷, YYYY-MM-DD-HHMM-hash.md)
├── recaps/        # 세션 종료 recap (session-lifecycle Step 3, YYYY-MM-DD_sessionN.md)
└── README.md      # 이 파일
```

**별도 위치 (QMD 인덱싱되지만 이 폴더 밖):**
- `memory/qmd_rules/` — TEMS 규칙 embedding source (`tems-wesanggoon` collection). `tems_engine.py:30` 하드코딩 경로 유지.
- `~/.claude/projects/e--DnT-DnT-WesangGoon/*.jsonl` — Claude Code native raw (프로젝트 외부, 시스템 관리).

## QMD Collection 등록

```bash
qmd collection add "E:/DnT/DnT_WesangGoon/qmd_drive" --name wesanggoon-qmd-drive
qmd update wesanggoon-qmd-drive
qmd embed
```

## S35 이관 이력 (2026-04-20)

| 이관 전 | 파일 수 | 이관 후 |
|---------|--------|---------|
| `QMD_drive/sessions/` (uppercase) | 43 | `qmd_drive/sessions/` |
| `Claude-Sessions/` | 2 | `qmd_drive/sessions/` (merge) |
| `qmd_sessions/` | 46 | `qmd_drive/recaps/` |
| **합계** | **91** | **sessions 45 + recaps 46 = 91** ✓ |

제거된 broken collection: `wesanggoon-sessions` (가리키던 `E:/AgentInterface/wesanggoon-sessions` 미존재).

## 금지 사항

- **외부 경로를 가리키는 QMD collection 금지** (C:\\Users\\...\\qmd_sessions, E:/AgentInterface/*, G:/내 드라이브/... 등)
- 세션 recap을 다시 `qmd_sessions/` 로 쓰기 금지 — `qmd_drive/recaps/` 로
- sync-claude-sessions가 기본값으로 `Claude-Sessions/` 에 쓰면 즉시 `qmd_drive/sessions/` 로 이동

## 관련 문서

- [[../docs/wiki/principles/Per_Agent_Local_QMD]] — 원리 페이지 (전 에이전트 공통)
- TCL #116 — QMD 로컬 관리 정책
- `.claude/rules/session-lifecycle.md` Step 3 — recap 저장 경로
