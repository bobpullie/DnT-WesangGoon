---
date: 2026-04-21
status: Implemented
aliases: []
tags: [sdc, tems, preflight, rule-based, mode-toggle, tcl-122]
phase: S38
scope: wesang-only
cssclass: twk-decision
---

# Decision — SDC §0 Auto-Dispatch 를 규칙기반(기본) / 자동트리거(확장) 모드로 분리

## TL;DR

기존 SDC.md §0 "Auto-Dispatch Check" 는 본체가 **매 task 수신 시 Auto-Trigger 키워드(commit/push/migrate/이식/…)를 자의적으로 탐색** 하는 구조였다. 일반 대화·설계 질문 등 SDC 가 불필요한 task 에도 §0 진입 비용이 상시 발생. 이를 해결하기 위해 **SDC 활성 조건을 TEMS preflight 메커니즘에 얹는다** — `sdc_trigger` 태그를 가진 TCL 이 task 에 매칭되어 주입될 때만 `[SDC]` 마커가 부착되고, 그 때만 3-question gate 수행. 자동 키워드 탐색은 별도 toggle TCL 등록 시에만 부활하는 확장 모드로 분리. 기본은 rule-based.

## 배경

- **S35 도입 시점**: SDC Auto-Dispatch Check 는 "매 prompt 키워드 매칭"을 skill 지침 차원에 녹인 구조. Trigger 없으면 skip 이라지만 **본체가 매번 §0 본문을 읽고 키워드 매칭을 수행해야** 했기에 기본 비용 상존.
- **TEMS preflight 철학과 불일치**: TEMS 는 2026-04 "조용한 TEMS" 로 전환 (매 prompt 무차별 주입 금지, BM25 score≥0.55 강매칭만). SDC 만 여전히 매 task 자의적 탐색.
- **S36 실사건 (후속)**: self-dispatch 실패로 본체가 gate 생략 → `tool_gate_hook` 에 SDC gate hook-level 편입 ([[2026-04-20_sdc-gate-phase3-integration]]). 이는 git 쓰기 시점 강제만 해결. LLM 레벨 매 prompt 탐색 비용은 여전.
- **사용자 요청 (S38)**: "규칙기반으로 SDC 활성화 선별. 자동트리거는 옵션으로." → TEMS preflight 의 selective 매칭을 SDC 에도 적용.

## 검토한 대안

| 대안 | 장점 | 단점 |
|------|------|------|
| (α) 기존 유지 (매 task 자의적 탐색) | 구현 공수 0. 하위호환 | 매 prompt 비용 상존. TEMS 선별 철학과 불일치 |
| (β) 별도 `sdc_config.json` + CLI 토글 | 강제력 명확. 모드 파일 분리 | config 파일·CLI 신설 = 추가 복잡도. "규칙 = 행동" TEMS 원칙 위배 |
| **(γ) TEMS TCL 등록 단일 채널로 통합** | preflight selective 매칭 재사용. 모드 전환 = TCL 등록/archive 만. 신설 파일 0 | LLM 컴플라이언스 의존 (텍스트 지침 강제력) — hook 레벨 강제는 별도 유지로 보완 |
| (δ) §0 전면 폐기, hook-level 만 유지 | 최소주의 | 코드 구현 등 git 외 영역 SDC 활용 불가 |

채택: **(γ)** — TEMS "규칙 = 행동" 원칙과 align, 신설 파일 0, hook-level 강제(tool_gate_hook)는 독립 유지로 이중 safety net.

## 결정

### 두 모드

| 모드 | 발동 신호 | 활성화 방법 |
|------|----------|------------|
| **규칙기반 (기본)** | `<preflight-memory-check>` 내 `[SDC]` 마커 TCL 주입 | TCL 을 `--tags "sdc_trigger"` 로 등록 |
| **규칙기반 + 자동트리거 (확장)** | 위 + `<sdc-mode>rule+auto</sdc-mode>` 신호 관측 시 Auto-Trigger 키워드 자의 탐색 | `sdc_auto_trigger_enabled` 태그 TCL 1건 등록 |

### 발동 판정 로직 (SDC.md §0)

