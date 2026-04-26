---
date: 2026-04-26
status: Accepted
type: spec
project: twk
scope: multi-vault-aggregation
tags: [spec, twk, vault, multi-project, mobile, cloudflare]
cssclass: twk-spec
session: S43
resolved_at: 2026-04-27
---

# TWK Multi-Vault Aggregation — Design Spec

> **목표:** 종일군의 E:\ 하위 6개 활성 TWK 프로젝트를 단일 통합 Vault로 묶고, 모바일에서 인증 후 조회 가능한 정적 위키 사이트로 배포한다. 신규 프로젝트는 단일 명령으로 합류 가능한 확장형 구조.

## Context & Motivation

종일군은 6개 프로젝트(`DnT_WesangGoon`, `DnT_Fermion`, `MRV_DnT`, `01_houdiniAgent`, `00_unrealAgent`, `GCE`)를 동시 운영하며, 각 프로젝트는 독립 git repo + 독자 TWK 위키 + 핸드오버 문서를 갖는다. 데스크탑에서는 프로젝트별로 IDE/Obsidian을 전환해야 하고, 모바일/외부 환경에서는 위키 접근 자체가 불가능하다.

**해결할 문제:**
1. **단일 진입점 부재** — 어떤 프로젝트에 무엇이 있는지 한눈에 못 봄
2. **모바일 접근 불가** — 종일군이 외부에서 메모/결정 검색 불가
3. **확장성 결여** — 새 프로젝트 추가 시 매번 수작업
4. **TWK 코어와 통합 메커니즘 분리** — 통합 로직이 단일 프로젝트 로컬에 머물면 다른 프로젝트가 못 씀

## Non-Goals

- 모바일에서의 wiki 편집 (조회 전용)
- 6개 프로젝트의 git history 통합 (각 repo는 독립 유지)
- 실시간 양방향 sync (세션 종료 단위로 충분)
- 전체 코드베이스 통합 (TWK 산출물만 통합)
- 외부 사용자 공유 (종일군 1인 비공개 위키)

## Key Decisions

| 결정 | 선택 | 근거 |
|------|------|------|
| 통합 범위 | 6개 활성 프로젝트 | TWK 활성도 검증 완료, KnowledgeHub 제외 |
| 통합 모드 | Workspace Vault (junction 기반) | 기존 git repo 구조 0 변경 |
| 모바일/인증 | GitHub Private + Quartz + Cloudflare Access | 무료, 종일군 git 친숙도 활용 |
| Sync 트리거 | 세션 종료 자동 + 수동 명령 | 세션 종료가 wiki 변경의 90%+ 시점 |
| 통합 메커니즘 위치 | TWK 패키지 코어 (v0.4 신규 모듈) | 캐노니컬 배포로 6개 프로젝트 동시 업데이트 |
| TWK repo vs Vault repo | TWK = `bobpullie/TWK` (코드), Vault = `bobpullie/KJI_WIKI` (위키 mirror) | 책임 분리 — TWK는 위상군 push, KJI_WIKI는 vault_sync.py 자동 push |
| Quartz Dataview 처리 | `quartz-plugin-dataview` 채택 | 자체 변환 구현 불필요, 빌드 시점 처리 |
| 도메인 | `kji-wiki.pages.dev` | 비용 0, 추후 커스텀 도메인 추가 가능 |

---

## 1. TWK 패키지 확장 — `vault aggregator` 모듈

### 1.1. 신규 자산

`~/.claude/skills/TWK/` 패키지에 추가:

```
scripts/
├── vault_init.py            # 메타 vault 폴더 생성 + .obsidian 초기화
├── vault_join.py            # 새 프로젝트를 메타 vault에 등록 (junction 자동 생성)
├── vault_leave.py           # 프로젝트 제거 (junction 해제, 원본 무영향)
├── vault_sync.py            # junction → mirror repo 복사 + git push
├── vault_status.py          # 등록된 모든 프로젝트 상태 점검
├── vault_discover.py        # E:/ 하위 미가입 TWK 프로젝트 자동 탐색
└── session_end_hook.py      # 세션 종료 시 호출되는 통합 hook (normalize + sync)

templates/
├── vault.config.json.template       # 메타 vault 설정 스키마
├── vault_index.md.template          # 메인 인덱스 (Dataview)
└── page-templates/
    └── project_index.md.template    # 권장 프로젝트 인덱스 템플릿

references/
└── vault-aggregation.md     # 통합 vault 운영 매뉴얼
```

