---
name: SDC
upstream: https://github.com/bobpullie/SDC
update_cmd: curl -o .claude/skills/SDC.md https://raw.githubusercontent.com/bobpullie/SDC/main/SKILL.md
description: Subagent Delegation Contract — 위상군(Opus 4.7)이 TEMS 모듈 구현/이식/재분류/탐색/smoke-test 등 실행 작업을 Sonnet 서브에이전트에 위임할 때의 계약(brief 5항목 + verification + 분업 매트릭스) 작성법과 작업 유형별 템플릿
---

# [SDC] Subagent Delegation Contract — 서브에이전트 위임 계약

위상군은 Triad Chord Studio의 **위상적 시스템 아키텍트**. 설계·판단·TEMS 규칙 분류는 Opus 4.7 본체, 실행 작업은 Sonnet 서브에이전트에 위임.
이 스킬은 위임 순간의 **실행가이드 작성**에 한정 — 도메인 게이트 자체는 각 규칙/스킬(`tems-protocol.md`, `dvc`, `handoff-build.md` 등) 참조.

**모델 배치 원칙**: 판단·추론·Audit 서브에이전트는 **Opus 4.7**, 실행·구현·테스트·탐색 서브에이전트는 **Sonnet 4.6**. code-reviewer / advisor 는 예외 없이 Opus 전담. 혼용 금지.

## 0. Auto-Dispatch Check (task 수신 즉시 실행 — Hybrid Trigger 모드)

새 task 수신 시 아래 절차를 **자동 실행**. Trigger 키워드 매칭 시에만 명시적 판정, 그 외에는 판정 생략 (Opus 본체 직접 처리, 내재화된 기본).

### Auto-Trigger 키워드

아래 패턴이 task에 포함되면 3-question gate 자동 실행:

- Git 명령: `commit` · `push` · `pull` · `merge` · `rebase` · `cherry-pick` · `fetch`
- 파일 조작: `mv` · `cp` · `rename` · `refactor` · `migrate`
- 배치: 동일 연산 ≥3회 반복 / "대량 / N개 모두 / 반복"
- 분류: `classify` · `sort` · `재분류` · `needs_review` · `7-카테고리`
- 검증: `verify` · `test` · `validate` · `smoke`
- 이식/배포: `Wave` · `이식` · `배포` · `port`

Trigger 없으면 → 게이트 생략, 본체 직접 판단 (일반 대화·설계 질문 등).

### 3-Question Gate

**Q1. Invariance Test** — "동일 spec·tools를 받은 5명의 구현자가 strictly 따른다면, 결과물이 의미적으로 동등한가?"
- NO (결과 편차 생김) → **KEEP Opus**
- YES → Q2

**Q2. Overhead Test** — "SDC brief 작성 + Sonnet warmup이 직접 실행보다 더 많은 tool call / 토큰을 요구하는가? (task 실행량 < ~2k Sonnet tokens 또는 1~2 step)"
- YES → **KEEP direct** (본체 즉시 처리, overhead 회피)
- NO → Q3

**Q3. Reversibility Gate** — 출력이 틀렸을 때 blast radius?
- Local & reversible (file edit, 로컬 test) → **DELEGATE (full)** — Sonnet 실행·보고
- Shared state (push / PR / 외부 API) → **DELEGATE + STAGING** — TCL #86: Sonnet은 `git add`까지만, commit/push는 Opus가 검토 후 실행
- Destructive (`rm -rf` / `DROP TABLE` / force-push to main) → **KEEP Opus + 사용자 명시 승인**

### Signal Heuristics (빠른 판정 보조)

| Signal | 방향 |
|--------|------|
| "이식 / 복사 / rename / migrate / 배포" | → DELEGATE |
| "대량 / N개 모두 / 반복" | → DELEGATE |
| "smoke test / 실증 / 확인 / readonly 탐색" | → DELEGATE |
| "아키텍처 / 설계 / 판정 / 근거 서술" | → KEEP |
| "best approach / trade-off / should we" | → KEEP |
| TEMS fallback 근거 / Phase 전환 / 신규 분류 축 | → KEEP |
| 동일 파일 2+ 편집 + 테스트 | → DELEGATE |
| 오타 1~2줄 수정 | → KEEP direct |

### 판정 결과 처리

