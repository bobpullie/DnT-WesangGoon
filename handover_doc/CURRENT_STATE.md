# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-20 Session 35 종료

## TEMS 호출 매뉴얼 (조용한 TEMS 아키텍처)
**기본 정책:** 매 prompt 무차별 주입 금지. 키워드 강매칭(score≥0.55) 시에만 자동 발동.
**등록 (수동 호출):**
```bash
python memory/tems_commit.py --type {TCL|TGL} --rule "..." --triggers "키워드들" --tags "..."
```
**자동 발동 트리거:** TCL 패턴(`이제부터/앞으로/항상`) / TGL 패턴(`하지마/금지/never/don't`) / Bash 실패 / preflight 자체 실패 / [Phase 3] TGL-T PreToolUse / active guard 위반.

## ⚠️ DVC ≠ TEMS TCL (용어 분리)
- **DVC case** (결정론적 빌드 검증) = `src/checklist/cases.json` + `chk_*.py`. `DISPLAY_HUMANIZE_001` 형식
- **TEMS TCL** (LLM 행동 교정) = `memory/error_logs.db`. `#N` 형식
- wiki compile: [[docs/wiki/concepts/DVC_vs_TEMS]]

## 모델 배치 원칙 (Opus 4.7 본체 + Sonnet 서브에이전트) — S34 도입
- **본체 (Opus 4.7):** 아키텍처 설계 · TEMS 규칙 분류 · Phase 전환 판정 · 핸드오버 결정 서술 · 팀 델리게이션
- **Sonnet 서브에이전트:** TEMS 모듈 구현 · Phase 이식 · 재분류 · DVC case · smoke test · Explore
- **Opus 서브에이전트:** `superpowers:code-reviewer` (Audit) · `advisor` (2안 비교)
- 상세: `.claude/skills/SDC.md` (Subagent Delegation Contract) + [[docs/wiki/concepts/SDC]]

## TWK / TriadWiKi (S34 도입, S35 llm-wiki → TWK rename)
- 글로벌 스킬: `C:/Users/bluei/.claude/skills/TWK/` (구 llm-wiki/)
- 프로젝트 config: `wiki.config.json` (Mode B, 5 섹션)
- 구조: `docs/wiki/{decisions,patterns,concepts,postmortems,principles}/` + `index.md` + `log.md`
- L2 추출: `docs/session_archive/` (session-lifecycle Step 5)
- Lint 주기: 5세션 / 10페이지
- 현재 13 pages compiled (TEMS 6 + DVC 5 + SDC 1 + Per_Agent_Local_QMD 1)

## QMD 로컬 관리 (S35 도입, 전 에이전트 공통)
- **정책:** 모든 에이전트는 QMD 데이터를 프로젝트 로컬 `qmd_drive/` 에서 관리 (TCL #116).
- **구조:** `qmd_drive/sessions/` (Claude 세션 export) + `qmd_drive/recaps/` (session-lifecycle Step 3 recap) + `memory/qmd_rules/` (TEMS 규칙).
- **위상군 이관 완료:** 91 files → `qmd_drive/` (sessions 45 + recaps 46). `wesanggoon-sessions`(broken) 제거, `wesanggoon-qmd-drive`(로컬) 등록·embed(48 docs, 63 chunks).
- **타 에이전트 대기:** 리얼군 / 코드군 / 디니군 / 어플군 / 기록군 / 빌드군 / 위상군(독립).
- **원리:** [[docs/wiki/principles/Per_Agent_Local_QMD]]

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **메타 프로젝트:** Atlas 비활성화 (S34) — SKILL.md.disabled
- **TEMS 위상군:** Phase 0-3 + Migration + SDC(S34, subagent-brief rename→SDC) + LLM Wiki(S34) — 규칙 #1~#114
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정)
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)

