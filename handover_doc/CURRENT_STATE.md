# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-20 Session 36 종료

## TEMS 호출 매뉴얼 (조용한 TEMS 아키텍처)
**기본 정책:** 매 prompt 무차별 주입 금지. 키워드 강매칭(score≥0.55) 시에만 자동 발동.
**등록 (수동 호출):**
```bash
python memory/tems_commit.py --type {TCL|TGL} --rule "..." --triggers "키워드들" --tags "..."
```
**자동 발동 트리거:** TCL 패턴(`이제부터/앞으로/항상`) / TGL 패턴(`하지마/금지/never/don't`) / Bash 실패 / preflight 자체 실패 / [Phase 3] TGL-T + **SDC PreToolUse (S36 신규)** / active guard 위반.

## ⚠️ DVC ≠ TEMS TCL (용어 분리)
- **DVC case** (결정론적 빌드 검증) = `src/checklist/cases.json` + `chk_*.py`. `DISPLAY_HUMANIZE_001` 형식
- **TEMS TCL** (LLM 행동 교정) = `memory/error_logs.db`. `#N` 형식
- wiki compile: [[docs/wiki/concepts/DVC_vs_TEMS]]

## 모델 배치 원칙 (Opus 4.7 본체 + Sonnet 서브에이전트) — S34 도입
- **본체 (Opus 4.7):** 아키텍처 설계 · TEMS 규칙 분류 · Phase 전환 판정 · 핸드오버 결정 서술 · 팀 델리게이션
- **Sonnet 서브에이전트:** TEMS 모듈 구현 · Phase 이식 · 재분류 · DVC case · smoke test · Explore
- **Opus 서브에이전트:** `superpowers:code-reviewer` (Audit) · `advisor` (2안 비교)
- 상세: `.claude/skills/SDC.md` ([[docs/wiki/concepts/SDC]])
- **S36 강화:** Phase 3 tool_gate_hook 에 **SDC Auto-Dispatch PreToolUse gate 편입** (TCL #120 자동 강제). git 쓰기 명령 직전 `<sdc-gate-alert>` 경고.

## TWK / TriadWiKi (S34 도입, S35 llm-wiki → TWK rename, **S36 Dataview+Calendar 호환화**)
- 글로벌 스킬: `C:/Users/bluei/.claude/skills/TWK/` (upstream: `bobpullie/TWK@db9766e`)
- 프로젝트 config: `wiki.config.json` v1.1 (Mode B, 5 섹션, frontmatter 계약 명시)
- 구조: `docs/wiki/{decisions,patterns,concepts,postmortems,principles}/` + `index.md` + `log.md` + `docs/daily/` (Calendar 허브)
- L2 추출: `docs/session_archive/` (session-lifecycle Step 5)
- Lint 주기: 5세션 / 10페이지
- **Frontmatter 계약**: `date` 무인용 ISO YYYY-MM-DD (Dataview Date coerce), `tags` 복수형 인라인, `cssclass` 템플릿별
- **Calendar ↔ Dataview 연동**: `docs/daily/YYYY-MM-DD.md` 허브 + `WHERE date = this.file.day` 쿼리
- 현재 16+ pages (S36 에 SDC gate decision + postmortem 추가 예정)

## QMD 로컬 관리 (S35 도입, 전 에이전트 공통)
- **정책:** 모든 에이전트는 QMD 데이터를 프로젝트 로컬 `qmd_drive/` 에서 관리 (TCL #116).
- **구조:** `qmd_drive/sessions/` (Claude 세션 export) + `qmd_drive/recaps/` (session-lifecycle Step 3 recap) + `memory/qmd_rules/` (TEMS 규칙).
- **위상군 이관 완료:** 94 files → `qmd_drive/` (sessions 48 + recaps 46). `wesanggoon-sessions`(broken) 제거, `wesanggoon-qmd-drive`(로컬) 등록·embed(48 docs, 63 chunks).
- **타 에이전트 대기:** 리얼군 / 코드군 / 디니군 / 어플군 / 기록군 / 빌드군 / 위상군(독립).
- **원리:** [[docs/wiki/principles/Per_Agent_Local_QMD]]

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **메타 프로젝트:** Atlas 비활성화 (S34)
- **TEMS 위상군:** Phase 0-3 + Migration + SDC(S34~S35) + SDC Gate(S36) + TWK(S34~S36) — 규칙 #1~#121
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정)
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)

