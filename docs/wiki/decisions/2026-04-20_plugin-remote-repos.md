---
date: 2026-04-20
status: Accepted
phase: S35
scope: all-agents,triad-plugin-ecosystem
tags: [plugin, remote-repo, upstream, distribution, tems, twk, dvc, sdc, cross-agent-sync, github]
---

# Decision — 4개 플러그인 원격 레포 체계 확립

## 요약

Triad Chord Studio의 핵심 인프라 4종(TEMS / TWK / DVC / SDC)을 **각각 독립된 GitHub 원격 레포**로 분리하고 upstream 메타데이터로 배포·업데이트 체계 확립.

## 레포 지도

| 플러그인 | URL | 분류 | 업데이트 메커니즘 |
|---------|-----|------|----------------|
| **TEMS** | https://github.com/bobpullie/TEMS | System (hook plugin) | `pip install -U git+...` + `tems scaffold` |
| **TWK** | https://github.com/bobpullie/TWK | Skill plugin (global) | `git -C ~/.claude/skills/TWK pull origin main` |
| **DVC** | https://github.com/bobpullie/DVC | Skill plugin (hybrid) | `git -C <install> pull origin main` |
| **SDC** | https://github.com/bobpullie/SDC | Skill plugin (single-file) | `curl -o <path>/SDC.md https://raw.githubusercontent.com/bobpullie/SDC/main/SKILL.md` |

## 배경

S34 말까지 4 자산은 모두 **위상군 프로젝트 로컬** 또는 **에이전트별 복사본**으로만 존재:
- SDC: `.claude/skills/SDC.md` (위상군 + 리얼군, 수동 복사)
- TEMS: `memory/*.py` (각 에이전트 scaffold 기반 복사본)
- TWK(구 llm-wiki): `~/.claude/skills/llm-wiki/` (git 레포 아님, 복사만)
- DVC: `.claude/skills/dvc/` (위상군 전용, 글로벌 승격 대기)

문제:
1. **cross-agent 전파 수동** — 위상군이 기능 개선해도 타 에이전트는 수동 복제 필요
2. **버전 추적 불가** — 각 복사본이 언제 최신인지 판단 어려움
3. **상충 가능성** — 에이전트별 로컬 수정이 원본과 diverge

## 결정 사항

### 1. 각 플러그인을 독립 GitHub 레포로 분리
- bobpullie/TEMS (기존) + bobpullie/TWK + bobpullie/DVC + bobpullie/SDC (신규 3개)

### 2. 표준 레포 레이아웃
```
<REPO>/
├── SKILL.md            # name + upstream + update_cmd + description (frontmatter)
├── README.md           # Install + Updating + Related Plugins
├── LICENSE             # MIT (공통)
├── .gitignore
└── (scripts/ templates/ references/ 등 스킬별 내용)
```

### 3. SKILL.md frontmatter 표준 메타데이터
```yaml
---
name: <PLUGIN_NAME>
upstream: https://github.com/bobpullie/<NAME>
update_cmd: <exact command to pull latest>
description: ...
---
```

### 4. 설치본은 가급적 git clone 구조
- Clone 가능한 스킬(TWK/DVC) → `~/.claude/skills/` 또는 `.claude/skills/<name>/` 에 clone
- 단일 파일 스킬(SDC) → curl로 파일 갱신
- Python 패키지 (TEMS) → `pip install git+...`

### 5. Nested repo 경계 처리 (프로젝트 로컬 clone 시)
- 주 프로젝트 `.gitignore` 에 clone 경로 추가
- 이미 추적된 파일은 `git rm --cached` 로 untrack
- 이로써 플러그인은 자기 repo가 관리, 주 프로젝트 status가 오염되지 않음

### 6. Cross-agent 업데이트 흐름
```
위상군 또는 임의 에이전트가 기능 개선
        │
        ▼
  local edit + commit + push to bobpullie/<PLUGIN>
        │
        ▼
  다른 모든 에이전트: upstream 메타데이터의 update_cmd 실행
  (git pull / pip install -U / curl)
```

## 대안 검토

| 대안 | 거부 사유 |
|------|---------|
| 단일 monorepo (triad-plugins) | 플러그인별 버전/릴리즈 독립성 손실, 타 에이전트가 필요한 플러그인만 선택 설치 어려움 |
| Git submodule | 초기 setup 복잡, 사용자가 `--recursive` 실수 빈발, subtree보다 인지 비용 큼 |
| npm/pypi 패키지로 배포 | 네임스페이스 확보·등록 수수료 부담, skill 성격과 맞지 않음 (.md 파일이 주) |
| 자체 distributable archive (zip/tar) | 업데이트 checksum 관리 필요, GitHub 인프라 이미 있음 |

## 영향

### 즉시
- 위상군이 update를 **1회 push로 전 에이전트 전파** 가능
- TWK/DVC는 `git pull` 한 줄로 최신 수신
- 플러그인별 독립 issue/PR 가능 (향후)

### 파급
- 타 에이전트 Rollout 필요 (S35 Task: TWK-DVC-SDC-Rollout P1, QMD-Local-Rollout P1)
- 플러그인 버전 태그 관리 프로토콜 미정 (v0.1.0 등 — 후속)
- CI/CD 미구성 (push 시 자동 테스트 없음)

## 위험 & 완화

| 위험 | 완화책 |
|-----|-------|
| 타 에이전트에 non-reviewed 코드 자동 전파 | clone 구조라서 pull 전 review 가능. 자동 pull 걸지 말 것 |
| 권한 누수 (private info in push) | README에 **"commit 전 secret 스캔 필수"** 명시 필요 (후속) |
| 플러그인 간 버전 불일치 (TEMS v0.2가 SDC v0.1 의존) | 후속: SKILL.md에 `compatibility:` 필드 도입 검토 |
| 원격 저장소 삭제/이동 | upstream 필드가 metadata로 존재, 다른 mirror로 point만 하면 복구 가능 |

## 실행 기록

| Commit | Repo | 내용 |
|--------|------|------|
| 73687f2 | TEMS | README upstream + Updating section |
| 540809b | TWK | upstream/update_cmd frontmatter + Updating |
| 25eb84b | DVC | upstream/update_cmd frontmatter + Updating |
| 121e3ee | SDC | Section 0 Auto-Dispatch Check |

(각 레포 초기 push는 `861c73f` `4b0d2aa` `4d000b6` 참조. bobpullie/TEMS는 기존 repo 활용)

## 관련

- [[../principles/Per_Agent_Local_QMD]] — 데이터 로컬 원리 (병행 도입)
- [[../concepts/System_vs_Skill]] — 플러그인 분류 체계
- [[../concepts/SDC]] — SDC skill 자체
- [[../concepts/TEMS]] — TEMS system 자체
- TCL #118 — TWK rebrand
- TCL #119 — 원격 레포 upstream 체계
- TCL #120 — SDC Auto-Dispatch Check (Section 0)