| 판정 | 처리 |
|------|------|
| **DELEGATE** | 필수 5항목 brief 작성 → `Agent(subagent_type="general-purpose", model="sonnet", prompt=brief)` 호출 → 결과 trust-but-verify (TCL #115) |
| **STAGING** | brief 작성 + 제약 추가: "`git add`까지만 실행, commit/push 금지 (TCL #86)" → Sonnet 결과 검토 → Opus가 최종 commit/push |
| **KEEP** | 본체 직접 실행. 내재화된 판단, verbalize 생략 가능. KEEP 근거 1줄 노트 권장 (예: "Q2 KEEP: 1줄 편집") |

### 기본값 (Default Reversal)

- **Q1 PASS + Q2 PASS + Q3 Local** → **자동 DELEGATE** (매번 "위임할까?" 묻지 말 것)
- **KEEP 판정은 근거 1줄 명시** (Q1 fail 이유 or Q2 overhead 압도)
- Trigger 없는 일반 대화/판단 요청은 게이트 자체를 생략

### 비용 고려 (세션 효율)

- 게이트 overhead (trigger-only): 세션당 ~$0.04-$0.45 (Opus 토큰)
- Delegation 고정비: ~$0.12/회 (brief + subagent warmup + verify)
- Break-even: task 실행량 ≥ ~2000 Sonnet tokens 시 delegation 순이득
- 예상 순이익: 세션당 토큰 $0.5-$1.5 절감 + context window 보존 (auto-compact 회피)

참조: TCL #86 (subagent commit 권한 통제) · TCL #115 (trust-but-verify) · TCL #117 (분류 작업 Sonnet 위임) · TCL #120 (이 dispatch policy)

## 위임 매트릭스

| 작업 유형 | 도메인 규칙/스킬 | Agent type | 모델 |
|----------|----------------|-----------|------|
| TEMS 모듈 구현·패치 (memory/*.py hook 등) | `tems-protocol.md` + `constraints.md` | `general-purpose` | sonnet |
| Phase 이식 (다른 에이전트 TEMS 배포) | `tems-protocol.md` + TCL #93 (위상군 선검증 원칙) | `general-purpose` | sonnet |
| needs_review 규칙 재분류 · Migration | `tems-protocol.md` (7-카테고리) | `general-purpose` | sonnet |
| DVC case 추가·검증 | `dvc` skill | `general-purpose` | sonnet |
| smoke test · 회귀 검증 | `constraints.md` (결정론적 검증) | `general-purpose` | sonnet |
| 광범위 코드/메모리 탐색 | — | `Explore` | sonnet |
| 독립 병렬 과제 2건+ | `superpowers:dispatching-parallel-agents` | `general-purpose` | sonnet |
| 기획/UX/심리학 도메인 질문 | `team-delegation.md` | `planner-agent` | (에이전트 자체) |
| TEMS/아키텍처 Audit · 편향 차단 | `superpowers:code-reviewer` | `superpowers:code-reviewer` | **opus** |
| 복잡한 설계 결정 2안 비교 | `advisor` | `advisor` | **opus** |

## 위상군 직접 수행 (위임 금지)

- 아키텍처 설계 판단 (나선형 파이프라인, 확장 아키텍처, 새 hook 도입 가부)
- TEMS 규칙 분류·등록 (TCL vs TGL 판단, 7-카테고리, L1~L3 abstraction)
- Phase 전환 판정 (관찰 결과 종합, Wave N 배포 여부)
- 핸드오버 결정 사항 작성 (종일군 지시 해석, 세션 성과 요약 — 기계적 부분은 위임 가능)
- 팀 델리게이션 결정 (어느 에이전트에 맡길지, 우선순위)
- trivial edit (1~2줄 오타, 주석 추가) — 위임 오버헤드가 작업 비용보다 큼
- 긴급 의사결정 + 즉시 수정이 엮인 경우
- `E:/MRV/src/` 직접 수정은 여전히 **빌드군 경유** (subagent 위임도 금지 — team-delegation.md)

## 실행가이드 필수 5항목

서브에이전트 prompt 필드에 아래 5항목을 반드시 포함.

1. **목적 (WHAT)** — 왜 이 작업을 하는지 1~2문장 배경. 서브에이전트가 맥락 추측하지 않도록.
2. **필수 게이트** — 해당 규칙/스킬의 게이트·산출물·도메인 원칙 원문 발췌 (요약 금지 — `tems-protocol` 카테고리 슬롯 등은 원문 그대로 전달).
3. **제약** — 건드리지 말 것, 가정하지 말 것, 바꾸지 말 것 (기존 DB 스키마, hook 순서, `E:/MRV/src/` 등).
4. **완료 기준** — 관측 가능한 조건 (파일 생성됨, 테스트 통과, 수치 범위, `python -m checklist.runner` OK 등).
5. **보고 형식** — 결과 요약 포맷 (변경 파일 목록, 주요 수치, 게이트 통과 체크표, 미완료 항목).

## 작업 유형별 실행가이드 템플릿

### 템플릿 1: TEMS 모듈 구현/패치 위임

```markdown
## 목적
[배경 1~2문장. 어떤 hook/모듈이 왜 필요한지, 어떤 실전 사고에서 도출됐는지]

## 필수 게이트 (tems-protocol.md)
1. self-contained 유지 — 외부 `tems` PyPI 패키지 의존 금지 (TGL #92)
2. 경로 하드코딩 금지 — `Path(__file__).parent` 기반 상대경로
3. 기존 DB 스키마 파괴 금지 — ALTER TABLE 추가만 허용, DROP 금지
4. hook 실패 시 `<...-degraded>` fallback 출력 (silent fail 금지)
5. TEMS 변경 = 위상군 자체에서 먼저 구현·검증·안정화 (TCL #93, 타 에이전트 전파 금지)

## 제약
- 기존 hook 순서 변경 금지 (preflight → PreToolUse → PostToolUse 순)
- active_guards.json 포맷 변경 시 compliance_tracker 동반 수정 필수
- [변경 불가 파일 명시]

## 완료 기준
- [ ] 해당 모듈 import 성공 (`python -c "from memory.X import Y"`)
- [ ] smoke test: UserPromptSubmit/PostToolUse 트리거 1회 정상 통과
- [ ] 기존 규칙 수 보존 (`SELECT COUNT(*) FROM memory_logs` 전후 비교)
- [ ] 에러 로그 없음

## 보고 형식
- 수정/추가 파일 + 라인 수
- 새 hook 등록 내역 (settings.local.json diff)
- smoke test 출력 3~5줄
- 기존 규칙 보존 확인 수치
```

### 템플릿 2: Phase 이식 (다른 에이전트 TEMS 배포) 위임

```markdown
## 목적
[타깃 에이전트 + 배포할 Wave 버전 + 배경. 위상군이 검증 완료했다는 근거]

## 필수 게이트 (TCL #93, tems-protocol.md)
1. 위상군 자체에서 이미 검증·안정화 완료 (전파 전제)
2. 타깃 에이전트 기존 DB 보존 (기존 규칙 수 선측정 → 이식 후 재측정)
3. 백업 필수: `memory/_bak_pre_wave{N}/` 에 원본 전체
4. Phase 3 (tool_gate_hook, compliance_tracker) 는 Wave 2 관찰 판정 후 배포 — Wave 1에 섞지 말 것
5. 타깃 에이전트의 도메인 hook(changelog_hook 등 타 프로젝트 연결)은 건드리지 말 것

## 제약
- 타깃 에이전트 CLAUDE.md 에 TCAS:IDENTITY 블록이 있으면 그 외 섹션만 업데이트
- `permissionMode: bypassPermissions` 설정은 원래 있던 값 그대로 유지 (신규 추가 금지)
- 경로 하드코딩 자동 치환: 위상군 절대경로 → 타깃 에이전트 절대경로

## 완료 기준
- [ ] 백업 디렉토리 존재 확인
- [ ] 위상군 ↔ 타깃 에이전트 파일 크기 매칭 (tems_engine.py, preflight_hook.py 등)
- [ ] 타깃 에이전트 기존 DB 규칙 수 100% 보존
- [ ] hook 구성 변경 diff 명시 (추가된 PostToolUse Bash, Stop 등)
- [ ] smoke test 4종 통과: tems_engine import / tems_commit import / preflight JSON 입력 / DB 규칙 수

## 보고 형식
- 복사 파일 목록 + 크기
- 경로 하드코딩 패치 내역 (있으면)
- hook 변경 diff
- smoke test 결과
- 위상군 원본과 차이점 (있으면 — 이유 명시)
```

### 템플릿 3: 규칙 재분류 · Migration 위임

```markdown
## 목적
[needs_review N건 / 레거시 규칙 재분류 배경. 어떤 분류 기준을 적용할지]

## 필수 게이트 (tems-protocol.md 7-카테고리)
- TGL-T (Tool Action) / TGL-S (System State) / TGL-D (Dependency) / TGL-P (Pattern Reuse) / TGL-W (Workflow) / TGL-C (Communication) / TGL-M (Meta-system)
- TGL-M fallback 사용 시 근거 원문 인용 필수 (FORBIDDEN fallback-only 방지)
- abstraction_level L2 sweet spot 강제 — L0/L4 거부
- 각 분류마다 `forbidden_action` + `required_action` + `verification.success_signal` + `verification.compliance_check` 필수

## 제약
- DB의 `id` 컬럼 변경 금지 (규칙 링크 깨짐)
- archive 상태 규칙 건드리지 말 것
- `keyword_trigger` 는 본문 핵심 명사 80% 이상 명시 (BM25 매칭 실패 방지)

## 완료 기준
- [ ] needs_review 잔여 건수 0 또는 사유 명시
- [ ] 분류 분포 보고 (TGL-T/S/D/P/W/C/M 각 몇 건)
- [ ] 각 건에 대해 재분류 근거 1~2줄 기록
- [ ] 기존 ID 보존, FTS5 재인덱싱 완료

## 보고 형식
- 재분류 전후 분포 표
- 재분류 근거 표 (id, 기존 → 신규, 근거)
- FORBIDDEN fallback 사용 건 리스트 (있으면)
- 실패/보류 건 (있으면)
```

### 템플릿 4: 탐색/smoke test 위임

```markdown
## 목적
[무엇을 확인하려는지. 가설 또는 검증 질문 1~2문장]

## 필수 게이트
[해당 작업의 도메인 규칙 원문. 없으면 "없음" 명시]

## 제약
- 파일 수정 금지 (탐색만) 또는 [수정 허용 범위 명시]
- 민감 정보 노출 금지 (credentials, .env, 개인 디렉토리)

## 완료 기준
- [ ] [확인 항목 1 — 예: 특정 함수 호출 그래프 도출]
- [ ] [확인 항목 2]
- [ ] 발견 사항 요약

## 보고 형식
- 핵심 발견 3~5개
- 파일:줄 인용 (클릭 가능한 링크 형식 [file.py:42](path#L42))
- 예상 외 발견 (있으면)
```

### 템플릿 5: Audit 위임 (Opus, 편향 차단)

TEMS 아키텍처 변경·Phase 전환·설계 결정 등에서 위상군 자체 편향 차단이 필요할 때.
**Agent 호출 시 반드시 `subagent_type: "superpowers:code-reviewer"` 또는 `advisor` 사용 + Opus 모델.**

공통 5항목:
1. **심사 대상** — spec / 구현 / 배포 결정 중 어느 것인지 명시 (파일 경로 원문 인용)
2. **검증 기준** — 아키텍처 정합성 / 회귀 안전성 / 성능 비용 / 타 에이전트 영향 중 어느 축
3. **심사 방법** — 가정 열거 → 대안 제시 → 반례 탐색 (Falsifiability)
4. **독립성 보장** — 위상군 본체 관점 배제, 외부 eye 로 평가 — "설계자가 놓친 무엇을 찾아내는가"
5. **출력 형식** — `PASS` / `FAIL` / `NEEDS REVISION` + 구체 지적사항 + 개선 제안

호출:
```
Agent(
  description="TEMS Phase 3 Audit",
  subagent_type="superpowers:code-reviewer",
  prompt="[AUDIT] 위 5항목 채움 ..."
)
```

### Audit 결과 수령 후 처리
- PASS → 다음 단계 진입
- NEEDS REVISION → Audit 피드백 반영 후 재제출 (동일 Auditor 재호출)
- FAIL → 위상군 판단: 재설계 or 배포 보류

Auditor 결과는 **권고** — 최종 반영은 위상군 판단. 단, FAIL 무시 시 `handover_doc/` 에 근거 기록 필수.

## 위임 호출 방식 (Agent tool)

```
Agent(
  description="간결한 3~5단어 설명",
  subagent_type="general-purpose",  # 또는 "Explore" / "planner-agent" / "superpowers:code-reviewer"
  model="sonnet",                   # 실행은 명시적 sonnet override
  prompt="(위 템플릿 5항목 채운 마크다운)"
)
```

독립 과제 2건 이상이면 **단일 메시지에 Agent 호출 여러 개**로 병렬 (`superpowers:dispatching-parallel-agents` 참조).

## 결과 수령 후 검증 (위상군 책임)

1. **게이트 통과 확인** — 서브에이전트의 체크리스트 응답을 파일·명령으로 실증 (trust but verify)
2. **산출물 실존 확인** — `git diff`, 파일 경로, smoke test 로그
3. **도메인 원칙 위반 탐지** — self-contained 위반, DB 스키마 파괴, 경로 하드코딩 회귀
4. **미흡 시 조치**: 재위임 (정교한 제약 추가) 또는 위상군 직접 보완
5. **TEMS 기록** — 반복 실수가 위임 프롬프트 누락에서 발생하면 TCL 등록