### 1.2. 버전 bump

TWK v0.3.x → **v0.4.0** (minor — 신규 기능 추가, 기존 wiki.config.json 호환 유지)

### 1.3. 메타 vault 설정 — `vault.config.json` (메타 vault 루트)

```json
{
  "version": "0.4",
  "vault_id": "kji-knowledge-vault",
  "vault_root": "E:/TWK_Vault",
  "mirror_root": "E:/KJI_WIKI",
  "mirror_remote": "https://github.com/bobpullie/KJI_WIKI.git",
  "auth": {
    "mobile_url": "kji-wiki.pages.dev",
    "provider": "cloudflare-access",
    "allowed_emails": ["blueitems7@gmail.com"]
  },
  "projects": [
    {
      "id": "wesang",
      "name": "DnT 위상군",
      "description": "Topological Systems Architect — DnT v3 메인 위상 설계",
      "root": "E:/DnT/DnT_WesangGoon",
      "wiki_path": "docs/wiki",
      "handover_path": "handover_doc",
      "session_archive_path": "docs/session_archive",
      "recap_path": "qmd_drive/recaps",
      "status": "Active",
      "tags": ["dnt", "core", "tems"],
      "joined_at": "2026-04-26"
    }
  ],
  "sync": {
    "trigger": "session_end + manual",
    "exclude_patterns": [".obsidian/workspace.json", "*.tmp", "__pycache__"]
  }
}
```

### 1.4. 각 프로젝트 `wiki.config.json` 확장 (1개 필드 추가)

```json
{
  "version": "1.2",
  "project_id": "wesang",
  "vault_membership": {
    "vault_id": "kji-knowledge-vault",
    "joined_at": "2026-04-26"
  }
}
```

각 프로젝트는 자기가 속한 메타 vault만 선언. 실제 연결 정보는 메타 vault `vault.config.json` 이 단일 진실 원천.

### 1.5. 디렉토리 구조

```
E:/TWK_Vault/                        # 메타 Obsidian Vault (편집/조회)
├── .obsidian/                       # Vault 설정 (테마, 플러그인, workspace)
├── vault.config.json                # 단일 진실 원천 (TWK가 읽음)
├── index.md                         # 메인 인덱스 (vault.config.json 기반 동적 Dataview)
├── _meta/
│   ├── templates/                   # TWK 템플릿 사본 (vault_init.py가 복사)
│   ├── projects.md                  # vault_sync.py가 자동 생성 (Dataview-readable)
│   ├── lint_log.md
│   └── new_project_guide.md         # 신규 프로젝트 추가 Quick reference
├── projects/                        # junction (vault.config.json.projects[]에서 자동 생성)
│   ├── wesang/      → E:/DnT/DnT_WesangGoon/docs/wiki/
│   ├── fermion/     → E:/QuantProject/DnT_Fermion/docs/wiki/
│   ├── mrv/         → E:/DnT/MRV_DnT/docs/wiki/
│   ├── houdini/     → E:/01_houdiniAgent/docs/wiki/
│   ├── unreal/      → E:/00_unrealAgent/docs/wiki/
│   └── gce/         → E:/GCE/docs/wiki/
├── handovers/                       # junction (자동)
│   └── (6개 프로젝트의 handover_doc/)
└── session_archive/                 # junction (해당 프로젝트가 있을 때만)
    └── (wesang, houdini, gce)

E:/KJI_WIKI/                         # Git push 대상 (vault_sync.py가 mirror)
├── .git/                            # GitHub private repo `bobpullie/KJI_WIKI` (통합 Vault 전용)
├── (Vault 구조와 동일하나 junction 대신 실제 파일)
└── quartz.config.ts                 # Quartz 사이트 설정 (quartz-plugin-dataview 활성화)
```

**원칙:**
- Vault root는 git repo가 **아님** (junction 안의 파일은 각자 원본 repo가 추적)
- Mirror repo (`bobpullie/KJI_WIKI`) 는 단방향 (Vault → Mirror), **통합 Vault 위키 전용** — TWK 패키지 자체는 별도 repo (`bobpullie/TWK`)
- `_meta/` 안의 인덱스/템플릿은 vault에서 직접 편집 + mirror로 복사되는 유일한 영역
- **통합 Vault 의 git push 책임자:** 6개 프로젝트 중 마지막으로 세션 종료하는 에이전트가 자동 수행 (session_end_hook)

