---
date: 2026-04-29
type: plan
session: S51
cssclass: twk-plan
tags: [plan, tems, hook, self-cognition, tgl-128, meta-defect]
status: draft-v2
audit: applied (Opus code-reviewer 2026-04-29)
---

# TEMS Self-Cognition Auto-Register Gate — 설계 Spec v2 (S51)

> **목적:** 자기실수 인지 시점에 TCL/TGL 등록을 **구조적으로 강제**하는 TEMS 근본 메커니즘 추가. S48/S49/S50 메타-결함 3차 재발 종단 차단.
> **위임 모델:** 위상군 (Opus 4.7) 설계 → `superpowers:code-reviewer` (Opus subagent) audit ✅ → `codex exec -m gpt-5.5 --full-auto -C E:/DnT/DnT_WesangGoon` 구현 → 위상군 trust-but-verify.
> **TGL #89 동형 패턴 인용:** "자율 의존 → 사용률 0% 수렴 / preflight hook 구조적 강제 필요." 본 설계는 동형 해법.
> **v2 변경:** Audit P0 4건 + 누락 시그널 2건 본문 반영 (Appendix A 참조). v1 vs v2 diff 는 이력만 — 시행은 v2 단일.

---

## 1. 문제 정의

### 1.1 직전 실패 (TGL #128 hook 한계)
- α (`audit_diagnostics_recent.py`) + β (`handover_failure_gate.py`) 는 **jsonl `*_failure` 이벤트** (production exception) 만 잡음
- 자기실수 인지의 다른 형태 — **자축어, 절대화, 사용자 질책 후 정정 누락, 수치 자가-감사 위조** — 미커버
- TGL #128 본문 자연어 룰 ("자기 인지 결함 자각 시 즉시 self-trigger") 자율 의존 → S48/S49/S50 3회 연속 미발동

### 1.2 동형 패턴 (TGL #89)
> "Atlas drill-down 이 에이전트 자발적 판단에만 의존하면 사용률이 0%로 수렴한다 ... preflight hook 에서 atlas-hint 를 주입하는 구조적 강제가 필요하다."

자기실수 인지/등록도 동일. 자율 의존 → 0%. 구조적 강제 = hook 자동 감지 + draft 생성 + 다음 prompt 강제 주입.

---

## 2. 설계 개요

### 2.1 신규 모듈 1개 + 기존 모듈 1개 확장 + 기존 모듈 1개 확장

| 파일 | 역할 |
|------|------|
| **신규** [memory/self_cognition_gate.py](memory/self_cognition_gate.py) | Stop hook. transcript 의 마지막 turn pair 스캔 → 6-layer detector (§3) 실행 → draft 생성 → pending 디렉토리 적재 + jsonl 기록 |
| **확장** [memory/preflight_hook.py](memory/preflight_hook.py) | UserPromptSubmit 시 `pending_self_cognition/*.json` 존재 시 `<self-cognition-pending>` 블록 강제 출력 (해소까지 누적) |
| **확장** [memory/audit_diagnostics_recent.py](memory/audit_diagnostics_recent.py) | SessionStart 시 24h 이상 stale pending draft 가시화 — `<self-cognition-stale count="N" oldest="...">` |

### 2.2 Transcript 입력 스키마 (P0 fix)

Claude Code Stop hook 은 stdin 으로 다음 JSON 전달:
```json
{"session_id": "...", "transcript_path": "C:/.../<id>.jsonl", "stop_hook_active": false, ...}
```

`transcript_path` 는 **JSONL 파일** — 라인별 객체. 핵심 형태:
```json
{"type": "user", "message": {"role": "user", "content": "..."}}
{"type": "assistant", "message": {"role": "assistant", "content": [
  {"type": "text", "text": "위상군 응답 텍스트"},
  {"type": "tool_use", "name": "Edit", "input": {"file_path": "...", "old_string": "...", "new_string": "..."}}
]}}
{"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", ...}]}}
```

