---
title: 세션 산출물 자동 인덱싱 설계
date: 2026-04-22
session: S41
status: Draft
scope: wiki+tooling
tags: [spec, twk, dataview, automation, session-artifacts]
cssclass: twk-decision
---

# 세션 산출물 자동 인덱싱 (Session Artifacts Auto-Indexing)

## 0. 배경

위상군 세션 중 생성되는 `.md` 문서는 4곳에 흩어진다:

| 폴더 | 성격 | 스키마 |
|------|------|--------|
| `docs/wiki/**` | L3 큐레이션 (Decisions / Concepts / Patterns / Principles / Postmortems) | 표준 frontmatter 존재 |
| `docs/session_archive/**` | L2 raw (기계 추출 Q&A) | frontmatter 없음 |
| `handover_doc/**` | 세션 핸드오버 | frontmatter 제각각 |
| `qmd_drive/recaps/**` | QMD session recap | frontmatter 제각각 |

**문제:** 새로 작성된 문서가 한 곳에 모여 보이지 않는다. TWK 인덱스(`docs/wiki/index.md`)는 L3 큐레이션만 커버하고, 나머지 3폴더는 파일 탐색기로만 접근 가능.

**목표:** "최근 작성 10 · 최근 수정 10" 을 4폴더 통합 범위로 자동 노출. Karpathy 3-Layer 철학의 L2/L3 구분은 유지.

## 1. 범위

**In scope:**
- `docs/wiki/**` + `docs/session_archive/**` + `handover_doc/**` + `qmd_drive/recaps/**` 의 `.md` 파일
- 자동 frontmatter 정규화 (누락 필드 보충, 기존 값 보존)
- Dataview 기반 인덱스 페이지 신설 + 기존 wiki index 에 embed

