# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-21 Session 37 종료

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
- **TEMS 위상군:** Phase 0-3 + Migration + SDC Gate + TWK — 규칙 #1~#121
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정)
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)

## 이번 세션 성과 (Session 37, 종료)
- **SDC-Helper 구현 완료 (`4058e2a`, TCL #120):**
  - `memory/sdc_commit.py` — brief 제출 CLI, gate clear, audit log
  - `memory/tests/test_sdc_commit.py` — 5 tests (10/10 with gate tests)
  - SELF_INVOCATION_MARKERS 추가 + .gitignore 갱신
- **bobpullie/handover 독립 스킬 신설 + 배포:**
  - 브레인스토밍(4Q) → 설계(4섹션) → Sonnet STAGING 위임 → trust-but-verify → 본체 커밋
  - `https://github.com/bobpullie/handover` (commits: `c374201`, `aa7d56c`)
  - `--migrate` 플래그: settings.json + settings.local.json 양쪽 탐지·교체
  - **다운로드 즉시 사용**: `git clone ... && python setup.py --agent-id X --cwd Y`

## 다음 세션 부트 (S38)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군): 4058e2a — master origin 동기화
HEAD (bobpullie/handover): aa7d56c — master
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋

위상군 TEMS: Phase 0-3 + Migration + SDC + SDC Gate + TWK. 규칙 #1~#121.
위상군 wiki: 16 페이지 (S37 추가분 없음 — S38 예정: SDC gate decision + postmortem)
```

## S38 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **SDC-Gate-Observation** | P0 | false positive 관찰, pull/fetch trigger 포함 여부, 세션 리셋 자동화 여부 |
| **handover-위상군-적용** | P0 | `--migrate`로 settings.local.json 기존 hook → 표준 교체 검증 |
| **Push-decision-other** | P1 | 코드군/디니군/리얼군 미푸시 판단 |
| **TWK-wiki-SDC-gate** | P1 | SDC gate Phase 3 편입 decision + postmortem (S36~S37 이월) |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 수동 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 |
| **QMD-Embed-115-121** | P2 | 신규 규칙 #115~#121 qmd embed |
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