**파싱 규칙 (binding):**
1. JSONL 라인별 read. 마지막 라인 truncated 시 graceful skip (try/except json).
2. `﻿` BOM 첫 라인에서 strip.
3. **Turn 재구성**: 연속 assistant 라인 (tool_use → tool_result → text → tool_use ...) 을 하나의 "assistant turn" 으로 그룹. user 라인 만나면 새 turn.
4. **마지막 turn pair = (last user turn, last assistant turn)**. assistant turn 안에서 N=4 라인까지 거슬러 capture (Layer A의 'rebuke without prior claim' edge 대응).
5. 각 라인의 `content` 처리:
   - `content` 가 `str` 이면 그대로 텍스트.
   - `content` 가 `list` 이면:
     - `type=="text"` → `text` 필드 추출 (Layer A/B/D/E 입력)
     - `type=="tool_use"` → `name`, `input` 추출 (Layer C 입력 — Edit/Write 의 `file_path` + `new_string`/`content` 검사)
     - 기타 (`tool_result` 등) → 본 hook 입력에서 제외

---

## 3. Detection Pipeline (6-layer, v2 — audit 반영)

### 3.1 Layer A — User Rebuke Detection
**입력:** 직전 user turn 의 텍스트 (`content` flatten)
**시그널 (정규식, `re.UNICODE | re.MULTILINE`):**
- 부정/질책: `또\s*실패`, `왜\s*[빼빠]`, `(잘못|오류|실수)(을|를|이|가)`, `안\s*했`, `못\s*했`
- 정정 요구: `정정해`, `다시\s*해`, `(니가|네가)\s*뭘`, `왜\s*[가-힣A-Za-z]+\s*안`
- 절대화 부정: `전부\s*아니`, `전혀\s*안`

**액션:** 검출 시 `signal_type = "user_rebuke"` + 직전 assistant turn (N-2 라인) 함께 capture
**한계 명시 (§11.A):** N=4 라인 window 너머 (예: 사용자가 N-1 에 질책 + N-3 에 위상군 claim) 는 미커버. 위상군 수동 등록 fallback.

### 3.2 Layer B — Self-Praise Detection (v2 — 화이트리스트 강화)
**입력:** 직전 assistant turn 의 `text` 블록만 (tool_use 제외)
**시그널 (정규식):**
- 자축어: `ㅋㅋ`, `ㅎㅎ`, `🎉`, `🥳`, `완벽(?:하|함|입니다)(?!\s*지\s*(?:않|못))`, `대단(?:하|함)(?!\s*지)`, `훌륭(?!\s*하지)`, `깔끔(?!\s*하지)`
- 절대화: `전면\s*강제`, `자율의존\s*종료`, `완전(?:히)?\s*[차해]`, `100%`, `절대\s*[안못](?!\s*[될하야])`
- 과장 단언: `해결됐습니다(?!\s*[?\?])`, `끝났습니다`, `(모두|전부)\s*통과`

**예외 화이트리스트 (binding, v2 강화):**
1. **사용자 호응 패턴**: 직전 user turn 의 `text` 에 동일 자축 토큰 존재 → skip. 사용자가 먼저 사용한 표현은 자축 X.
2. **코드/인용 컨텍스트**:
   - 백틱 인용 (`` ` `` ... `` ` ``) 안 매칭 → skip.
   - Fenced code block (` ``` ` ~ ` ``` `) 안 매칭 → skip.
   - Blockquote 라인 (`^>` 또는 `^>\s`) 시작 → skip.
   - `예시:` / `인용:` / `quote:` / `S\d{2}:` (예: `S50:`) 마커 직후 60자 → skip.
3. **부정 컨텍스트**: 매칭 토큰 직후 30자 안 `지\s*(?:않|못)` / `아니` / `없` 존재 → skip (예: "완벽하지 않다").
4. **과거 회고/메타 분석**: 매칭 토큰 ±30자 안 `었어` / `었었` / `예전(?:에)?` / `과거(?:에)?` / `S\d{2}\s*(?:에서|의)` / `직전\s*세션` / `재발` 존재 → skip.

**액션:** 화이트리스트 통과 시 `signal_type = "self_praise"` 또는 `"absolutization"` + 매칭 토큰 capture.

