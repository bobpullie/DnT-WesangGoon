---
date: 2026-04-20
status: Implemented
aliases: []
tags: [sdc, tems, phase-3, tool-gate, auto-dispatch, tcl-120]
phase: Phase-3
scope: wesang-only
cssclass: twk-decision
---

# Decision — SDC Auto-Dispatch gate 를 Phase 3 tool_gate_hook 에 편입

## TL;DR

SDC (TCL #120) 는 본체 self-dispatch 규칙이라 자동 강제가 없었다. S36 세션 중 본체가 commit/push 작업에서 3-question gate verbalize 를 생략해 위반이 발생. 이를 조기 탐지하기 위해 `memory/tool_gate_hook.py` 에 `check_sdc_gate()` 를 편입하여 **git 쓰기 명령 직전 `<sdc-gate-alert>` 경고**를 본체 컨텍스트에 주입하도록 한다. Warning only — 차단 없음.

## 배경

- **S35 도입 시점**: SDC Auto-Dispatch Check 는 "본체가 task 문자열을 스스로 매칭해 3-question gate 실행" 하는 **self-dispatch 규칙**으로 설계됨. `.claude/skills/SDC.md` 본문만 참조, hook 강제 없음.
- **S36 세션 실사건**: 사용자 명령 "현재 커밋되지 않은 사항들을 커밋하고 배포하라" 수행 중, 본체가 5 commit + push 를 직접 수행. 이 때 trigger 키워드(`commit`, `push`, `이식`, `배포`) 다중 매칭이었음에도 gate verbalize 생략.
- **사용자 지적**: "그럼 이건 규칙 위반 아닌가?" — 본체 자가 확인 결과 TCL #120 (3-question gate 의무) + TCL #86 (STAGING) 두 규칙 위반 인정.
- **근본 원인**: self-dispatch 규칙은 수행자(본체) 가 자각 실패 시 조용히 skip 가능. 감사 불가능 영역.

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| (α) self-dispatch 유지 + postmortem 기록만 | 공수 0 | 동일 위반 반복 불가피. 감사 경로 여전 부재 |
| (β) TCL/TGL 신규 규칙 등록 (preflight 주입) | 기존 TEMS 패턴 재사용 | preflight 는 UserPromptSubmit 시점 — git 호출 직전 시점과 어긋남. 타이밍 늦음 |
| **(γ) Phase 3 tool_gate_hook PreToolUse 편입** | git 쓰기 명령 직전 정확 타이밍. 기존 hook 인프라 재사용. 오버헤드 미미 | 기존 hook 수정 (회귀 리스크). `deny` 승격 남용 위험 |
| (δ) 별도 sdc_gate_hook.py 독립 파일 | 파일 분리로 리스크 격리 | PreToolUse hook 체인 복잡도 증가, 동일 payload 두 번 파싱 |

채택: **(γ)** — 타이밍 정확 + 인프라 재사용 + warning only 로 승격 위험 차단.

## 결정

### 구현 요지

- **Trigger regex**: `\bgit\s+(commit|push|merge|rebase|cherry-pick|revert)\b` (대소문자 무시)
- **매칭 제외**: `SELF_INVOCATION_MARKERS` (기존 상수) — TEMS 자체 호출(tems_commit.py 등) 무시
- **Gate clear 조건**: `active_guards.json.sdc_brief_submitted == True`
- **출력**: 매칭 + brief 미제출 시 `<sdc-gate-alert>` 태그 stdout append. `deny` 승격 **금지**.
- **실행 위치**: 기존 TGL-T 매칭 루프 완료 직후. 결과 없으면 `output_lines` 에 축적.

### 오버헤드 수용 기준

| 항목 | 추정/측정 |
|------|----------|
| p50 레이턴시 | +5~10ms (regex 1개 + JSON read) |
| p99 레이턴시 | +~20ms |
| Hook LLM 비용 | $0 (정규식 + JSON only) |
| Context tokens / session | ~$0.005 (경고 태그 5~10회) |
| 개발 공수 | 1 세션 (Sonnet 위임) |

Break-even: 위반 1건 교정 비용($1~2) 대비 **200:1 효율**.

## 위험 및 제약

- **False positive**: 매 세션 초기에 `sdc_brief_submitted=false` 로 시작 → brief 제출 helper 부재 시 모든 git 쓰기에 경고 fire (노이즈).
  - **완화**: S37 우선순위로 `memory/sdc_commit.py` helper 구현. brief 제출 시 토글.
- **git pull/fetch 제외**: SDC.md 의 Auto-Trigger 에는 포함되지만 이번 regex 에서 제외 (읽기 성격, reversibility 낮음). 관찰 후 포함 여부 재판정 (S37 P0).
- **hook 자체 장애 시**: `active_guards.json` 파싱 실패 → diagnostic 로그만 남기고 gate skip. Bash 호출은 정상 허용.
- **warning-only 한계**: 본체가 경고를 인지·반영하지 않으면 여전히 위반 가능. 단 감사 가능(active_guards 에 기록) — 사후 교정 경로 확보.

## 참조

- [[../concepts/SDC]] — SDC(Subagent Delegation Contract) 정의 + Auto-Dispatch Check
- [[../postmortems/20260420_sdc-gate-violation]] — 이 결정의 트리거가 된 실사건
- [[../concepts/TEMS]] — Phase 3 tool_gate_hook 구조
- TCL #120 (SDC Auto-Dispatch) / TCL #86 (서브에이전트 commit 권한) / TCL #115 (trust-but-verify)
- 커밋: `bobpullie/DnT-WesangGoon@8b5cc06`
- 파일: [memory/tool_gate_hook.py](../../../memory/tool_gate_hook.py) / [memory/tests/test_sdc_gate.py](../../../memory/tests/test_sdc_gate.py)
