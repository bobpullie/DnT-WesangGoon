---
date: 2026-04-27
type: handover
cssclass: twk-handover
tags: [session, handover]
---

# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-27 Session 44 종료 (TWK Multi-Vault Aggregation 설계 완료 + Phase 0 Foundation 6/21 task 구현)

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
- **TEMS 위상군:** Phase 0-3 + Layer 1 강화 + Migration + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE concept + Session Artifacts Auto-Indexing + Package Distribution + Dense Backend Rework + History Cleanse — 규칙 #1~#122
- **TWK Multi-Vault Aggregation (S44 신규):** 6개 활성 프로젝트(wesang/fermion/mrv/houdini/unreal/gce) 단일 Vault + 모바일 (Quartz + Cloudflare Pages + Access) 설계 완료 + **TWK v0.4 Phase 0 Foundation 6/21 task 구현** (worktree `~/.claude/skills/TWK-v0.4-wt`, branch `v0.4-vault-aggregator`). 미완료 T7-T21 → S45.
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정) → **S43 기준 v0.3.1 로 Wave 2 이식 대체 권장**
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)
- **TEMS canonical 패키지:** **bobpullie/TEMS (S43 기준 v0.3.1, HEAD `45a4407`, 단일 cleansed init commit)** — `pip install -U git+https://github.com/bobpullie/TEMS.git` + `tems scaffold` + (선택) LM Studio 임베딩 서버 설치
- **TWK canonical 패키지:** **bobpullie/TWK** (HEAD `83a0e70` main, branch `v0.4-vault-aggregator` worktree 작업 중) — v0.4.0 release 대기 (T21에서 머지 + tag + push)
- **KJI_WIKI mirror repo (S44 신규, 미생성):** `bobpullie/KJI_WIKI` Phase 4 시점 종일군 작업 — 6개 프로젝트 통합 위키 mirror, `kji-wiki.pages.dev` 배포
- **TEMS LICENSE:** MIT, Copyright (c) 2026 KIM JONG IL (S43 익명화 후)
- **TEMS 백업 (로컬, S43 squash 직전):** `E:/bobpullie/_backups/TEMS_pre_squash_20260426_210037.bundle` (118KB, complete pre-squash history) + 폴더 통째

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

## 이번 세션 성과 (Session 44, 종료)
- **TWK Multi-Vault Aggregation Spec 작성 + commit** (`5d6b0fe`) — 6개 활성 프로젝트 (wesang 27 wiki / fermion 26 / mrv 19 / houdini 16 / unreal 11 / gce 6 handover) 단일 통합 Obsidian Vault. spec ~640줄, 6개 design section 종일군 OK 통과. KnowledgeHub 제외.
- **4개 핵심 결정 (브레인스토밍):**
  1. 통합 모드 = Workspace Vault (junction `mklink /J` 기반) — 6개 git repo 0 변경
  2. 모바일/인증 = GitHub Private + Quartz + Cloudflare Access (`kji-wiki.pages.dev`, `blueitems7@gmail.com` 화이트리스트, $0/월)
  3. Sync 트리거 = 세션 종료 자동 (어느 에이전트든 마지막이 push) + 수동 명령
  4. **통합 메커니즘 위치 = TWK 패키지 코어** (종일군 지적 — 확장성 + 캐노니컬 배포로 6개 프로젝트 동시 업데이트)