## 이번 세션 성과 (Session 36, 종료)
- **TWK Dataview+Calendar 호환 frontmatter 계약 확립 (`bobpullie/TWK@db9766e`)**
  - 6 page-templates 통일 frontmatter + daily-note.md 신설 + lint 강화 (quoted date / 단수 tag 탐지)
  - SKILL.md + obsidian-integration.md 갱신
- **위상군 wiki 반영 + Daily Note 허브**
  - `wiki.config.json` v1.1 + `docs/templates/daily-note.md` + `docs/daily/2026-04-20.md`
  - Calendar 에서 4월 20일 클릭 시 Dataview 쿼리가 13 wiki 페이지 자동 집계
- **S34-S35 누적 미커밋 정리 + push**
  - 5 그룹 논리 분할 (QMD 이관 / TEMS 규칙 / 스킬 / wiki+vault / 핸드오버)
  - `bobpullie/DnT-WesangGoon@4c9b468..82fcf5d` push 완료
- **SDC Gate Phase 3 편입 (`8b5cc06`, TCL #120 자동 강제)**
  - 세션 중 발생한 SDC violation 을 즉시 root cause fix 로 전환
  - Sonnet 위임(brief 5항목) + trust-but-verify(5/5 pass) + 본체 commit/push (STAGING 프로토콜 실증)
  - `check_sdc_gate()` PreToolUse, warning only, self-invocation 제외
- **누적 규칙:** TCL/TGL #1~#121, archive: #64, #98. 신규 S36: 없음 (위반을 규칙 등록이 아닌 hook 편입으로 해결).

## 이전 세션 성과 요약

### Session 35 — SDC rename + QMD 로컬 + 원격 레포 + SDC Auto-Dispatch Check
- subagent-brief → SDC rename / QMD 로컬 관리 정책 (TCL #116)
- 4개 플러그인 원격 레포 (TEMS/TWK/DVC/SDC) 생성 + pull-based 업데이트
- SDC Auto-Dispatch Check 도입 (TCL #120, Hybrid trigger 모드, 3-question gate)

### Session 34 — TEMS 표준화 + SDC + TWK + Atlas 비활성화
- Wave 1 (Phase 0-2) 전 에이전트 표준 승격 / 디니·리얼군 이식
- SDC 스킬 2군 장착 (위상군 + 리얼군)
- 글로벌 TWK 스킬 신설 (Karpathy 3-Layer + 3 Operations)
- Atlas 비활성화

### Session 33 — Phase 3 재검증 + DVC skill + 코드군 Wave 1
- Phase3-Audit-Reverify + stale eviction 패치
- DVC skill 생성 + 위상군 dogfood
- 코드군 Wave 1 이식 + Migration-Classification 31건

## 다음 세션 부트 (S37)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군): 8b5cc06 — master origin 동기화
HEAD (위상군 독립): 03d6638 (변경 없음)
HEAD (TWK 글로벌): bobpullie/TWK@db9766e
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋

위상군 TEMS: Phase 0-3 + Migration + SDC + SDC Gate(S36) + TWK. 규칙 #1~#121.
위상군 wiki: 16 페이지 + daily note 허브 + (S37 추가 예정: SDC gate decision + postmortem)
위상군 CLAUDE.md: v2026.4.20

Hook 구성 (위상군 동일):
  - SessionStart: CURRENT_STATE 주입
  - UserPromptSubmit: preflight_hook
  - PreToolUse '': tool_gate_hook (TGL-T + SDC Auto-Dispatch, S36 신규)
  - PostToolUse Write|Edit: changelog + memory_bridge
  - PostToolUse Bash: tool_failure_hook
  - PostToolUse '': compliance_tracker
  - Stop: retrospective_hook

SDC Gate 상태:
  - active_guards.json.sdc_brief_submitted = false (runtime state, 매 세션 리셋)
  - 다음 Bash(git commit/push/merge/...) 호출 시 <sdc-gate-alert> 자동 주입 예상
  - 노이즈 억제 위해 SDC-Helper(sdc_commit.py) 우선 구현 필요 (P0)

상태: 종일군 지시 대기
```

## S37 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **SDC-Helper** | P0 | `memory/sdc_commit.py` — brief 제출 시 `active_guards.json.sdc_brief_submitted=true` 자동 세팅 |
| **SDC-Gate-Observation** | P0 | 다음 세션 운영 중 false positive 관찰, `pull`/`fetch` trigger 포함 여부 판단 |
| **Push-decision-other** | P1 | 코드군/디니군/리얼군 미푸시 판단 (위상군은 완료) |
| **Phase3-Observation** | P1 | Phase 3 violation/compliance 통계 1-2주 수집 |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 수동 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 |
| **QMD-Local-Rollout** | P1 | TCL #116 타 에이전트 이관 |
| **TWK-Expand** | P1 | 타 에이전트 TWK 배포 (코드군 fermion-wiki 호환 확인 선행) |
| **DVC-Global-Promotion** | P2 | 위상군 dogfood 1-2세션 후 판단 |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |
| **QMD-Embed-115-121** | P2 | 신규 규칙 #115~#121 qmd embed |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **SDC Gate Phase 3 편입** | S36 세션 중 발생한 본체 SDC 위반 → 자동 강제 필요. warning only, 200:1 효율 | 4/20 S36 |
| **TWK frontmatter Dataview+Calendar 호환** | 플러그인 스펙 조사 + 6/6 템플릿 정규화 | 4/20 S36 |
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |
| **Phase 3 위상군 단독 관찰** | S32 신규, 1-2주 통계 후 Wave 2 판정 | 4/20 S34 |
| **Atlas 비활성화** | 종일군 불필요 선언 | 4/20 S34 |
| **SDC(Subagent Delegation Contract)** | 깊은 추론 없는 실행을 Sonnet 위임으로 | 4/20 S34~S35 |
| **TWK (TriadWiKi)** | Karpathy 3-Layer 범용화, 리얼·코드군 양립 | 4/20 S34~S35 |
| **DVC ≠ TEMS TCL 용어 분리** | S33 혼동 사고 기반 wiki 정식화 | 4/20 S34 |

## 팀 현황
| 에이전트 | 위치 | TEMS | SDC | SDC Gate | TWK | 현재 태스크 |
|---------|------|------|-----|----------|-----|------------|
| 위상군 (DnT) | E:\DnT\DnT_WesangGoon | Wave 1 + Phase 3 | ✓ S34 | ✓ S36 | ✓ S36 호환화 | 대기 |
| 위상군 (독립) | E:\WesangGoon | 신규 구축 완료 | — | — | — | 대기 |
| 코드군 | E:\QuantProject\DnT_Fermion | Wave 1 (52f8dff) | ✓ 원조 | — | 자체 fermion-wiki | needs_review 14건 |
| 디니군 | E:\01_houdiniAgent | Wave 1 (S34) | — | — | — | ANKR Phase 1 |
| 리얼군 | E:\00_unrealAgent | Wave 1 (S34, migration) | ✓ S34 | — | — | TEMS cleanup 대기 |
| 어플군 | E:\ChildSchedule | 구버전 (tems_core) | — | — | — | Wave 1 이식 대기 |
| 기록군 | E:\KnowledgeHub | 구버전 | — | — | — | L2 키워드 보강 대기 |
| 빌드군 | E:\DnT\MRV_DnT | 구버전 | — | — | — | 대기 (Q-002) |
