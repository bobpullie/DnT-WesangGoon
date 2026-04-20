---
date: 2026-04-21
status: Implemented
aliases: [handover-skill, handover-packaging]
tags: [decision, handover, skill-system, agent-infrastructure]
phase: 운영중
scope: 전 에이전트 (신규 생성 시)
project: ALL
cssclass: twk-decision
---

# Decision — 핸드오버 시스템 독립 스킬(`bobpullie/handover`) 패키징

## TL;DR

위상군 수동 핸드오버 시스템을 `bobpullie/handover` GitHub 리포로 패키징. 신규 에이전트는 `git clone + python setup.py` 한 방으로 설치, 기존 에이전트 폴더 참조 불필요.

## 배경

새 에이전트를 생성할 때마다 기존 에이전트 폴더(e.g. DnT_WesangGoon)를 참조해서 SessionStart hook 명령어, CURRENT_STATE.md 구조, 세션 핸드오버 형식을 수동 복사·적응했다. 다른 미니PC의 Claude Code 에이전트나 새 로컬 에이전트 생성 시 이 과정이 매번 반복되며 일관성 저하와 실수 가능성이 있었다.

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| A: 단일 SKILL.md | 파일 1개, 설치 단순 | 스크립트가 SKILL.md에 묻힘, 수정 불편 |
| **B: 디렉토리 구조 (채택)** | TWK 패턴 일관성, 파일 독립 업데이트, adapter 분리 | 초기 clone 필요 |
| C: hook-heavy (settings.json 중심) | 스크립트 파일 없음 | settings.json에 로직 묻힘, 유지보수 어려움 |

Stop hook 범위:
- A: Skeleton만 (기계적 섹션 자동, TODO placeholder) ← 채택
- B: LLM 초안 생성 (API 추가 비용 + 품질 불확실)
- C: 명시적 CLI 트리거 (Stop hook 의미 없음)

## 결정

**B (디렉토리 구조) + A (Skeleton Stop hook)** 채택.

```
bobpullie/handover/
├── SKILL.md              # Boot/Shutdown Protocol
├── scripts/setup.py      # hook 자동 등록, --migrate 플래그
├── scripts/stop_hook.py  # git log/status 포함 draft 자동 생성
├── templates/            # CURRENT_STATE.md + session-doc.md
└── adapters/triad.json   # TEMS+QMD+TWK 연동 단계 on/off
```

TWK 스킬과 동일한 디렉토리 구조로 팀 패턴 일관성 유지. `adapters/triad.json`으로 Triad 스택 연동 단계 분리 — 독립형 에이전트도 사용 가능.

`--migrate` 플래그: settings.json + settings.local.json 양쪽에서 기존 핸드오버 hook 탐지 → OLD/NEW diff → 확인 후 교체.

## 위험 및 제약

- stop_hook_runner.py에 global skill 경로 하드코딩 — skill 이동 시 `--update`로 재생성 필요
- Stop hook은 300초 rate limit — 짧은 세션에서 draft가 생성 안 될 수 있음
- CURRENT_STATE.md의 판단 섹션(성과/결정/다음세션)은 에이전트가 수동 작성 필요 — LLM 초안 자동화는 의도적으로 제외

## 참조

[[../../session_archive/20260421_session1_raw]]