- **Repo 책임 분리 결정:** `bobpullie/TWK` (TWK 코드, 위상군 push) vs **`bobpullie/KJI_WIKI`** (통합 vault mirror, vault_sync.py 자동 push) — 별도 repo. KJI_WIKI 미생성, Phase 4 시점 종일군 작업.
- **Implementation Plan 작성 + commit** (`667538b`) — 21 task TDD plan, ~2900줄. 7개 신규 스크립트 + 2개 헬퍼 + 3개 템플릿 + 1개 매뉴얼 + tests/. Phase 0a-0g 분할.
- **TWK v0.4 Foundation 구현 6/21 (worktree `~/.claude/skills/TWK-v0.4-wt`):**
  - T1 `65838b8` — pytest 셋업 + conftest fixtures
  - T2 `e2ac23c` — vault.config.json template + 매뉴얼 skeleton
  - T3 `32097b1` + `eec3eb2` (review fix) — `_vault_common.py` (load/save vault & wiki configs, find_vault_config, VaultConfigError) + 7 tests. **Code reviewer가 JSONDecodeError 누락 발견 → wrap to VaultConfigError + 회귀 테스트 추가.**
  - T4 `debf2e2` — `_vault_junction.py` (Win32 `mklink /J` + POSIX symlink fallback) + 4 Win32-gated tests. **T3 lesson 사전 적용** (subprocess error → JunctionError wrap).
  - T5 `1185398` — `vault_init.py` (메타 vault 초기화) + 3 tests. **Windows backslash → JSON escape 이슈 발견 + `Path.as_posix()` hardening.**
  - T6 `bd42f37` — `vault_index.md.template` (3 dataview 블록) + `project_index.md.template` (6 placeholders).
- **누적 7 commits TWK worktree (모든 pytest 통과), 2 commits 위상군 repo (spec + plan).**
- **3 implementation lessons 도출** (다음 세션 T7+ 적용):
  1. 외부 라이브러리 예외 → 도메인 예외 wrap (T3 review에서 발견, T4에서 사전 적용)
  2. Subprocess error → 도메인 예외 wrap (T4에서 정착)
  3. Windows 경로 JSON 들어갈 때 `Path.as_posix()` 필수 (T5에서 정착)
- **남은 15 task (T7-T21) 다음 세션 (S45) 진행 — 자연스러운 phase boundary 도달.**

## 다음 세션 부트 (S45)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군 master):  <S44 종료 commit> — S44 핸드오버 + spec + plan + recap
HEAD (TWK worktree v0.4-vault-aggregator): bd42f37 — T6 templates 완료 (Phase 0 Foundation 6/21)
  위치: C:/Users/bluei/.claude/skills/TWK-v0.4-wt
HEAD (bobpullie/TWK main): 83a0e70 — 변경 없음 (T21에서 v0.4 머지 + push 예정)
HEAD (bobpullie/TEMS):     45a4407 — v0.3.1, 변경 없음
HEAD (bobpullie/handover): aa7d56c — 변경 없음
HEAD (bobpullie/wesangAgent): 03d6638 — 변경 없음
HEAD (bobpullie/KJI_WIKI):  미생성 (Phase 4 종일군 작업)
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시 (v0.3.1 직접 이식 권장)
HEAD (디니군): S34 이식 변경, 미커밋 (v0.3.1 재스캐폴딩 권장)
HEAD (리얼군): S34 이식 + migration 변경, 미커밋 (v0.3.1 재스캐폴딩 권장)
HEAD (아트군): TEMS v0.2.1 신규 설치 (E:/DnT/DnT_ArtGoon) — v0.3.1 업그레이드 가능

