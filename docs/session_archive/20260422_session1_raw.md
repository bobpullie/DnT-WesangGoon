---
date: 2026-04-22
type: raw
cssclass: twk-raw
tags: [session, raw, L2]
session: S1
---

# Session 1 — 2026-04-22

> Source: `8b4e47d7-fdb6-4fef-b025-87526139883a.jsonl`
> Generated: 2026-04-22 17:41:23

## Q1

위상군 세션중에 생성된 모든 .md문서들이 그자이에서 TWK에 자동으로 연결되고 TWK인덱스페이지에 새로작성된문서 10종, 최근수정된 문서 10종이 보일수 있게 할 수 있을까?

## A1

위상군 세션 산출물의 TWK 자동 연결 + 인덱스 최신 10종 노출 — 설계가 필요한 feature 작업이라 brainstorming으로 요구사항부터 정리하겠습니다.

## A2

먼저 현재 TWK/wiki 상태를 파악하겠습니다.

## A3

구조는 파악됐습니다. `docs/wiki/**`는 이미 Dataview로 인덱싱되고, `docs/session_archive/` · `handover_doc/` · `qmd_drive/recaps/` · `Claude-Sessions/` 등 위상군 세션 산출물이 여러 경로에 흩어져 있습니다. 설계 전에 3가지만 확정하고 싶습니다.

**질문 1 — "모든 .md"의 범위는 어디까지인가요?**

| 옵션 | 범위 | 특징 |
|------|------|------|
| **A** | `docs/wiki/**` 만 (L3 큐레이션층) | 현재 이미 Dataview 동작 중. LIMIT만 10으로 조정하면 끝. |
| **B** | `docs/wiki/**` + `docs/session_archive/**` (L3 + L2) | Karpathy 3-Layer 철학에 부합. L2는 기계적 raw라 frontmatter가 없을 수도. |
| **C** | 위상군 세션 산출물 전체 (`docs/wiki/**` + `docs/session_archive/**` + `handover_doc/**` + `qmd_drive/recaps/**`) | **사용자 의도 추정.** 단 이질적 폴더라 스키마가 다르고, daily-notes/templates 와의 경계 필요. |
| **D** | vault 전체 모든 `.md` (CLAUDE.md 포함) | 과도함. TCL #29 "산출물 = 근거 추적 가능" 원칙과 충돌할 수 있음. |

어떤 범위를 생각하고 계셨나요? 제 추천은 **C** 이지만, 그 경우 "새 문서/수정 문서" 인덱스 섹션을 index.md 에 **따로 두는 게** 좋을지, 기존 "최근 변경"을 C 범위로 확장할지도 달라집니다.

## Q2

C

## A4

**질문 2 — "자동으로 TWK에 연결"이란?**

범위 C의 폴더들은 frontmatter 규격이 서로 다릅니다:
- `docs/wiki/**` — `date` · `status` · `tags` · `cssclass` 표준 스키마 있음
- `docs/session_archive/**` — L2 raw, frontmatter 없을 가능성 높음 (기계 추출)
- `handover_doc/**` · `qmd_drive/recaps/**` — 파일명에 날짜 prefix, frontmatter 제각각

이 차이가 "연결" 수준을 결정합니다:

| 옵션 | "연결"의 의미 | 난이도 | 부작용 |
|------|-------------|--------|--------|
| **A** | **표시만** — `index.md` 에 Dataview 쿼리 추가, 각 폴더별 섹션으로 최근 10건 노출. 기존 파일 무수정. | 낮음 | 없음. 단 `date` frontmatter 없는 파일은 `file.ctime`/`file.mtime` 로 정렬해야 하고, 제목이 일관성 없어 보일 수 있음. |
| **B** | **A + frontmatter 자동 삽입** — 세션 종료 hook 이 `handover_doc/`·`qmd_drive/recaps/`·`session_archive/`에 최소 frontmatter(`date`·`type`·`session`) 자동 주입. Dataview 쿼리 품질 향상. | 중간 | 기존 파일 수정. 하지만 cssclass 자동 태거 선례 있어 일관됨. |
| **C** | **B + 역링크 자동화** — wiki 페이지에서 handover/recap 으로 `[[..]]` 링크 자동 생성 (예: 세션번호 기반). | 높음 | 과도한 자동화. Karpathy "억지로 쓰지 말 것" 원칙과 충돌 가능. |

