---
date: 2026-04-20
status: Active
phase: S34-introduced,S35-renamed
scope: wesang-all-agents
tags: [sdc, subagent-delegation, model-allocation, opus-4-7, sonnet-4-6, brief-template, contract, trust-but-verify]
---

# Concept — SDC (Subagent Delegation Contract)

## 정의

**SDC (Subagent Delegation Contract)** 는 Opus 4.7 본체가 Sonnet 서브에이전트에 실행 작업을 위임할 때 교환되는 **계약**이다. Design by Contract(Hoare logic)의 구조적 동형:

- **Precondition** — 필수 5항목(목적 / 필수 게이트 / 제약 / 완료 기준 / 보고 형식)
- **Postcondition** — 서브에이전트 보고서(체크리스트 통과 + 산출물 증거)
- **Invariant** — 분업 매트릭스(어떤 작업이 Opus인지 Sonnet인지)
- **Verification** — 위상군 본체의 trust-but-verify (파일·명령으로 실증)

핵심 원리: 서브에이전트는 맥락을 추측하지 않는다 — 계약서에 명시된 것만 수행한다.

## 출처 문헌

경험적 도출 — 위상군 S34 (2026-04-20) 도입. 리얼군에도 동시 배포.

- 초기 스킬명: `subagent-brief` (2026-04-20 S34 도입)
- **Rename: `SDC` (2026-04-20 S35)** — 사유:
  1. Anthropic 향후 동일 이름 스킬 출시 충돌 위험 회피
  2. TEMS/TCL/TGL/DVC와 3-letter 약어 리듬 통일
  3. TCL #80 (수학적 정합성 네이밍) 부합 — "Contract" = Hoare logic 대응

관련 TCL: #80 (네이밍 원리), #113 (모델 배치 원칙), #115 (Trust-but-verify).

## 이 프로젝트 내 적용처

### 스킬 파일 위치

| 에이전트 | 경로 |
|---------|------|
| 위상군 (DnT) | `.claude/skills/SDC.md` |
| 리얼군 | `E:\00_unrealAgent\.claude\skills\SDC.md` |

향후 배포 대상: 디니군 / 어플군 / 기록군 / 빌드군 (Wave 1+).

### 필수 5항목 (Contract Slots)

| 슬롯 | 역할 | Contract 대응 |
|------|------|--------------|
| 1. 목적 (WHAT) | 배경·이유 1~2문장 | Specification intent |
| 2. 필수 게이트 | 도메인 규칙 원문 발췌 (요약 금지) | Precondition |
| 3. 제약 | 건드리지 말 것 / 바꾸지 말 것 | Invariant |
| 4. 완료 기준 | 관측 가능한 조건 (파일·수치·명령 결과) | Postcondition |
| 5. 보고 형식 | 결과 요약 포맷 | Output interface |

### 작업 유형별 템플릿 (5종)

| 템플릿 | 위상군 도메인 | 리얼군 도메인 |
|--------|-------------|-------------|
| 1 | TEMS 모듈 구현/패치 | Blueprint 편집·리팩터 |
| 2 | Phase 이식 (타 에이전트 배포) | C++ 구현·수정 |
| 3 | 규칙 재분류·Migration | Asset·Material·Niagara 조작 |
| 4 | 탐색/smoke test | 대규모 네트워크·Blueprint 분석 (Explore) |
| 5 | Audit 위임 (Opus, 편향 차단) | Audit 위임 (Opus, 편향 차단) |

### 분업 매트릭스 (Opus/Sonnet)

- **본체 (Opus 4.7) 직접 수행:** 아키텍처 설계 / TEMS 규칙 분류 / Phase 전환 판정 / 핸드오버 결정 서술 / 팀 델리게이션 / trivial edit / 긴급 의사결정
- **Sonnet 서브에이전트 위임:** 코드 구현·패치 / Phase 이식 / 규칙 재분류 / DVC case / smoke test / 광범위 탐색 / 독립 병렬 과제
- **Opus 서브에이전트 (편향 차단):** `superpowers:code-reviewer` (구현 완료 후 독립 Audit) / `advisor` (2안 비교). 혼용 금지.

### 호출 방식 (Agent tool)

```
Agent(
  description="간결한 3~5단어 설명",
  subagent_type="general-purpose",  # 또는 "Explore" / "superpowers:code-reviewer" / "advisor"
  model="sonnet",                   # 실행은 명시적 sonnet override
  prompt="(SDC 5항목 채운 마크다운)"
)
```

독립 과제 2건 이상 → 단일 메시지에 Agent 호출 여러 개 병렬 (`superpowers:dispatching-parallel-agents` 스킬).

## 주의점

**SDC의 실패 모드 3종:**

1. **필수 게이트 요약** — 도메인 규칙을 "요약"하면 서브에이전트가 해석 여지를 만든다. 원문 그대로 전달 필수.
2. **검증 생략** — 서브에이전트 보고서만 믿고 파일 실존/명령 결과 확인을 생략하면 오기록이 시스템에 진입 (TCL #115 기반 교훈).
3. **본체 판단 작업 위임** — 아키텍처 설계·TEMS 분류·Phase 판정을 Sonnet에 넘기면 구조적 판단력 손실. 본체 전담 영역 엄수.

**배포 전제:**
- 각 에이전트 도메인 게이트는 SDC가 아닌 해당 규칙/스킬 파일 참조 (`tems-protocol.md`, `dvc`, `unreal-blueprint-editing` 등)
- SDC는 **위임 순간의 계약 양식**에 한정 — 도메인 판단은 각 스킬 책임

## 관련 개념

[[TEMS]] [[TCL_vs_TGL]] [[DVC]] [[../patterns/Classification_7_Category]]

## 참조

- [[../decisions/2026-04-20_wave1-standardization]] — Wave 1 표준화 결정 (SDC 동시 배포)
- TCL #80 — 스킬/시스템 네이밍 수학적 정합성 원리
- TCL #113 — 모델 배치 원칙 (SDC 5항목 필수)
- TCL #115 — Trust-but-verify (위임 효율과 검증 책임의 비례)
- `.claude/rules/team-delegation.md` — 에이전트 팀 위임 규칙 (SDC보다 상위 — 다른 에이전트 전달)