### 3.3 Layer C — Failure Citation Skipping (v2 — 정정)
**입력:**
- (1) 직전 assistant turn 의 **`tool_use` 블록들** (Edit/Write 만)
- (2) `tems_diagnostics.jsonl` 24h `*_failure` 이벤트
- (3) Edit/Write tool_use 의 `new_string` (Edit) 또는 `content` (Write) **필드 본문**

**조건:** `(1)` 중 하나의 `file_path` 가 핸드오버/recap 경로 매칭 (handover_doc/, Claude-Sessions/, qmd_drive/recaps/, docs/session_archive/) AND `(2)` ≥1건 AND `(3)` 본문에 24h failure 의 timestamp 인용 0건 (substring 검사 — 첫 19자 `2026-04-29T17:23:20` 등)

**액션:** `signal_type = "failure_citation_skip"` + 누락 failure 목록 capture
**중요:** 검사 대상은 chat 텍스트가 아니라 **파일 본문 (Edit/Write payload)**. v1 의 chat-text 검사 오류 정정.

### 3.4 Layer D — Self-Reversal without TGL Registration
**입력:** 직전 assistant turn `text` 블록
**시그널:** `정정합니다`, `잘못\s*보고`, `S4[89](?:/S5\d)?\s*동일`, `메타[-\s]?결함`, `재발`, `자축\s*부적절`
**조건:** 시그널 검출 AND 같은 turn 안 `tool_use` 중 `name` 이 `Bash` AND `command` 가 `tems_commit.py` 호출 0건
**액션:** `signal_type = "reversal_without_registration"` + 정정 텍스트 capture

### 3.5 Layer E — Numeric Self-Audit Falsification (v2 신규 — S49 패턴)
**입력:** 직전 assistant turn `text` 블록 + `tems_diagnostics.jsonl` 24h `*_failure` 이벤트
**시그널:** chat 텍스트에 다음 정규식 매칭:
- `errors?\s*[=:]\s*0` (예: "errors=0", "error: 0")
- `failure\s*[=:]\s*0` / `failures?\s*[=:]\s*0`
- `(?:문제|결함|오류|장애)\s*(?:없|0건)`
- `clear|alive|all\s*pass`(영문 — 영어 stage)

**조건:** 시그널 매칭 AND 24h jsonl `*_failure` 이벤트 ≥1건
**액션:** `signal_type = "numeric_self_audit_falsification"` + 매칭 토큰 + 누락 failure 목록 capture
**우선순위:** S49 의 정확한 재현 패턴이므로 `priority="high"` 기본값.

### 3.6 Layer F — Hook-Author Self-Praise Escalation (v2 신규 — S50 패턴)
**입력:**
- (1) 직전 assistant turn 의 `tool_use` 중 `Edit`/`Write` `file_path` 가 `memory/.*hook.*\.py$` 또는 `memory/.*gate.*\.py$` 또는 `memory/audit.*\.py$` 매칭
- (2) Layer B 또는 D 가 같은 turn 에서 시그널 검출

**조건:** `(1)` AND `(2)` 동시 충족
**액션:** Layer B/D 의 draft 에 `priority = "critical"` escalation. 별도 signal_type 추가 X — 기존 signal 강조만.

---

## 4. Draft Generation

### 4.1 Draft 파일 포맷 (`memory/pending_self_cognition/<id>.json`)
```json
{
  "draft_id": "scd_20260429_173045_user_rebuke",
  "created_at": "2026-04-29T17:30:45.123456+09:00",
  "signal_type": "user_rebuke|self_praise|absolutization|failure_citation_skip|reversal_without_registration|numeric_self_audit_falsification",
  "matched_tokens": ["또 실패", "ㅋㅋ"],
  "priority": "normal|high|critical",
  "context": {
    "user_prompt_excerpt": "직전 user turn 의 처음 500자",
    "assistant_response_excerpt": "직전 assistant turn 의 처음 1000자",
    "tool_uses_summary": [{"name": "Edit", "file_path": "..."}],
    "missing_failures": [{"timestamp": "2026-04-29T16:02:59", "event": "decay_ths_sweep_setup_failure"}]
  },
  "suggested_classification": "TGL-C|TGL-W|TCL|TGL-M",
  "suggested_abstraction": "L2",
  "suggested_topological_case": "...",
  "suggested_forbidden": "...",
  "suggested_required": "...",
  "suggested_triggers": "키워드들",
  "suggested_tags": "self-cognition,meta-defect",
  "draft_status": "pending"
}
```