---

## 2. Mirror Sync 동작 + 세션 종료 통합

### 2.1. `vault_sync.py` 알고리즘

```
1. vault.config.json 로드
2. 각 project 순회:
   a. junction → 실제 파일 경로 해석 (Win32 GetFinalPathNameByHandle)
   b. 원본 git repo에서 변경 감지 (git status, last commit hash)
   c. wiki/handover/session_archive/recap 4개 폴더를 mirror_root/projects/{id}/ 로 복사
      (rsync 스타일, 변경분만, --delete-extra)
      exclude: vault.config.json.sync.exclude_patterns
3. _meta/templates/, index.md, vault.config.json 도 mirror로 복사
4. _meta/projects.md 자동 생성 (vault.config.json → Dataview-readable)
5. mirror_root에서 git diff 확인:
   a. 변경 없음 → 종료 (no-op)
   b. 변경 있음 → git add . / commit "vault sync: {timestamp} ({N} projects)" / push
6. CF Pages가 push 감지 → Quartz 빌드 자동 트리거
```

### 2.2. 세션 종료 통합 — `session_end_hook.py`

세션 종료 시 호출 (각 프로젝트 `.claude/rules/session-lifecycle.md` step 5.6):

```bash
python ~/.claude/skills/TWK/scripts/session_end_hook.py --auto
```

수행 단계:
1. `normalize_session_frontmatter.py --apply` (기존 step 5.5 흡수)
2. `vault_sync.py --vault-id <id>` (NEW) — 자기 프로젝트만 mirror 갱신
3. **KJI_WIKI mirror commit + push** — 모든 프로젝트의 누적 변경분 일괄 push
4. 결과 로그 출력

**Push 책임 정책:** 6개 프로젝트 중 어느 에이전트든 세션 종료 시 push 수행. 즉 "마지막 세션 종료 에이전트"가 그 시점까지 누적된 모든 변경을 KJI_WIKI 에 반영. 중복 push는 git 자체에서 no-op (변경 없으면 commit 안 됨).

`--auto` 모드는 `wiki.config.json.vault_membership` 을 읽어 자동 분기:
- 있으면 → vault sync 수행
- 없으면 → skip (vault 미가입 프로젝트 영향 0)

### 2.3. 수동 명령

```bash
twk vault sync                    # 현재 디렉토리 vault.config.json 자동 탐색
twk vault sync --dry-run          # 변경 미리보기
twk vault sync --project wesang   # 특정 프로젝트만
twk vault status                  # 7개 프로젝트 sync 상태
```

### 2.4. 충돌 / 실패 처리

| 케이스 | 처리 |
|--------|------|
| Mirror에서 직접 편집한 변경 발견 | abort + 경고. `--force-overwrite` 명시 시에만 진행 |
| 원본/mirror가 다른 git 호스트 | 두 repo 독립 — sync는 file copy 수준 |
| Junction 깨짐 (원본 폴더 이동/삭제) | vault_status.py가 감지 + `health="broken"` 표시 + 해당 프로젝트만 skip |
| git push 실패 | mirror commit은 유지, 다음 sync에서 재시도 |
| Network down | 로컬 mirror만 갱신, push 보류 |

---

## 3. 메인 인덱스 + 프로젝트 인덱스

### 3.1. 메인 인덱스 (`E:/TWK_Vault/index.md`)

**렌더링 전략:**
- 데스크탑 Obsidian: Dataview 동적 쿼리
- 모바일 Quartz: `vault_sync.py --build-static` 가 빌드 시 정적 markdown table로 pre-render

**구성:**
```markdown
---
title: KJI Knowledge Vault
cssclass: twk-index
---

# 🧭 KJI Knowledge Vault
> Triad Chord Studio 통합 지식 베이스 — 6개 프로젝트 단일 진입점

## 📊 프로젝트 현황
[Dataview: _meta/projects → name(link), status, description, last_activity, page_count]

## 📝 최근 등록된 작업 (전 프로젝트, 7일)
[Dataview: projects/** WHERE date >= today-7d, LIMIT 15]

## 🔄 최신 핸드오버 (각 프로젝트 1건)
[Dataview: handovers/** type=handover, GROUP BY 프로젝트, LIMIT 6]

## 🔧 새 프로젝트 추가
`twk vault join --vault-id kji-knowledge-vault --project-root <경로>`
```

### 3.2. `_meta/projects.md` 자동 생성