## 이번 세션 성과 (Session 34)
- **TEMS 표준화 판정:** 코드군 8세션 운영 결과 Wave 1 코드 무수정 확인 → Phase 0-2 공식 표준. Phase 3 위상군 단독 관찰 1-2주.
- **디니군 Wave 1 이식:** 10+1 파일 복사 + PostToolUse Bash/Stop hook 추가. 기존 14 규칙 보존.
- **리얼군 Wave 1 재이식 (구조적 사고 해결):** 이원화 DB(`memory/error_logs.db` 빈 vs `tems/tems_db.db` 10규칙) 발견 → migration 10/11 규칙 보존. memory_bridge 경로 정정.
- **SDC 스킬 2군 장착 (← S35에서 subagent-brief → SDC rename):** 위상군(TEMS/아키텍처 도메인) + 리얼군(Unreal 도메인). Opus/Sonnet 분업 매트릭스 + 5항목 템플릿 + 5 작업 유형 템플릿. TCL #113 등록.
- **Atlas 비활성화:** SKILL.md → .disabled, 위상군 settings atlas permission 제거. 기록군 graceful exit 기구현이라 무수정.
- **글로벌 llm-wiki 스킬 신설 (→ S35에서 TWK로 rename):** Karpathy 3-Layer + 3 Operations 범용화. 20 파일. Mode A(Pure) / B(Session-Extract) 지원. init/lint/extract 스크립트. 스킬 로더 공식 등록.
- **위상군 wiki 초기화 + 통합:** session-lifecycle Step 5-7 추가. CLAUDE.md 조건부 규칙 등록. TCL #114. 11 페이지 첫 compilation (TEMS 6 + DVC 5) + lint 0건.
- **누적 규칙:** TCL/TGL #1~#116, archive: #64, #98. 신규 S34: #113 #114 #115. S35: #116 (QMD 로컬 관리).

## 이전 세션 성과 요약

### Session 33 — Phase 3 재검증 + DVC skill + 코드군 Wave 1
- Phase3-Audit-Reverify + P1-a-follow + stale eviction 패치
- DVC skill 생성 + 위상군 dogfood
- 코드군 Wave 1 이식 (52f8dff) + Migration-Classification 31건

### Session 32 — Phase 3 구현 + P0/P1 패치
- 3A tool_gate_hook + 3B compliance_tracker + 3C decay
- P0/P1 다수 패치

### Session 31 — Phase 0/0.5/0.6/1/2 구축
- 자기관찰 + 조용한 TEMS + 자가진화 + 게이트

## 다음 세션 부트 (S35)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주), 타 에이전트 이식 대기
HEAD (위상군): eec891e — S31-S33 통합 커밋, 미푸시 (+ S34 대규모 변경 미커밋)
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시
HEAD (디니군): S34 이식 변경, 미커밋
HEAD (리얼군): S34 이식 + migration 변경, 미커밋
HEAD (wesangAgent 독립): 03d6638 (변경 없음)

위상군 TEMS: Phase 0-3 + Migration + SDC + TWK(구 llm-wiki). 규칙 #1~#114 (S35에서 SDC wiki concept 추가 예정).
위상군 wiki: 11 페이지 (TEMS/DVC) + index + log.
위상군 CLAUDE.md: v2026.4.20 (모델 배치 원칙 + TWK 행).
코드군 TEMS: Wave 1 + fermion-wiki 자체 운영.
디니군 TEMS: Wave 1 (S34).
리얼군 TEMS: Wave 1 + SDC (S34).

Hook 구성 (위상군 동일):
  - SessionStart: CURRENT_STATE 주입
  - UserPromptSubmit: preflight_hook
  - PreToolUse '': tool_gate_hook (Phase 3, 위상군 전용)
  - PostToolUse Write|Edit: changelog + memory_bridge
  - PostToolUse Bash: tool_failure_hook
  - PostToolUse '': compliance_tracker (Phase 3)
  - Stop: retrospective_hook

