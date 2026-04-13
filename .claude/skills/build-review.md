---
name: build-review
description: "빌드군→기획군 자율 티키타카 루프. 빌드+UX검증+기획리뷰를 자동 체이닝하고 최종 결과만 반환."
user_invocable: true
context: fork
---

# /build-review — Autonomous Build-Review Tikitaka Loop (v2026.3.29)

## Usage
```
/build-review <task_id> [project_path]
```

## Purpose
위상군의 컨텍스트를 보호하면서 빌드→검증→리뷰 전체 과정을 자율 실행.
TCL #33 (빌드→기획 리뷰→종일군 테스트) 프로��스의 자동화 구현.

**v2026.3.29 (관리군 개선):** `/ux-verify`, `/fix-verify` 자동 체이닝 추가.

---

## Step 1. Parse Arguments & Load Context
- `task_id`: 필수 (예: TASK-M1-001)
- `project_path`: 기본 `E:\MRV`
- 태스��� 문서, ADR, CLAUDE.md, build-goon.md 로드

---

## Step 2. Build Phase — 빌드 에이전트 호출
Agent tool로 빌드군 호출. 프롬프트에 반드시 포함:
- 제품 도메인 지식 (TCL #26)
- 태스크 문서 + ADR 경로
- PROTECTED_CODE.md 참조
- Thin Return Protocol 준수

빌드군 FAILED → 재시도 1회. 불가 → ESCALATE 종료.

---

## Step 3. 자동 검증 �� UX-VERIFY / FIX-VERIFY (v2026.3.29 신규)

빌드 완료(DONE) 후, **위상군이 직접 지시하지 않아도 자동으로 검증 실행:**

### 판단 기준:
- 태스크가 **UI 관련** (changed_files에 `.tsx` 포함, 또는 태스크명에 UI/UX/레이아웃/차트/패널 포함)
  → 빌드군에게 **`/ux-verify`** 실행 지시
- 태스크가 **버그 수정** (태스크명에 BUG/FIX/수정/패치 포함)
  → 빌드군에게 **`/fix-verify`** 실행 지시
- **둘 다 해당되면 둘 다 실행**

### 실행 방법:
빌드군을 다시 호출하되, 프롬프트에 추가:
```
[검증 단계]
빌드가 완료되었습니다. 이제 다음 검증을 실행하세요:
- /ux-verify {변경된 ��요 컴포넌트}  (UI 관련 시)
- /fix-verify {버그 설명}  (버그 수정 시)
검증 결과를 빌드 리포��� 하단에 추가하세요.
```

검증 PARTIAL이면 리뷰에 전달하여 기획군이 판단.

---

## Step 4. Review Phase — 기획군(planner-agent) 호출

빌드+검증 완료 후, Agent tool(subagent_type: `planner-agent`)로 기획군 호출.

프롬프트 필수 포함:
- 빌드 리포트 경로 + 원본 태스크 + ADR
- 검증 결과 (UX-VERIFY/FIX-VERIFY 포함 여부)
- 판정 기준: PASS | REVISE | REJECT
- TGL #30 확인 지시
- Thin Return Protocol

---

## Step 5. 자동 기획 품질 체크 (v2026.3.29 신규)

기획군 ���뷰 결과를 ��으면, **자동으로 다음을 확인:**

1. 기획��이 **심리 4단계**(타겟감정/메커니즘/행동유도/건전성)를 리��에 반영했는가?
2. REVISE 판정 시 `revise_items`가 **구체적이고 실행 가능**한가?
3. REJECT 판정 시 **근본 원인**이 명시되었는가?

불충분하면 기획군에게 보완 요청 (1회).

---

## Step 6. Routing — PASS/REVISE/REJECT

| Verdict | Action |
|---------|--------|
| **PASS** | Step 7로 → 최종 결과 반환 |
| **REVISE** | Step 2로 (revise_items + review_path를 빌드 프롬프트에 추가) |
| **REJECT** | Step 7로 → REJECT로 종료 |

**최대 반복: 3회.** 3회 REVISE 후에도 PASS 못 받으면 ESCALATE.

---

## Step 7. Final Return

```
## Build-Review Complete
- **Task:** {task_id}
- **Verdict:** {PASS|REJECT|ESCALATE}
- **Rounds:** {N}회
- **Build Report:** {final_report_path}
- **Review Report:** {final_review_path}
- **UX-VERIFY:** {PASS|PARTIAL|N/A}
- **FIX-VERIFY:** {PASS|PARTIAL|N/A}
- **Summary:** {기획군 최종 판정}
- **Changed Files:** {파일 목록}
```

## Hard Rules
1. 리포트 내용을 반환값에 포함하지 않음 (경로만)
2. 빌드 품질이나 기획 적합성을 직접 판단하지 않음 (라우터 역할)
3. 최대 3회전 (무한 루프 방지)
4. **UI 태스크는 UX-VERIFY, 버그 태스크는 FIX-VERIFY 자동 실행** (v2026.3.29)
5. **기획군 리뷰에 심리 4단계 반영 확인** (v2026.3.29)