vault.config.json 변경 시 vault_sync.py가 Dataview-readable 형식으로 풀어줌:

```markdown
---
auto_generated: true
generated_by: vault_sync.py
generated_at: 2026-04-26T18:00:00
---

## wesang
- name:: DnT 위상군
- project_id:: wesang
- description:: Topological Systems Architect ...
- status:: 🟢 Active
- last_activity:: 2026-04-22
- page_count:: 27
```

→ 메인 index의 Dataview가 이 파일 읽음. 프로젝트 추가/제거가 vault.config.json 한 곳에서만 일어나고 인덱스 자동 반응.

### 3.3. 프로젝트 인덱스 — `projects/{id}/index.md`

**원칙:** 각 프로젝트가 자기 `docs/wiki/index.md` 를 그대로 소유. Junction을 통해 메타 vault에서 자동 노출. 메인 인덱스 첫 컬럼 클릭 → `projects/wesang/` → 프로젝트 인덱스로 이동.

**TWK 권장 템플릿** (강제 X — 통일감 원하는 프로젝트만 채택):
```markdown
---
title: <프로젝트명> Wiki
cssclass: twk-project-index
project_id: <id>
status: Active
description: <한 줄>
date: YYYY-MM-DD
---

# <프로젝트명>
> <한 줄 소개>

## 📍 현재 마일스톤
## 📚 핵심 개념 [Dataview: projects/<id>/concepts]
## ⚖️ 주요 결정 [Dataview: projects/<id>/decisions SORT date DESC]
## 🔄 핸드오버 [link to handovers/<id>/]
```

### 3.4. Quartz Dataview 처리 — `quartz-plugin-dataview` 채택

Quartz는 기본 Dataview 미지원이나, **`quartz-plugin-dataview`** 커뮤니티 플러그인을 통해 빌드 시점에 Dataview 쿼리를 정적 markdown으로 변환.

- vault_sync.py 자체 구현 불필요 (단순화)
- `quartz.config.ts` 의 plugins 배열에 등록
- 메인 인덱스의 dataview 블록은 데스크탑 Obsidian과 모바일 Quartz 사이트 양쪽에서 동일 결과
- Phase 0 prototyping 시 플러그인 호환성 검증 (현재 vault.config.json 의 `_meta/projects.md` 형식 등)
- 만약 플러그인이 특정 쿼리 미지원 → 해당 쿼리만 `_meta/projects.md` 처럼 pre-rendered 형식으로 fallback

### 3.5. 종일군 4가지 요구 매핑

| 요구 | 구현 |
|------|------|
| 각 프로젝트 간단한 소개 | `vault.config.json.projects[].description` |
| 진행 현황 | `status` + `last_activity` (auto-detect) |
| 최근 등록된 작업들 | Dataview FROM "projects" WHERE date >= 7일 전 |
| 최신 핸드오버들 | Dataview FROM "handovers" GROUP BY 프로젝트 |
| 클릭 → 프로젝트 인덱스 | 메인 테이블 첫 컬럼 wikilink `projects/{id}/` |

---

## 4. Quartz + Cloudflare Access 배포 파이프라인

### 4.1. 정적 사이트 생성기 — Quartz v4 + `quartz-plugin-dataview`

선택 근거: Obsidian-first wikilink/embed/callout 자동 변환, 가벼움, 무료. lunr.js 기반 full-text search 내장.

**한계 + 대응:**
| 한계 | 대응 |
|------|------|
| Dataview 기본 미지원 | `quartz-plugin-dataview` 커뮤니티 플러그인 채택 |
| 플러그인 특정 쿼리 미지원 | 해당 쿼리만 vault_sync.py 가 정적 markdown 으로 fallback |

### 4.2. 빌드 파이프라인

CF Pages는 GitHub repo 직접 연결 → push 자동 빌드. 별도 GitHub Actions 불필요.

```
[종일군 세션 종료] (어느 프로젝트든)
   ↓
session_end_hook.py --auto
   ↓
vault_sync.py
   ├─ 6개 프로젝트 wiki junction → mirror (E:/KJI_WIKI/) 복사
   ├─ _meta/projects.md 자동 생성 (vault.config.json → Dataview-readable)
   └─ git commit + push → bobpullie/KJI_WIKI
        ↓
[Cloudflare Pages 자동 빌드]
   ├─ npx quartz build (quartz-plugin-dataview 가 빌드 시 dataview 변환)
   ├─ public/ 디렉토리 생성
   └─ kji-wiki.pages.dev 배포
```

