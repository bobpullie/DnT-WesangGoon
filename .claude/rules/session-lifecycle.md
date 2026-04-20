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
3. **QMD 세션 recap:** `qmd_drive/recaps/YYYY-MM-DD_session{N}.md`로 저장 (S35에서 구 `qmd_sessions/` → `qmd_drive/recaps/` 로 이관 — TCL #116 / [[docs/wiki/principles/Per_Agent_Local_QMD]])
4. **FTS5 세션 요약 커밋:** 이번 세션의 핵심 교훈을 메모리 DB에 기록
5. **LLM Wiki L2 추출 (Mode B):**
   ```bash
   python ~/.claude/skills/TWK/scripts/extract_session_raw.py --config ./wiki.config.json
   ```
   출력: `docs/session_archive/YYYYMMDD_sessionN_raw.md` (기계적 Q&A, 0 토큰)
6. **LLM Wiki L3 Curation:** 이번 세션에 새 **결정/위상 패턴/개념/원리**가 있었나?
   - YES → `docs/wiki/<section>/` 에 템플릿(`~/.claude/skills/TWK/templates/page-templates/`) 복사해 작성
     - `[[../../session_archive/YYYYMMDD_sN_raw]]` 로 L2 wikilink + `index.md` 등록 + `log.md` append
   - NO → skip (억지로 쓰지 말 것 — Karpathy 원칙)
7. **Lint 주기 확인:** 5세션마다 또는 10페이지 추가 시
   ```bash
   python ~/.claude/skills/TWK/scripts/lint.py --config ./wiki.config.json
   ```