**Step 1 — 항상 수행:**
- `<preflight-memory-check>` 안 `[SDC]` 마커 TCL 발견 → 3-Question Gate.
- 없으면 Step 2.

**Step 2 — 모드 분기:**
- `<sdc-mode>rule+auto</sdc-mode>` 관측 → Auto-Trigger 키워드를 task 본문에서 자의 탐색.
- `<sdc-mode>` 신호 없음 → §0 완전 생략.

### 구현 요지 (본체 직접, Commit `4d31cf5`)

- `.claude/skills/SDC.md` §0 전면 재작성 (+57 -7 lines)
- `memory/preflight_hook.py`:
  - `detect_sdc_mode()` — DB `sdc_auto_trigger_enabled` 태그 활성 TCL 검사
  - `_has_sdc_trigger_tag()` — TCL hit context_tags 태그 검사
  - `format_rules()` TCL loop: `sdc_trigger` 보유 시 `#N [SDC]: ...` prefix
  - `main()`: 모드가 `rule+auto` 면 `<sdc-mode>rule+auto</sdc-mode>` 1줄 출력 (기본 rule-based 는 침묵)

### 등록된 초기 trigger TCL

**#122** — `tags: sdc_trigger,project:meta`
> 앞으로 git commit/push/merge/rebase/cherry-pick 등 배포 명령 수행 전 SDC 3-question gate 수행. Shared state 수정이므로 KEEP/DELEGATE+STAGING 판정 명시.
> triggers: `git, commit, push, merge, rebase, cherry-pick, deploy, 배포, 푸시, 커밋, 병합`

확장 모드 TCL 은 현재 미등록 — 기본 rule-based 만 가동.

## 검증 (S38 smoke test)

| 케이스 | 기대 | 결과 |
|--------|------|------|
| `"git push origin master 해줘"` | `#122 [SDC]` 마커 주입 | ✓ |
| `"오늘 날씨 어때"` | preflight 침묵 | ✓ |
| `"이 파일 내용 설명"` | 다른 TCL 매칭, `[SDC]` 없음 | ✓ |
| `detect_sdc_mode()` | `rule-based` (toggle TCL 미등록) | ✓ |
| `tool_gate_hook` git gate 회귀 | 정상 | ✓ |

## Hook-level 강제와의 관계

`tool_gate_hook.py` 의 git `<sdc-gate-alert>` 은 **모드 독립**. `git commit/push/merge/rebase/cherry-pick/revert` 실행 직전 `sdc_brief_submitted=false` 면 경고 주입 — SDC.md §0 mode 와 무관하게 항상 작동. 이중 safety net 구조:

1. **LLM 레벨 (이번 결정)**: preflight 가 주입한 `[SDC]` 마커 → 본체가 task 전에 3-question gate
2. **Tool 레벨 ([[2026-04-20_sdc-gate-phase3-integration]])**: git 호출 직전 hook 이 brief 제출 확인 경고

## 연쇄 효과

- **TEMS 일관성 강화**: "규칙 = 행동" 원칙이 SDC 까지 통합. 별도 config 파일·CLI 무신설.
- **매 prompt 비용 감소**: §0 본문 자의적 매칭 제거 → 일반 대화·질문에서 SDC skill 본문을 컨텍스트에 얹지 않아도 됨 (rule-based 기본 시).
- **사용자 제어성**: 어느 task 범위에 SDC 를 걸지 TCL 등록으로 직접 설계. 원하는 영역(git/구현/리팩터 등)만 선별 가능.

## 미결 / 후속

- [ ] **S39 관찰**: #122 실전 발동 기록 수집. false positive 빈도, pull/fetch 포함 필요성 판단.
- [ ] **코드구현 TCL 추가 여부**: 이번 세션은 의도적 등록 보류 (triggers 범위 광범위 → selective 장점 희석 우려). 실측 데이터 누적 후 결정.
- [ ] **확장 모드 실전**: `sdc_auto_trigger_enabled` TCL 은 당분간 미사용. 사용 케이스 관찰.

## 참조

- [[../concepts/SDC]] — SDC 정의
- [[2026-04-20_sdc-gate-phase3-integration]] — hook-level 강제 원조
- [[../../session_archive/20260421_session2_raw|S38 L2 raw]]
- Commit `4d31cf5` (master origin)