CF Pages 설정:
- Build command: `npx quartz build`
- Output directory: `public`
- Build 시간: 약 30~60초 (300+ 파일)

### 4.3. Cloudflare Access 인증

Free plan: 50 users 무료. 종일군 1명 등록.

설정:
1. **Access Application 생성**
   - Domain: `kji-wiki.pages.dev`
   - Type: Self-hosted
2. **Policy**
   - Action: Allow
   - Include: `Emails: blueitems7@gmail.com`
3. **Identity Provider**
   - Google OAuth (1순위) + One-time PIN 백업
4. **Session Duration**
   - 30 days (모바일 매번 로그인 회피)

**모바일 사용자 경험:**
1. `twk-vault.pages.dev` 접속
2. CF Access 게이트 → Sign in with Google
3. 종일군 계정 인증 → Quartz 사이트 진입

### 4.4. 도메인 옵션

| 옵션 | 비용 | URL |
|------|------|-----|
| 종일군 보유 도메인 | $0 (보유 시) | `vault.<own-domain>` |
| Pages 기본 서브도메인 | $0 | `kji-wiki.pages.dev` |

**결정 완료 (S43, 2026-04-27):** Pages 기본 서브도메인 `kji-wiki.pages.dev` 사용. 추후 커스텀 도메인 필요 시 5분 작업으로 추가 가능.

### 4.5. 비용

| 항목 | 비용 |
|------|------|
| GitHub private repo | $0 |
| Cloudflare Pages | $0 (월 500 builds) |
| Cloudflare Access | $0 (50 users free) |
| 도메인 | 선택사항 |
| **총** | **$0/월** |

### 4.6. 보안 / 실패

- **mirror repo 노출:** GitHub private + 2FA. PAT 유출 시 즉시 rotate.
- **CF Access 토큰 탈취:** 30일 세션 만료 + 디바이스 등록 정책 추가 가능.
- **빌드 실패:** CF Pages 이메일 알림. 마지막 성공 빌드 유지 (사이트 안 죽음).
- **Dataview 변환 버그:** vault_sync.py fallback으로 raw 코드 블록 출력 (사이트는 빌드되되 그 섹션만 plaintext).

---

## 5. 신규 프로젝트 추가 — `twk vault join` UX

### 5.1. 명령 인터페이스

```bash
# 대화형 (권장)
twk vault join

# 명시적 (CI/스크립트)
twk vault join \
  --vault-id kji-knowledge-vault \
  --project-root E:/NewAgent \
  --project-id newagent \
  --description "Unreal 에이전트 — RTS 프로토타입" \
  --status Active \
  --tags "unreal,prototype"

# 사전 점검
twk vault join --dry-run --project-root E:/NewAgent
```

### 5.2. 대화형 모드 (6단계)

```
[1/6] 메타 vault 자동 탐색 (vault_id 또는 vault_root 명시도 가능)
[2/6] 현재 프로젝트 정보 수집 (wiki.config.json, 폴더 존재, git remote)
[3/6] 메타데이터 입력 (description, status, tags)
[4/6] Junction 미리보기 + 사용자 확인
[5/6] 적용 (트랜잭션):
  - 프로젝트 wiki.config.json 에 vault_membership 추가
  - 메타 vault vault.config.json 에 projects[] 항목 추가
  - Junction 생성 (mklink /J)
  - _meta/projects.md 갱신
[6/6] 다음 단계 안내 (Obsidian 새로고침, sync 명령)
```

### 5.3. 트랜잭션 안전성

```python
def vault_join(project_root, vault_root, **opts):
    # 1. 사전 검증 (실패 시 변경 0)
    assert_project_has_wiki_config(project_root)
    assert_no_duplicate_id(vault_root, opts['project_id'])
    assert_no_existing_junction(vault_root / 'projects' / project_id)

    # 2. staging
    project_cfg_patch = build_wiki_config_patch(opts)
    vault_cfg_patch   = build_vault_config_patch(opts)
    junctions         = plan_junctions(project_root, vault_root, opts)

    # 3. 미리보기 + 확인
    if not opts.get('yes'):
        show_preview(...)
        if not confirm(): abort()

    # 4. 적용 (try/except 롤백)
    try:
        backup_paths = backup([project_cfg_path, vault_cfg_path])
        apply_json_patch(project_cfg_path, project_cfg_patch)
        apply_json_patch(vault_cfg_path, vault_cfg_patch)
        for src, dst in junctions:
            create_junction(src, dst)
        regenerate_meta_projects(vault_root)
    except Exception:
        rollback(backup_paths)
        remove_partial_junctions()
        raise
```

