# Build Verification — DVC

이 프로젝트는 **DVC (Deterministic Verification Checklist)** 를 사용한다.

## 중요 — TEMS TCL 과의 구분

**DVC ≠ TEMS TCL**. 두 시스템은 층위가 완전히 다르다:

| 축 | DVC (이 시스템) | TEMS TCL |
|----|----------------|----------|
| 실행 시점 | build-time / CI / cron | prompt-time (LLM preflight hook) |
| 저장 형태 | `cases.json` + `chk_*.py` Python | SQLite DB 자연어 규칙 |
| 검증 방식 | 정적 분석 + 파일 패턴 + SSH 해시 | LLM 의미 매칭 + 컨텍스트 주입 |
| 소비자 | 개발자, CI 서버, cron | LLM agent (Claude) |
| 결과 | pass/fail + suggestion | 규칙 본문 주입 |

이 저장소에서 **"TCL"** 이라는 단어는 **DVC case 가 아닌 TEMS TCL 규칙**을 의미한다.
DVC 점검 항목은 **"case"** 로 지칭한다 (예: `DISPLAY_HUMANIZE_001`).

## 실행

```bash
python -m checklist.runner                    # 전체 점검
python -m checklist.runner --module example   # 특정 모듈
python -m checklist.runner --audit-bypass     # 바이패스 감사
python -m checklist.runner --audit-cases      # 케이스 생명주기 분석
python -m checklist.runner --list             # 등록된 모듈 목록
```

## 상세 가이드

- `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/SKILL.md` — skill 메타데이터
- `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/ARCHITECTURE.md` — 설계 원리 10가지
- `E:/DnT/DnT_WesangGoon/.claude/skills/dvc/GUIDE.md` — 새 case 추가 절차, 바이패스 규약, CI 통합

## 파일 구조

```
src/checklist/
├── __init__.py
├── base.py              BaseChecklist + CheckResult + 바이패스 시스템
├── runner.py            CLI + 자동 discovery + 감사 도구
├── cases.json           케이스 레지스트리
└── chk_*.py             도메인별 checker 모듈
```

## 바이패스 규약

소스 코드에 예외를 허용할 때:

```python
secret = "hardcoded_value"  # chk:skip CONFIG_HARDCODE 로컬 테스트용 더미
```

- `# chk:skip CASE_ID 사유` — 사유 필수. 없으면 바이패스 무효
- prefix 매칭 — `CONFIG_HARDCODE` 로 쓰면 `CONFIG_HARDCODE_001`, `CONFIG_HARDCODE_002` 모두 바이패스
- `--audit-bypass` 로 전체 바이패스 감사 가능