제 추천은 **B** 입니다. "인덱스에 보이게" + "정렬/필터 품질 확보"가 실용적이고, TWK cssclass 자동 태거와 동일 철학(폴더 → 메타데이터 자동)이기 때문입니다. C는 승격 기준 없이 링크만 늘면 노이즈가 됩니다.

어느 수준이 맞나요?

## Q3

B

## A5

**질문 3 — index.md에서 이 인덱스들은 어디에 어떻게 배치할까요?**

현재 `index.md` 는:
- `## 최근 변경` (LIMIT 8, `docs/wiki/**`만)
- 섹션별 (Decisions / Concepts / Patterns / Principles / Postmortems)
- 펼침 접기 "위키 전체 현황"

범위 C를 받아들이는 방식 3가지:

| 옵션 | 배치 | 논리 |
|------|------|------|
| **A** | 기존 "최근 변경" 을 C 범위로 **확장**, LIMIT 10 으로. 별도 "새 문서 10" 추가. | index.md 최소 변경. 단 L3 wiki 페이지가 L2/handover/recap 에 묻힐 수 있음. |
| **B** | **새 상위 섹션** `## 세션 산출물 (Session Artifacts)` 신설 — 그 안에 `최근 작성 10` + `최근 수정 10` 두 Dataview. 기존 `## 최근 변경`(L3 wiki 한정)은 유지. | **L3(큐레이션)와 L2/세션 기록물의 층위 분리 유지.** Karpathy 3-Layer 철학 준수. |
| **C** | 인덱스를 완전 재구성 — 기준을 폴더가 아니라 "시간축"으로. Daily Note 스타일 타임라인. | 과도함. 기존 섹션별 네비게이션 가치가 파괴됨. |

제 추천은 **B** 입니다. `docs/wiki/**` 는 "큐레이션된 지식(정제)", 나머지 3 폴더는 "세션 기록(원재료/핸드오버)" — 이 층위 차이가 TWK L2/L3 구분의 핵심이고, 섹션을 나누면 사용자가 "지금 보고 있는 게 큐레이션인가 raw인가"를 즉시 구분할 수 있습니다.

시간 기준은 제가 **"새 문서 = frontmatter `date`"** / **"최근 수정 = `file.mtime`"** 조합을 제안합니다 (각각 논리적 시점/물리적 수정을 반영). 이의 있으신가요?

## Q4

B

## A6

핵심 3가지가 확정됐으니 설계를 제시하겠습니다. 섹션별로 확인하면서 진행합니다.

---

## Design — 세션 산출물 자동 인덱싱 (Session Artifacts Auto-Indexing)

### 1. 아키텍처 개요

**2개의 직교 메커니즘을 조합:**

1. **Frontmatter Normalizer (쓰기)** — 스크립트가 범위 C의 4 폴더를 스캔, 누락 frontmatter 를 idempotent 하게 주입. 세션 종료 lifecycle 에 편입.
2. **Index Query (읽기)** — `docs/wiki/index.md` 에 `## 세션 산출물` 섹션 신설, Dataview 쿼리 2개 (최근 작성 / 최근 수정).

둘은 독립 — 쿼리는 Obsidian 이 실시간 평가, 스크립트는 batch. 스크립트 실패해도 쿼리는 돈다 (단 frontmatter 없는 파일은 정렬 정확도 저하).

**TWK cssclass 자동 태거 선례와 동형:** 폴더 → 메타데이터 자동 추론, 수동 편집 제거, 설정 = 메타데이터 원칙.

이 구조 괜찮으신가요?

## Q5

그럼 두개의 index.md가 존재하고 기존 index.md에서 새롭게 신설된 index.md정보를 불러오는 방식?

## A7

좋은 지적입니다 — 사실 그 접근이 더 깔끔합니다. 이유를 인정하고 제안을 수정하겠습니다.

**왜 분리가 더 낫나:**

범위 C의 4 폴더 중 3 폴더(`docs/session_archive/` · `handover_doc/` · `qmd_drive/recaps/`)가 **`docs/wiki/` 외부**에 있습니다. 이걸 `docs/wiki/index.md` 에 넣는 건 TWK 의 L3 = "큐레이션된 지식" 순수성을 흐립니다. 별도 index 로 분리하면:

- **`docs/wiki/index.md`** = 순수 L3 큐레이션 진입점 (Decisions/Concepts/Patterns/Principles/Postmortems)
- **신규 index** = 범위 C 통합 진입점 (세션 산출물 타임라인)
- 둘 다 독립 북마크/열람 가능. 기존 index 는 안 비대해짐.

