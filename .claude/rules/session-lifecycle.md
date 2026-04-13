---
description: 세션 시작(부트), 종료(퇴근/마무리), 핸드오버 문서 작성 시 적용
alwaysApply: true
---

# 세션 라이프사이클 프로토콜

## 세션 시작 (Boot) — 첫 응답 전 반드시 실행
1. `E:/MRV/.workflow/STATE.md` 읽기 — 프로젝트 현재 상태
2. `E:/MRV/.workflow/CHANGELOG.md` 스캔 — 마지막 세션 이후 변경분
3. `E:/MRV/.workflow/QUEUE.md` 확인 — 태스크 현황
4. `handover_doc/CURRENT_STATE.md` 읽기 — 위상군 자체 컨텍스트 복원
5. FTS5 DB에서 활성 TCL/TGL 규칙을 로드하여 현재 세션에 적용

## 세션 종료 (Shutdown)
"퇴근", "종료", "마무리", "끝" 등의 트리거 감지 시:
1. **핸드오버 문서 작성:** `handover_doc/YYYY-MM-DD_session{N}.md`
   - 논의, 결정, 코드 변경, 미완료 사항, 다음 세션 TODO 포함
2. **CURRENT_STATE.md 갱신:** 롤링 상태 문서 업데이트 (< 100줄)
3. **QMD 세션 기록:** `qmd_sessions/YYYY-MM-DD_session{N}.md`로 저장
4. **FTS5 세션 요약 커밋:** 이번 세션의 핵심 교훈을 메모리 DB에 기록
