---
date: 2026-04-22
type: handover
cssclass: twk-handover
tags: [session, handover]
---

# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-22 Session 42 종료

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
- **TEMS 위상군:** Phase 0-3 + Layer 1 강화 + Migration + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE concept + Session Artifacts Auto-Indexing + **Package Distribution (S42)** — 규칙 #1~#122
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정) → **S42 기준 v0.2.1 로 Wave 2 이식 대체 권장**
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)
- **TEMS canonical 패키지:** **bobpullie/TEMS (S42 기준 v0.2.1, HEAD 7373fb5)** — `pip install -U git+https://github.com/bobpullie/TEMS.git` + `tems scaffold`

## SDC 트리거 모드 (S38 도입)
- **기본:** rule-based — `sdc_trigger` 태그 TCL이 task에 매칭될 때만 `[SDC]` 마커 주입 → 3-question gate 수행
- **확장:** rule+auto — `sdc_auto_trigger_enabled` TCL 1건 등록 시 `<sdc-mode>rule+auto</sdc-mode>` 출력 → §0 키워드 자동탐색 재활성
- **현재 등록된 trigger TCL:** #122 (git 배포 전용)
- **확장 모드 TCL:** 미등록 (현재 rule-based만)
- **Hook-level git gate** (tool_gate_hook.py)는 모드 독립 강제 유지

## Wiki 시각 스타일 (S39~)
- **CSS 스니펫:** `.obsidian/snippets/twk.css` 활성 — **10 카테고리 accent palette** (S41 추가: handover/recap/timeline + raw→default slate 재사용)
- **cssclass 자동 태거:** `scripts/tag_wiki_cssclass.py` — 폴더 → `twk-{category}` 매핑, dry-run 지원
- **적용 범위:** 위상군 로컬 20 wiki 페이지 + 138 세션 산출물. TCL #93 기본 보류, **S41 에 TWK 글로벌 배포 override** (아래 참조).
- **범용 규칙 (vault-wide):** `word-break: keep-all` (한글 어절 보존) · `min-width: 5em` (칸 붕괴 방지) · `:has(table)` 기반 line-width 해제

## Session Artifacts Auto-Indexing (S41 도입)
- **스크립트:** `scripts/normalize_session_frontmatter.py` (+ `~/.claude/skills/TWK/scripts/` 글로벌 배포)
- **Config:** `wiki.config.json.session_artifacts` — folders · date_patterns · wiki_validate_root
- **인덱스 페이지:** `docs/session_artifacts.md` (최근 작성 10 / 최근 수정 10 Dataview) → `docs/wiki/index.md` 에 `![[..]]` embed
- **자동화:** session-lifecycle step 5.5 에 `normalize_session_frontmatter.py --apply` 편입
- **현재 운용:** 138 files frontmatter normalized (종일군 "잘 보임" 확인)
- **TCL #93 override:** 종일군 결정으로 TWK 글로벌 배포 완료 (`bobpullie/TWK` HEAD `83a0e70`)

## 이번 세션 성과 (Session 42, 종료)
- **TEMS Layer 1 강화 (위상군 로컬)** — preflight 포맷에 violation_count 노출 + TGL 헤더 "필수 준수" 승격 + 준수 명시 directive. 위상군 commit `3a37c2a`.
- **memory/README.md 캐노니컬 문서 459줄 작성** — 13 섹션 (TL;DR / 개념 / 아키텍처 / 라이프사이클 / 계층 / 진화 / 등록 / 배포 / 분리 / 진단 / 이력). 위상군 commit `331e768`.
- **bobpullie/TEMS Phase 3 포팅 + 패키지 배포 (S42 핵심 성과)** — `v0.2.0` (Phase 3 hook 템플릿 8종 + scaffold 6-hook 등록 + rule_health Phase 2→3 ALTER 마이그레이션) + `v0.2.1` (template preflight cwd fallback + case-insensitive project 태그 + `__version__` 동기화 + QMD Dense Fallback README 섹션 추가).
- **아트군 실설치 (E:/DnT/DnT_ArtGoon)** — Phase 3 TEMS v0.2.1 live 동작 확인. 기존 3 hook (specs_scanner / artkoon_session_end_sync / changelog_hook) 자동 보존.
- **자연어 TGL 강제력 4-계층 구조 정립 (L1/L2/L3/L4)** — 클로드군 비교 + 오버헤드 4축 분석 → Layer 1+2 실무 채택.
- **사용자 지적 반영** — QMD Dense Fallback 코드는 있지만 README 에서 축약됐던 것 자백 + v0.2.1 섹션 복원.