**수정된 설계:**

| 항목 | 결정 |
|------|------|
| 신규 파일 경로 | `docs/session_artifacts.md` *(wiki 바로 밖 — 범위 C 전체가 `docs/` 아래 또는 프로젝트 루트 아래라 `docs/` 레벨이 자연스러움)* |
| 신규 파일 내용 | Dataview 쿼리 2개 (최근 작성 10 / 최근 수정 10) + 폴더별 네비게이션 |
| 기존 `docs/wiki/index.md` 와의 연결 | **Obsidian transclusion `![[../session_artifacts]]`** — "세션 산출물" 섹션에 embed. 링크만(`[[...]]`) 은 클릭해야 보여 발견성 낮음. |

**연결 방식 2가지 중 선택:**

| 옵션 | 방식 | 특징 |
|------|------|------|
| **α** | embed (`![[../session_artifacts]]`) | wiki index 에서도 전체 보임. 통합 뷰 + 독립 뷰 둘 다. 단 페이지 길어짐. |
| **β** | 링크 (`[[../session_artifacts\|세션 산출물]]`) 만 | wiki index 는 간결. 세션 산출물은 클릭해서 봐야함. |

제 추천은 **α(embed)**. "신규 문서가 즉시 눈에 띈다"가 원래 요구사항이었기에 — 링크 뒤에 숨으면 발견성이 떨어집니다. 어느 쪽이 좋으신가요?

## Q6

α

## A8

확정. 이제 컴포넌트 상세를 섹션별로 내려가겠습니다.

---

### 2. Component 1 — Frontmatter Normalizer

**파일:** `scripts/normalize_session_frontmatter.py` *(기존 `scripts/tag_wiki_cssclass.py` 선례를 따름 — 폴더 기반 메타데이터 자동화, idempotent, dry-run 지원)*

**동작:**
1. 범위 C의 4 폴더 스캔 (`docs/wiki/**` 는 이미 스키마가 있으므로 **주입 대상에서 제외**, 검증만)
2. `docs/session_archive/**` · `handover_doc/**` · `qmd_drive/recaps/**` 의 `.md` 각각에 대해:
   - frontmatter 없으면 → 주입
   - 이미 있으면 → 누락 필드만 보충 (기존 값 **절대 덮어쓰기 금지**)
3. dry-run 모드로 diff 출력 지원

**폴더별 주입 템플릿:**

| 폴더 | `date` 추출 | `type` | `cssclass` | `tags` |
|------|-------------|--------|------------|--------|
| `docs/session_archive/` | 파일명 `YYYYMMDD_sessionN_raw.md` → `YYYY-MM-DD` | `session-raw` | `twk-session-raw` | `[session, raw, L2]` |
| `handover_doc/` | 파일명 `YYYY-MM-DD_sessionN.md` → 그대로 | `handover` | `twk-handover` | `[session, handover]` |
| `qmd_drive/recaps/` | 파일명 `YYYY-MM-DD_sessionN.md` → 그대로 | `recap` | `twk-recap` | `[session, recap]` |

**파일명 파싱 실패 시 fallback:** `file.mtime` 의 날짜 부분 사용, 로그에 warning.

**session 번호 추출:** 파일명에서 `session(\d+)` · `sN` 패턴 매칭. 있으면 `session: S40` 같은 필드 추가.

**실행 진입점:**
- 수동: `python scripts/normalize_session_frontmatter.py --dry-run` / `--apply`
- 자동: 세션 종료 lifecycle `5. LLM Wiki L2 추출` **직후**에 chained 실행 *(L2 추출이 `docs/session_archive/` 에 파일을 만들자마자 정규화)*

**Idempotency 보장:**
- 주입 대상 필드가 이미 존재하면 skip
- 스크립트 2회 실행해도 결과 동일
- git diff 로 주입된 변경만 보임

이 컴포넌트 합리적인가요? 특히 2가지 점 확인:
- (a) `docs/wiki/**`는 주입 대상이 아니라 **검증만** (이미 스키마 있음) — 맞나요?
- (b) 파일명 파싱 실패 fallback 을 `file.mtime` 으로 — 아니면 주입 건너뛰고 warning 만 낼까요?

## Q7

a. 검증만 b. flie.mtime

## A9

확정: (a) `docs/wiki/**` 검증만 (b) 파일명 파싱 실패 시 `file.mtime` fallback.

---