### 5.4. Edge Cases

| 케이스 | 처리 |
|--------|------|
| `wiki.config.json` 없음 | 안내 + `--auto-init` 옵션 (init_wiki.py 자동 실행) |
| `docs/wiki/` 폴더 없음 | 자동 생성 + 빈 index.md 시드 |
| project_id 중복 | abort + 충돌 정보 표시 |
| Junction 대상 이미 존재 | abort, `--force` 명시 시에만 진행 |
| Windows junction 권한 부족 | 안내 (관리자 또는 개발자 모드) + symlink fallback |
| 비-Windows | symlink fallback (별도 PR 예정) |
| 다른 드라이브 | 동일 드라이브 권장 메시지 |

### 5.5. 역방향 — `twk vault leave`

```bash
twk vault leave --project-id newagent
```
- 프로젝트 wiki.config.json 의 vault_membership 제거
- 메타 vault projects[] 에서 항목 제거
- Junction 삭제 (rmdir, **원본 폴더 무영향**)
- _meta/projects.md 재생성
- 다음 sync 시 mirror 에서도 제거

### 5.6. 상태 점검 — `twk vault status`

```
[kji-knowledge-vault] (E:/TWK_Vault)
Mirror: bobpullie/twk-vault
Last sync: 2026-04-26 14:32 (3시간 전)
Pending changes: 12 files (5 projects)

Projects:
  ✓ wesang     │ 27 pages  │ 84 handovers │ 4d ago    │ healthy
  ✓ fermion    │ 26 pages  │ 27 handovers │ 22h ago   │ healthy
  ...
  ✗ obsolete   │  -- pages │ -- handovers │ --        │ broken
```

### 5.7. 자동 탐색 — `twk vault discover`

```bash
twk vault discover --search-root E:/
```
→ E:/ 하위에서 wiki.config.json 가진 폴더 탐색, 메타 vault 미가입 프로젝트 나열 + 일괄 join 옵션.

---

## 6. 마이그레이션 — 6개 프로젝트 첫 합류

### 6.1. 원칙

1. 6개 프로젝트 모두 활성 — 작업 중단 0
2. 단계적 진행 — phase 검증 후 다음
3. dry-run 우선
4. 자동 hook 마지막 활성화

### 6.2. Phase 시퀀스

```
Phase 0: TWK v0.4 vault aggregator 모듈 개발 (별도 implementation plan)
   ↓
Phase 1: 메타 vault 초기화
   - twk vault init --vault-id kji-knowledge-vault --vault-root E:/TWK_Vault
   - 검증: Obsidian으로 빈 vault 열기
   ↓
Phase 2: Pilot — 1개 프로젝트 합류 (00_unrealAgent — 위험 적음)
   - twk vault join --project-root E:/00_unrealAgent
   - 검증: 페이지 표시, wikilink, 원본 편집 → vault 반영
   - 실패 시: twk vault leave --project-id unreal
   ↓
Phase 3: 나머지 5개 일괄 합류
   - twk vault discover --search-root E:/
   - twk vault join --batch <yaml-config>
   - 검증: twk vault status 7개 healthy
   ↓
Phase 4: 첫 수동 mirror + 로컬 Quartz 빌드
   - bobpullie/KJI_WIKI 가 비어있다면 첫 commit 으로 main branch 생성
   - twk vault sync (첫 push)
   - cd E:/KJI_WIKI && npm install + quartz-plugin-dataview 설치
   - npx quartz build && npx quartz preview
   - 검증: localhost:8080 사이트 + dataview 렌더링 확인
   ↓
Phase 5: Cloudflare Pages + Access 연결
   - CF Pages 프로젝트 생성 → bobpullie/KJI_WIKI 연결 → kji-wiki.pages.dev 자동 발급
   - CF Access Application (Domain: kji-wiki.pages.dev) + Email policy (blueitems7@gmail.com)
   - 모바일 테스트 (게이트 → Google 인증 → 진입)
   ↓
Phase 6: 세션 종료 자동 hook 활성화
   - 6개 프로젝트 .claude/rules/session-lifecycle.md 에 step 5.6 추가
   - 다음 세션 종료 1회 모니터링
```