상태: 종일군 지시 대기 (push / needs_review / Wave 2 / 타 에이전트 확장 / Phase 3 관찰 통계)
```

## 이번 세션 성과 (Session 35, in progress)
- **subagent-brief → SDC rename:** 스킬 2개(위상군/리얼군) + CLAUDE.md + 규칙 참조 + TEMS DB + wiki concept 등록.
- **QMD 로컬 관리 정책 도입 (TCL #116):** 모든 에이전트 공통 원리. 위상군 이관 완료 (91 files → `qmd_drive/sessions/` + `qmd_drive/recaps/`). broken collection `wesanggoon-sessions` 제거.
- **Wiki +2 pages:** `concepts/SDC.md` + `principles/Per_Agent_Local_QMD.md`.
- **llm-wiki → TWK rename (TCL #118):** 글로벌 스킬 디렉토리 rename + SKILL.md frontmatter + 6 글로벌 파일 + 위상군 프로젝트 파일 5종 + TEMS DB #114 + FTS5 rebuild.
- **4개 원격 레포 생성·push (TEMS/TWK/DVC/SDC):** `bobpullie/{TEMS,TWK,DVC,SDC}` 신설 (TEMS 기존). 각 repo LICENSE(MIT)/README/.gitignore + frontmatter `upstream`+`update_cmd`. TCL #119 등록.
- **설치본 clone 변환 (pull-based 업데이트 체계):** `~/.claude/skills/TWK/` + `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/` 에 `.git/` 부착(`git init + reset --hard origin/main`). 위상군 root `.gitignore` 에 `.claude/skills/dvc/` 추가 + `git rm --cached` 로 nested 경계 처리. 이후 `git -C <install> pull origin main` 한 줄로 업데이트 수신 가능.
- **SDC Auto-Dispatch Check 도입 (TCL #120, bobpullie/SDC 121e3ee):** Hybrid trigger 모드. Auto-trigger 키워드(git commit/push, mv/cp, 배치, classify, verify, 이식) 매칭 시만 3-question gate 실행. Q1(invariance)·Q2(overhead)·Q3(reversibility-blast-radius) 판정. Q3=Shared state면 STAGING 패턴(Sonnet add만, Opus 검토 후 commit/push — TCL #86 생인). 기본값: Q1+Q2+Q3Local 통과 시 자동 DELEGATE. 세션 효율: overhead ~\$0.04-0.45, 순이득 \$0.5-1.5 예상 + context 보존.

## S35 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **Push-decision** | P0 | 4 에이전트 미푸시 (위상·코드·디니·리얼) 판단 |
| **Realgoon-tems_commit-cleanup** | P0 | 리얼군 memory/tems_commit.py 구버전 95줄 정리 (Wave 1 22KB와 공존) |
| **Phase3-Observation** | P1 | Phase 3 violation/compliance 통계 1-2주 수집 |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 수동 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 |
| **QMD-Local-Rollout** | P1 | TCL #116 타 에이전트 이관 — 리얼군/코드군/디니군/어플군/기록군/빌드군/위상군(독립). 각자 `qmd_drive/` 생성 + collection 재등록 |
| **sync-claude-sessions-config** | P2 | 글로벌 스킬 기본 출력 경로 `Claude-Sessions/` → `qmd_drive/sessions/` 로 리다이렉트 방안 검토 (skill 수정 vs symlink vs post-hook) |
| **TWK-Expand** | P1 | 타 에이전트 TWK(구 llm-wiki) 배포 (코드군 fermion-wiki 호환 확인 선행) |
| **DVC-Global-Promotion** | P2 | 위상군 dogfood 1-2세션 후 판단 |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |
| **QMD-Embed-107-114** | P2 | #107~#114 qmd embed |
| **Phase3-P2-Tests** | P3 | 단위 테스트 3종 |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |
| ~~Atlas-피드백~~ | — | **Atlas 비활성화로 무효 (S34)** | 종료 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |
| **Phase 3 위상군 단독 관찰** | S32 신규, 1-2주 통계 후 Wave 2 판정 | 4/20 S34 |
| **Atlas 비활성화** | 종일군 불필요 선언 | 4/20 S34 |
| **SDC(Subagent Delegation Contract) 스킬 도입 (Opus/Sonnet 분업)** | 깊은 추론 없는 실행을 Sonnet 위임으로. 초기 이름 subagent-brief, S35에서 SDC로 rename (3-letter 약어 통일·이름 충돌 방지·수학적 계약 구조 반영) | 4/20 S34~S35 |
| **TWK (TriadWiKi) 글로벌 스킬 채택 (구 llm-wiki, S35 rename)** | Karpathy 3-Layer 범용화, 리얼·코드군 양립 | 4/20 S34~S35 |
| **DVC ≠ TEMS TCL 용어 분리** | S33 혼동 사고 기반 wiki 정식화 | 4/20 S34 |
| **DVC skill 채택 + dogfood** | 종일군 확정 | 4/20 S33 |

## 팀 현황
| 에이전트 | 위치 | TEMS | SDC | TWK(llm-wiki) | 현재 태스크 |
|---------|------|------|----------------|----------|------------|
| 위상군 (DnT) | E:\DnT\DnT_WesangGoon | Wave 1 + Phase 3 | ✓ S34 | ✓ S34 (11 pages) | 대기 |
| 위상군 (독립) | E:\WesangGoon | 신규 구축 완료 | — | — | 대기 |
| 코드군 | E:\QuantProject\DnT_Fermion | Wave 1 (52f8dff) | ✓ 원조 | 자체 fermion-wiki | needs_review 14건 |
| 디니군 | E:\01_houdiniAgent | Wave 1 (S34) | — | — | ANKR Phase 1 |
| 리얼군 | E:\00_unrealAgent | Wave 1 (S34, migration) | ✓ S34 | — | TEMS cleanup 대기 |
| 어플군 | E:\ChildSchedule | 구버전 (tems_core) | — | — | Wave 1 이식 대기 |
| 기록군 | E:\KnowledgeHub | 구버전 | — | — | L2 키워드 보강 대기 |
| 빌드군 | E:\DnT\MRV_DnT | 구버전 | — | — | 대기 (Q-002) |
