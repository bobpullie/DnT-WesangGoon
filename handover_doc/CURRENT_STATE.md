---
date: 2026-04-30
type: handover
cssclass: twk-handover
tags: [session, handover]
---

# 위상군 — 현재 프로젝트 상태 (Rolling State)
> 마지막 갱신: 2026-04-30 Session 54 (본업) 종료 — **codex-exe 위임 wrapper 정착 + 슬래시 명령 캡슐화**. S51 cross-model 위임 패턴 (Opus 4.7 ≠ 구현자 = GPT-5.5) 을 절차로 정착. wrapper script + 슬래시 명령으로 향후 호출 부담 0화. (1) [`scripts/codex_exec.sh`](../scripts/codex_exec.sh) 신규 — 직접 codex 호출 + watch-mode (stderr "tokens used" 마커 polling + SIGTERM, 30s→6s 단축) + sentinel (.done/.exit) + hard timeout. (2) [`.claude/commands/codex-exe.md`](../.claude/commands/codex-exe.md) 신규 — 위임 게이트 4 signal + prompt 5섹션 + TBV 7항목 + S51→S54 진화 표. (3) End-to-end 검증 PASS = pong round-trip + workspace-write smoke task (`tests/test_codex_exe_smoke.py` 입증자료, codex 가 직접 작성 + pytest 1/1 PASS, scope 격리 확정). **TWK v0.4 Phase 0 진전 0** (S44 이래 9세션 연속 이월). **S52~S53 P0 (self_cognition detector false positive 7건) 진전 0** (S54 신규 발생 0). 다음 회차 (S55) 권장 시퀀스: (A) self_cognition_gate detector 임계 재설계 (P0, 3회 이월) / (B) PR-3a (handover_failure_gate path 외부화) / (C) codex zombie 정리 정책 / (D) TWK v0.4 재개.
> 직전 본업 세션: **S54 종료** — scripts/codex_exec.sh + .claude/commands/codex-exe.md + tests/test_codex_exe_smoke.py (codex 작성 입증자료) 신규 3건. 신규 TGL/TCL 0건 (코드로 해결한 패턴은 wrapper 에 박는 게 룰보다 강한 강제력)
> 본업 누적: S44 (TWK 설계 + Phase 0 6/21) → S48 (TEMS 자기진단 + viewer 도입) → S49 (TEMS 복구 + 메타-결함 정정) → S50 (TGL #128 hook 강제 + 메타-결함 3차 재발) → S51 (Self-Cognition Gate + 위임 모델 첫 적용) → S52 (TEMS 점검 + DVC 자동화 + canonical v0.4) → S53 (viewer 인프라 마무리 + canonical TEMS_GUI_Editor 첫 push) → **S54 (codex-exe 위임 wrapper 정착 + 슬래시 명령)**
> aux 세션 누적: S45 (PC 보안/KRX NOS), S46 (홈서버 HTTPS), S47 (홈서버 운영 정상화) — 본업 무관

## S54 핵심 산출 (본업, codex-exe 위임 wrapper)
- **`scripts/codex_exec.sh` 신규** — codex CLI 호출 wrapper. 핵심 4원칙: (A) codex 직접 호출 (POSIX wrapper `exec node codex.js` → cmd.exe 우회 불필요, S51 cmd.exe wrapper 는 PowerShell tool 환경 한정) / (B) stdin file redirect (`< prompt.txt`) — non-TTY pipe EOF 없어 hang 회피 / (C) GNU `timeout` hard bound — codex 0.125.0 known shutdown hang (rollout error + WebSocket cleanup) 회피 / (D) Watch mode — stderr `^tokens used$` 마커 polling 즉시 SIGTERM → 30s→6s 단축. Output: `<prefix>_stdout.log` / `<prefix>_stderr.log` / `<prefix>.done` / `<prefix>.exit`
- **`.claude/commands/codex-exe.md` 신규** — 슬래시 명령. §0 위임 게이트 4 signal (메타-결함 차단 hook / 분량 ≥15 파일 / TBV 비판 검토 필요 / audit 통과 spec) / §1 prompt 5섹션 (Scope / Spec / Deliverables / Smoke / Anti-Acceptance + Done Reporting) / §2 호출 패턴 (foreground for ping / background+sentinel for impl) / §3 TBV 7항목 / §4 주의사항 / §5 S51 vs S54 진화 표 / §6 워크플로우 체크리스트
- **End-to-end 검증 (TGL #63 적용)** — 종일군 "확실히 된거야?" 모호 확인 → ASCII 시퀀스 + 실전 mini task 강제. (1) pong round-trip = wrapper 6초 완료 + semantic_ok=1 + .done sentinel ✓ (2) workspace-write smoke task = `tests/test_codex_exe_smoke.py` 신규 1 파일 (426 bytes, codex 자가 작성, pytest 1/1 PASS) + scope 격리 (`git status --porcelain` = 1줄) + 본체 TBV 4항목 (파일 존재 / 내용 일치 / scope / pytest 재실행) 모두 PASS + anti-acceptance 위반 0건
- **신규 TGL/TCL 0건** — codex 호출 패턴은 wrapper script 가 코드로 해결. 룰 (LLM 자율 준수 의존) 보다 코드 (강제 실행) 가 더 강한 강제력. S52 P0 였던 "Windows codex CLI 호출 패턴 TGL 신규" 를 슬래시 명령 + wrapper 로 대체
- **메타-결함 0건** — 외부 모델 위임 = 본체 ≠ 구현자 분리 → 자기-방어 동기 구조적 차단. S48/S49/S50 의 메타-결함 3차 재발 cycle 본 세션 적용 0건 (S51 첫 적용에 이은 두 번째 입증)
- **codex zombie 누적** — 본 세션 호출로 codex.exe 7개 + cmd.exe 7개 잔존 (codex 0.125.0 cleanup 이슈). taskkill 권한 미보유로 정리 불가 — 종일군이 PC 재기동 시 자연 정리 또는 권한 추가 필요. S55 P0 후속
- 자세한 핸드오버 + 반성: `handover_doc/2026-04-30_session54.md`

## S53 핵심 산출 (본업, viewer 마무리 + canonical 첫 push)
- **viewer 잔존 결함 4건 정정** ([viewer/rule_viewer.py](viewer/rule_viewer.py))
  - **D1**: main guard `if __name__ in ("__main__", "__mp_main__"):` → `if __name__ == "__main__":` 1 토큰 제거. NiceGUI native_mode 의 `mp.Process(_open_window)` 자식 spawn 시 main() 재진입 차단. S48 의 "native 모드 실패 → --browser fallback" 결정 = 진단 불완전이었음을 재검토 통해 확정
  - **D2**: [.claude/commands/tems-view.md](.claude/commands/tems-view.md) launcher 가 `sys.executable` (python.exe console subsystem) → `pythonw.exe` (windows subsystem, conhost.exe 없음) 분기 + `CREATE_NO_WINDOW` 플래그 추가. PowerShell `Get-CimInstance Win32_Process` 검증 시 자식 트리에 conhost.exe 0건
  - **D3**: 외곽 스크롤바 + pagination 잘림 — 임시 JS DOM dump (`ui.run_javascript`) 로 chain 추출 → q-layout / q-page-container 가 Quasar default `display: block` 으로 flex chain 단절 발견 → chain 전체 강제 (`html, body, body > div, .nicegui-layout, .q-page-container, .q-page-container > .q-page, .q-page > .nicegui-content`) `display: flex !important; flex-direction: column !important; flex: 1 1 auto !important; min-height: 0 !important;` + 최상단 100vh + `.q-table__middle { overflow: auto }` + 형제 sticky `flex: 0 0 auto`. 검증: 두 번째 dump 에서 모든 chain element h ≤ viewport.h (763px)
  - **D4**: THS 컬럼 툴팁의 "⚠️ 미구현 — 모두 0.50" 경고 stale = S49 시점 갱신됐던 코드를 PID 15684 (S48 시점 메모리) 가 그대로 가지고 있던 문제. 재기동만으로 자연 해소. 별도 패치 0
- **Refresh THS now 버튼 신규** ([viewer/rule_viewer.py:447-485](viewer/rule_viewer.py#L447-L485)) — footer 에 추가. `memory.decay.apply_decay(dry_run=False)` 호출 → 전 규칙 ths_score 재계산 + 60일/90일 status 전이 (24h 가드 무시 = 수동 강제). toast 알림 (recomputed/transitions/cold+/archive+)
- **canonical bobpullie/TEMS_GUI_Editor 첫 push** — main HEAD `ef80e95`. 5 file (README.md / __init__.py / requirements.txt / rule_viewer.py / .gitignore). working dir = `E:/bobpullie/TEMS_GUI_Editor` (bobpullie/TEMS / TWK / handover 와 같은 위치)
- **위상군 master push** — `1e65876..27c2e54`. viewer/ 4 file + .claude/commands/tems-view.md + .gitignore (`viewer/_launch.log` 추가)
- **TCL #129** (workflow/debugging) — UI 문제 (layout/CSS/렌더링) 수정 시 진단 필수, patch-and-pray 금지. 트리거: UI 문제, layout, CSS, 스크롤, pagination, DOM 구조, NiceGUI, Quasar, flex
- **TGL #130** (TGL-P/L2) — SPA viewport-fit 풀-페이지 layout 의 flex chain 단절 패턴. forbidden: 부분 CSS 추측 추가 / 정적 SPA HTML grep 으로 DOM 추론. required: client-side JS DOM chain dump → display:block 단절 layer 동정 → chain 전체 flex column + 100vh 강제 → 단일 element 만 overflow:auto. **Gate 경고 2건** (B_abstraction L1 경계, E_verifiability compliance_check 미정의) — S54 P0
- **메타-결함 자기-진단 (patch-and-pray 2회 + 종일군 질책)** — D3 해결 시 본인이 두 차례 부분 CSS 패치 (`overflow: hidden` 추가 / `q-table__container { display:flex }` 만 추가) → 같은 증상 지속 → 종일군 "그때그때 부분적인 코드만 고쳐서 해결하려고하지말고" → 비로소 client-side JS DOM dump 진단. SPA 의 정적 served HTML (49KB shell + JSON config) 만 grep 해서 framework default class 단정한 게 근본 원인. TGL #130 의 forbidden 절이 정확히 본인 본인의 패턴을 잡음
- **메타-결함 자기-진단 (self_cognition false positive 2건 추가)** — `scd_20260430_135036_*_self_praise` ("깔끔" — Windows pythonw subprocess 의 객관적 outcome 묘사) / `scd_20260430_140829_*_absolutization` ("100%" — CSS literal). 둘 다 reject. 누적 6건 → 7건 (S52 4 + S53 2 + S51 잔존 1). detector 가 단일 토큰 매칭만으로 판정해 기술적 outcome / code literal 을 자축으로 오분류. **S54 P0 = detector 임계 재검토** (S52 부터 이월된 그대로)
- 자세한 핸드오버 + 반성: `handover_doc/2026-04-30_session53.md`

## S52 핵심 산출 (본업, TEMS 점검 + DVC + canonical v0.4)
- **TEMS 12 항목 alive 전수 검증** — THS 산식 (rule#102 = 0.226536 ≈ S49 ref) / system_health (overall 0.892) / decay sweep / .resolve() canonical / record_modification wire / hook 단위 작동 / pytest 50/50. 잔존 결함 4건 (D1~D4) 보고
- **D1 fix (위상군)** — [memory/tems_engine.py](memory/tems_engine.py) top-level 에 `_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent); if _PROJECT_ROOT not in sys.path: sys.path.insert(0, _PROJECT_ROOT)` 추가. `python memory/tems_engine.py` 직접 실행 호환. DVC 8/8 silent 전환
- **DVC TEMS 자동화** — [src/checklist/chk_tems.py](src/checklist/chk_tems.py) 신규 (TEMSChecklist + 8 checker 메서드 + AST docstring 회피) + [src/checklist/cases.json](src/checklist/cases.json) 8 case 등록 (S49~S52 결함 일반화)
- **DVC Stop hook 통합** — [scripts/dvc_stop_hook.py](scripts/dvc_stop_hook.py) 신규 (silent + 재귀 회피 `DVC_TEMS_AUDIT_RUNNING=1` + 5s timeout + `logs/checklist/dvc_stop_audit.jsonl` 적재). [.claude/settings.local.json](.claude/settings.local.json) Stop chain 3rd entry. 매 응답 종료 ~470ms 자동 점검 정착
- **canonical TEMS PR 4건 일괄 머지** — bobpullie/TEMS master HEAD `5c4b2d1` (v0.3.1 → v0.4.0):
  - **PR #4** ([f87ecf6](https://github.com/bobpullie/TEMS/pull/4)): compute_ths input swap (fire_count/compliance/violation/last_fired) + compute_system_health last_fired migration + supersede_rule wire record_modification + .resolve() canonical 9 templates (10 files, +55/-25)
  - **PR #5** ([95919a9](https://github.com/bobpullie/TEMS/pull/5)): Diagnostics & Self-Audit layer 3 templates (run_decay_if_due / audit_diagnostics_recent / audit_dead_state) + scaffold._PHASE4_TEMPLATES + _HOOK_PLAN 4-tuple args (4 files, +665/-10)
  - **PR #6** ([f7ea82a](https://github.com/bobpullie/TEMS/pull/6)): tems_engine.py direct run 호환 (relative→absolute import + sys.path 보강) (1 file, +9/-1)
  - **PR #7** ([5c4b2d1](https://github.com/bobpullie/TEMS/pull/7)): README "버전/Phase 이력" v0.3.1 + v0.4.0 항목 추가 (1 file, +4/-2)
- **위상군 = canonical strict superset 명시** — 위상군 self-contained `memory/*.py` (`from memory.X` import) + canonical 미반영 layer (handover_failure_gate / self_cognition_gate + 6 templates + 14 tests). canonical 머지가 위상군에 미치는 영향 0
- **canonical 미반영 (PR-3a/3b 보류)** — TCL #93 부합. handover_failure_gate path 외부화 + self_cognition 영문 시그널 추가 후 v0.5 표준화 권장
- **self_cognition gate detector false positive 4차 누적** — 단일 토큰 매칭 ("alive" "깔끔" "메타-결함") 이 객관 보고/historical reference/PR 머지 결과 인용을 자축으로 오분류. S53 P0 = detector 임계 재검토
- 자세한 핸드오버 + 반성: `handover_doc/2026-04-30_session52.md`

## S51 핵심 산출 (본업, Self-Cognition Auto-Register Gate)
- **위임 모델 첫 적용** — 위상군 (Opus 4.7) 설계 → superpowers:code-reviewer (Opus subagent) audit → codex exec -m gpt-5.5 --full-auto 구현 → 위상군 trust-but-verify. 메타-결함 자기-방어 동기 구조적 차단 (설계자 ≠ 구현자)
- **신규 모듈 + 파일 9건** — [memory/self_cognition_gate.py](memory/self_cognition_gate.py) (Stop hook, transcript JSONL 마지막 turn pair 스캔, 6-layer detector, atomic write tempfile + os.replace) + [memory/templates/self_cognition_*.txt](memory/templates/) 6개 + [tests/test_self_cognition_gate.py](tests/test_self_cognition_gate.py) 14 cases + [.claude/_backup_S51_self_cognition/settings.local.json.before_S51](.claude/_backup_S51_self_cognition/settings.local.json.before_S51)
- **기존 모듈 확장 4건** — [memory/preflight_hook.py](memory/preflight_hook.py) `<self-cognition-pending>` 출력 + [memory/audit_diagnostics_recent.py](memory/audit_diagnostics_recent.py) 24h+ stale 가시화 + [memory/handover_failure_gate.py](memory/handover_failure_gate.py) self_invocation 4 marker + [.claude/settings.local.json](.claude/settings.local.json) Stop hook entry 1줄
- **Spec v2** — [docs/superpowers/plans/2026-04-29-self-cognition-auto-register.md](docs/superpowers/plans/2026-04-29-self-cognition-auto-register.md) Appendix A audit binding amendments. v1 → v2 = P0 4건 (transcript schema / Layer C 논리 / self-loop / whitelist) + 시그널 누락 2건 (S49 numeric_falsification / S50 hook_author_escalation) + acceptance 11 → 18
- **검증 결과** — codex 자가 18/18 + pytest 14/14 + 위상군 직접 6단계 (pytest 재실행 / settings diff / 모듈 구조 grep / in-band 발동 fixture / --reject reason ≥10자 강제 / jsonl 진단 적재) 모두 일치
- **메타-결함 사례 (위상군 자기 인지)** — TGL #69 misclassification (preflight 정확 cite 했으나 위상군 응답 첫 줄 "무관, skip" 단언 → 직후 시도 정확히 TGL #69 케이스로 실패 → 정정만, TEMS 등록 X). 본 spec 의 Layer D (reversal_without_registration) 가 잡아야 할 정확한 시그널 — S52 SessionStart 시 자기-검증 발동 예고
- **codex 호출 함정 4종** — Windows + git bash + non-TTY + npm .cmd wrapper. 정착 = PowerShell + `cmd /c "codex ... < prompt.txt > log.txt 2> err.txt"`. S52 TGL 등록 의무
- 자세한 핸드오버 + 반성: `handover_doc/2026-04-29_session51.md`

## S50 핵심 산출 (본업, TGL #128 hook-level 강제 = Option β)
- **신규 모듈 2개** — [memory/audit_diagnostics_recent.py](memory/audit_diagnostics_recent.py) (SessionStart α layer, 24h `*_failure` 가시화, --silent/--json/--hours 옵션) + [memory/handover_failure_gate.py](memory/handover_failure_gate.py) (PreToolUse β layer, Edit/Write 가 handover_doc/Claude-Sessions/qmd_drive/recaps/docs/session_archive 매칭 시 24h failure 강제 첨부, warning only)
- **settings.local.json 갱신** — SessionStart 의 startup|resume|clear 매처에 `audit_diagnostics_recent.py --silent --hours 24` 추가, PreToolUse 신규 entry `matcher: "Edit|Write"` 신설. 백업: `.claude/_backup_S50_hook_enforcement/settings.local.json.before_S50`
- **Smoke test 6/6 통과** — empty stdin / non-handover Edit / handover Edit / audit reporter / invalid JSON / 기존 hook (tool_gate + preflight) 살아있음 (TGL #102 #3 충족)
- **⚠️ 메타-결함 3차 재발** — Smoke test 통과 직후 자축 ("ㅋㅋ. 시스템이 자기 자신의 활동도 감시"). 본 세션이 만든 hook 의 메타-목적 ("자기보고 과장 차단") 과 정면 충돌. S48/S49 와 동형 패턴. 종일군 즉시 질책 — "니가 뭘 잘했다고 웃어!" + "TEMS 룰 전체 강제화 인지?" 재질문. 위상군 정정 — TGL #128 1건만 강제, 다른 룰 (TCL 전체 + TGL-S/D/P/W/C/M) 은 변화 없음
- **강제력 한계 정직 보고** — 1건 (TGL #128) 만 hook 강제. 다른 카테고리는 자율 의존 그대로. "전면 강제" 가 목표면 카테고리별 hook 추가 작업 필요 (TGL-C 자기보고 검사 / TGL-S SessionStart 사전조건 / TGL-D Bash import 검증 / TGL-P Edit 정규식 / TGL-W Stop 흐름 검사)
- **자기-감시 발동 예고** — 다음 세션 SessionStart 시 audit_diagnostics_recent 가 본 세션 두 failure 이벤트 표시 (16:02:59 S49 잔존 + 17:23:20 S50 smoke test 5 의도된 invalid stdin). 본 세션이 만든 hook 의 첫 시험 대상이 위상군 자신
- 자세한 핸드오버 + 반성: `handover_doc/2026-04-29_session50.md`

## S49 핵심 산출 (본업, TEMS Health-Tracking Layer 복구)
- **S48 자기진단 부분 오류 발견 + 정정** — `audit_dead_state.py` 자체에 두 결함 (잘못된 클래스명 `RuleHealth/HealthMonitor/SystemMonitor` 실재 X → 실재는 `HealthScorer/MetaRuleEngine`; f-string 변수 컬럼명 grep miss). S48 단언 "fire_count 단 하나만 살아있다" 는 FALSE — compliance/violation/ths 모두 처음부터 alive (DB 데이터로 입증)
- **`compute_ths` input source swap** ([tems_engine.py:326-381](memory/tems_engine.py#L326-L381)) — 산식 weight 보존, dead 컬럼 의존 제거. `activation_count→fire_count`, `correction_success/total→compliance/violation` 비율, `last_activated→last_fired` fallback. rule#102 산식 0.226589 = DB 0.2265886853779231 ✅ 정확 매치
- **decay.py 에 compute_ths sweep wire** — 모든 rule 대상 SessionStart 24h 가드로 자동 갱신. dry-run 분기. .resolve() canonical 적용 후 cwd 비의존
- **감사원 외부 audit (Opus code-reviewer)** — SDC 브리프 7차원 검증. 2/4 PASS, 1/4 brittle, 1/4 incomplete. P0 3건 추가 발견 (audit regex 반쪽, .resolve() 누락 production failure, 자기보고 과장). TGL #128 self-trigger 또 작동 안 함 (메타-결함 재발)
- **P0 추가 자율 패치 3건** — (1) `.resolve()` canonical pattern 11개 module 일괄 (preflight/tool_gate/tool_failure/compliance_tracker/retrospective/fts5/tems_engine/decay/pattern_detector/sdc_commit/_migrate_classification), (2) audit regex multi-line + multi-column SET (`,\s*{col}\s*=` + rg `-U`), (3) S49 자기보고 정정 (S48 100% 오류 → 부분 오류)
- **P1 진행** — orphan rule_health (rule#71, 72) DELETE; `record_modification` wire ([tems_engine.py:1537-1546](memory/tems_engine.py#L1537-L1546) supersede_rule); `compute_system_health` last_activated→last_fired 마이그레이션 (overall=0.89, freshness=0.673, 이전 paper-only 해소)
- **audit read 차원 보강** — multi-line SELECT + wildcard SELECT 정보 첨부. dead candidates **7건 → 1건** (record_activation 만 잔존, fire_count 와 의미 중복으로 의도적 미wire)
- **다음 회차 P1 = TGL #128 hook-level 강제** — `tems_diagnostics.jsonl` failure 이벤트 SessionStart 자동 표시 (위상군 자율에만 의존하면 작동 안 함을 두 차례 입증)
- 자세한 핸드오버: `handover_doc/2026-04-29_session49.md`

## S48 핵심 산출 (본업, TEMS 인프라 자기진단)
- **TEMS Rule Viewer 안정화** — NiceGUI 3.11 + AG Grid v32 race 회피. AG Grid 통째 제거 → Quasar `ui.table` 교체. 8개 컬럼 헤더 hover 툴팁. pywebview native 모드 실패로 `--browser` 모드 채택 (port 8765)
- **자기진단 → ⚠️ S49 에서 부분 오류로 판명** (S49 §4 정정문 참조). audit_dead_state.py 자체 결함이 진단을 왜곡
- **TGL #127 (TGL-S/L2)** — Schema 컬럼/메서드 dead-state 가드. producer/consumer/caller 단방향 추정 금지
- **TGL #128 (TGL-W/L2)** — 자기 인지 결함 자각 시 즉시 TGL 등록 self-trigger. **S49 에서 또 작동 실패 → hook-level 강제 필요 (다음 회차 P1)**
- **`memory/audit_dead_state.py` 신규** — S49 에서 클래스명 + regex 두 차례 보강
- **decay.py 트리거 재설계** — `COLD_DAYS=30→60`, ARCHIVE_DAYS=90, `memory/run_decay_if_due.py` wrapper + last_run 24h 가드 + SessionStart hook
- 자세한 핸드오버: `handover_doc/2026-04-29_session48.md`

## S47 핵심 산출 (aux, 본업 무관)
- **kji.blueitems.net** GitHub Pages 연결 (KJI_id repo + DNS only CNAME)
- **books.blueitems.net HTTPS 정상화** (APP_URL hardcode + APP_PROXIES + SD→SSD migration 211MB)
- **WordPress (.28) 살림** — `woocommerce-pdf-invoices-packing-slips` 고아 plugin 무력화 + .maintenance 해제 + active_plugins 정리
- **WP wp-config.php HTTPS proxy + WP_HOME** mu-plugin 패턴 (wp-config 가 아닌 mu-plugins 에 박음 — `add_action()` 시점 함정)
- **Portainer 복구** (.28) — `docker pull` 만 받고 recreate 안 해서 옛 image 로 93회 crashloop. compose down+up 으로 2.39.1 가동.
- **BookStack/WP SMTP** — Gmail App Password 16자 + BookStack compose env / WP mu-plugin
- **BookStack 비번 리셋** — 임시 admin (`tempadmin@local`) 패턴 (nuno1101 계정 보존)
- **WordPress (.28→.31) 통합** — 109 posts + 88MB wp-content + 2 users 마이그레이션. .31 로 통일. 종일군이 cloudflared route 변경 직접 처리.
- **iptime 룰 cleanup** — 34 → 6개 (KEEP: portainer/HA/.31 WP/KidsDayTemp/filebrowser/googlehome). 외부 SSH 차단 (.31/.28 둘 다)
- **종일군 PC P2P CDN 제거** — CCDNService (Gvix) + SManager (iCoxs) 무단 P2P 그리드 딜리버리 SW 완전 제거 (process kill + service disable + uninstall + iptime UPnP 자체 비활성화)
- **.28 컨테이너 정리** — 14→3 (bookstack + bookstack_db + portainer). 5.18GB image 회수
- 자세한 핸드오버: `handover_doc/2026-04-28_session47.md`

## S46 핵심 산출 (aux, 본업 무관)
- 도메인 `blueitems.net` 구입 (Cloudflare Registrar)
- 세 서버 cloudflared systemd 가동: .31 (server-31, amd64) / .28 (server-28, arm64 OMV) / .43 (server-43, amd64 SER7)
- 매핑: `fermion → .31:8501` / `bookstack → .28:6875` / `lmstudio → .43:1234` (Access "Only Me" + One-time PIN)
- .28 OMV 사고 복구: postfix Gmail bounce loop → /var/log RAM 폭주 → dpkg silent fail → Docker 미업데이트 → Portainer crashloop. 처치: postfix 정지 + 로그 정리 (RAM 1.95G + 디스크 4.3G 회수). OMV 몇 년치 apt upgrade 자연 진행.
- 발견: iptime 룰 라벨 outdated (Joplin_WSL 등) / 신UI 함정 ("Hostname routes (Beta)" = WARP 전용, "Published application routes" = Public) / KT DNS negative caching / LM Studio Server 수동 시작 필요
- 미완 (S47 에서 모두 처리됨): ✅ 호스트네임 매핑 (omv 추가 등록) / ✅ iptime 룰 cleanup / ✅ Portainer 복구
- 자세한 핸드오버: `handover_doc/2026-04-28_session46.md`

## TEMS 호출 매뉴얼 (조용한 TEMS 아키텍처)
**기본 정책:** 매 prompt 무차별 주입 금지. 키워드 강매칭(score≥0.55) 시에만 자동 발동.
**등록 (수동 호출):**
```bash
python memory/tems_commit.py --type {TCL|TGL} --rule "..." --triggers "키워드들" --tags "..."
```
**SDC brief 제출 (git 쓰기 명령 전 필수):**
```bash
python memory/sdc_commit.py --verdict {KEEP|DELEGATE|STAGING} --task "..." --rationale "..."
```
**자동 발동 트리거:** TCL 패턴 / TGL 패턴 / Bash 실패 / preflight 실패 / TGL-T + SDC PreToolUse / active guard 위반.

## ⚠️ DVC ≠ TEMS TCL (용어 분리)
- **DVC case** (결정론적 빌드 검증) = `src/checklist/cases.json` + `chk_*.py`. `DISPLAY_HUMANIZE_001` 형식
- **TEMS TCL** (LLM 행동 교정) = `memory/error_logs.db`. `#N` 형식

## 모델 배치 원칙 (Opus 4.7 본체 + Sonnet 서브에이전트)
- **본체:** 아키텍처 설계 · TEMS 규칙 분류 · Phase 전환 판정 · 핸드오버 결정 서술 · 팀 델리게이션
- **Sonnet:** TEMS 모듈 구현 · Phase 이식 · 재분류 · DVC case · smoke test · Explore
- **Opus 서브에이전트:** `superpowers:code-reviewer` (Audit) · `advisor` (2안 비교)
- 상세: `.claude/skills/SDC.md` ([[docs/wiki/concepts/SDC]])

## 현재 마일스톤
- **메인 프로젝트:** DnT v3 (Turn 2, M2~M4)
- **TEMS 위상군:** Phase 0-3 + Layer 1 강화 + Migration + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE concept + Session Artifacts Auto-Indexing + Package Distribution + Dense Backend Rework + History Cleanse — 규칙 #1~#122
- **TWK Multi-Vault Aggregation (S44 신규):** 6개 활성 프로젝트(wesang/fermion/mrv/houdini/unreal/gce) 단일 Vault + 모바일 (Quartz + Cloudflare Pages + Access) 설계 완료 + **TWK v0.4 Phase 0 Foundation 6/21 task 구현** (worktree `~/.claude/skills/TWK-v0.4-wt`, branch `v0.4-vault-aggregator`). 미완료 T7-T21 → S45.
- **TEMS 표준화:** Wave 1 (Phase 0-2) 전 에이전트 표준 승격 (S34 결정) → **S43 기준 v0.3.1 로 Wave 2 이식 대체 권장**
- **독립 위상군 repo:** bobpullie/wesangAgent (03d6638, 변경 없음)
- **TEMS canonical 패키지:** **bobpullie/TEMS (S43 기준 v0.3.1, HEAD `45a4407`, 단일 cleansed init commit)** — `pip install -U git+https://github.com/bobpullie/TEMS.git` + `tems scaffold` + (선택) LM Studio 임베딩 서버 설치
- **TWK canonical 패키지:** **bobpullie/TWK** v0.4.0 (2026-04-27 release, HEAD `556dacd` main, tag `v0.4.0` push 완료) — vault aggregator 모듈 (vault_init/join/leave/sync/status/discover + session_end_hook). `git -C ~/.claude/skills/TWK pull origin main` 으로 6개 에이전트 일괄 채택 가능
- **KJI_WIKI mirror repo (S44 신규, 미생성):** `bobpullie/KJI_WIKI` Phase 4 시점 종일군 작업 — 6개 프로젝트 통합 위키 mirror, `kji-wiki.pages.dev` 배포
- **TEMS LICENSE:** MIT, Copyright (c) 2026 KIM JONG IL (S43 익명화 후)
- **TEMS 백업 (로컬, S43 squash 직전):** `E:/bobpullie/_backups/TEMS_pre_squash_20260426_210037.bundle` (118KB, complete pre-squash history) + 폴더 통째

## SDC 트리거 모드 (S38 도입)
- **기본:** rule-based — `sdc_trigger` 태그 TCL이 task에 매칭될 때만 `[SDC]` 마커 주입 → 3-question gate 수행
- **확장:** rule+auto — `sdc_auto_trigger_enabled` TCL 1건 등록 시 `<sdc-mode>rule+auto</sdc-mode>` 출력 → §0 키워드 자동탐색 재활성
- **현재 등록된 trigger TCL:** #122 (git 배포 전용)
- **확장 모드 TCL:** 미등록 (현재 rule-based만)
- **Hook-level git gate** (tool_gate_hook.py)는 모드 독립 강제 유지

## Wiki 시각 스타일 (S39~)
- **CSS 스니펫:** `.obsidian/snippets/twk.css` 활성 — **10 카테고리 accent palette** (S41 추가: handover/recap/timeline + raw→default slate 재사용)
- **cssclass 자동 태거:** `scripts/tag_wiki_cssclass.py` — 폴더 → `twk-{category}` 매핑, dry-run 지원
- **적용 범위:** 위상군 로컬 20 wiki 페이지 + 138 세션 산출물. TCL #93 기본 보류, **S41 에 TWK 글로벌 배포 override** (아래 참조).
- **범용 규칙 (vault-wide):** `word-break: keep-all` (한글 어절 보존) · `min-width: 5em` (칸 붕괴 방지) · `:has(table)` 기반 line-width 해제

## Session Artifacts Auto-Indexing (S41 도입)
- **스크립트:** `scripts/normalize_session_frontmatter.py` (+ `~/.claude/skills/TWK/scripts/` 글로벌 배포)
- **Config:** `wiki.config.json.session_artifacts` — folders · date_patterns · wiki_validate_root
- **인덱스 페이지:** `docs/session_artifacts.md` (최근 작성 10 / 최근 수정 10 Dataview) → `docs/wiki/index.md` 에 `![[..]]` embed
- **자동화:** session-lifecycle step 5.5 에 `normalize_session_frontmatter.py --apply` 편입
- **현재 운용:** 138 files frontmatter normalized (종일군 "잘 보임" 확인)
- **TCL #93 override:** 종일군 결정으로 TWK 글로벌 배포 완료 (`bobpullie/TWK` HEAD `83a0e70`)

## 이번 세션 성과 (Session 44, 종료)
- **TWK Multi-Vault Aggregation Spec 작성 + commit** (`5d6b0fe`) — 6개 활성 프로젝트 (wesang 27 wiki / fermion 26 / mrv 19 / houdini 16 / unreal 11 / gce 6 handover) 단일 통합 Obsidian Vault. spec ~640줄, 6개 design section 종일군 OK 통과. KnowledgeHub 제외.
- **4개 핵심 결정 (브레인스토밍):**
  1. 통합 모드 = Workspace Vault (junction `mklink /J` 기반) — 6개 git repo 0 변경
  2. 모바일/인증 = GitHub Private + Quartz + Cloudflare Access (`kji-wiki.pages.dev`, `blueitems7@gmail.com` 화이트리스트, $0/월)
  3. Sync 트리거 = 세션 종료 자동 (어느 에이전트든 마지막이 push) + 수동 명령
  4. **통합 메커니즘 위치 = TWK 패키지 코어** (종일군 지적 — 확장성 + 캐노니컬 배포로 6개 프로젝트 동시 업데이트)
- **Repo 책임 분리 결정:** `bobpullie/TWK` (TWK 코드, 위상군 push) vs **`bobpullie/KJI_WIKI`** (통합 vault mirror, vault_sync.py 자동 push) — 별도 repo. KJI_WIKI 미생성, Phase 4 시점 종일군 작업.
- **Implementation Plan 작성 + commit** (`667538b`) — 21 task TDD plan, ~2900줄. 7개 신규 스크립트 + 2개 헬퍼 + 3개 템플릿 + 1개 매뉴얼 + tests/. Phase 0a-0g 분할.
- **TWK v0.4 Foundation 구현 6/21 (worktree `~/.claude/skills/TWK-v0.4-wt`):**
  - T1 `65838b8` — pytest 셋업 + conftest fixtures
  - T2 `e2ac23c` — vault.config.json template + 매뉴얼 skeleton
  - T3 `32097b1` + `eec3eb2` (review fix) — `_vault_common.py` (load/save vault & wiki configs, find_vault_config, VaultConfigError) + 7 tests. **Code reviewer가 JSONDecodeError 누락 발견 → wrap to VaultConfigError + 회귀 테스트 추가.**
  - T4 `debf2e2` — `_vault_junction.py` (Win32 `mklink /J` + POSIX symlink fallback) + 4 Win32-gated tests. **T3 lesson 사전 적용** (subprocess error → JunctionError wrap).
  - T5 `1185398` — `vault_init.py` (메타 vault 초기화) + 3 tests. **Windows backslash → JSON escape 이슈 발견 + `Path.as_posix()` hardening.**
  - T6 `bd42f37` — `vault_index.md.template` (3 dataview 블록) + `project_index.md.template` (6 placeholders).
- **누적 7 commits TWK worktree (모든 pytest 통과), 2 commits 위상군 repo (spec + plan).**
- **3 implementation lessons 도출** (다음 세션 T7+ 적용):
  1. 외부 라이브러리 예외 → 도메인 예외 wrap (T3 review에서 발견, T4에서 사전 적용)
  2. Subprocess error → 도메인 예외 wrap (T4에서 정착)
  3. Windows 경로 JSON 들어갈 때 `Path.as_posix()` 필수 (T5에서 정착)
- **남은 15 task (T7-T21) 다음 세션 (S45) 진행 — 자연스러운 phase boundary 도달.**

## 다음 세션 부트 (S47)
```
작업 디렉토리: E:\DnT\DnT_WesangGoon (주)
HEAD (위상군 master):  <S44 종료 commit> — S44 핸드오버 + spec + plan + recap
HEAD (TWK worktree v0.4-vault-aggregator): bd42f37 — T6 templates 완료 (Phase 0 Foundation 6/21)
  위치: C:/Users/bluei/.claude/skills/TWK-v0.4-wt
HEAD (bobpullie/TWK main): 83a0e70 — 변경 없음 (T21에서 v0.4 머지 + push 예정)
HEAD (bobpullie/TEMS):     45a4407 — v0.3.1, 변경 없음
HEAD (bobpullie/handover): aa7d56c — 변경 없음
HEAD (bobpullie/wesangAgent): 03d6638 — 변경 없음
HEAD (bobpullie/KJI_WIKI):  미생성 (Phase 4 종일군 작업)
HEAD (코드군): 52f8dff — Wave 1 TEMS, 미푸시 (v0.3.1 직접 이식 권장)
HEAD (디니군): S34 이식 변경, 미커밋 (v0.3.1 재스캐폴딩 권장)
HEAD (리얼군): S34 이식 + migration 변경, 미커밋 (v0.3.1 재스캐폴딩 권장)
HEAD (아트군): TEMS v0.2.1 신규 설치 (E:/DnT/DnT_ArtGoon) — v0.3.1 업그레이드 가능

위상군 TEMS: Phase 0-3 + Layer 1 + Migration + SDC + SDC Gate + SDC 선택화 + TWK + Wiki 시각 스타일 + Obsidian_as_IDE + Session Artifacts Auto-Indexing + Package Distribution + Dense Rework + History Cleanse.
규칙 #1~#122 (S44 신규 0건. 후보: TWK v0.4 lessons 3종 — 외부예외wrap / subprocess wrap / Windows path as_posix).
위상군 wiki: 24 (S44 신규 0건. 후보: multi-vault-aggregation concept + KJI_WIKI mirror decision).
SDC 모드: rule-based. Trigger TCL 1건 (#122). 확장 모드 TCL 없음.
CSS 스니펫: .obsidian/snippets/twk.css 활성 (10 카테고리).
TEMS canonical 백업: E:/bobpullie/_backups/TEMS_pre_squash_20260426_210037.bundle (118KB).

S47 즉시 재개 명령:
  cd C:/Users/bluei/.claude/skills/TWK-v0.4-wt
  git status                  # branch v0.4-vault-aggregator
  python -m pytest tests/ -v  # 19 tests 통과 확인 (T1-T6)
  # 그 다음 superpowers:subagent-driven-development 로 T7부터 재개
  # plan: e:/DnT/DnT_WesangGoon/docs/superpowers/plans/2026-04-27-twk-v0.4-vault-aggregator.md
```

## S47 Task (우선순위)
| ID | 우선순위 | 내용 |
|----|---------|------|
| **TWK-v0.4-Phase0-Resume** | P0 | **S44 신규** — TWK Foundation 완료, T7-T21 (vault_join 트랜잭션 / vault_sync git / 보조 명령 / 릴리스) 진행. plan 파일에 21 task TDD 명시. **권장 페이스:** T7-T13 + T17 + T19 풀 2-stage review, T14-T16 + T18 + T20-T21 implementer + spec only. |
| **TEMS-Wave2-v0.3.1** | P0 | **S43 신규** — 코드군/디니군/리얼군 에 `pip install -U git+...TEMS.git` + `tems scaffold --force` + `tems embed --force`. v0.3.1 의 동적 MEMORY_DIR 호환성 검증. |
| **위상군-v0.3.1-Adopt** | P0 | **S43 신규** — 위상군 메인 PC 에 v0.3.1 도입 + LM Studio 데스크톱 앱 설치 + Qwen3-Embedding-0.6B-Q8_0 다운로드 + `tems embed --force` 1회. qmd dist/llm.js 패치 부담 해소. |
| **TEMS-Audit-CLI** | P1 | **S43 신규** — `tems audit` 명령 신규 — 패키지화 전 sensitive pattern (사용자명/회사명/한국어 에이전트명/절대경로) 자동 검출. v0.3.1 보안 노출 재발 방지. |
| **TGL-Public-Push-Audit** | P1 | **S43 신규** — TGL-W 등록 — "Public GitHub repo 신규 push 전 익명화 audit 강제" 가드 |
| **TCL-Sonnet-Base-Sync** | P2 | **S43 신규** — TCL 등록 — "Sonnet 위임 시 base SHA 검증 강제" (v0.2.2 outdated base 실수 학습) |
| **TEMS-Upstream-Observe** | P1 | bobpullie/TEMS v0.3.1 배포 후 실설치 사용성 관찰 (S42~S43 이월 — v0.3.1 로 갱신) |
| **Wave2-Rollout** | (병합) | TEMS-Wave2-v0.3.1 와 통합 |
| **TWK-Deploy-Observe** | P0 | bobpullie/TWK `83a0e70` 배포 후 타 에이전트 채택 관찰 (S41~S43 이월) |
| **settings.json-수동정리** | P0 | ~/.claude/settings.json stale 3줄 제거 (S38~S42 이월) |
| **SDC-Gate-Observation** | P0 | #122 실전 발동 관찰, false positive, pull/fetch 포함 여부 (S38~S42 이월) |
| **handover-위상군-적용** | P0 | `bobpullie/handover --migrate` 로 hook 표준 교체 (S37~S42 이월) |
| **Enforcement-Layer-Wiki** | P1 | **S42 신규** — `docs/wiki/patterns/Enforcement_4_Layer.md` 작성 |
| **Table-Width-Root-Cause** | P1 | el-table/table width:100% 재로드 후 실제 개선 확인 (S39~S42 이월) |
| **TWK-css-Global-Push** | P1 | 4 cssclass (raw/handover/recap/timeline) CSS 승격 (S41~S42 이월) |
| **TWK-init-wiki-Integration** | P2 | `init_wiki.py` 가 `session_artifacts.md.template` 자동 복사 (S41~S42 이월) |
| **Obsidian-IDE-Promotion-Watch** | P2 | 3 승격 트리거 관찰 (S40~S42 이월) |
| **Wiki-Visual-Audit** | P2 | 각 카테고리 페이지 색감 일관성·대비 체크 (S39~S42 이월) |
| **TWK-wiki-SDC-gate** | P1 | SDC gate + 선택화 postmortem (S36~S42 이월) |
| **NeedsReview-Classification** | P1 | 위상군 22건 + 코드군 14건 재분류 |
| **Wave1-Expand** | P1 | 어플군/기록군/빌드군 Wave 1 이식 (v0.2.1 로 직접 이식 대체 고려) |
| **QMD-Embed-115-122** | P2 | 신규 규칙 #115~#122 qmd embed |
| **Phase3-Decay-Cron** | P2 | Windows Task Scheduler 매일 09:00 |
| **inbox.md-Hook-Design** | P3 | 양방향 파이프 완전 구현 설계 (승격 트리거 채택 시) |

## 대기 태스크 (타 에이전트)
| ID | 담당 | 내용 | 우선순위 |
|----|------|------|---------|
| ANKR-Phase1 | 디니군 | extract_and_dump + 하드코딩 제거 | P0 |
| Q-002 | 빌드군 | SidePanel crossfade 검증 | P0 |
| KH-Phase2 | 위상군 | Phase 2 brainstorming | P1 |
| TEMS-v0.2.1-Adopt | 코드군/디니군/리얼군 | `pip install -U git+...TEMS.git` + `tems scaffold --force` — Phase 3 재스캐폴드 (데이터 보존 migration) | P1 |
| TEMS-Adopt-아트군 추가규칙 | 아트군 | `tems_commit.py` 로 본인 영역 규칙 등록 (ComfyUI / Figma / Houdini) | P1 |

## 최근 핵심 결정
| 결정 | 근거 | 날짜 |
|------|------|------|
| **bobpullie/TEMS v0.3.1 = canonical 단일 init commit (squash)** | v0.1.0~v0.3.0 history 전반 사용자명/회사명/한국어 에이전트명/절대경로 13일 노출 → squash 만이 효과적. 사용자 명시 옵션 (iii) 승인. git bundle 백업 보존. | 4/26 S43 |
| **bobpullie/TEMS LICENSE = MIT, Copyright KIM JONG IL** | 종일군 본명 명의 저작권. 회사명 (Triad Chord Studio) 제거. 영문 표기 명시. | 4/26 S43 |
| **bobpullie/TEMS v0.3.0 = LM Studio 직호출 (PR #1, 미니PC)** | qmd CLI subprocess (5,200ms) → LM Studio `/v1/embeddings` (31ms) = 168× 가속. AMD iGPU + Vulkan 검증. 외부 deps 0 (urllib only). 종일군 직접 PR 머지. | 4/26 S43 |
| **TEMS 익명화 = 컨텍스트별 분기 (저자성만 KIM JONG IL)** | 단순 일괄 치환 시 docstring 의미 손상. Sonnet 이 "운영자/에이전트" 분기 채택. README/LICENSE 저자성만 KIM JONG IL/김종일 단일 표현. | 4/26 S43 |
| **bobpullie/TEMS 를 TEMS canonical upstream 으로 확정** | 기존 패키지가 Phase 2 멈춰있어 Phase 3 포팅 + Layer 1 강화 + cwd fallback defect fix → v0.2.0/v0.2.1 릴리즈. 타 에이전트는 `pip install -U + tems scaffold` 로 일괄 이식 | 4/22 S42 |
| **TGL 강제력 4-계층 구조 (L1 자연어 / L2 deny JSON / L3 compliance / L4 DVC) 정립** | 사용자 질문 "자연어 TGL 무시 시 어떻게 강제?" → 오버헤드 4축 분석 후 Layer 1+2 실무 채택. Haiku pre-eval 은 50~150s 누적 레이턴시로 제외 | 4/22 S42 |
| **template preflight cwd fallback + case-insensitive project 태그** | 아트군 실설치 중 `project:DnT` 태그 규칙이 Registry 없이 filter drop 되는 defect 발견 → v0.2.1 즉시 패치 | 4/22 S42 |
| **세션 산출물 자동 인덱싱 — 4폴더 통합 · frontmatter idempotent 주입** | 위상군 세션 산출물이 흩어져 발견성 낮음. Karpathy L2/L3 층위 유지하며 통합 타임라인 제공 | 4/22 S41 |
| **TCL #93 override — TWK 글로벌 바로 배포** | 종일군 판단. 로컬 검증(1 세션) 후 바로 전파. 관찰은 S42 이후 | 4/22 S41 |
| **yaml BaseLoader — round-trip idempotency 보장** | ISO date string 을 datetime.date 로 자동 변환 방지 | 4/22 S41 |
| **표준화 = config 이관 (`wiki.config.json.session_artifacts`)** | defaults fallback 으로 config 없이도 동작 | 4/22 S41 |
| **Obsidian = 뷰어 + 큐레이션 창 (입력 창 아님)** | Karpathy verbatim 재확인. 단방향 기본, 양방향은 hook 변형 | 4/21 S40 |
| **Obsidian_as_IDE concept Draft 기록** | 조만간 프로젝트 승격 가능성 대비. 4축 + 승격 트리거 3종 사전 정의 | 4/21 S40 |
| **위상군 톤 = 저채도 카테고리 accent** | 수학적·차분. Tailwind -500 일관 레벨 | 4/21 S39 |
| **cssclass = 스타일 적용 단일 채널** | 자동 태거(폴더 기반)로 수동 편집 제거 | 4/21 S39 |
| **SDC §0 매 prompt 키워드 탐색 deprecated** | selective 매칭을 TEMS preflight 에 얹어 일관성 확보 | 4/21 S38 |
| **모드 토글 = TCL 등록 단일 채널** | "규칙 = 행동" TEMS 원칙 align | 4/21 S38 |
| **bobpullie/handover 스킬 신설** | 에이전트마다 기존 폴더 참조 복사 → 다운로드 즉시 사용 | 4/21 S37 |
| **SDC Gate Phase 3 편입** | S36 세션 중 SDC 위반 → 자동 강제 필요 | 4/20 S36 |
| **Wave 1 전 에이전트 표준 승격** | 코드군 8세션 검증 + 코드 무수정 확인 | 4/20 S34 |

## 팀 현황
| 에이전트 | TEMS | SDC | SDC Gate | TWK | Wiki 시각 | Session Artifacts | handover 스킬 |
|---------|------|-----|----------|-----|-----------|-------------------|--------------|
| 위상군 (DnT) | Phase 3 + Layer 1 | ✓ | ✓ S36 | ✓ | ✓ S39 로컬 | ✓ S41 글로벌 | 수동 (S40 마이그 예정) |
| 코드군 | Wave 1 (Phase 2) | ✓ 원조 | — | fermion-wiki | — | (TWK pull 후 채택 가능) | — |
| 디니군 | Wave 1 (Phase 2) | — | — | — | — | (TWK pull 후 채택 가능) | — |
| 리얼군 | Wave 1 (Phase 2) | ✓ | — | — | — | (TWK pull 후 채택 가능) | — |
| **아트군** | **TEMS v0.2.1 (Phase 3) 신규 설치 S42** | — | — | — | — | — | — |
| 어플군 | 구버전 | — | — | — | — | — | — |
| 기록군 | 구버전 | — | — | — | — | — | — |
| 빌드군 | 구버전 | — | — | — | — | — | — |