### 6.3. 롤백 안전성

| Phase | 롤백 비용 | 원본 영향 |
|-------|---------|---------|
| 1 | `rm -rf E:/TWK_Vault` | 0 |
| 2 | `twk vault leave` | wiki.config.json 1줄 추가만 — 즉시 원복 |
| 3 | `twk vault leave` x5 | wiki.config.json x5에 1줄씩 — 즉시 원복 |
| 4 | mirror repo 삭제 | 0 |
| 5 | CF Application 삭제 | 0 |
| 6 | session-lifecycle.md 1줄 제거 | 0 |

**원본 6개 프로젝트는 어느 phase에서도 wiki.config.json 의 `vault_membership` 1개 필드 추가 외에 변경 없음.**

### 6.4. 도메인 결정 — 결정 완료

`kji-wiki.pages.dev` (Pages 기본 서브도메인). 추후 필요 시 커스텀 도메인 추가 (5분 작업).

### 6.5. 예상 소요 시간

| Phase | 위상군 | 종일군 |
|-------|--------|--------|
| 0 (개발) | 4~6h | - |
| 1 (init) | 5m | 5m |
| 2 (Pilot) | 2m | 15m |
| 3 (5개) | 10m | 10m |
| 4 (빌드) | 15m | 10m |
| 5 (CF) | 20m | 10m |
| 6 (hook) | 10m | 다음 세션 |
| **총** | **약 5~7h** | **약 1h** |

### 6.6. 발견 가능 문제

| 문제 | 대응 |
|------|------|
| Wikilink 충돌 (예: `[[index]]` 다중 존재) | Obsidian 폴더 컨텍스트 우선. 충돌 시 절대경로 권장 |
| 글로벌 Dataview 쿼리 결과 변동 | 각 프로젝트는 `FROM "projects/<id>"` 로 scope 제한 |
| 거대 binary asset | exclude 패턴 또는 Git LFS |
| Quartz 빌드 시간 초과 (CF 20분 한도) | 300파일 1분 미만 예상 — 1만 파일 넘으면 재고 |

---

## Resolved Questions (S43, 2026-04-27)

1. **TWK upstream repo 권한** ✓ — `bobpullie/TWK` 는 위상군이 직접 commit/push. 통합 Vault 위키는 별도 repo `bobpullie/KJI_WIKI` 사용. 책임 분리:
   - `bobpullie/TWK` ← TWK 패키지 코드 (v0.4 vault aggregator 모듈 포함). 위상군 push.
   - `bobpullie/KJI_WIKI` ← 6개 프로젝트 통합 mirror (vault_sync.py 가 push). 마지막 세션 종료 에이전트가 책임.
2. **도메인** ✓ — `kji-wiki.pages.dev` (Pages 기본 서브도메인) 사용.
3. **Quartz Dataview 처리** ✓ — `quartz-plugin-dataview` 커뮤니티 플러그인 채택. 자체 구현 불필요. 플러그인 미지원 쿼리만 fallback.
4. **모바일 latency** ✓ — 즉시 반영 불필요. 약 1~2분 latency (sync → push → CF 빌드 → 배포) 허용.

## Success Criteria

- [ ] TWK v0.4 가 캐노니컬 패키지에 release되어 모든 프로젝트가 `git pull` 한 번으로 vault aggregator 사용 가능
- [ ] 6개 프로젝트가 모두 메타 vault에 합류하고 데스크탑 Obsidian에서 단일 vault로 표시
- [ ] 메인 인덱스에서 4가지 정보(소개/현황/최근작업/최신핸드오버) 모두 표시
- [ ] 모바일 브라우저에서 CF Access 인증 후 위키 조회 가능
- [ ] 세션 종료 시 자동 sync → mirror push → CF 빌드 → 모바일 반영 (총 약 2분)
- [ ] 신규 프로젝트가 `twk vault join` 한 줄로 추가되고 메인 인덱스에 자동 노출
- [ ] 6개 프로젝트의 기존 작업 흐름에 0 영향 (각 repo 독립 유지)

## Out of Scope (이후 spec)

- TWK v0.4 모듈의 implementation plan (Phase 0) — 본 spec 이후 writing-plans로 별도 작성
- LiveSync 등 양방향 실시간 sync (필요 시 v0.5)
- 외부 사용자 협업 기능
- Atlas/multi-agent 통합 (별도 도메인)
