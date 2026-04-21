# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-21 Session 38 종료

## TEMS 호출 매뉴얼 (조용한 TEMS 아키텍처)
**기본 정책:** 매 prompt 무차별 주입 금지. 키워드 강매칭(score≥0.55) 시에만 자동 발동.
**등록 (수동 호출):**
```bash
python memory/tems_commit.py --type {TCL|TGL} --rule "..." --triggers "키워드들" --tags "..."
```
**SDC brief 제출 (git 쓰기 명령 전 필수):**
```bash
python memory/sdc_commit.py --verdict {KEEP|DELEGATE|STAGING} --task "..." --rationale "..."
```
**자동 발동 트리거:** TCL 패턴 / TGL 패턴 / Bash 실패 / preflight 실패 / TGL-T + SDC PreToolUse / active guard 위반.

## ⚠️ DVC ≠ TEMS TCL (용어 분리)
- **DVC case** (결정론적 빌드 검증) = `src/checklist/cases.json` + `chk_*.py`. `DISPLAY_HUMANIZE_001` 형식
- **TEMS TCL** (LLM 행동 교정) = `memory/error_logs.db`. `#N` 형식

## 모델 배치 원칙 (Opus 4.7 본체 + Sonnet 서브에이전트)
- **본체:** 아키텍처 설계 · TEMS 규칙 분류 · Phase 전환 판정 · 핸드오버 결정 서술 · 팀 델리게이션
- **Sonnet:** TEMS 모듈 구현 · Phase 이식 · 재분류 · DVC case · smoke test · Explore
- **Opus 서브에이전트:** `superpowers:code-reviewer` (Audit) · `advisor` (2안 비교)
- 상세: `.claude/skills/SDC.md` ([[docs/wiki/concepts/SDC]])

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **TEMS 위상군:** Phase 0-3 + Migration + SDC Gate + SDC 선택화 + TWK — 규칙 #1~#122
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정)
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)

## SDC 트리거 모드 (S38 도입)
- **기본:** rule-based — `sdc_trigger` 태그 TCL이 task에 매칭될 때만 `[SDC]` 마커 주입 → 3-question gate 수행
- **확장:** rule+auto — `sdc_auto_trigger_enabled` TCL 1건 등록 시 `<sdc-mode>rule+auto</sdc-mode>` 출력 → §0 키워드 자동탐색 재활성
- **현재 등록된 trigger TCL:** #122 (git 배포 전용)
- **확장 모드 TCL:** 미등록 (현재 rule-based만)
- **Hook-level git gate** (tool_gate_hook.py)는 모드 독립 강제 유지

## 이번 세션 성과 (Session 38, 종료)
- **SDC 트리거 선택화 (`4d31cf5`):**
  - `.claude/skills/SDC.md` §0 재작성 — rule-based(기본) / rule+auto(확장) 분리. 매 prompt 키워드 탐색 deprecated.
  - `memory/preflight_hook.py` — `detect_sdc_mode()` + `_has_sdc_trigger_tag()` + `[SDC]` 마커 + `<sdc-mode>` 출력
  - Smoke test: 관련 prompt만 `[SDC]` 주입 확인, 무관 prompt 침묵
- **TCL #122 등록** — git 배포(commit/push/merge/rebase/cherry-pick) 전용 sdc_trigger
- **글로벌 ~/.claude 최적화:**
  - `~/.claude/CLAUDE.md` 52줄 → 7줄 (86% 감축) — Advisor SDK 레퍼런스 섹션 + 설치 상태 정보 제거
  - `~/.claude/scripts/artkoon_bootstrap.py`, `artkoon_session_end_sync.py` 삭제 (아트군 로컬 이전)
  - `~/.claude/settings.json` stale permissions 제거는 harness self-modification 보호로 **블록** — 종일군 수동 적용 대기

## 다음 세션 부트 (S39)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군): 4d31cf5 + S38 handover commit — master origin 동기화
HEAD (bobpullie/handover): aa7d56c — 변경 없음
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋

위상군 TEMS: Phase 0-3 + Migration + SDC + SDC Gate + SDC 선택화 + TWK. 규칙 #1~#122.
위상군 wiki: 17 페이지 (S38 추가: SDC_Selective_Dispatch)
SDC 모드: rule-based. Trigger TCL 1건 (#122). 확장 모드 TCL 없음.
```

## S39 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **settings.json-수동정리** | P0 | ~/.claude/settings.json stale 3줄 제거 (self-mod 블록 회피: 종일군 직접 편집 or 한시 Bash 권한) |
| **SDC-Gate-Observation** | P0 | #122 실전 발동 기록 관찰, false positive, pull/fetch trigger 포함 여부 |
| **handover-위상군-적용** | P0 | `bobpullie/handover` `--migrate` 로 settings.local.json 기존 hook → 표준 교체 |
| **Push-decision-other** | P1 | 코드군/디니군/리얼군 미푸시 판단 |
| **TWK-wiki-SDC-gate** | P1 | SDC gate + SDC 선택화 postmortem (S36~S38 이월) |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 수동 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 |
| **QMD-Embed-115-122** | P2 | 신규 규칙 #115~#122 qmd embed |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **SDC §0 매 prompt 키워드 탐색 deprecated** | selective 매칭을 TEMS preflight 메커니즘에 얹어 일관성 확보. 일반 대화 §0 진입 비용 제거 | 4/21 S38 |
| **모드 토글 = TCL 등록 단일 채널** | "규칙 = 행동" TEMS 원칙 align. 별도 config 파일/CLI 신설 금지 | 4/21 S38 |
| **글로벌 CLAUDE.md 80%+ 감축** | 매 세션 주입 텍스트 최소화. advisor SDK 레퍼런스는 빌드 시에만 필요 | 4/21 S38 |
| **bobpullie/handover 스킬 신설** | 새 에이전트마다 기존 폴더 참조 복사 → 다운로드 즉시 사용으로 전환 | 4/21 S37 |
| **SDC-Helper CLI** | gate 해제를 JSON 직접 편집이 아닌 선언적 CLI로 | 4/21 S37 |
| **SDC Gate Phase 3 편입** | S36 세션 중 SDC 위반 → 자동 강제 필요 | 4/20 S36 |
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |

## 팀 현황
| 에이전트 | TEMS | SDC | SDC Gate | TWK | handover 스킬 |
|---------|------|-----|----------|-----|--------------|
| 위상군 (DnT) | Wave 1+Phase 3 | ✓ | ✓ S36 | ✓ | 수동 (S38 마이그 예정) |
| 코드군 | Wave 1 | ✓ 원조 | — | fermion-wiki | — |
| 디니군 | Wave 1 | — | — | — | — |
| 리얼군 | Wave 1 | ✓ | — | — | — |
| 어플군 | 구버전 | — | — | — | — |
| 기록군 | 구버전 | — | — | — | — |
| 빌드군 | 구버전 | — | — | — | — |