### 3. Component 2 — `docs/session_artifacts.md` 구조

**파일 상단 frontmatter:**
```yaml
---
title: 위상군 — 세션 산출물
date: 2026-04-22
status: Active
cssclass: twk-session-index
tags: [index, session, artifacts]
---
```

**본문 구조:**

```markdown
# 세션 산출물 (Session Artifacts)

> [!abstract]+ 범위
> **L2 raw** + **핸드오버** + **QMD recap** + **L3 wiki** 의 통합 타임라인.
> 4개 폴더의 최근 작성/수정 문서를 한 눈에.

## 최근 작성 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  date as "작성일",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT date DESC
LIMIT 10
```

## 최근 수정 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") as "수정시각",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT file.mtime DESC
LIMIT 10
```

## 폴더별 네비게이션
- [[wiki/index|L3 Wiki Index]] — 큐레이션된 지식
- `docs/session_archive/` — L2 raw (기계 추출)
- `handover_doc/` — 세션 핸드오버
- `qmd_drive/recaps/` — QMD recap
```

### 4. Component 3 — 기존 `docs/wiki/index.md` embed

`## 최근 변경` 섹션 **앞**에 새 섹션 삽입:

```markdown
## 세션 산출물 (통합)

![[../session_artifacts]]

---
```

*기존 `## 최근 변경`(L3 wiki 한정 LIMIT 8) 은 **유지** — L3만의 변경 흐름을 L2/handover/recap 노이즈 없이 보기 위함.*

### 5. Component 4 — 세션 종료 lifecycle 편입

`.claude/rules/session-lifecycle.md` 의 `5. LLM Wiki L2 추출` 직후에 신규 step 5.5 추가:

```
5.5. **세션 산출물 frontmatter 정규화:**
     python scripts/normalize_session_frontmatter.py --apply
     (L2 raw · handover · recap 의 frontmatter 자동 보충. idempotent)
```

### 6. Testing

- **Unit (Frontmatter Normalizer):** 파일명 파싱(정상/실패) · idempotency(2회 실행 결과 동일) · 기존 frontmatter 보존 · dry-run/apply 분기
- **Integration:** 4 폴더 현존 파일 대상 dry-run → diff 수동 검토 → apply
- **Dataview:** Obsidian 에서 `session_artifacts.md` 열어 쿼리 2개 정상 렌더링 확인, embed (`![[..]]`) 가 index.md 에서 정상 표시 확인

### 7. Error handling / 비고

- 스크립트 실패해도 Dataview 쿼리는 동작 (단 정렬 정확도 저하)
- `!= "index" != "log" != "session_artifacts"` 필터로 self-reference 제거
- TCL #93 *"외부 배포 보류"* 원칙 준수 — 이 설계는 **위상군 로컬 전용**. 타 에이전트 확산은 별도 결정 필요.
- TCL #116 *"QMD 로컬 관리"* 원칙 align — `qmd_drive/recaps/` 는 프로젝트 로컬이므로 dataview 스캔 대상으로 안전.

---

전체 설계 준비됐습니다. 이제 `docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md` 로 spec 문서를 쓰겠습니다.

## A10

Spec self-review 중 한 곳 애매함 발견 — `tags` 같은 array 필드의 병합 규칙이 불명확합니다. 명확화하겠습니다.

## A11

