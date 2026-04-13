---
name: plan-feature
description: "기획군에게 새 기능 기획을 위임합니다. 심리 4단계 + 벤치마크 + 밸런스 포함 기획서 자동 생성."
user_invocable: true
context: fork
---

# /plan-feature — 기획군에게 기능 기획 위임

## Usage
```
/plan-feature <feature_name> [context]
```

**Examples:**
- `/plan-feature heatmap-overlay M2에서 집단 센티먼트 시각화`
- `/plan-feature auto-stake 과녁 배치로 자동 포지션`

## Purpose
종일군의 요청이나 위상군의 설계 필요로 새 기능 기획이 필요할 때, 기획군(planner-agent)에게 위임하여 전문 기획서를 생성���니다.

## Step 1. 컨텍스트 수집
- `E:/MRV/.workflow/STATE.md` 읽기 (프로젝트 현재 상태)
- CURRENT_STATE.md 읽기 (현재 마일스톤/페이즈)
- 관련 ADR이 있으면 읽기
- feature 설명과 context를 정리

## Step 2. 기획군 호출 (planner-agent)

Agent tool(subagent_type: `planner-agent`)로 호출. 프롬프트:

```
당신은 기획군(GihwekGoon)입니다.

[기획 요청]
기능명: {feature_name}
컨텍스트: {context}

[필수 산출물]
다음 포맷으로 기획��를 작성하세요:
1. 유저 심리 모델 (타겟감정, 메커니즘, 행동유도, 건전성경계)
   - 참조: .claude/agents/planner-references/psychology.md를 Read
2. 기획 상세
3. 밸런스 분��� (EV, 지배전략)
4. 벤치마크 비교
   - 참조: .claude/agents/planner-references/benchmarks.md를 Read
5. 리텐션 영향 예측 (D1/D7/D30)
6. 위상군 전달 사항 (��약, 요구사항, 상태머신)

[코인 분석이 필요한 경우]
- ��조: .claude/agents/planner-references/coin-analysis.md를 Read

[저장 경로]
docs/planning/{feature_name}_plan.md

[반환값]
PLAN_RESULT:
- status: DONE|NEED_INPUT
- plan_path: {저장 경로}
- summary: {한줄 요약}
- psychology_model: {타겟 감정 한줄}
- architect_constraints: {위상군 ���달 핵심 제약 1~3개}
```

## Step 3. 기획서 품질 자동 검증

기획군 반환 후 자동 체크:
1. **심리 4단계 완성도** — 4개 항목 모두 채워졌는가?
2. **위��군 전달 사항** — 제약/요구사항이 구현 가능한 수준으로 구체적인가?
3. **TGL #30 준수** — 가격 파라미터가 동적 값 기반인가?

불충분하면 기획군에게 1회 보완 요청.

## Step 4. 결과 반환

```
## Plan-Feature Complete
- **Feature:** {feature_name}
- **기획서:** {plan_path}
- **심리 모델:** {타겟 감정}
- **위상군 핵심 제약:** {1~3���}
- **다음 단계:** /design-ux → /handoff-build → /build-review
```

## Hard Rules
- 기획군의 기획서를 위상군이 수정하지 않��� (피드백만)
- 위상군은 §6(전달 사항)만 검증
- 기획서에 심리 4단계 없으면 PASS 안 됨