**Atomic write (v2 P1):** `tempfile.NamedTemporaryFile(dir=pending_dir, delete=False)` → fsync → `os.replace(tmp, final)`. 직접 `open(..., 'w')` 금지.

### 4.2 분류 휴리스틱 (시그널 → 카테고리 매핑)

| signal_type | classification | abstraction | priority |
|-------------|----------------|-------------|----------|
| user_rebuke | TGL-C | L2 | normal |
| self_praise | TGL-C | L2 | normal (§3.6 충족 시 critical) |
| absolutization | TGL-C | L2 | normal (§3.6 충족 시 critical) |
| failure_citation_skip | TGL-W | L2 | high |
| reversal_without_registration | TGL-M | L2 | normal (§3.6 충족 시 critical) |
| numeric_self_audit_falsification | TGL-W | L2 | high |

### 4.3 Suggested 본문 자동 생성

**Templates 디렉토리:** `memory/templates/self_cognition_*.txt` (6개 — 각 signal_type 1개)

**변수 schema (binding, v2):**
- `{matched_tokens}` — comma-separated string
- `{user_excerpt}` — 직전 user 발췌 500자
- `{assistant_excerpt}` — 직전 assistant 발췌 1000자
- `{turn_index}` — 1-based 마지막 turn 번호
- `{missing_failures}` — `failure_citation_skip` / `numeric_self_audit_falsification` 만 사용. JSON list str.

**Template 1 예시 (`self_cognition_self_praise.txt`):**
```
자축/과장 표현 검출 — TGL-C 후보.
매칭 토큰: {matched_tokens}
직전 응답 발췌:
  {assistant_excerpt}
forbidden: 메타-결함 차단 hook/규칙 적용 직후 또는 검증 미완료 단계에서 자축어({matched_tokens}) 사용
required: 객관 수치 + 명시적 한계 인정 + 미해결 항목 cite. 자축어 0회 유지
verification:
  success_signal: 동일 컨텍스트에서 자축 토큰 0회
  compliance_check: 핸드오버/recap 본문 grep '{matched_tokens[0]}' = 0건
```

