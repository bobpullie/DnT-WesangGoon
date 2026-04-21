# Wiki Change Log

> append-only. 삭제 금지. 최신이 위.

## 2026-04-21 — [Session Close] S38 종료
- [Ingest] decisions/2026-04-21_sdc-selective-dispatch (Implemented, S38) — SDC §0 규칙기반/자동트리거 모드 분리 / 커밋 `4d31cf5`
- L2 추출: `docs/session_archive/20260421_session2_raw.md` (Q=9, A=34)
- TCL #122 신규 — git 배포 전용 sdc_trigger (선별적 SDC 활성화 출발점)
- 글로벌 ~/.claude 최적화: CLAUDE.md 52→7줄 (86% 감축), artkoon 스크립트 2개 삭제
- 위상군 wiki 페이지: 17 → 18 (+decision)
- 다음 lint 주기: S41 (5세션 후) 또는 20 페이지 시점 (S36 지정 유지)
- 핸드오버: [[../../handover_doc/2026-04-21_session38]]

## 2026-04-21 — [Session Close] S37 종료
- [Ingest] decisions/2026-04-21_handover-skill-packaging (Implemented) — bobpullie/handover 독립 스킬 패키징 결정
- L2 추출: `docs/session_archive/20260421_session1_raw.md` (Q=17, A=29)
- SDC-Helper `memory/sdc_commit.py` 구현 + 배포 (`4058e2a`)
- bobpullie/handover 리포 신설 배포 (`c374201`, `aa7d56c`)
- 위상군 wiki 페이지: 16 → 17 (+decision)
- 핸드오버: [[../../handover_doc/2026-04-21_session37]]
- QMD recap: [[../../qmd_drive/recaps/2026-04-21_session37]]

## 2026-04-20 — [Session Close] S36 종료
- [Ingest] decisions/2026-04-20_sdc-gate-phase3-integration (Implemented) — SDC Auto-Dispatch gate Phase 3 편입 / 커밋 `8b5cc06`
- [Ingest] postmortems/20260420_sdc-gate-violation (Confirmed, T1+T2) — S36 본체 SDC 위반 실사건 + 축적 교훈
- [Ingest] daily/2026-04-20.md — Calendar ↔ Dataview 허브 (wiki/ 바깥이지만 index 연결)
- TWK 글로벌 스킬 frontmatter 계약 Dataview+Calendar 호환화 (`bobpullie/TWK@db9766e`)
- 6 page-templates 정규화 + daily-note.md 신설 + lint 강화
- 위상군 wiki 페이지: 14 → 16 (+decision +postmortem)
- 누적 push (`bobpullie/DnT-WesangGoon@8b5cc06`): S34-S35 대규모 정리 + SDC gate
- 다음 lint 주기: S41 (5세션 후) 또는 20 페이지 시점
- 핸드오버: [[../../handover_doc/2026-04-20_session36]]
- QMD recap: [[../../qmd_drive/recaps/2026-04-20_session36]]

## 2026-04-20 — [Session Close] S35 종료
- L2 추출: `docs/session_archive/20260420_session2_raw.md` (Q=16, A=56, 기계적, 0 토큰)
- TCL 신규 (5+1): #116 QMD 로컬 · #117 분류 Sonnet 위임 · #118 TWK rename · #119 원격 레포 · #120 SDC Auto-Dispatch Check · #121 S35 교훈
- 위키 신규 (+3): concepts/SDC · principles/Per_Agent_Local_QMD · concepts/System_vs_Skill (+ decisions/plugin-remote-repos 최종 추가)
- 총 위키 페이지: 14 (TEMS 6 + DVC 5 + SDC 1 + Per_Agent_Local_QMD 1 + System_vs_Skill 1 + plugin-remote-repos 1)
- 다음 lint 주기: S39 (4세션 후) 또는 16 페이지 시점
- 핸드오버: [[../../handover_doc/2026-04-20_session35]]
- QMD recap: [[../../qmd_drive/recaps/2026-04-20_session35]]

## 2026-04-20 — [Ingest] Plugin Remote Repos decision (S35 close)
- [Decision] 4개 플러그인 원격 레포 체계 (Accepted) | docs/wiki/decisions/2026-04-20_plugin-remote-repos.md

