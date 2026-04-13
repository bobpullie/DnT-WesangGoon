---
name: tems-sweep
description: "TEMS 규칙 건강도 점검 + 상태 전이 + 가비지 정리. 규칙 생명주기를 자동 관리합니다."
user_invocable: true
---

# /tems-sweep — TEMS 규칙 건강도 점검 및 정리

## Usage
```
/tems-sweep [--report-only]
```
- `--report-only`: 리포트만 출력하고 실제 변경은 하지 않음

## Execution Steps

### 1. 현재 상태 스냅샷
```python
from memory.tems_engine import HealthScorer
scorer = HealthScorer()
report_before = scorer.get_health_report()
```
전체 규칙 수, 상태별(hot/warm/cold/archive) 분포를 기록합니다.

### 2. THS 재계산 + 상태 전이
```python
result = scorer.run_lifecycle_sweep()
```
모든 규칙의 THS를 재계산하고 상태를 전이합니다:
- Hot (THS≥0.7) → 활발히 사용 중
- Warm (0.4~0.7) → 보통
- Cold (<0.4) → 비활성
- Archive → Cold 6개월 이상 유지 시

### 3. 예외케이스 분류 (Phase 3)
```python
from memory.tems_engine import AnomalyCertifier
certifier = AnomalyCertifier()
certifier.run_exception_sweep()
```
- Type A (커버리지 부족) → 기존 규칙 확장 제안
- Type B (규칙 충돌) → 우선순위 재조정 제안
- Type C (진짜 이상치) → 독립 예외 규칙 저장
- 고 persistence 예외 → 정식 TGL 승격 후보 보고

### 4. 메타규칙 건강도 체크 (Phase 4)
```python
from memory.tems_engine import MetaRuleEngine
meta = MetaRuleEngine()
suggestion = meta.suggest_weight_adjustment()
```
시스템 건강도(coverage + stability + freshness)를 평가하고,
필요 시 THS 가중치(α,β,γ,δ,ε) 조절을 **제안**합니다 (자동 적용하지 않음).

### 5. 수정 3회 이상 규칙 보고
수정 횟수가 3회 이상인 규칙을 "재구성 후보"로 보고합니다.
위상군이 직접 규칙을 재작성할지 판단합니다.

### 6. 리포트 출력
다음 형식으로 사용자에게 보고합니다:

```
## TEMS Health Sweep Report
- **총 규칙:** N개
- **상태 분포:** Hot: N, Warm: N, Cold: N, Archive: N
- **전이 발생:** warm→cold: N건, cold→archive: N건
- **재구성 후보:** N건 (수정 3회+)
- **예외 승격 후보:** N건
- **메타규칙 제안:** (있으면 표시)
```

### 7. --report-only가 아닌 경우
Cold→Archive 전이를 적용하고, archive 규칙을 preflight에서 제외합니다.

## Hard Rules
- Archive 규칙은 **삭제하지 않습니다** (검색은 가능, preflight 주입에서만 제외)
- 메타규칙 가중치 변경은 제안만 하고, **종일군 승인 후** 적용
- 이 스킬은 최소 주 1회 또는 5세션마다 실행을 권장
