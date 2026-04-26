---
date: 2026-04-27
status: Draft
type: concept
project: twk
scope: vault-aggregation
tags: [concept, twk, vault, multi-project, junction]
cssclass: twk-concept
session: S44
---

# Multi-Vault Aggregation (TWK v0.4+)

> **정의:** 여러 독립 TWK 프로젝트의 wiki/handover/session_archive 산출물을 단일 통합 Obsidian Vault 로 결합하되, 각 프로젝트의 git repo 와 디렉토리 구조는 0 변경하는 패턴.

## 핵심 원칙

### 1. 각 프로젝트는 자기 wiki를 그대로 소유
- 각 프로젝트 repo (예: `E:/DnT/DnT_WesangGoon`) 의 `docs/wiki/` 는 단일 진실 원천
- 메타 vault 는 그 위에 얹힌 view 일 뿐 — 별도 데이터 복제 없음 (junction 기반)

### 2. junction = 데스크탑 view, mirror = 모바일/배포
- **데스크탑 Obsidian Vault** (`E:/TWK_Vault/`): junction 으로 6개 프로젝트 wiki 통합 view 제공
- **Mirror repo** (`E:/KJI_WIKI/`): junction 안의 실제 파일을 복사한 git repo. GitHub push 후 Cloudflare Pages 빌드.
- 두 폴더는 **단방향 (Vault → Mirror)**. Mirror 직접 편집 금지.

### 3. 단일 진실 원천 = `vault.config.json`
- 메타 vault 루트의 `vault.config.json` 이 등록된 프로젝트 리스트, mirror remote, 인증 정보 단일 보유
- Vault 구조의 모든 파생물 (`_meta/projects.md` Dataview 인덱스, mirror 디렉토리 구조) 은 이 파일에서 자동 생성
- 새 프로젝트 추가 = `vault.config.json.projects[]` 에 항목 추가 + junction 생성

### 4. 각 프로젝트는 자기 vault 멤버십을 선언
- 각 프로젝트의 `wiki.config.json` 에 `vault_membership: { vault_id, joined_at }` 필드 1개 추가
- 이 필드 존재 = 세션 종료 시 자동 sync 대상
- 필드 부재 = vault aggregator 영향 0 (격리)

### 5. Push 책임 = 마지막 세션 종료 에이전트
- 6개 프로젝트 중 어느 에이전트든 세션 종료 시 `vault_sync.py` 자동 실행
- 누적된 모든 변경분을 KJI_WIKI mirror 로 일괄 push
- 중복 push 는 git 자체에서 no-op

## 구성 요소 (TWK v0.4+ 패키지)

| 컴포넌트 | 역할 |
|---------|------|
| `vault_init.py` | 메타 vault 폴더 + `vault.config.json` 생성 |
| `vault_join.py` | 프로젝트 합류 (junction 자동 생성, 트랜잭션 보장) |
| `vault_leave.py` | 프로젝트 제거 (junction 해제, 원본 무영향) |
| `vault_sync.py` | junction → mirror 복사 + git commit + push |
| `vault_status.py` | 프로젝트별 healthy/broken 점검 |
| `vault_discover.py` | 미가입 TWK 프로젝트 자동 탐색 |
| `session_end_hook.py` | 세션 종료 시 normalize + sync 통합 호출 |
| `_vault_common.py` | config 헬퍼 (load/save vault & wiki configs) |
| `_vault_junction.py` | Win32 mklink/J 래퍼 (POSIX symlink fallback) |

## 디렉토리 모델

```
E:/TWK_Vault/                    ← 메타 Obsidian Vault (편집/조회)
├── vault.config.json            ← 단일 진실 원천
├── index.md                     ← 메인 인덱스 (Dataview)
├── _meta/projects.md            ← vault.config.json 자동 풀이 (Dataview-readable)
├── projects/
│   ├── wesang/    → junction → E:/DnT/DnT_WesangGoon/docs/wiki/
│   └── ... (6개)
├── handovers/                   ← junction (각 프로젝트 handover_doc)
└── session_archive/             ← junction (해당 프로젝트가 있을 때만)

E:/KJI_WIKI/                     ← Git push 대상 (vault_sync.py 가 mirror)
├── .git/                        ← bobpullie/KJI_WIKI
├── (Vault 구조와 동일하나 junction 대신 실제 파일)
└── quartz.config.ts             ← Quartz 사이트 설정
```

## 모바일 접근

1. 종일군 모바일 브라우저 → `kji-wiki.pages.dev` 접속
2. Cloudflare Access 게이트 → "Sign in with Google"
3. `blueitems7@gmail.com` 인증 → Quartz 사이트 진입
4. 메인 인덱스 → 프로젝트별 카드 클릭 → 해당 프로젝트 인덱스 → wiki 페이지

## 확장성

새 프로젝트 추가 = 한 줄:
```bash
twk vault join --vault-id kji-knowledge-vault --project-root E:/NewAgent
```
→ `wiki.config.json` 에 vault_membership 추가, `vault.config.json` 에 항목 추가, junction 2~3개 자동 생성, `_meta/projects.md` 자동 갱신, 메인 인덱스 Dataview 가 자동 인식 (코드 수정 불필요).

## 비교: 다른 multi-project wiki 패턴

| 패턴 | 장점 | 단점 |
|------|------|------|
| **Junction Vault Aggregation (TWK v0.4)** | 기존 repo 0 변경, 단일 Vault view, 모바일 mirror 별도 | Win32 의존 (POSIX는 symlink fallback) |
| Monorepo 통합 | 단일 git push | 기존 6개 repo 분리 깨짐 |
| Git Submodule | 단일 명령으로 모든 데이터 fetch | submodule 운영 비용, sync 까다로움 |
| Obsidian Multi-Vault Search 플러그인 | 사용자 액션 필요 없음 | Vault 간 wikilink 끊김, 통합 인덱스 X |

## 위상수학적 동형

multi-vault aggregation 은 본질적으로 **콘텐츠 데이터 (각 프로젝트 wiki) 와 view (메타 vault) 의 분리** — DBMS 의 view 와 동일 구조. View 는 메타데이터 (`vault.config.json`) 만 보유, 실제 데이터는 base table (각 프로젝트 git repo) 에 위치. View 변경이 base table 에 영향 없음.

## 참조

- 결정: [[../decisions/2026-04-27_twk-multi-vault-architecture]]
- Spec: [[../../superpowers/specs/2026-04-26-twk-multi-vault-aggregation-design]]
- Plan: [[../../superpowers/plans/2026-04-27-twk-v0.4-vault-aggregator]]
- 핵심 개념 (TWK 자체): [[TWK]] · [[../../wiki/concepts/Obsidian_as_IDE]]
