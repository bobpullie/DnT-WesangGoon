---
name: design-ux
description: "DESIGN 단계에서 게임/인터랙티브 시스템의 4개 UX Layer 산출물을 생성합니다. (TCL #25)"
user_invocable: true
---

# /design-ux — UX Layer 산출물 생성

## Usage
```
/design-ux <feature_name> [adr_path]
```

**Examples:**
- `/design-ux heatmap-overlay`
- `/design-ux auto-stake docs/decisions/ADR-011.md`

## Purpose
DESIGN 단계에서 ADR + MODULE.md에 추가로 **4개 UX Layer 산출물**을 생성합니다.
기술 구현 이전에 유저 심리 모델을 먼저 정의합니다 (TCL #25, #28).

## Execution Steps

### Step 1. 컨텍스트 로드
- ADR 문서가 있으면 Read로 읽기
- 관련 기획 문서 확인 (docs/planning/)
- 현재 CURRENT_STATE.md 확인

### Step 2. Layer 1 — 심리 모델 (Psychology Model)
이 기능이 유저에게 유발해야 할 감정과 행동을 정의합니다:

```markdown
## 심리 모델
- **타겟 감정:** {이 기능이 유발해야 할 감정}
- **트리거:** {감정을 유발하는 구체적 메커니즘}
- **보상 스케줄:** {Variable Ratio / Fixed Interval / etc.}
- **이탈 방지:** {유저가 포기하지 않도록 하는 장치}
```

### Step 3. Layer 2 — 상태 머신 (State Machine)
유저 인터랙션의 상태 전이를 정의합니다:

```markdown
## 상태 머신
| 상태 | 진입 조건 | 유저 행동 | 전이 대상 |
|------|----------|----------|----------|
| idle | ... | ... | ... |
```

### Step 4. Layer 3 — 이벤트 분배 (Event Distribution)
입력 레이어 구분, 입력 수단별 동작 매핑, 경합 해결 규칙 (TCL #36):

```markdown
## 이벤트 분배
- **입력 레이어:** {차트 / 오버레이 / 패널}
- **마우스:** {좌클릭 / 우클릭 / 휠}
- **터치:** {탭 / 드래그 / 핀치}
- **경합 해결:** {pointer-events 전략}
```

### Step 5. Layer 4 — 시각 검증 기준 (Layout Visual Spec)
빌드 후 시각적 검증에 사용할 기준 (TCL #42):

```markdown
## LVS (Layout Visual Spec)
| 요소 | data-layout | 상태별 제약 | 검증 기준 |
|------|-------------|-----------|----------|
```

### Step 6. 산출물 저장
```
docs/planning/{feature_name}_ux_layers.md
```
에 4개 Layer를 통합 문서로 저장합니다.

### Step 7. 사용자에게 요약 보고
```
## UX Layers Complete
- **Feature:** {feature_name}
- **파일:** {저장 경로}
- **심리 모델:** {타겟 감정 1줄 요약}
- **상태 수:** {N}개 상태, {M}개 전이
- **입력 레이어:** {N}개
- **LVS 항목:** {N}개
```

## Hard Rules
- 기술 구현 세부사항은 포함하지 않음 (그건 ADR의 영역)
- 심리 모델이 불명확하면 기획군에게 위임 제안
- 모든 산출물은 한국어로 작성 (TCL #29)
