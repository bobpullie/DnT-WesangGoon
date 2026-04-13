# 위상군 활성 규칙 (TEMS)

_동기화: 2026-03-23 19:36:49_

## [TCL] Rule #12
- **Tags:** knowledge_boundary, web_search, no_hallucination, research_first
- **Trigger:** 모르겠 불확실 대안없 확신없 방법없 어떻게 조사 검색 리서치 research search unknown uncertain alternative 최신 논문 paper
- **Rule:** 지식 한계 도달 시 행동 규칙: (1) 요청/제안에 대해 확신이 없거나 대안이 부족할 때 반드시 WebSearch/WebFetch로 최신 논문/기술 조사 수행 (2) 추측이나 오래된 지식으로 답변하지 말 것 (3) 조사 결과를 근거로 전문적 제안 제시 (4) 이는 CLAUDE.md 섹션 4.3 지식한계인식(No Hallucination) 원칙의 실행적 확장
- **Severity:** directive

## [TCL] Rule #11
- **Tags:** exception_management, lifecycle, topological_overhead, core_methodology
- **Trigger:** 예외 예외케이스 exception edge_case 생명주기 lifecycle 비활성화 deactivate 재구성 reconstruct 오버헤드 overhead
- **Rule:** 예외케이스 생명주기 관리: (1) 예외 발생 시 위상 케이스로 변환하여 FTS5 저장 (2) keyword_trigger로 리마인드 (3) 9개월 미사용 → 비활성화 (4) 3회 이상 수정 → 재구성하여 새 규칙으로 승격 (5) 이를 통해 위상화 오버헤드를 억제하면서 헛점을 보완
- **Severity:** directive

## [TCL] Rule #10
- **Tags:** core_value, studio_philosophy, topological_modeling, self_evolving
- **Trigger:** 핵심가치 철학 위상적 패턴 모델링 자가순환 자가발전 TCL TGL topological self-evolving core_value
- **Rule:** 모든 경험(지시/실수/성공)은 위상적 케이스로 추상화하여 FTS5에 축적하고, BM25 검색으로 자동 회수하는 자가순환 구조를 항상 유지. 단순 기록이 아닌 패턴 모델링이 목적. TCL/TGL은 이 철학의 구현체.
- **Severity:** directive

## [TGL] Rule #9
- **Tags:** Windows, Python, encoding, subprocess, cp949, utf-8
- **Trigger:** subprocess Windows cp949 UnicodeDecodeError 인코딩 encoding utf-8 한국어 Korean stdout
- **Rule:** Windows에서 subprocess 사용 시: (1) input은 .encode("utf-8")로 bytes 전달 (2) stdout은 .decode("utf-8")로 수동 디코딩 (3) capture_output=True + bytes 모드 사용 (4) text=True 사용 금지 — cp949 자동 디코딩됨
- **Severity:** error

## [TCL] Rule #8
- **Tags:** meta_rule, TGL, error_handling, self_correction
- **Trigger:** 에러 오류 실패 실수 시행착오 error fail mistake bug crash exception TGL guard
- **Rule:** 오류/실패/시행착오 발생 시: (1) 구체적 에러를 위상적 패턴으로 추상화 (2) 동일 유형의 미래 오류를 포착할 keyword_trigger 설계 (3) TGL 카테고리로 FTS5 커밋 (4) 이후 유사 작업 진입 시 preflight()로 자동 검색하여 과거 실패 패턴 회피.
- **Severity:** directive

## [TCL] Rule #7
- **Tags:** meta_rule, TCL, hook_trigger, directive_detection
- **Trigger:** 앞으로 이제부터 이제 이후로 다음부터 from_now_on henceforth directive 지시 규칙추가
- **Rule:** 사용자 발화에서 미래방향 지시어(앞으로|이제부터|이제|이후로|다음부터) 감지 시: (1) 구체적 지시를 추상적 위상 케이스로 일반화 (2) 유사 상황을 포괄하는 keyword_trigger 설계 (3) TCL 카테고리로 FTS5 커밋. 이는 일종의 소프트 hook — 위상군 스스로가 패턴매칭으로 준수해야 할 행동 규칙.
- **Severity:** directive

## [TCL] Rule #6
- **Tags:** session_lifecycle, session_start, context_restore, QMD
- **Trigger:** 세션시작 시작 안녕 hello 인사 session_start boot startup 컨텍스트복원
- **Rule:** 세션 시작 시: (1) QMD wesanggoon-sessions 컬렉션 최신 상태 확인 (2) handover_doc/에서 가장 최근 핸드오버 문서를 읽어 컨텍스트 복원 (3) FTS5에서 활성 TCL/TGL 규칙 로드
- **Severity:** directive

## [TCL] Rule #5
- **Tags:** session_lifecycle, QMD, session_end, persistence
- **Trigger:** 퇴근 종료 마무리 끝 세션종료 QMD qmd_sessions 세션기록
- **Rule:** 세션 종료 시: qmd_sessions/YYYY-MM-DD_session{N}.md에 세션 기록을 QMD 포맷으로 작성하여 저장. wesanggoon-sessions 컬렉션에 자동 인덱싱됨.
- **Severity:** directive

## [TCL] Rule #4
- **Tags:** session_lifecycle, handover, documentation, session_end
- **Trigger:** 퇴근 종료 마무리 끝 세션종료 session_end handover 핸드오버 인수인계 마감 bye
- **Rule:** 세션 종료 트리거(퇴근|종료|마무리|끝|세션종료) 감지 시: (1) 현재 세션의 모든 논의, 결정, 코드 변경, 미완료 사항, 컨텍스트를 빠짐없이 기록 (2) handover_doc/YYYY-MM-DD_session{N}.md로 저장 (3) 디테일 누락 금지 — 대화 흐름, 기술적 결정 근거, 다음 세션 TODO 포함
- **Severity:** directive

## [3DGS] Rule #2
- **Tags:** 3DGS, CUDA, HAC++, OOM_Error
- **Trigger:** 
- **Rule:** Must sample only 5% anchors per iteration during entropy training
- **Severity:** error

## [setup] Rule #1
- **Tags:** FTS5, BM25, setup
- **Trigger:** 
- **Rule:** 메모리 시스템은 memory/ 디렉토리 내 error_logs.db에 위치
- **Severity:** info