## 다음 세션 부트 (S43)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군):  <S42 종료 commit> — S42 핸드오버 포함
HEAD (bobpullie/TEMS):     7373fb5 — v0.2.1 (Phase 3 + Layer 1 + cwd fallback)
HEAD (bobpullie/handover): aa7d56c — 변경 없음
HEAD (bobpullie/TWK):      83a0e70 — 변경 없음
HEAD (bobpullie/wesangAgent): 03d6638 — 변경 없음
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋
HEAD (아트군): TEMS v0.2.1 신규 설치 (E:/DnT/DnT_ArtGoon) — 구 `tems/` 디렉토리 보존

위상군 TEMS: Phase 0-3 + Layer 1 + Migration + SDC + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE + Session Artifacts Auto-Indexing + Package Distribution.
규칙 #1~#122 (S42 TCL 신규 0, 핸드오버 하단 "규칙 피드백" 참조).
위상군 wiki: 20 → 22 예상 (decisions/tems-upstream-canonical + patterns/Enforcement_4_Layer).
SDC 모드: rule-based. Trigger TCL 1건 (#122). 확장 모드 TCL 없음.
CSS 스니펫: .obsidian/snippets/twk.css 활성 (10 카테고리).
```

## S43 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **TEMS-Upstream-Observe** | P0 | **S42 신규** — bobpullie/TEMS v0.2.1 배포 후 실설치 사용성 관찰 (아트군 Live + 타 에이전트 재스캐폴드 권유) |
| **Wave2-Rollout** | P0 | **S42 신규** — 코드군/디니군/리얼군 에 `pip install -U` + `tems scaffold --force` (데이터 보존 migration) 로 Phase 3 이식 |
| **TWK-Deploy-Observe** | P0 | bobpullie/TWK `83a0e70` 배포 후 타 에이전트 채택 관찰 (S41~S42 이월) |
| **settings.json-수동정리** | P0 | ~/.claude/settings.json stale 3줄 제거 (S38~S42 이월) |
| **SDC-Gate-Observation** | P0 | #122 실전 발동 관찰, false positive, pull/fetch 포함 여부 (S38~S42 이월) |
| **handover-위상군-적용** | P0 | `bobpullie/handover --migrate` 로 hook 표준 교체 (S37~S42 이월) |
| **Enforcement-Layer-Wiki** | P1 | **S42 신규** — `docs/wiki/patterns/Enforcement_4_Layer.md` 작성 |
| **Table-Width-Root-Cause** | P1 | el-table/table width:100% 재로드 후 실제 개선 확인 (S39~S42 이월) |
| **TWK-css-Global-Push** | P1 | 4 cssclass (raw/handover/recap/timeline) CSS 승격 (S41~S42 이월) |
| **TWK-init-wiki-Integration** | P2 | `init_wiki.py` 가 `session_artifacts.md.template` 자동 복사 (S41~S42 이월) |
| **Obsidian-IDE-Promotion-Watch** | P2 | 3 승격 트리거 관찰 (S40~S42 이월) |
| **Wiki-Visual-Audit** | P2 | 각 카테고리 페이지 색감 일관성·대비 체크 (S39~S42 이월) |
| **TWK-wiki-SDC-gate** | P1 | SDC gate + 선택화 postmortem (S36~S42 이월) |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 (v0.2.1 로 직접 이식 대체 고려) |
| **QMD-Embed-115-122** | P2 | 신규 규칙 #115~#122 qmd embed |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |
| **inbox.md-Hook-Design** | P3 | 양방향 파이프 완전 구현 설계 (승격 트리거 채택 시) |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |
| TEMS-v0.2.1-Adopt | 코드군/디니군/리얼군 | `pip install -U git+...TEMS.git` + `tems scaffold --force` — Phase 3 재스캐폴드 (데이터 보존 migration) | P1 |
| TEMS-Adopt-아트군 추가규칙 | 아트군 | `tems_commit.py` 로 본인 영역 규칙 등록 (ComfyUI / Figma / Houdini) | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **bobpullie/TEMS 를 TEMS canonical upstream 으로 확정** | 기존 패키지가 Phase 2 멈춰있어 Phase 3 포팅 + Layer 1 강화 + cwd fallback defect fix → v0.2.0/v0.2.1 릴리즈. 타 에이전트는 `pip install -U + tems scaffold` 로 일괄 이식 | 4/22 S42 |
| **TGL 강제력 4-계층 구조 (L1 자연어 / L2 deny JSON / L3 compliance / L4 DVC) 정립** | 사용자 질문 "자연어 TGL 무시 시 어떻게 강제?" → 오버헤드 4축 분석 후 Layer 1+2 실무 채택. Haiku pre-eval 은 50~150s 누적 레이턴시로 제외 | 4/22 S42 |
| **template preflight cwd fallback + case-insensitive project 태그** | 아트군 실설치 중 `project:DnT` 태그 규칙이 Registry 없이 filter drop 되는 defect 발견 → v0.2.1 즉시 패치 | 4/22 S42 |
| **세션 산출물 자동 인덱싱 — 4폴더 통합 · frontmatter idempotent 주입** | 위상군 세션 산출물이 흩어져 발견성 낮음. Karpathy L2/L3 층위 유지하며 통합 타임라인 제공 | 4/22 S41 |
| **TCL #93 override — TWK 글로벌 바로 배포** | 종일군 판단. 로컬 검증(1 세션) 후 바로 전파. 관찰은 S42 이후 | 4/22 S41 |
| **yaml BaseLoader — round-trip idempotency 보장** | ISO date string 을 datetime.date 로 자동 변환 방지 | 4/22 S41 |
| **표준화 = config 이관 (`wiki.config.json.session_artifacts`)** | defaults fallback 으로 config 없이도 동작 | 4/22 S41 |
| **Obsidian = 뷰어 + 큐레이션 창 (입력 창 아님)** | Karpathy verbatim 재확인. 단방향 기본, 양방향은 hook 변형 | 4/21 S40 |
| **Obsidian_as_IDE concept Draft 기록** | 조만간 프로젝트 승격 가능성 대비. 4축 + 승격 트리거 3종 사전 정의 | 4/21 S40 |
| **위상군 톤 = 저채도 카테고리 accent** | 수학적·차분. Tailwind -500 일관 레벨 | 4/21 S39 |
| **cssclass = 스타일 적용 단일 채널** | 자동 태거(폴더 기반)로 수동 편집 제거 | 4/21 S39 |
| **SDC §0 매 prompt 키워드 탐색 deprecated** | selective 매칭을 TEMS preflight 에 얹어 일관성 확보 | 4/21 S38 |
| **모드 토글 = TCL 등록 단일 채널** | "규칙 = 행동" TEMS 원칙 align | 4/21 S38 |
| **bobpullie/handover 스킬 신설** | 에이전트마다 기존 폴더 참조 복사 → 다운로드 즉시 사용 | 4/21 S37 |
| **SDC Gate Phase 3 편입** | S36 세션 중 SDC 위반 → 자동 강제 필요 | 4/20 S36 |
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |

## 팀 현황
| 에이전트 | TEMS | SDC | SDC Gate | TWK | Wiki 시각 | Session Artifacts | handover 스킬 |
|---------|------|-----|----------|-----|-----------|-------------------|--------------|
| 위상군 (DnT) | Phase 3 + Layer 1 | ✓ | ✓ S36 | ✓ | ✓ S39 로컬 | ✓ S41 글로벌 | 수동 (S40 마이그 예정) |
| 코드군 | Wave 1 (Phase 2) | ✓ 원조 | — | fermion-wiki | — | (TWK pull 후 채택 가능) | — |
| 디니군 | Wave 1 (Phase 2) | — | — | — | — | (TWK pull 후 채택 가능) | — |
| 리얼군 | Wave 1 (Phase 2) | ✓ | — | — | — | (TWK pull 후 채택 가능) | — |
| **아트군** | **TEMS v0.2.1 (Phase 3) 신규 설치 S42** | — | — | — | — | — | — |
| 어플군 | 구버전 | — | — | — | — | — | — |
| 기록군 | 구버전 | — | — | — | — | — | — |
| 빌드군 | 구버전 | — | — | — | — | — | — |