위상군 TEMS: Phase 0-3 + Layer 1 + Migration + SDC + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE + Session Artifacts Auto-Indexing + Package Distribution + Dense Rework + History Cleanse.
규칙 #1~#122 (S44 신규 0건. 후보: TWK v0.4 lessons 3종 — 외부예외wrap / subprocess wrap / Windows path as_posix).
위상군 wiki: 24 (S44 신규 0건. 후보: multi-vault-aggregation concept + KJI_WIKI mirror decision).
SDC 모드: rule-based. Trigger TCL 1건 (#122). 확장 모드 TCL 없음.
CSS 스니펫: .obsidian/snippets/twk.css 활성 (10 카테고리).
TEMS canonical 백업: E:/bobpullie/_backups/TEMS_pre_squash_20260426_210037.bundle (118KB).

S45 즉시 재개 명령:
  cd C:/Users/bluei/.claude/skills/TWK-v0.4-wt
  git status                  # branch v0.4-vault-aggregator
  python -m pytest tests/ -v  # 19 tests 통과 확인 (T1-T6)
  # 그 다음 superpowers:subagent-driven-development 로 T7부터 재개
  # plan: e:/DnT/DnT_WesangGoon/docs/superpowers/plans/2026-04-27-twk-v0.4-vault-aggregator.md
```

## S45 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **TWK-v0.4-Phase0-Resume** | P0 | **S44 신규** — TWK Foundation 완료, T7-T21 (vault_join 트랜잭션 / vault_sync git / 보조 명령 / 릴리스) 진행. plan 파일에 21 task TDD 명시. **권장 페이스:** T7-T13 + T17 + T19 풀 2-stage review, T14-T16 + T18 + T20-T21 implementer + spec only. |
| **TEMS-Wave2-v0.3.1** | P0 | **S43 신규** — 코드군/디니군/리얼군 에 `pip install -U git+...TEMS.git` + `tems scaffold --force` + `tems embed --force`. v0.3.1 의 동적 MEMORY_DIR 호환성 검증. |
| **위상군-v0.3.1-Adopt** | P0 | **S43 신규** — 위상군 메인 PC 에 v0.3.1 도입 + LM Studio 데스크톱 앱 설치 + Qwen3-Embedding-0.6B-Q8_0 다운로드 + `tems embed --force` 1회. qmd dist/llm.js 패치 부담 해소. |
| **TEMS-Audit-CLI** | P1 | **S43 신규** — `tems audit` 명령 신규 — 패키지화 전 sensitive pattern (사용자명/회사명/한국어 에이전트명/절대경로) 자동 검출. v0.3.1 보안 노출 재발 방지. |
| **TGL-Public-Push-Audit** | P1 | **S43 신규** — TGL-W 등록 — "Public GitHub repo 신규 push 전 익명화 audit 강제" 가드 |
| **TCL-Sonnet-Base-Sync** | P2 | **S43 신규** — TCL 등록 — "Sonnet 위임 시 base SHA 검증 강제" (v0.2.2 outdated base 실수 학습) |
| **TEMS-Upstream-Observe** | P1 | bobpullie/TEMS v0.3.1 배포 후 실설치 사용성 관찰 (S42~S43 이월 — v0.3.1 로 갱신) |
| **Wave2-Rollout** | (병합) | TEMS-Wave2-v0.3.1 와 통합 |
| **TWK-Deploy-Observe** | P0 | bobpullie/TWK `83a0e70` 배포 후 타 에이전트 채택 관찰 (S41~S43 이월) |
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
| **bobpullie/TEMS v0.3.1 = canonical 단일 init commit (squash)** | v0.1.0~v0.3.0 history 전반 사용자명/회사명/한국어 에이전트명/절대경로 13일 노출 → squash 만이 효과적. 사용자 명시 옵션 (iii) 승인. git bundle 백업 보존. | 4/26 S43 |
| **bobpullie/TEMS LICENSE = MIT, Copyright KIM JONG IL** | 종일군 본명 명의 저작권. 회사명 (Triad Chord Studio) 제거. 영문 표기 명시. | 4/26 S43 |
| **bobpullie/TEMS v0.3.0 = LM Studio 직호출 (PR #1, 미니PC)** | qmd CLI subprocess (5,200ms) → LM Studio `/v1/embeddings` (31ms) = 168× 가속. AMD iGPU + Vulkan 검증. 외부 deps 0 (urllib only). 종일군 직접 PR 머지. | 4/26 S43 |
| **TEMS 익명화 = 컨텍스트별 분기 (저자성만 KIM JONG IL)** | 단순 일괄 치환 시 docstring 의미 손상. Sonnet 이 "운영자/에이전트" 분기 채택. README/LICENSE 저자성만 KIM JONG IL/김종일 단일 표현. | 4/26 S43 |
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
