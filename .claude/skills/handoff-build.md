---
name: handoff-build
description: "설계→빌드 핸드오프 패키지 생성. 태스크 유형에 따라 검증 명령을 자동 포함합니다."
user_invocable: true
---

# /handoff-build — 설계→빌드 핸드오프 패키지 생성 (v2026.3.29)

## Usage
```
/handoff-build <task_id> [project_path]
```

## Purpose
설계 산출물을 빌드군에게 전달할 때, 도메인 지식/UX 검증 기준을 함께 패키징.
**v2026.3.29:** 태스크 유형에 따라 빌드군 검증 명령을 자동 포함.

## Step 1. 태스크 문서 로드
- `{project_path}/docs/planning/` 에서 태스크 문서
- 관련 ADR, UX Layer 문서, PROTECTED_CODE.md

## Step 2. 태스크 유형 자동 감지 + 검증 명령 결정

| 감지 조건 | 포함할 검증 명령 |
|-----------|----------------|
| 태스크에 UI/UX/레이아웃/차트/패널 포함 | `빌드 완료 후 /ux-verify 실행 필수` |
| 태스크에 BUG/FIX/수정/패치 포함 | `수정 완료 후 /fix-verify 실행 필수` |
| 기획서에 심리 모델이 있음 | `구현 후 기획 의도 자가 점검 필수` |
| 해당 없음 | 기본 자체 검���만 |

## Step 3. 핸드오프 패키지 구성

```markdown
# Build Handoff: {task_id}

## 1. 제품 도메인 지식
- DnT: 크립토 가격 예측 게임 (3~5분 라운드)
- 이 태스크의 위치와 목적

## 2. 설계 목적 (Why)
- 해결하려는 유저 문제
- 성공 기준

## 3. 기술 명세 (What)
- ADR 참조, 데이터 모델, API 인터페이스

## 4. UX 검증 기준 (How to Verify)
- 상태별 예상 동작, LVS 항목, 엣지 케이스

## 5. 보호 코드 (Protected Code)
- 수정 금지 파일/함수 + 이유

## 6. 필수 검증 명령 ← v2026.3.29 자동 삽입
- {태스크 유형에 따라 자동 결정된 /ux-verify 또는 /fix-verify 지시}
```

## Step 4. .workflow/ 연동
1. `E:/MRV/.workflow/HANDOFF.md`에 활성 핸드오프 기록:
   ```markdown
   ### [HO-{번호}] 위상군 → 빌드군
   - **작업:** {task_id} — {태스크 요약}
   - **입력 문서:** docs/handoff/{task_id}_handoff.md
   - **기대 산출물:** {구현 대상}
   - **완료 조건:** {성공 기준}
   - **검증 명령:** {/ux-verify 또는 /fix-verify}
   - **상태:** PENDING
   ```
2. `E:/MRV/.workflow/QUEUE.md`에 태스크 등록 (담당: 빌드군)
3. `E:/MRV/.workflow/CHANGELOG.md`에 핸드오프 이벤트 기록

## Step 5. 저장 및 보고
`docs/handoff/{task_id}_handoff.md`에 저장.

## Hard Rules
- 도메인 지식 섹션 생략 금지
- **검증 명령 섹션은 태스크 유형에 따라 자동 포함** (위상군이 기억할 필요 없음)
- `.workflow/HANDOFF.md` 기록 없이 핸드오프 완료 금지
- `/build-review`와 연계 가능
