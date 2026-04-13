---
name: plan-review-request
description: "기획군에게 빌드군 구현물의 기획 의도 리뷰�� 위임합니다. /build-review 내부에서 자동 호출됩니다."
user_invocable: true
context: fork
---

# /plan-review-request — 기획군에게 빌드 리뷰 위임

## Usage
```
/plan-review-request <task_id> <build_report_path> [project_path]
```

## Purpose
빌드군의 구현이 기획 의도에 부합하는지 기획군에게 독립적으로 리뷰를 요청합니다.
`/build-review`의 Step 4에서 자동 호출되지만, 단독으로도 사용 가능합니다.

## Step 1. 컨텍스트 로드
- `E:/MRV/.workflow/CHANGELOG.md` 최근 변경분 읽기 (빌드군 최신 수정 파악)
- 빌드 리포트 읽기
- 원본 태스크 문서 읽기
- 관련 ADR/기획서 읽기

## Step 2. 기획군 호출 (planner-agent)

```
당신은 기획군(GihwekGoon)입니다. 빌드군의 구현물을 기획 의도 관점에서 검토합니다.

[리뷰 대상]
- 빌드 리포트: {build_report_path}
- 태스크 문서: {task_path}
- ADR: {adr_path}

[리뷰 절차]
1. 빌드 리포트 Read → 코드 Read → 설계 문서 Read
2. 기획 의도 부합 검증
3. TGL #30 확인 (가격 파라미터 동적 값)
4. 심리 모델 관점에서 UX 검증

[판정]
- PASS: 기획 의도 일치 + 핵심 요구 충족
- REVISE: 구체적 수정항목 명시
- REJECT: 근본 재설계 필요

[저장]
docs/reviews/{task_id}_plan_review{_vN}.md

[반환값]
REVIEW_RESULT:
- verdict: PASS|REVISE|REJECT
- review_path: {경로}
- summary: {50자}
- revise_items: [{항목}]
- psychology_check: {심리 모델 부합 여부}
```

## Step 3. 결과 반환
```
## Plan-Review Complete
- **Task:** {task_id}
- **Verdict:** {PASS|REVISE|REJECT}
- **Review:** {review_path}
- **Summary:** {기획군 판정}
- **심리 모델 부합:** {YES|PARTIAL|NO}
```
