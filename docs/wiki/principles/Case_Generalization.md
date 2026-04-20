---
date: 2026-04-20
status: Active
scope: all-projects
tags: [dvc, generalization, regression-prevention, principle]
---

# Principle — Case Generalization (케이스 일반화 우선)

## 원리

버그를 발견했을 때 **개별 픽스만 하지 말고**, 먼저 물어라:

> "이 부류의 버그가 다른 파일·다른 시점에 또 날 수 있는가?"

YES라면, 버그 수정과 동시에 그 부류를 포착하는 **DVC case**를 `cases.json`에 등록한다.  
이 case는 CI / pre-commit / 주기 실행을 통해 팀 전체의 영구 회귀 방지 장치가 된다.

## 출처 문헌

DVC 원조 코드군(FermionQuant) 운영 패턴에서 귀납.  
Karpathy "compilation > RAG" 원칙과 동형: 지식을 분산 저장이 아닌 구조화된 체계로 통합.

## 적용 범위

DVC 체계 전체. 버그 발견 시 반드시 일반화 가능성을 검토한다.

## 근거

1. **재발 비용** — 같은 부류 버그가 다른 파일에서 재발하면 또 디버깅·수정 비용 발생.
2. **팀 지식 컴파일** — 일반화된 case는 개인 기억이 아닌 레포지토리 수준의 구조화된 지식이 된다.
3. **결정론적 보장** — case는 LLM 판정 없이 항상 동일 결과 → 신뢰도 높음.
4. **복리 효과** — case 누적 → 회귀 방지 범위 확대 → 신규 버그가 기존 case에 걸릴 확률 증가.

## 실행 방법

```
1. 버그 수정 전: 일반화 가능성 판단 (10초 질문)
2. 일반화 가능: cases.json에 case 정의 + chk_*.py 구현
3. 수정 전 case FAIL → 수정 후 case PASS 확인 (회귀 테스트)
4. python -m checklist.runner 전체 통과
```

상세 절차: [[../patterns/DVC_Case_Lifecycle]]

## 예외 (case 등록 생략 가능)

- 일회성 데이터 오류 (외부 서비스 장애, 수동 실수)
- 재발 가능성이 구조적으로 0에 가까운 경우
- 단, **기록은 남긴다** — `origin_bug` 필드에라도 사유 보존

## 검증 방법

수정 PR에 다음 질문에 대한 답 포함 필수:

> "이 패턴이 재발했을 때 어떻게 탐지되는가?"

DVC case를 추가했다면 → `python -m checklist.runner` 통과 증거.  
추가 안 했다면 → 예외 사유를 명시.

## 주의점

- **LLM 판정 case 금지** — 결정론 불가. TEMS TGL로 이전.
- **case 먼저, 수정 나중** 순서 혼동 금지 — 수정 전 FAIL이 증거.
- 일반화 과잉도 경계 — "모든 버그를 case로"는 유지 비용 증가. 재발 가능성 판단이 핵심.

## 관련 개념

[[../concepts/DVC]] [[../patterns/DVC_Case_Lifecycle]] [[Self_Containment(TEMS 자기완결성)]]

## 참조

- [[../concepts/DVC]] — DVC 프레임워크 전체 정의
- [[../patterns/DVC_Case_Lifecycle]] — case 일반화의 구체적 6단계 순환
- [[Self_Containment(TEMS 자기완결성)]] — 자기완결성 원리 (유사 컴파일 철학)
