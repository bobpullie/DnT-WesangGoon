---
date: 2026-04-27
status: Accepted
type: decision
project: twk
scope: vault-aggregation
tags: [decision, twk, vault, multi-project, mobile, cloudflare]
cssclass: twk-decision
session: S44
---

# TWK Multi-Vault Aggregation Architecture

> S44 결정 — 6개 활성 TWK 프로젝트를 단일 통합 Obsidian Vault로 묶고 GitHub mirror + Cloudflare Pages 로 모바일 접근 가능한 위키 사이트 배포.

## 결정

### 통합 모드: Workspace Vault (junction 기반)
- **선택:** Windows `mklink /J` junction 으로 6개 프로젝트의 `docs/wiki/` 를 단일 메타 Vault 에 연결
- **이유:** 기존 6개 git repo 구조 0 변경. 각 프로젝트가 자기 wiki 소유 유지. Obsidian 은 단일 Vault 로 인식.
- **대안 기각:**
  - A (물리 통합 / Monorepo): 기존 워크플로우 파괴
  - C (Git Submodule): 운영 비용 큼 (commit 두 번, sync 까다로움)

### 모바일/인증: GitHub Private + Quartz + Cloudflare Access
- **선택:** Mirror repo `bobpullie/KJI_WIKI` → Cloudflare Pages → `kji-wiki.pages.dev` → Cloudflare Access (이메일 화이트리스트)
- **이유:** 무료 ($0/월), 종일군 git 친숙도 활용, Quartz가 Obsidian wikilink 자동 변환, CF Access 가 Google OAuth 게이트 제공
- **인증 정책:** `blueitems7@gmail.com` 단독 화이트리스트, 30일 세션
- **대안 기각:**
  - Obsidian Sync 공식: $5/월
  - Self-hosted LiveSync: 서버 운영 부담

### Repo 책임 분리: TWK ≠ KJI_WIKI
- **`bobpullie/TWK`** ← TWK 패키지 코드 (v0.4 vault aggregator 모듈 포함). 위상군 직접 push.
- **`bobpullie/KJI_WIKI`** ← 6개 프로젝트 통합 위키 mirror (vault_sync.py 자동 push). **마지막 세션 종료 에이전트가 push 책임** (어느 프로젝트 에이전트든).
- **이유:** TWK는 코드/스킬, KJI_WIKI는 데이터/콘텐츠. 격리하여 backup·permission·release cadence 독립.

### 통합 메커니즘 위치: TWK 패키지 코어 (v0.4 신규 모듈)
- **선택:** vault aggregator 를 TWK 패키지 자체에 7개 신규 스크립트 (`vault_init/join/leave/sync/status/discover/session_end_hook`) + 2개 헬퍼 (`_vault_common`, `_vault_junction`) 로 추가.
- **이유 (종일군 지적):** 일회성 통합이 아닌 확장 가능한 구조 필요. 캐노니컬 패키지 배포로 6개 프로젝트가 `git pull` 한 번에 동시 업데이트. 새 프로젝트는 `twk vault join` 한 줄로 합류.
- **버전:** TWK v0.3.x → **v0.4.0** (minor bump, 기존 wiki.config.json 호환 유지)

### Sync 트리거: 세션 종료 자동 + 수동 명령 (Hybrid)
- **자동:** session_end_hook 이 normalize_session_frontmatter + vault_sync 통합 실행. `wiki.config.json.vault_membership` 있으면 sync, 없으면 skip.
- **수동:** `twk vault sync` 즉시 실행
- **이유:** 세션 종료가 wiki 변경의 90%+ 시점. 종일군 별도 명령 익히지 않아도 자동 동작.

### 도메인: kji-wiki.pages.dev
- **선택:** Cloudflare Pages 기본 서브도메인 (무료)
- **추후:** 커스텀 도메인 필요 시 5분 작업으로 추가 가능

### Quartz Dataview: 커뮤니티 플러그인 채택
- **선택:** `quartz-plugin-dataview`
- **이유:** 자체 정적 변환 구현 부담 회피. 빌드 시점 처리.

### 모바일 latency: 즉시 반영 불필요
- 약 1~2분 (sync → push → CF 빌드 → 배포) 허용

## 통합 범위 (6개 활성 프로젝트)

| 프로젝트 | 위치 | wiki | handover |
|---------|------|------|----------|
| DnT 위상군 | E:/DnT/DnT_WesangGoon | 27 | 84 |
| DnT Fermion (Quant) | E:/QuantProject/DnT_Fermion | 26 | 27 |
| MRV 빌드군 | E:/DnT/MRV_DnT | 19 | 0 |
| 01_houdiniAgent | E:/01_houdiniAgent | 16 | 44 |
| 00_unrealAgent | E:/00_unrealAgent | 11 | 34 |
| GCE | E:/GCE | 0 | 6 |

**제외:** KnowledgeHub (종일군 명시 결정).

## 산출물

- Spec: [[../../superpowers/specs/2026-04-26-twk-multi-vault-aggregation-design]] (`5d6b0fe`)
- Plan: [[../../superpowers/plans/2026-04-27-twk-v0.4-vault-aggregator]] (`667538b`, 21 task TDD)
- 구현 (S44 진행): TWK worktree `~/.claude/skills/TWK-v0.4-wt`, branch `v0.4-vault-aggregator`, 6/21 tasks 완료

## 후속 (S45+)

- T7-T21 구현 완료 (vault_join 트랜잭션 / vault_sync git / 보조 명령 / 릴리스)
- Phase 1 메타 vault 초기화 (`twk vault init`)
- Phase 2 Pilot (00_unrealAgent 단독 합류 → 검증)
- Phase 3 나머지 5개 일괄 합류
- Phase 4 KJI_WIKI repo 생성 + 첫 mirror push + 로컬 Quartz 빌드
- Phase 5 Cloudflare Pages + Access 연결
- Phase 6 세션 종료 자동 hook 활성화

## 참조

- 개념: [[../concepts/Multi_Vault_Aggregation]]
- L2 raw: [[../../session_archive/20260427_session1_raw]]
