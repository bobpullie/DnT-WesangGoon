---
name: rule-review
description: "현재 TEMS DB의 전체 규칙을 표로 출력하여 위상군이 직접 검토/정리할 수 있도록 합니다."
user_invocable: true
---

# /rule-review — TEMS 규칙 전체 리뷰

## Usage
```
/rule-review [--filter project:dnt] [--status hot|warm|cold]
```

## Purpose
현재 TEMS DB에 저장된 모든 규칙을 가독성 높은 표로 출력합니다.
위상군이 직접 규칙을 검토하고, 병합/삭제/수정을 결정할 수 있도록 돕습니다.

## Execution Steps

### Step 1. DB에서 전체 규칙 로드
```python
from memory.tems_engine import HealthScorer
scorer = HealthScorer()
report = scorer.get_health_report()
```

### Step 2. 필터 적용
인자가 있으면 해당 조건으로 필터링:
- `--filter project:dnt` → context_tags에 'project:dnt' 포함된 규칙만
- `--status warm` → rule_health.status가 'warm'인 규칙만

### Step 3. 계층별 분류 출력
규칙을 4개 Layer로 분류하여 출력합니다:

```
## Layer 0: 항상성 (Homeostatic) — Hook/자동화
| ID | 상태 | THS | 규칙 요약 | 태그 |

## Layer 1: 절차적 (Procedural) — /커스텀명령으로 커버
| ID | 상태 | THS | 규칙 요약 | 연결 스킬 |

## Layer 2: 도메인 특화 (Domain-Specific) — Preflight
| ID | 상태 | THS | 규칙 요약 | 프로젝트 |

## Layer 3: 행동 원칙 (Behavioral) — CLAUDE.md/rules/
| ID | 상태 | THS | 규칙 요약 |
```

### Step 4. 관리군 주석 표시
`[⚠️ 관리군 검토요청]`이 포함된 규칙은 별도 섹션으로 분리하여 강조합니다.

### Step 5. 액션 제안
- 중복 후보: keyword_trigger 유사도 높은 규칙 쌍
- Archive 후보: THS < 0.3 규칙
- 재구성 후보: 수정 3회 이상 규칙

## Hard Rules
- 규칙을 수정/삭제하지 않음 (리뷰만)
- 위상군이 이 리포트를 보고 직접 판단