(나머지 5개 template — codex 가 동일 schema 로 작성, §9 #4 acceptance.)

---

## 5. preflight_hook 확장

### 5.1 추가 동작
기존 BM25 + dense 매칭 출력 후, 마지막에:
```
<self-cognition-pending count="N">
  ⚠ 자기-인지 강제 등록 보류 N건 — 다음 응답 전 처리 의무.
  [scd_20260429_173045_self_praise] signal=self_praise priority=critical matched="ㅋㅋ"
    suggested: TGL-C / L2 / "..."
    조치: python memory/tems_commit.py --type TGL --classification TGL-C ... (draft path: memory/pending_self_cognition/scd_*.json)
    또는 reject: python memory/self_cognition_gate.py --reject scd_20260429_173045_self_praise --reason "최소 10자 사유"
  [scd_...] ...
</self-cognition-pending>
```

### 5.2 해소 검증
- `tems_commit.py` commit 성공 시 `pending_self_cognition/<id>.json.committed` 으로 rename + jsonl event="self_cognition_resolved"
- `--reject` 시 `<id>.json.rejected` rename + rationale jsonl 기록
- **--reject 검증 (v2 P1):** `--reason` 길이 ≥10 강제. 빈 / 짧은 사유는 exit 1.

---

## 6. 자기-루프 차단 (v2 — audit 반영)

### 6.1 SELF_INVOCATION_MARKERS 확장 (binding)
codex 는 `handover_failure_gate.py` 의 `SELF_INVOCATION_MARKERS` 에 다음 4건 **반드시 추가**:
- `memory/self_cognition_gate.py`
- `memory/pending_self_cognition/`
- `memory/templates/self_cognition_`
- `docs/superpowers/plans/2026-04-29-self-cognition-auto-register.md`

### 6.2 Self-Reference Whitelist (binding)
다음 토큰이 텍스트에 존재하면 Layer B/D/E 검사 skip (메타-분석 텍스트):
- `pending_self_cognition`
- `self_cognition_gate`
- `self_cognition` (path-like)
- `audit reviewer` / `audit findings`
- 본 spec 문서 경로 substring

### 6.3 잠재 메타-루프 위험 (§11.D 로 이동)

---

## 7. Smoke Test Plan (12건, v2 — audit 반영)

| # | 케이스 | 기대 결과 |
|---|--------|---------|
| 1 | empty stdin | exit 0 silent |
| 2 | invalid JSON stdin | exit 0 + jsonl `self_cognition_gate_stdin_parse_failure` 기록 |
| 3 | transcript_path 부재 / read 실패 | exit 0 + jsonl `self_cognition_gate_transcript_read_failure` 기록 |
| 4 | Layer B detect: assistant turn `text` 에 "ㅋㅋ" | draft 생성 (signal=self_praise, normal) |
| 5 | Layer A detect: user turn `text` 에 "또 실패" | draft 생성 (signal=user_rebuke) |
| 6 | False positive: user turn 이 먼저 "ㅋㅋ" 사용 + assistant 호응 | skip |
| 7 | False positive: 백틱 / fenced code / blockquote 안 "완벽" | skip (3 sub-test: inline `완벽`, fenced ``` 완벽 ```, `> 완벽`) |
| 8 | False positive: "완벽하지 않다" | skip (negation lookahead) |
| 9 | False positive: "S50 에서 ㅋㅋ 자축했다" (과거 회고) | skip (회고 화이트리스트) |
| 10 | Layer C: Edit `handover_doc/test.md` `new_string` 에 timestamp 인용 0 + jsonl 24h failure 1건 | draft 생성 (signal=failure_citation_skip, high) |
| 11 | Layer E (신규): assistant text 에 "errors=0" + jsonl 24h failure ≥1 | draft 생성 (signal=numeric_self_audit_falsification, high) |
| 12 | Layer F (escalation): turn 에 Edit `memory/foo_hook.py` + Layer B "완벽" 매칭 | draft 의 priority="critical" |

각 케이스 fixture (transcript JSONL stub) 로 검증. `tests/test_self_cognition_gate.py` 에 12 테스트 작성.

---

## 8. settings.local.json 갱신

### 8.1 Stop hook 추가 entry
```json
{
  "matcher": "",
  "hooks": [
    {"type": "command", "command": "python \"E:/DnT/DnT_WesangGoon/memory/retrospective_hook.py\"", "timeout": 8},
    {"type": "command", "command": "python \"E:/DnT/DnT_WesangGoon/memory/self_cognition_gate.py\"", "timeout": 8}
  ]
}
```

### 8.2 백업 (TGL #102)
`.claude/_backup_S51_self_cognition/settings.local.json.before_S51` 생성 의무.

### 8.3 SessionStart 확장 (Optional, audit P1)
`audit_diagnostics_recent.py` 가 stale pending 도 동시 출력. settings 변경 X (기존 entry 가 hooked).

---

## 9. Acceptance Criteria (v2 — codex GPT-5.5 충족 조건, 18개)

1. ✅ 모듈 [memory/self_cognition_gate.py](memory/self_cognition_gate.py) 생성, §3 의 6-layer detector 구현 (Layer A-F)
2. ✅ §2.2 transcript 파싱 규칙 정확 적용 — JSONL 라인별 + BOM strip + turn 재구성 + content type 분기
3. ✅ Layer B 화이트리스트 4종 (사용자 호응 / 코드 인용 / 부정 lookahead / 과거 회고) 정확 작동 — false positive 테스트 #6, #7, #8, #9 통과
4. ✅ Templates 디렉토리 `memory/templates/` 생성 + 6개 template 파일 (signal_type 별) §4.3 변수 schema 적용
5. ✅ Layer C 가 Edit/Write tool_use 의 `new_string`/`content` 필드를 검사 (chat 텍스트 X). 테스트 #10 통과
6. ✅ Layer E 신규 (numeric_self_audit_falsification) 구현 + 테스트 #11 통과
7. ✅ Layer F 신규 (priority=critical escalation) 구현 + 테스트 #12 통과
8. ✅ Draft 파일 §4.1 스키마 정확 매치 + atomic write (tempfile + os.replace)
9. ✅ [memory/preflight_hook.py](memory/preflight_hook.py) §5.1 출력 추가 — 기존 출력 보존, 새 블록은 끝에 append. 핵심: 기존 BM25/dense 매칭 출력 회귀 X
10. ✅ `--reject <id> --reason "..."` 명령 구현 + reason ≥10자 강제 (빈/짧은 사유 exit 1)
11. ✅ Self-loop 차단 (§6) — `SELF_INVOCATION_MARKERS` 4건 확장 + Self-Reference Whitelist 5건 적용
12. ✅ 12건 smoke test 모두 통과 — `tests/test_self_cognition_gate.py` 작성
13. ✅ jsonl 진단 적재 — 모든 except 분기에서 `*_failure` 이벤트 기록 + commit/reject 시 `self_cognition_resolved`/`self_cognition_rejected` 기록
14. ✅ `.resolve()` canonical path 사용 (S49 P0 패턴), 모든 파일 open `encoding='utf-8'` 명시
15. ✅ TGL #102 #3 — 기존 hook (retrospective / preflight / tool_gate / handover_failure / tool_failure / compliance_tracker) 무회귀 확인. 각 hook empty stdin 테스트 alive
16. ✅ settings.local.json §8.2 백업 후 §8.1 갱신
17. ✅ `audit_diagnostics_recent.py` 확장 — pending 24h+ stale 시 `<self-cognition-stale count="N" oldest="...">` 출력
18. ✅ Anti-acceptance — 본 모듈 안에서 **`tems_commit.py` 직접 호출 금지**, **LLM API 호출 금지**, settings.local.json 수정 §8.1 + §8.2 외 금지

**Acceptance 미충족 시:** codex 결과 reject + 위상군 수동 패치 또는 codex 재지시.

---

## 10. 비-목표 (Out of Scope, v2 강조)

- **자동 commit 절대 금지** (위상군 검토 없이 tems_commit 호출 X) — pending 디렉토리 stage 까지만. §9 #18 anti-acceptance.
- **LLM 기반 의도 분석 절대 금지** (regex + 화이트리스트만, 토큰 비용 0 유지). §9 #18 anti-acceptance.
- TGL-S/D/P/W/M 카테고리별 hook 확장 (별 task)
- 본 hook 의 ML training (정규식 시그널만, 학습 X)
- Frequency-based whitelist 자동 승격 (P2 — S52+)
- 영문 시그널 (P2 — S52+)
- compliance_tracker 통합 (P2 — S52+)

---

## 11. 위험 / 알려진 제약

### 11.A — Layer A N=4 turn window
N>4 turn 거슬러 가는 시그널 미커버 (예: 사용자가 N-1 질책 + N-3 위상군 claim). 의도된 한계. 위상군 수동 등록 fallback. S52 에서 window 확대 검토.

### 11.B — Regex 한계
자축/절대화 표현은 무한 변종. 초기 시그널 set 은 §3 명시 패턴만. 신규 패턴은 위상군 수동 추가. False negative 재발 시 spec amendment + 재구현.

### 11.C — Pending 누적 폭주
위상군이 처리 안 하고 세션 종료 시 누적. §8.3 SessionStart stale 가시화 (24h+) 로 강조. 위상군이 reject 거부 시 종일군 escalation.

### 11.D — 잠재 메타-루프
본 spec/audit/template 텍스트 자체가 자축/질책 토큰 다수 포함. §6 Self-Reference Whitelist 로 차단. 본 영역 신규 hook 작성 시 항상 Whitelist 갱신 필수.

### 11.E — Transcript path 의존
Claude Code 한정. codex/gemini 환경에서 작동 X. 의도된 한계.

### 11.F — Race condition
Stop hook 에서 retrospective_hook.py 와 self_cognition_gate.py 병렬 실행 가능. 각자 독립 jsonl 기록 + atomic write 적용으로 안전. 공유 file lock 미사용 (필요 X).

### 11.G — False positive 잔존 가능성
화이트리스트로도 못 잡는 케이스 발생. 위상군 `--reject --reason "false positive: <설명>"` 로 처리. P2 — frequency-based whitelist 자동 승격 추후 도입.

---

## 12. 다음 단계 (실행 순서)

1. ✅ **본 spec v2 작성 완료**
2. ✅ **superpowers:code-reviewer audit 적용** (Appendix A)
3. **codex exec -m gpt-5.5 --full-auto** 구현 지시 ← **다음**
4. **위상군 trust-but-verify** — smoke test 12건 실행 + 무회귀 확인 + jsonl 적재 확인 + 1 turn 실전 검증 (의도된 자축 텍스트 → draft 생성 → pending 표시)
5. 합격 시 commit + handover 갱신, 불합격 시 codex 재지시 또는 위상군 수동 정정

---

## 13. 메모

- 본 spec 자체에 자축어/절대화 표현 사용 금지 — 본 메커니즘이 잡아야 할 패턴이 spec 안에 들어가면 메타-부조리. 본문 점검 완료 (객관 단언만).
- §9 Acceptance Criteria 18항이 codex 평가 절대 기준. spec 외 추가 기능 도입은 reject 사유.
- §10 / §9 #18 의 anti-acceptance (자동 commit, LLM 호출, settings 외 수정) 위반은 자동 reject.

---

## Appendix A — Audit Findings (binding amendments, 2026-04-29 Opus code-reviewer)

> Audit verdict: **ACCEPT_WITH_FIXES**. P0 4건 + critical missing signals 2건 + P1 7건. v1 spec 의 본질적 결함 cite.

### A.1 P0 (모두 본문 §3 / §4 / §6 에 반영 완료)
1. **Transcript schema 미정의** → §2.2 binding 파싱 규칙 추가 (5 step)
2. **Layer C 논리 깨짐** (chat 텍스트 검사 → Edit/Write payload 검사 정정) → §3.3 정정
3. **Self-loop bypass 불완전** → §6.1 (4 markers 추가) + §6.2 (5 self-reference whitelist) 추가
4. **Whitelist 위험할 정도로 얇음** → §3.2 4종 화이트리스트 (호응/코드인용/부정lookahead/과거회고) 강화

### A.2 Critical Missing Signals (모두 §3 신규 layer 추가)
5. **S49 패턴 미커버** ("errors=0" + jsonl failure 존재) → §3.5 Layer E (numeric_self_audit_falsification) 신규
6. **S50 패턴** (hook 자작 직후 자축) → §3.6 Layer F (priority=critical escalation) 신규

### A.3 P1 (모두 §9 acceptance / §4.1 / §5.2 에 반영)
- Atomic write → §4.1 + §9 #8
- 인코딩 (BOM, encoding='utf-8') → §2.2 + §9 #14
- Stale pending 가시화 → §8.3 + §9 #17
- --reject reason ≥10 강제 → §5.2 + §9 #10
- Templates 디렉토리 + variable schema → §4.3 + §9 #4
- Smoke test fenced/blockquote/inline 분리 → §7 #7 (3 sub-test)
- Layer A N=4 turn 한계 명시 → §3.1 + §11.A

### A.4 P2 (S52+ 이월 — §10 비-목표 명시)
- Frequency-based whitelist auto-promotion
- Bilingual (English) signal
- compliance_tracker 통합

### A.5 Audit reviewer 추가 권고 (codex prompt 인용)
> "Implement spec verbatim, but (1) treat the P0 items above as binding amendments to §3 / §4 / §6, (2) when ambiguous, choose the more-conservative (fewer false positives, more false negatives) interpretation — first-cut deployment prioritizes precision over recall, (3) do NOT add features outside §9 acceptance list even if obvious — that's reject criterion per §13. Hard fence: no LLM calls, no `tems_commit.py` invocation from gate, no settings.local.json edits beyond §8.1 entry + §8.2 backup."

이 권고는 codex 호출 prompt 에 verbatim 첨부.