## 2026-04-20 — [Ingest] System vs Skill vs Hybrid 분류 + TWK brand (S35)
- [Concept] System_vs_Skill: 3-way 분류 체계 | docs/wiki/concepts/System_vs_Skill.md
- TCL #117: 분류 작업 Sonnet SDC 위임 규칙
- TCL #118: llm-wiki → TWK(TriadWiKi) rebrand (fork 브랜치 공식화)
- TWK rename은 SDC 스킬의 첫 "분류 규칙 기반 Sonnet 위임" 시범 적용

## 2026-04-20 — [Ingest] Per-Agent Local QMD principle (S35 전 에이전트 정책)
- [Principle] Per_Agent_Local_QMD | docs/wiki/principles/Per_Agent_Local_QMD.md
- 위상군 이관 완료: `QMD_drive/sessions/`(43) + `Claude-Sessions/`(2) + `qmd_sessions/`(46) → `qmd_drive/sessions/`(45) + `qmd_drive/recaps/`(46) = 91 files
- QMD collection 변경: `wesanggoon-sessions`(broken, E:/AgentInterface 참조) 제거 → `wesanggoon-qmd-drive`(로컬) 추가
- 추가 파일: `qmd_drive/README.md` (프로젝트별 QMD 정책 문서)
- 규칙: TCL #116 (모든 에이전트 QMD 로컬 관리)
- 타 에이전트 이관 대기: 리얼군 / 코드군 / 디니군 / 어플군 / 기록군 / 빌드군 / 위상군(독립)

## 2026-04-20 — [Ingest] SDC concept (S35 rename 기록)
- [Concept] SDC: Subagent Delegation Contract | docs/wiki/concepts/SDC.md
- 스킬 rename: `subagent-brief` → `SDC` (2 에이전트: 위상군, 리얼군)
- 근거: (1) Anthropic 동일 이름 충돌 회피 (2) TEMS/DVC 3-letter 리듬 통일 (3) TCL #80 수학적 정합성 (Contract = Hoare logic 대응)
- 반영 파일: 위상군 CLAUDE.md / 리얼군 CLAUDE.md / handover CURRENT_STATE.md / memory/qmd_rules/rule_0113.md / rule_0115.md / 리얼군 tems/reclassify_20260420.py
- TEMS DB 본문(#113, #115) 및 QMD re-embed는 S35 후속으로 수행

## 2026-04-20 — [Session Close] S34 종료
- L2 추출: `docs/session_archive/20260420_session1_raw.md` (Q=11 / A=49, 기계적, 0 토큰)
- TCL 신규: #113 (모델 배치 원칙), #114 (llm-wiki 운영), #115 (S34 Trust-but-verify 교훈)
- wiki 총 11 페이지 (TEMS 6 + DVC 5) + lint 0건
- 핸드오버: [[../../handover_doc/2026-04-20_session34]]
- 다음 lint 주기까지: 4 세션 (현재 S34, 다음 lint 대상 S39)

## 2026-04-20 — [Ingest] DVC 5 엔트리 (S34)
- [Concept] DVC: Deterministic Verification Checklist | docs/wiki/concepts/DVC.md
- [Concept] DVC vs TEMS 분리 기준 | docs/wiki/concepts/DVC_vs_TEMS.md
- [Pattern] DVC Case Lifecycle | docs/wiki/patterns/DVC_Case_Lifecycle.md
- [Decision] DVC 스킬 승격 + 위상군 dogfood (Accepted) | docs/wiki/decisions/2026-04-20_dvc-skill-promotion.md
- [Principle] Case Generalization | docs/wiki/principles/Case_Generalization.md

## 2026-04-20 — [Ingest] TEMS 초기 6 엔트리 (S34)
- [Concept] TEMS: LLM 행동 교정 메모리 시스템 | docs/wiki/concepts/TEMS.md
- [Concept] TCL vs TGL 분류 기준 | docs/wiki/concepts/TCL_vs_TGL.md
- [Pattern] 7-Category 분류 체계 | docs/wiki/patterns/Classification_7_Category.md
- [Decision] Wave 1 표준화 (Accepted) | docs/wiki/decisions/2026-04-20_wave1-standardization.md
- [Decision] Phase 3 관찰 유보 (Observation) | docs/wiki/decisions/2026-04-20_tems-phase3-deployment.md
- [Principle] Self-Containment | docs/wiki/principles/Self_Containment.md

## 2026-04-20 — [Init] wiki 초기화 | 섹션: decisions, patterns, concepts, postmortems, principles
