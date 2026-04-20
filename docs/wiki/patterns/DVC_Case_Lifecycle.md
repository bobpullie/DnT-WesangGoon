---
date: 2026-04-20
status: Active
scope: dvc-framework
tags: [dvc, lifecycle, pattern, regression-prevention, deterministic]
---

# Pattern — DVC Case Lifecycle

## ID

PAT-DVC-LIFECYCLE

## 정의

버그 발견 → case 일반화 → cases.json 등록 → chk_*.py 구현 → runner 통과 → 영구 회귀 방지의  
6단계 순환 패턴. DVC 프레임워크의 핵심 작동 원리.

## 데이터 소스 / 의존성

- `src/checklist/cases.json` — case 레지스트리
- `src/checklist/chk_<category>.py` — 도메인별 checker 구현
- `src/checklist/base.py` — `BaseChecklist`, `CheckResult` 기반 클래스
- `python -m checklist.runner` — 전체 검증 실행

## 6단계 패턴

### 1. Detect — 버그/회귀 포착

증상 파악: 무엇이 잘못되었는가? 어떤 파일/경로/데이터에서?

### 2. Generalize — 일반화 질문

> "같은 부류의 버그가 다른 파일·다른 시점에 또 날 수 있는가?"

YES → case로 일반화. NO (1회성) → 단순 수정 후 `origin_bug`에 기록만.

### 3. Define Case — cases.json 등록

```json
{
  "case_id": "CATEGORY_NAME_001",
  "category": "category",
  "title": "점검 항목명",
  "generalized": "이 부류의 버그를 포괄하는 점검 서술",
  "origin_bug": "2026-04-20 — 어떤 상황에서 발생했는지",
  "checker": "chk_category.py → check_category_name",
  "scope": "src/**/*.py",
  "auto_discover": true,
  "added_date": "2026-04-20",
  "severity": "MEDIUM"
}
```

**Case ID 규칙:** `UPPER_SNAKE_CASE_NNN`. 카테고리는 `chk_<category>.py`와 반드시 짝.

### 4. Implement Check — chk_*.py 구현

```python
class CategoryChecklist(BaseChecklist):
    def check_category_name_001(self) -> CheckResult:
        # 결정론 필수 — 랜덤·LLM·네트워크 호출 금지
        # 동일 입력 → 항상 동일 결과
        ...
        return CheckResult(passed=True, case_id="CATEGORY_NAME_001")
```

### 5. Verify Regression — 수정 전후 검증

수정 전: case FAIL 확인 → 수정 후: case PASS 확인.  
"수정 없이 case만 등록해 green 증가" anti-pattern 방지.

### 6. CI Integration — 전체 runner 통과

```bash
python -m checklist.runner   # 모든 case PASS 확인
```

## 현재 상태

위상군 dogfood 설치 (2026-04-20): case 3개 (EXAMPLE 카테고리 baseline), chk_example.py 1개.  
실제 도메인 case 추가는 운영 중 버그 발생 시 점진적으로.

## Anti-Pattern

| Anti-pattern | 설명 | 올바른 대안 |
|-------------|------|-----------|
| LLM 판정 case | `runner`가 LLM 호출로 pass/fail 결정 | TEMS TGL로 이전 |
| 환경 의존 case | 네트워크·랜덤 시드·현재 시각 사용 | 결정론적 입력으로 재설계 |
| 빈 case 등록 | checker 구현 없이 cases.json만 추가 | 반드시 chk_*.py 동시 구현 |
| 수정 전 green | 버그 수정 전에 case 통과 설계 | 수정 전 FAIL → 수정 후 PASS 순서 준수 |

## 관련 개념

[[../concepts/DVC]] [[../concepts/DVC_vs_TEMS]] [[../principles/Case_Generalization]]

## 참조

- [[../concepts/DVC]] — DVC 프레임워크 전체 정의
- [[../concepts/DVC_vs_TEMS]] — TEMS TCL과의 혼동 방지
- [[../principles/Case_Generalization]] — 일반화 우선 원리