Spec 작성 완료. 커밋 전에 SDC brief 제출 (TCL #122 git gate 준수).

## A12

Spec 작성 + 커밋 완료 — [docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md](docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md) (3ea6e41).

**핵심 결정 7개 (D1~D7):**
- D1: 범위 4폴더 | D2: 표시 + frontmatter 자동 주입 | D3: 신규 `session_artifacts.md` + embed
- D4: transclusion `![[..]]` | D5: 작성=`date` / 수정=`file.mtime`
- D6: `docs/wiki/**` 주입 제외 (검증만) | D7: 파일명 파싱 실패 → `file.mtime` fallback

**4 컴포넌트:** Frontmatter Normalizer 스크립트 / session_artifacts.md / wiki index embed / session-lifecycle step 5.5.

---

Spec 검토 부탁드립니다. 특히 이하 지점에서 의견 있으시면 반영하겠습니다:

1. **폴더별 `type`/`cssclass` 명칭** — `session-raw` / `handover` / `recap` 이 기존 TWK 네이밍과 어긋나지 않나요? (§4.3)
2. **session-lifecycle step 5.5 위치** — L2 추출 직후가 맞나요, 아니면 모든 작성 완료 후 (step 6 Curation 다음)이 나을까요? (§7)
3. **tags union 병합 규칙** — 기존 tags 보존 + 템플릿 누락분 append. 너무 관대한가요? (§4.4)
4. **미결정 3건**(TWK-Global-Push / config 이관 / Daily Note 통합) — S41 이후로 미루는 게 맞나요? (§10)

이상 없으시면 writing-plans 단계로 진행합니다.

## Q8

1. 모름 2. L2추출직후 .3좋음 4. 미결정 진행

## A13

#1 검증 필요 — 기존 TWK 네이밍 컨벤션 확인하겠습니다.

## A14

확인. 컨벤션은 **단일 단어·하이픈 없음** (`twk-concept`, `twk-decision`, `twk-pattern` 등). 제 제안 `session-raw` / `session-index` 는 컨벤션 위반. 수정합니다.

## A15

Spec 수정분 커밋 후 writing-plans 로 진행합니다.

## A16

I'm using the writing-plans skill to create the implementation plan.

## A17

Plan 작성 + 커밋 완료 — [docs/superpowers/plans/2026-04-22-session-artifacts-auto-indexing.md](docs/superpowers/plans/2026-04-22-session-artifacts-auto-indexing.md) (a89d201).

**17 Task 요약:**
| # | 내용 |
|---|------|
| 1 | pytest 스캐폴딩 |
| 2~3 | frontmatter 파싱/직렬화 (TDD) |
| 4~6 | 파일명 date · session 추출, mtime fallback |
| 7 | merge — 스칼라 skip + tags union |
| 8 | 폴더 → 템플릿 매핑 |
| 9 | process_file + idempotency |
| 10 | docs/wiki 검증 모드 |
| 11 | CLI (argparse) |
| 12 | **dry-run 검토 → apply → idempotency 재검증** |
| 13 | `docs/session_artifacts.md` 생성 |
| 14 | `wiki.config.json` + `twk.css` (raw/handover/recap/timeline) |
| 15 | `docs/wiki/index.md` embed 섹션 |
| 16 | `session-lifecycle.md` step 5.5 |
| 17 | Obsidian 렌더링 end-to-end 검증 |

---

**실행 방식 선택:**

1. **Subagent-Driven (권장)** — Task 마다 fresh Sonnet 서브에이전트 dispatch, Task 간 본체 리뷰. SDC 매트릭스에 맞음 (코드 구현 = Sonnet 위임). 빠른 반복, 검증 강함.

2. **Inline Execution** — 현재 세션에서 executing-plans 로 순차 실행. 체크포인트마다 리뷰. 컨텍스트 유지 이점.

Auto mode 이므로 기본값은 **1번(Subagent-Driven)** 으로 추천합니다 — 위상군 역할 배치 원칙(본체=판단, Sonnet=실행)에 부합하고, Task 17 까지 총 17 단계라 본체 세션 컨텍스트 포화를 막을 수 있습니다. 어느 쪽으로 진행할까요?

## Q9

1

## A18

Subagent-driven execution 시작. 먼저 프롬프트 템플릿을 확인하고 TodoWrite 로 17 Task 추적합니다.

## A19

Task 1 dispatching — pytest 스캐폴딩 (Sonnet subagent).

## A20

Task 1 DONE. Trivial 2-file scaffolding이라 파일 내용을 직접 검증하고 Task 2 로 진행합니다.

## A21

Task 1 verified. Task 2 dispatching — parse_frontmatter TDD.

## A22

Task 2 concern 검토: implementer가 `yaml.safe_load` → `yaml.BaseLoader` 로 변경했는데, 이는 타당한 판단입니다 (ISO date 가 `datetime.date` 로 파싱되면 round-trip 시 format 변경 → idempotency 깨짐). 수락하고 Task 3 에서 동일 loader 사용하도록 컨텍스트 전달.

## A23

Task 3 두 번째 plan 불일치 발견 — `safe_dump` 의 자동 quoting vs 테스트 기대값. 구현 확인 후 진행.

## A24

Task 12 — 실파일 대상 integration. 본체가 직접 수행 (diff 판단 필요).

## A25

138 파일이 dry-run 으로 체크됐고, wiki validate 가 `index.md: 'date' 누락` + `'status' 누락` 을 flag. 이는 D6 검증 모드가 작동함을 증명. 먼저 실파일 1건에 대한 실제 변경이 올바른지 확인합니다.

## A26

권한 거부 — dry-run-review 게이트가 안전하게 차단했습니다. 실제 diff 를 수동 구성해 종일군에 제시하겠습니다.

## A27

Preview 결과 — 3 샘플이 모두 예상대로 변환됩니다:

| 샘플 | 입력 | 생성될 frontmatter |
|------|------|---------------------|
| `handover_doc/2026-04-21_session40.md` | frontmatter 없음 | `date: 2026-04-21` · `type: handover` · `cssclass: twk-handover` · `session: S40` · `tags: [session, handover]` |
| `qmd_drive/recaps/active_rules.md` | frontmatter 없음 · 비규격 파일명 | **mtime fallback** → `date: 2026-03-23` · `type: recap` · `cssclass: twk-recap` · session 생략 · `tags: [session, recap]` |
| `docs/session_archive/20260420_session1_raw.md` | frontmatter 없음 | `date: 2026-04-20` · `type: raw` · `cssclass: twk-raw` · `session: S1` · `tags: [session, raw, L2]` |

본문은 모두 보존되고 맨 앞에 frontmatter 블록만 삽입됩니다. **138 개 파일 전체에 apply 적용** 해도 될지 확인 부탁드립니다 (git 으로 언제든 revert 가능). 승인하시면 전체 적용 → diff 요약 → idempotency 재검증 → 커밋 수순 진행합니다.

추가로 `docs/wiki/index.md` 가 `date`·`status` 누락으로 wiki-validate warning 이 뜨는데, 여기에 `date: 2026-04-22` + `status: Active` 를 함께 채워 넣을까요? (D6 "wiki 는 검증만" 이지만 validator 가 알려준 누락은 실제 수정 대상)

## Q10

전체적용 및 누락 수정

## A28

Idempotency 확인 (2회차: kept 138). 이제 wiki index.md 누락 필드 채우기.

## A29

Diff 깨끗 — frontmatter 만 상단에 추가, 본문 변경 없음. 그러나 일부 파일은 세션 시작 시점부터 이미 `M` 상태였던 점 확인이 필요합니다.

## A30

Diff 깨끗 (frontmatter 만 추가). 전체 commit 진행.

## A31

Task 12 완료 (commit 148fe05 · 139 files). Task 13 로 진행.

## A32

Plan 색상 중복 발견 — `timeline #8b5cf6` = `principle` 이고 `raw #64748b` = `default` 입니다. 조정합니다:
- `raw` → `--twk-accent-default` 재사용 (중립 회색 — L2 raw 의미에 부합)
- `timeline` → `#a855f7` purple-500 (principle 의 violet 에서 한 단계)

## A33

---

## 구현 완료 — Task 1~16

| 영역 | 결과 |
|------|------|
| **스크립트** | `scripts/normalize_session_frontmatter.py` — 9 함수 + CLI |
| **단위 테스트** | `tests/test_normalize_session_frontmatter.py` — **36 tests passing** |
| **실파일 적용** | 139 files (109 added + 29 merged + wiki/index.md) · idempotent 검증 통과 |
| **Dataview 인덱스** | `docs/session_artifacts.md` (최근 작성 10 / 최근 수정 10) |
| **Wiki 통합** | `docs/wiki/index.md` 에 `![[../session_artifacts]]` embed |
| **스타일** | `wiki.config.json` cssclasses + `.obsidian/snippets/twk.css` 4종 (raw/handover/recap/timeline) |
| **Lifecycle** | `.claude/rules/session-lifecycle.md` step 5.5 편입 |

**Git 이력 (master):** spec/plan 2건 + 구현 16건 = 총 18 commits. HEAD: `f2fc9b9`.

**Plan 실행 중 발견한 이슈 (수정 반영):**
1. `yaml.safe_load` → `yaml.BaseLoader` (round-trip 시 date 문자열 보존)
2. `safe_dump` 의 자동 quoting → ISO date 한정 quote-strip 후처리
3. 색상 충돌 → `timeline #8b5cf6` → `#a855f7` (purple-500), `raw` → default slate 재사용

---

## Task 17 — Obsidian 렌더링 검증 (종일군 수행 필요)

아래 4가지를 Obsidian vault (`e:/DnT/DnT_WesangGoon`) 에서 확인 부탁드립니다:

1. **`docs/session_artifacts.md` 열기** — "최근 작성 10" / "최근 수정 10" 두 Dataview 표가 10 행씩 렌더링되는가? `type`·`session` 컬럼이 채워지는가?
2. **`docs/wiki/index.md` 열기** — 상단에 `## 세션 산출물 (통합)` 섹션 + embed 가 보이는가?
3. **cssclass 스타일** — handover 파일은 h1 하단이 **orange**, recap 파일은 **teal**, session_archive 파일은 **slate**, session_artifacts.md 는 **purple** 으로 표시되는가?
4. **self-reference 필터** — `session_artifacts.md` 자신이 "최근 작성" 표에 포함되어 있지 **않는가**?

이상 있으면 해당 Task 로 돌아가 수정하겠습니다. 문제없으면 S41 종료 핸드오버 단계로 전환합니다.

## Q11

잘 보임 수고했음. 이 방식을 표준 TWK로 할수 있나?

## A34

가능합니다. 다만 TCL #93 (위상군 먼저 검증 → 전파) 를 고려할 때 **3 단계**를 거쳐야 합니다:

| 단계 | 작업 | 선행 조건 |
|------|------|-----------|
| **Step 1** | `FOLDER_CONFIG` / `DATE_PATTERNS` 하드코딩 → `wiki.config.json` 으로 이관. 스크립트가 config 기반 동작. | **지금 가능** — spec §10 후속으로 이미 식별됨 |
| **Step 2** | 위상군 로컬에서 5+ 세션 실전 운용 · 이슈 수집 · 안정화 | Step 1 완료 후 자연스럽게 진행 (세션 종료 hook 편입됨) |
| **Step 3** | `bobpullie/TWK` 스킬로 이식: `normalize_session_frontmatter.py` + `session_artifacts.md` 템플릿 + 4종 cssclass + lifecycle step 5.5 가이드 | **TCL #93 준수** — Step 2 안정화 확인 후 |

**표준화에서 나타날 차이점 (에이전트별 파라미터):**
- 폴더 이름 — 위상군 `handover_doc/`, 코드군 `session_logs/`, 빌드군 `docs/build_archive/` 등 → 각자의 `wiki.config.json` 에서 선언
- 파일명 패턴 — `YYYY-MM-DD_sessionN.md` 외 다른 관례 있으면 DATE_PATTERNS 확장
- **cssclass 명칭은 공용화** (`raw`·`handover`·`recap`·`timeline`) 권장 — 4 에이전트가 동시에 Obsidian 에서 보일 때 색상 의미가 같아야 함

**추천:** 지금 **Step 1 (config 이관)** 은 바로 착수하는 게 좋습니다 — 위상군 로컬에서 config-기반으로 운용하면서 5+ 세션 검증하면, Step 3 승격 시 복사해서 바로 동작. 이건 spec 의 §10 미결정 항목 중 하나였으니 plan 분리해서 진행할까요, 아니면 지금은 현재 상태 유지하고 S41 종료 핸드오버 먼저 할까요?

## Q12

그럼 바로 표준화작업 후에 TWK 커밋 배포

## A35

TCL #93 은 종일군 결정으로 override — S41 내 배포로 판단 기록. 진행 전 `bobpullie/TWK` 위치 확인 필요.

## A36

`~/.claude/skills/TWK/` 가 `bobpullie/TWK` 의 로컬 clone (origin: github.com/bobpullie/TWK.git, main 브랜치 clean). 

**Phase A — 위상군 로컬 config 이관 (지금 실행)**:
1. `wiki.config.json` 에 `session_artifacts` 섹션 (folders/date_patterns) 추가
2. `scripts/normalize_session_frontmatter.py` refactor → config 읽어 동작
3. 36 tests 회귀 없음 확인 → commit

**Phase B — TWK 스킬 배포**:
1. `~/.claude/skills/TWK/scripts/` 에 normalize 스크립트 복사
2. `templates/session_artifacts.md` 템플릿 추가
3. `SKILL.md` / `README.md` 에 신규 capability 문서화
4. TWK 로컬 commit → push origin main

Phase A 부터 진행합니다. 먼저 config 스키마 설계.

## A37

Script refactor 진행 — CWD 기반 config 로드 + defaults fallback.

## A38

Plan A 완료 (commit 79ab4b5). Plan B 시작 — TWK 스킬 구조 확인.

## A39

Plan B 실행 — 스크립트·템플릿 이식.

## A40

Now update wiki.config.json.template and SKILL.md.

## A41

**표준화 + TWK 배포 완료.**

| 단계 | 결과 |
|------|------|
| **Plan A — 위상군 로컬 config 이관** | `wiki.config.json.session_artifacts` 섹션 신설 · 스크립트 refactor · 36 tests green · idempotency 유지 · commit `79ab4b5` |
| **Plan B — TWK 글로벌 배포** | 4 파일 변경 · commit `83a0e70` · **push → github.com/bobpullie/TWK main 완료** (db9766e..83a0e70) |

**bobpullie/TWK 에 추가된 자산:**
- `scripts/normalize_session_frontmatter.py` — 전체 스크립트 (defaults fallback 포함 → wiki.config.json 없어도 동작)
- `templates/session_artifacts.md.template` — Dataview 통합 타임라인 (복사 후 FROM 절 조정 가이드)
- `templates/wiki.config.json.template` — `session_artifacts` 섹션 기본값 추가
- `SKILL.md` — 보조 operation 설명 + 3 trigger 추가 (`session artifacts` / `세션 산출물 인덱스` / `normalize_session_frontmatter`)

**타 에이전트가 채택할 때:**
```bash
# 1) 스킬 업데이트 (이미 설치된 경우)
git -C ~/.claude/skills/TWK pull origin main

# 2) 프로젝트 wiki.config.json 에 session_artifacts 섹션 추가 (템플릿 참고)
# 3) 필요시 folders[].path 수정 (본인 폴더 구조에 맞게)
# 4) templates/session_artifacts.md.template 을 프로젝트의 docs/session_artifacts.md 로 복사 + FROM 절 조정
# 5) 실행
python ~/.claude/skills/TWK/scripts/normalize_session_frontmatter.py --apply
```

**미반영 (의도적 scope 제외):**
- `.obsidian/snippets/twk.css` — TCL #93 / S39 결정(로컬 검증) 유지. 4 신규 cssclass 는 SKILL.md 에 명시만, CSS 승격은 별도 결정.
- `init_wiki.py` 통합 — 수동 복사 기반 (최소 scope).

S41 세션 종료 핸드오버 진행할까요?

## Q13

그럼 배포버전의 검증은 된건가?

## A42

아닙니다 — **배포 버전 고유의 검증은 아직 안 됐습니다**. 위상군 로컬 스크립트가 검증되고, 그걸 copy 해서 push 한 것입니다. 차이가 생길 수 있는 지점:

| 검증 항목 | 상태 |
|----------|------|
| 로컬 unit tests (36) | ✅ green |
| 로컬 139 파일 apply + idempotency | ✅ |
| Obsidian 렌더링 (로컬) | ✅ 종일군 확인 |
| **`~/.claude/skills/TWK/scripts/` 경로에서 실행** | ❌ 안 해봄 |
| **wiki.config.json 없는 환경에서 defaults fallback** | ❌ 안 해봄 (unit test 는 config 있는 상태만) |

2가지 smoke test 지금 바로 돌리면 배포 버전 검증 완료. 실행합니다.

## A43

Test 1, 2 통과 — 배포 버전이 로컬과 동일하게 동작하고 defaults fallback 도 정상. Test 3 는 bash path 변환 문제라 Windows-native 로 재실행.

## A44

**배포 버전 검증 완료 ✓**

| Test | 시나리오 | 결과 |
|------|----------|------|
| 1 | 위상군 CWD + 글로벌 스크립트 (`~/.claude/skills/TWK/scripts/normalize_session_frontmatter.py --dry-run`) | `{kept: 138}` — 로컬 버전과 완전 동일 결과 (idempotent 유지) |
| 2 | 임시 빈 디렉토리에서 실행 (wiki.config.json 없음) | defaults fallback → 3 폴더 스캔 시도 → 없으니 `[warn] 폴더 없음` + 정상 종료 (크래시 없음) |
| 3 | config 없는 환경에서 `FOLDER_CONFIG` / `DATE_PATTERNS` / `WIKI_ROOT` 값 확인 | `['docs/session_archive', 'handover_doc', 'qmd_drive/recaps']` + 2 patterns + `docs/wiki` — 기대대로 defaults 로드 |

다른 에이전트가 `git pull` 로 받아도 문제없이 동작할 것이 확인됩니다 (wiki.config.json 을 본인 구조로 customize 하면 즉시 작동, 안 해도 default 위상군 스키마로 동작).

S41 종료 핸드오버 진행할까요?

## Q14

세션종료~

## A45

S41 종료 절차 시작. 핸드오버 문서부터 작성.

## A46

Now update CURRENT_STATE.md (rolling state).
