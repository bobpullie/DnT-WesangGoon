---
date: 2026-04-21
type: handover
cssclass: twk-handover
tags: [session, handover]
---

# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-21 Session 40 종료

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
- **TEMS 위상군:** Phase 0-3 + Migration + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE concept(Draft) — 규칙 #1~#122
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정)
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)

## SDC 트리거 모드 (S38 도입)
- **기본:** rule-based — `sdc_trigger` 태그 TCL이 task에 매칭될 때만 `[SDC]` 마커 주입 → 3-question gate 수행
- **확장:** rule+auto — `sdc_auto_trigger_enabled` TCL 1건 등록 시 `<sdc-mode>rule+auto</sdc-mode>` 출력 → §0 키워드 자동탐색 재활성
- **현재 등록된 trigger TCL:** #122 (git 배포 전용)
- **확장 모드 TCL:** 미등록 (현재 rule-based만)
- **Hook-level git gate** (tool_gate_hook.py)는 모드 독립 강제 유지

## Wiki 시각 스타일 (S39 도입 · 위상군 로컬)
- **CSS 스니펫:** `.obsidian/snippets/twk.css` 활성 — 6 카테고리 accent palette (sky/emerald/blue/amber/violet/red/slate)
- **cssclass 자동 태거:** `scripts/tag_wiki_cssclass.py` — 폴더 → `twk-{category}` 매핑, dry-run 지원
- **적용 범위:** 위상군 로컬 20 wiki 페이지. TCL #93 준수로 `bobpullie/TWK` 글로벌 배포 **보류**.
- **범용 규칙 (vault-wide):** `word-break: keep-all` (한글 어절 보존) · `min-width: 5em` (칸 붕괴 방지) · `:has(table)` 기반 line-width 해제
- **미완 이슈:** 표 양옆 여백 일부 환경에서 미개선. `el-table`/`table` width:100% 추가본 재로드 후 확인 필요.

## 이번 세션 성과 (Session 40, 종료)
- **Karpathy Obsidian-as-IDE 이해 정렬** — 원문 verbatim 기반 4개 질문(IDE 의미/Web Clipper/이미지 로컬 다운로드/Marp 플러그인) 답변. 종일군 "Obsidian = 프롬프트 입력 창" 오해 교정 → 단방향 기본 + 양방향 hook 변형 구분
- **concepts/Obsidian_as_IDE.md (Draft)** — Karpathy verbatim 2건 인용, 4축 매트릭스(Viewer/Navigator/Query Engine/Ingestion), 양방향 파이프 변형 5 메커니즘, 승격 트리거 3종 사전 정의
- **Marp 플러그인 주류 확정** — `samuele-cozzi/obsidian-marp-slides` (2026-04 WebSearch 기준)
- **코드 변경 없음** — 이해 정렬 + L3 curation 세션

## 다음 세션 부트 (S41)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군): 50a3fb6 — S39+S40 통합 commit 대기 (종일군 authorization)
HEAD (bobpullie/handover): aa7d56c — 변경 없음
HEAD (bobpullie/TWK): 변경 없음 (로컬 검증 단계)
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋

위상군 TEMS: Phase 0-3 + Migration + SDC + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE concept. 규칙 #1~#122 (S40 TCL 신규 0).
위상군 wiki: 18 → 19 (concepts/Obsidian_as_IDE Draft 신규).
SDC 모드: rule-based. Trigger TCL 1건 (#122). 확장 모드 TCL 없음.
CSS 스니펫: .obsidian/snippets/twk.css 활성 (위상군 로컬).
```

## S41 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **settings.json-수동정리** | P0 | ~/.claude/settings.json stale 3줄 제거 (S38→S40 이월) |
| **SDC-Gate-Observation** | P0 | #122 실전 발동 관찰, false positive, pull/fetch 포함 여부 (S38→S40 이월) |
| **handover-위상군-적용** | P0 | `bobpullie/handover --migrate` 로 hook 표준 교체 (S37→S40 이월) |
| **Table-Width-Root-Cause** | P1 | el-table/table width:100% 재로드 후 실제 개선 확인 (S39→S40 이월) |
| **TWK-Index-Template-Parameterize** | P1 | 카테고리별 callout·description 파라미터화 (S39→S40 이월) |
| **TWK-Global-Push-Decision** | P1 | `bobpullie/TWK` push 여부 결정 (S39→S40 이월) |
| **Obsidian-IDE-Promotion-Watch** | P2 | **S40 신규** — 3 승격 트리거(외부 ingest/발표 수요/inbox.md hook) 관찰 |
| **Wiki-Visual-Audit** | P2 | 각 카테고리 페이지 색감 일관성·대비 체크 (S39→S40 이월) |
| **TWK-wiki-SDC-gate** | P1 | SDC gate + 선택화 postmortem (S36→S40 이월) |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 |
| **QMD-Embed-115-122** | P2 | 신규 규칙 #115~#122 qmd embed |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |
| **inbox.md-Hook-Design** | P3 | 양방향 파이프 완전 구현 설계 (승격 트리거 채택 시) |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **Obsidian = 뷰어 + 큐레이션 창 (입력 창 아님)** | Karpathy verbatim 재확인. 단방향 기본, 양방향은 hook 변형 | 4/21 S40 |
| **Obsidian_as_IDE concept Draft 기록** | 조만간 프로젝트 승격 가능성 대비. 4축 + 승격 트리거 3종 사전 정의 | 4/21 S40 |
| **위상군 톤 = 저채도 6-카테고리 accent** | 수학적·차분. Tailwind -500 일관 레벨로 라이트/다크 양방향 | 4/21 S39 |
| **cssclass = 스타일 적용 단일 채널** | 자동 태거(폴더 기반)로 수동 편집 제거. 설정 = 메타데이터 원칙 | 4/21 S39 |
| **CSS 스니펫 로컬 적용 · 글로벌 TWK 배포 보류** | TCL #93 — 위상군 검증 후 전파. 시각 안정화 전 push 금지 | 4/21 S39 |
| **Universal table 규칙 vault-wide** | word-break/min-width 는 한글 환경 보편 이슈 — cssclass 독립 적용 | 4/21 S39 |
| **SDC §0 매 prompt 키워드 탐색 deprecated** | selective 매칭을 TEMS preflight 메커니즘에 얹어 일관성 확보 | 4/21 S38 |
| **모드 토글 = TCL 등록 단일 채널** | "규칙 = 행동" TEMS 원칙 align. 별도 config 파일/CLI 신설 금지 | 4/21 S38 |
| **글로벌 CLAUDE.md 80%+ 감축** | 매 세션 주입 텍스트 최소화. advisor SDK 레퍼런스는 빌드 시에만 필요 | 4/21 S38 |
| **bobpullie/handover 스킬 신설** | 새 에이전트마다 기존 폴더 참조 복사 → 다운로드 즉시 사용으로 전환 | 4/21 S37 |
| **SDC Gate Phase 3 편입** | S36 세션 중 SDC 위반 → 자동 강제 필요 | 4/20 S36 |
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |

## 팀 현황
| 에이전트 | TEMS | SDC | SDC Gate | TWK | Wiki 시각 | handover 스킬 |
|---------|------|-----|----------|-----|-----------|--------------|
| 위상군 (DnT) | Wave 1+Phase 3 | ✓ | ✓ S36 | ✓ | ✓ S39 로컬 | 수동 (S40 마이그 예정) |
| 코드군 | Wave 1 | ✓ 원조 | — | fermion-wiki | — | — |
| 디니군 | Wave 1 | — | — | — | — | — |
| 리얼군 | Wave 1 | ✓ | — | — | — | — |
| 어플군 | 구버전 | — | — | — | — | — |
| 기록군 | 구버전 | — | — | — | — | — |
| 빌드군 | 구버전 | — | — | — | — | — |