**Out of scope:**
- 자동 wikilink 역링크 생성 (Karpathy "억지로 쓰지 말 것" 원칙 — 승격은 수동 큐레이션)
- vault 전체 `.md` 확장 (CLAUDE.md 등 — TCL #29 "산출물 = 근거 추적" 경계 보호)
- 타 에이전트 배포 (TCL #93 — 위상군 로컬 검증 완료 후 별도 결정)

## 2. 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| D1 | 범위 = 4 폴더 (C안) | 세션 산출물 전체 통합 필요 |
| D2 | "연결" = 표시 + frontmatter 자동 주입 (B안) | 정렬/필터 품질 확보. cssclass 자동 태거 선례와 동형 |
| D3 | 인덱스 = 신규 `docs/session_artifacts.md` + 기존 wiki index 에 embed | 4폴더 중 3폴더가 wiki 외부 → 층위 분리 유지 |
| D4 | embed 방식 = transclusion `![[../session_artifacts]]` (α안) | 통합 뷰 + 독립 뷰 둘 다 제공. 링크만은 발견성 저하 |
| D5 | 시간 기준 = 작성 → frontmatter `date`, 수정 → `file.mtime` | 논리적 시점 / 물리적 수정 분리 |
| D6 | `docs/wiki/**` 는 주입 대상 제외 (검증만) | 이미 표준 스키마 존재 |
| D7 | 파일명 파싱 실패 fallback = `file.mtime` 날짜 부분 | 주입 건너뛰면 정렬 누락 → 데이터 보존 우선 |

## 3. 아키텍처

**2개의 직교 메커니즘:**

```
[Frontmatter Normalizer]         [Index Query]
      (쓰기, batch)                 (읽기, 실시간)
            |                           |
            v                           v
   frontmatter 보충            Dataview 쿼리 평가
            |                           |
            +--------- 독립 ------------+
```

- 둘은 **독립**. 스크립트 실패해도 쿼리는 동작 (단 정렬 정확도 저하)
- **Idempotent** — 스크립트 2회 실행해도 결과 동일
- **Polling 없음** — Obsidian Dataview 가 파일 변경 감지 자동 반영

## 4. Component 1 — Frontmatter Normalizer

### 4.1 파일

`scripts/normalize_session_frontmatter.py`

### 4.2 CLI

```bash
# dry-run (기본)
python scripts/normalize_session_frontmatter.py --dry-run

# 적용
python scripts/normalize_session_frontmatter.py --apply

# 특정 폴더만
python scripts/normalize_session_frontmatter.py --apply --only handover_doc
```

### 4.3 폴더별 주입 템플릿

| 폴더 | 파일명 패턴 | `date` 추출 | `type` | `cssclass` | `tags` | `session` |
|------|-----------|-------------|--------|------------|--------|-----------|
| `docs/session_archive/` | `YYYYMMDD_sessionN_raw.md` | `YYYYMMDD` → `YYYY-MM-DD` | `session-raw` | `twk-session-raw` | `[session, raw, L2]` | `S{N}` |
| `handover_doc/` | `YYYY-MM-DD_sessionN.md` | 그대로 | `handover` | `twk-handover` | `[session, handover]` | `S{N}` |
| `qmd_drive/recaps/` | `YYYY-MM-DD_sessionN.md` | 그대로 | `recap` | `twk-recap` | `[session, recap]` | `S{N}` |

### 4.4 동작 규약

1. `docs/wiki/**` 스캔 — **검증만** (필수 필드 `date` · `status` 존재 확인). 실패 시 warning (비차단).
2. 나머지 3 폴더 스캔 — 각 `.md` 에 대해:
   - frontmatter 블록(`---...---`) 없음 → 전체 주입
   - 있음 → 필드별 병합 규칙 적용:
     - **스칼라 (`date` · `type` · `cssclass` · `session`):** 이미 존재하면 **skip** (기존 값 보존). 없을 때만 템플릿 값 주입.
     - **배열 (`tags`):** **union 병합** — 기존 tags 에 템플릿 tags 중 누락분만 append. 기존 원소 제거/재정렬 금지.
3. 파일명 파싱 실패 시:
   - `date` → `file.mtime` 의 `YYYY-MM-DD` 부분
   - `session` → 생략 (nullable)
   - stderr 에 warning 로그
4. dry-run 모드: 각 파일에 대해 예정 변경을 unified diff 형식으로 출력, 파일은 수정 안 함.

### 4.5 Idempotency 검증

- 동일 파일에 스크립트 2회 연속 실행 → 2회차는 no-op
- git diff 로 1회차 후 변경만 보이고, 2회차 후 추가 변경 없음

## 5. Component 2 — `docs/session_artifacts.md`

### 5.1 frontmatter

```yaml
---
title: 위상군 — 세션 산출물
date: 2026-04-22
status: Active
cssclass: twk-session-index
tags: [index, session, artifacts]
---
```

### 5.2 본문 구조

```markdown
# 세션 산출물 (Session Artifacts)

> [!abstract]+ 범위
> **L2 raw** + **핸드오버** + **QMD recap** + **L3 wiki** 의 통합 타임라인.
> 4개 폴더의 최근 작성/수정 문서를 한 눈에.

## 최근 작성 10

​```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  date as "작성일",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT date DESC
LIMIT 10
​```

## 최근 수정 10

​```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") as "수정시각",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT file.mtime DESC
LIMIT 10
​```

## 폴더별 네비게이션

- [[wiki/index|L3 Wiki Index]] — 큐레이션된 지식
- `docs/session_archive/` — L2 raw (기계 추출)
- `handover_doc/` — 세션 핸드오버
- `qmd_drive/recaps/` — QMD recap
```

*(코드블록 fence 는 spec 이 렌더되지 않도록 zero-width 공백 포함)*

## 6. Component 3 — `docs/wiki/index.md` embed

`## 최근 변경` 섹션 **앞**에 신규 섹션 삽입:

```markdown
---

## 세션 산출물 (통합)

> [!tip] 4폴더 통합 타임라인
> 아래는 [[../session_artifacts]] 의 embed 입니다. 독립 열람도 가능.

![[../session_artifacts]]

---

## 최근 변경
...(기존 유지)
```

**기존 `## 최근 변경` (L3 wiki 한정 LIMIT 8) 유지 근거:** L2/handover/recap 노이즈 없이 큐레이션 흐름만 보는 채널을 보존.

## 7. Component 4 — 세션 종료 lifecycle 편입

`.claude/rules/session-lifecycle.md` 의 `5. LLM Wiki L2 추출` 직후 신규 step:

```
5.5. **세션 산출물 frontmatter 정규화:**
     python scripts/normalize_session_frontmatter.py --apply
     (L2 raw · handover · recap 의 frontmatter 자동 보충. idempotent — 재실행 안전)
```

## 8. Testing

### 8.1 Unit (Frontmatter Normalizer)

- **파일명 파싱 정상:** `20260420_session1_raw.md` → `date: 2026-04-20`, `session: S1`
- **파일명 파싱 실패:** `irregular_name.md` → `file.mtime` fallback, warning 로그
- **Idempotency:** 동일 파일 2회 apply → 2회차 no-op
- **기존 스칼라 값 보존:** frontmatter 에 이미 `date: 2026-04-15` 있으면 파일명 날짜가 달라도 덮어쓰지 않음
- **tags union:** 기존 `tags: [custom]` + 템플릿 `tags: [session, recap]` → `[custom, session, recap]` (기존 순서 보존 + 누락분 append)
- **dry-run vs apply:** dry-run 후 파일 mtime 불변, apply 후만 변경
- **폴더별 cssclass 매핑:** 3폴더 각각 올바른 cssclass 주입

### 8.2 Integration

1. 현존 파일 대상 `--dry-run` 실행 → diff 수동 검토
2. diff 이상 없으면 `--apply` → git diff 로 변경 확인
3. 재실행 `--apply` → no-op 확인 (idempotency)

### 8.3 Dataview / Obsidian

- `session_artifacts.md` 열어 쿼리 2개 정상 렌더링 (10건씩)
- `docs/wiki/index.md` 에서 embed (`![[..]]`) 정상 표시
- self-reference 필터 작동 (session_artifacts 자신이 쿼리 결과에 없음)
- cssclass 스타일 적용 확인 (`.obsidian/snippets/twk.css`)

## 9. 영향 분석

### 9.1 변경 파일

- **신규:** `scripts/normalize_session_frontmatter.py`, `docs/session_artifacts.md`
- **수정:** `docs/wiki/index.md` (embed 섹션 추가), `.claude/rules/session-lifecycle.md` (step 5.5 추가)
- **자동 수정 (스크립트 apply):** `docs/session_archive/**` · `handover_doc/**` · `qmd_drive/recaps/**` 의 frontmatter 누락 파일들

### 9.2 위험

- 기존 frontmatter 가 있는 파일에 대한 **기존 값 덮어쓰기** — 4.4 규약의 "절대 덮어쓰기 금지" 로 방지. Unit test 로 검증.
- Dataview 쿼리 실패 시 index 공백 — 쿼리 자체가 잘못되면 Obsidian 이 에러 표시. 복구 가능.
- 폴더 구조 변경 시 쿼리 깨짐 — `FROM` 절 경로 하드코딩. wiki.config.json 과의 동기화는 별도 이슈.

### 9.3 롤백

- 스크립트 apply 결과는 git revert 로 복구
- 인덱스 파일 2개는 단순 텍스트 — 삭제로 롤백
- session-lifecycle.md step 5.5 삭제로 자동화 해제

## 10. 미결정 / 후속

- **TWK-Global-Push 여부 (TCL #93):** 이 설계는 위상군 로컬 검증 단계. 5+ 세션 동안 문제 없으면 `bobpullie/TWK` 스킬로 승격 논의.
- **`wiki.config.json` 연동:** 현재 스크립트의 4폴더 경로가 하드코딩. 추후 config 로 이관 고려 (YAGNI — 지금은 불필요).
- **Daily Note 통합:** `docs/daily/` 와의 상호 임베드는 별도 과제 (S41 Task `inbox.md-Hook-Design` 과 연계 가능).
