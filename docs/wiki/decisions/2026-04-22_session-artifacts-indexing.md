---
date: 2026-04-22
status: Implemented
aliases: [session-artifacts, session-artifacts-indexing, normalize-session-frontmatter]
tags: [decision, twk, dataview, automation, session-artifacts]
phase: 운영중
scope: 위상군 로컬 + bobpullie/TWK 글로벌 (S41 override)
project: DnT_WesangGoon + ALL (TWK pull)
cssclass: twk-decision
---

# Decision — 세션 산출물 자동 인덱싱 (Session Artifacts Auto-Indexing)

## TL;DR

세션 중 생성된 4 폴더 `.md` 산출물에 **자동 frontmatter 주입** (idempotent 병합) + **Dataview 통합 타임라인 인덱스** + **기존 wiki index 에 transclusion embed**. 위상군 로컬 검증 후 TCL #93 override 로 글로벌 TWK 스킬에 즉시 배포.

## 배경

위상군 세션은 다음 4 곳에 `.md` 산출물을 남긴다:

| 폴더 | 성격 | 이전 상태 |
|------|------|-----------|
| `docs/wiki/**` | L3 큐레이션 | 표준 frontmatter 있음, Dataview 인덱스 있음 |
| `docs/session_archive/**` | L2 raw (기계 추출) | frontmatter 없음, 탐색 불가 |
| `handover_doc/**` | 세션 핸드오버 | frontmatter 제각각 |
| `qmd_drive/recaps/**` | QMD recap | frontmatter 제각각 |

**문제:** `docs/wiki/index.md` 는 L3 만 커버하고 나머지 3 폴더는 파일 탐색기로만 접근. 새로 작성된 문서가 "한 곳에 모여 보이지" 않음.

## 검토한 대안

### A. 범위 — "어디까지 자동 인덱싱?"

| 옵션 | 내용 | 결과 |
|------|------|------|
| A1 | `docs/wiki/**` 만 (현행) | ❌ 발견성 문제 미해결 |
| A2 | L3 + L2 (2 폴더) | ❌ handover/recap 누락 |
| **A3** | **4 폴더 전부 (채택)** | ✅ 세션 산출물 완전 집합 |
| A4 | vault 전체 | ❌ TCL #29 추적성 경계 침해 |

### B. "연결"의 의미

| 옵션 | 내용 | 결과 |
|------|------|------|
| B1 | Dataview 쿼리만 추가 | ❌ frontmatter 없는 파일은 정렬 불가 |
| **B2** | **쿼리 + frontmatter 자동 주입 (채택)** | ✅ 정렬·필터 품질 확보 |
| B3 | B2 + wikilink 역링크 자동 생성 | ❌ Karpathy "억지로 쓰지 말 것" 원칙 위반 |

### C. 인덱스 페이지 구조

| 옵션 | 내용 | 결과 |
|------|------|------|
| C1 | 기존 `docs/wiki/index.md` 확장 | ❌ L3 순수성 파괴 (3/4 폴더가 wiki 외부) |
| **C2** | **신규 `docs/session_artifacts.md` + embed 로 연결 (채택)** | ✅ L2/L3 층위 분리 유지 |
| C3 | 시간축 통합 재구성 | ❌ 섹션별 네비게이션 가치 파괴 |

**embed 방식:** α (transclusion `![[../session_artifacts]]`) — 독립 열람 + 통합 뷰 둘 다 제공.

## 결정

**A3 + B2 + C2α** 채택.

### 구현 아키텍처

```
[Frontmatter Normalizer]              [Index Query]
 (scripts/normalize_...)                (docs/session_artifacts.md)
      ↓ idempotent write               ↓ 실시간 Dataview
 [3 폴더 frontmatter 보충]        [최근 작성 10 / 최근 수정 10]
      ↓                                  ↓
      └───────── 독립 ──────────────┐    ↓
                                    ↓    ↓
                         [docs/wiki/index.md]
                         ![[../session_artifacts]]
```

### 핵심 설계 결정 (D1~D7)

