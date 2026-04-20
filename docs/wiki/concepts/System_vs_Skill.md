---
date: 2026-04-20
status: Active
phase: S35-introduced
scope: wesang-meta-classification
tags: [taxonomy, system, skill, hybrid, tems, dvc, sdc, twk, meta, runtime-vs-guide]
---

# Concept — System vs Skill vs Hybrid (분류 체계)

## 정의

위상군 인프라 구성요소는 **세 가지 작동 방식**으로 분류된다. 분류 기준은 "누가 언제 호출하는가".

| 분류 | 호출 주체 | 호출 시점 | LLM 의식적 참여 |
|------|----------|----------|---------------|
| **System** | Claude Code harness (hook) | 런타임 이벤트 발생 시 자동 | ❌ 의식 없음 (자동 주입만) |
| **Skill** | LLM (`Skill` 도구) | LLM 판단 시 | ✅ LLM이 능동 호출 |
| **Hybrid** | 양쪽 혼용 | 자동 + 수동 | 부분적 |

## 위상군 인프라 분류

### System (hook 자동)

| 이름 | 구성 | 발동 hook |
|------|------|----------|
| **TEMS** | `memory/tems_engine.py` + SQLite + FTS5 + QMD dense + `memory/*.py` hooks | SessionStart / UserPromptSubmit(preflight) / PreToolUse(tool_gate) / PostToolUse(changelog·memory_bridge·tool_failure·compliance_tracker) / Stop(retrospective) |
| **AutoMemory** | Claude Code native 메모리 시스템 (MEMORY.md 인덱스) | 세션 컨텍스트 자동 주입 |
| **CURRENT_STATE 주입** | SessionStart hook `cat handover_doc/CURRENT_STATE.md` | SessionStart |

### Skill (LLM `Skill` 도구 호출)

| 이름 | 위치 | 주 사용 시점 |
|------|------|-------------|
| **SDC** (Subagent Delegation Contract) | `.claude/skills/SDC.md` | Opus → Sonnet 실행 위임 계약 작성 시 |
| **DVC** (Deterministic Verification Checklist) | `~/.claude/skills/dvc/` (global) | 빌드 검증 case 추가/실행 시 |
| **TWK** (TriadWiKi, 구 llm-wiki) | `~/.claude/skills/TWK/` (global) | Wiki Ingest / Query / Lint 수행 시 |
| **subagent-brief** (deprecated, → SDC) | - | - |
| **qmd-embed** | `~/.claude/skills/qmd-embed/` | QMD CUDA 백엔드 트러블슈팅 시 |
| **sync-claude-sessions** | `~/.claude/skills/sync-claude-sessions/` | 세션 export/resume 시 |
| **recall** | `~/.claude/skills/recall/` | 과거 세션·주제 조회 시 |
| **superpowers:***, **advisor** 등 | global | 브레인스토밍·디버깅·Audit 시 |

### Hybrid

| 이름 | System 레이어 | Skill 레이어 |
|------|-------------|-------------|
| **DVC** | `src/checklist/runner.py` 수동/cron 실행 가능 + cases.json 자동 로드 | `dvc` 스킬이 case 등록 방법 가이드 |
| **TWK** | `~/.claude/skills/TWK/scripts/extract_session_raw.py` 세션 종료 시 수동 실행 (session-lifecycle Step 5) | `TWK` 스킬이 3-Layer / 3 Operations 방법론 가이드 |
| **TEMS 규칙 등록** | `tems_commit.py` CLI (수동) — 단, 등록된 규칙은 preflight_hook이 자동 발동 | (스킬 없음 — 프로토콜 문서 `.claude/rules/tems-protocol.md` 로만 제공) |

## 구분이 중요한 이유

1. **부팅 신뢰도** — System은 LLM이 "잊어도" 작동. Skill은 LLM이 호출해야만 작동 → 부팅 의존성 다름.
2. **계약 위치** — System의 계약은 hook 설정(`settings.local.json`)에 있음. Skill의 계약은 `SKILL.md` frontmatter의 `name`/`description`/`triggers`에 있음.
3. **배포 경로** — System은 프로젝트별 hook 배선(Wave N) 필요. Skill은 글로벌 등록 + 프로젝트 config로 충분.
4. **실패 모드** — System이 silent fail 하면 규칙이 주입되지 않아 모델이 오류 반복(TGL #92 사례). Skill이 호출되지 않으면 LLM 판단 기회를 놓칠 뿐.

## 분류 결정 알고리즘

```
Q1: 이 컴포넌트는 LLM이 의식적으로 호출해야 작동하는가?
├─ YES, 항상 LLM 호출 필요 → **Skill**
├─ NO, hook만으로 작동 → **System**
└─ 수동 호출 경로도 있고 자동 hook도 있다 → **Hybrid**
```

추가 질문:
- "만약 LLM이 스킬 존재 자체를 잊어도 이 기능이 작동해야 하는가?" → YES면 System, NO면 Skill
- "이 컴포넌트의 `name:` 필드가 SKILL.md에 있는가?" → YES면 (최소한) Skill 레이어를 가짐

## TEMS 시스템이 스킬이 아닌 이유 (FAQ)

- `.claude/skills/TEMS.md` 파일이 없음 — Skill 도구로 호출 불가
- preflight_hook은 매 UserPromptSubmit마다 **무조건** 실행 — LLM 의식 없음
- 등록 CLI(`tems_commit.py`)는 LLM이 호출하나, 이는 "System에 쓰기"이지 Skill 호출 아님
- 프로토콜 문서(`tems-protocol.md`)는 "System 사용 매뉴얼" 역할 — 스킬과 외형 유사하나 Skill 도구로 호출 대상 아님

## 관련 개념

[[TEMS]] [[DVC]] [[SDC]] [[../principles/Per_Agent_Local_QMD]]

## 참조

- TCL #113 — 모델 배치 (Opus 본체 / Sonnet 서브에이전트)
- TCL #117 — 분류 작업 Sonnet SDC 위임 (S35)
- TCL #118 — TWK 브랜드 명명 (S35, llm-wiki fork)
- [TEMS concept](TEMS.md) — System 예시 상세
- [DVC concept](DVC.md) — Hybrid 예시 상세
- [SDC concept](SDC.md) — Skill 예시 상세