| # | 결정 | 근거 |
|---|------|------|
| D1 | 범위 = 4 폴더 | 세션 산출물 전체 통합 필요 |
| D2 | "연결" = 표시 + frontmatter 자동 주입 | cssclass 자동 태거 선례와 동형 |
| D3 | 분리 + embed | 4 폴더 중 3 폴더가 wiki 외부 |
| D4 | transclusion `![[..]]` | 통합 뷰 + 독립 뷰 |
| D5 | 작성=`date` / 수정=`file.mtime` | 논리적 시점 vs 물리적 수정 분리 |
| D6 | `docs/wiki/**` 주입 제외 (검증만) | 이미 표준 스키마 존재 |
| D7 | 파싱 실패 fallback = `file.mtime` | 데이터 보존 우선 |

### 구현 특성

- **Idempotent 병합:** 스칼라 값은 기존 보존, 배열(tags) 은 union 병합. 2회차 apply 시 no-op 보장.
- **YAML BaseLoader:** ISO date 를 string 으로 유지하여 round-trip 깨짐 방지.
- **quote-strip 후처리:** safe_dump 의 자동 quoting 제거 → 파일 가독성 유지.
- **CWD 기반 config 로드 + defaults fallback:** wiki.config.json 없어도 크래시 없이 동작.

## 구현 경과

- **설계:** `docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md`
- **Plan:** `docs/superpowers/plans/2026-04-22-session-artifacts-auto-indexing.md` (17 Task)
- **실행:** superpowers workflow full cycle — brainstorming → writing-plans → subagent-driven (16 coding tasks, Sonnet dispatch)
- **검증:** 36 unit tests · 139 파일 실파일 apply · idempotency 2-cycle · Obsidian 렌더링 종일군 확인

### 표준화 + 글로벌 배포

1. **Plan A (위상군 로컬):** `wiki.config.json.session_artifacts` 섹션 신설, 스크립트 config-기반 refactor (commit `79ab4b5`)
2. **Plan B (TWK 글로벌):** `bobpullie/TWK` 에 script·template·SKILL.md 추가 후 `git push origin main` (commit `83a0e70`, pushed to github.com/bobpullie/TWK)

**배포 버전 smoke test 3 pass:**
1. 위상군 CWD + 글로벌 스크립트 실행 → 로컬과 동일 결과
2. 빈 디렉토리 실행 → defaults fallback graceful
3. 모듈 import 시 `FOLDER_CONFIG`/`DATE_PATTERNS`/`WIKI_ROOT` 기대값 로드

### TCL #93 override

기본 정책 "위상군에서 N 세션 검증 후 글로벌 배포" 는 종일군 판단으로 이번 한정 override. 사후 관찰 Task (`TWK-Deploy-Observe`) 가 S42 이후 우선순위 P0.

## 귀결 · 영향

### 위상군 로컬
- 138 파일 (S41 종료 시점 141) frontmatter normalized
- `docs/session_artifacts.md` Dataview 인덱스 운용
- `docs/wiki/index.md` 상단에 세션 산출물 통합 섹션
- session-lifecycle step 5.5 자동화

### bobpullie/TWK 글로벌 (83a0e70)
- `scripts/normalize_session_frontmatter.py` — defaults fallback 포함 (441 LOC)
- `templates/session_artifacts.md.template` — Dataview 쿼리 템플릿
- `templates/wiki.config.json.template` — `session_artifacts` 기본 섹션
- `SKILL.md` — 보조 Operation 문서화 + trigger 3 종 추가

### 다른 에이전트 채택 경로
```bash
git -C ~/.claude/skills/TWK pull origin main
# wiki.config.json 에 session_artifacts 섹션 복사 (template 참고)
# folders[].path 를 본인 폴더 구조로 수정
# templates/session_artifacts.md.template → docs/session_artifacts.md 복사 + FROM 절 조정
python ~/.claude/skills/TWK/scripts/normalize_session_frontmatter.py --apply
```

## 관련 자료

- Raw: [[../../session_archive/20260422_session1_raw]]
- Handover: `handover_doc/2026-04-22_session41.md`
- Recap: `qmd_drive/recaps/2026-04-22_session41.md`
- Spec: `docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md`
- Plan: `docs/superpowers/plans/2026-04-22-session-artifacts-auto-indexing.md`
- Index: [[../../session_artifacts]]

## 후속 결정 대기

- **twk.css 글로벌 승격** — 4 신규 cssclass 의 CSS 스타일은 위상군 로컬만. TWK 에는 이름만 등록.
- **init_wiki.py 통합** — `session_artifacts.md.template` 자동 복사.
- **TWK pull 후 타 에이전트 채택 관찰** — S42 이후 P0.
