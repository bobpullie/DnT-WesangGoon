"""
DVC 프로젝트 스캐폴딩 CLI.

새 프로젝트에 DVC 체크리스트 시스템을 설치한다.

사용법:
  python init.py <project_root> [--force]

생성:
  {project_root}/
  ├── dvc_config.json          — 경로 커스터마이징 기본값
  ├── docs/BUILD_VERIFICATION.md  — DVC 정체성 문서
  └── src/checklist/
      ├── __init__.py
      ├── base.py
      ├── runner.py
      ├── cases.json
      └── chk_example.py
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPT_DIR / "templates"


DEFAULT_CONFIG = {
    "src_dir": "src",
    "data_dir": "data",
    "logs_dir": "logs",
    "scan_dirs": {}
}


BUILD_VERIFICATION_DOC = """# Build Verification — DVC

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
"""


def scaffold(project_root: Path, force: bool = False) -> int:
    """DVC 체크리스트 시스템을 프로젝트에 설치."""

    if not project_root.exists():
        print(f"❌ 프로젝트 루트가 존재하지 않음: {project_root}", file=sys.stderr)
        return 1

    if not project_root.is_dir():
        print(f"❌ 디렉토리가 아님: {project_root}", file=sys.stderr)
        return 1

    checklist_dest = project_root / "src" / "checklist"
    config_dest = project_root / "dvc_config.json"
    docs_dest = project_root / "docs" / "BUILD_VERIFICATION.md"

    # 충돌 검사
    conflicts = []
    if checklist_dest.exists() and any(checklist_dest.iterdir()):
        conflicts.append(str(checklist_dest))
    if config_dest.exists():
        conflicts.append(str(config_dest))
    if docs_dest.exists():
        conflicts.append(str(docs_dest))

    if conflicts and not force:
        print("⚠️  이미 존재하는 파일/디렉토리:", file=sys.stderr)
        for c in conflicts:
            print(f"    {c}", file=sys.stderr)
        print("\n--force 옵션으로 덮어쓰거나 수동으로 처리하세요.", file=sys.stderr)
        return 1

    # 1) src/checklist/ 생성 + 템플릿 복사
    checklist_dest.mkdir(parents=True, exist_ok=True)
    template_files = ["base.py", "runner.py", "chk_example.py", "cases.json", "__init__.py"]
    for tf in template_files:
        src = TEMPLATES_DIR / tf
        dst = checklist_dest / tf
        if not src.exists():
            print(f"  ⚠️  템플릿 부재: {src}", file=sys.stderr)
            continue
        shutil.copy2(src, dst)
        print(f"  ✅ {dst.relative_to(project_root)}")

    # 2) dvc_config.json
    if not config_dest.exists() or force:
        config_dest.write_text(
            json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  ✅ {config_dest.relative_to(project_root)}")

    # 3) docs/BUILD_VERIFICATION.md
    docs_dest.parent.mkdir(parents=True, exist_ok=True)
    if not docs_dest.exists() or force:
        docs_dest.write_text(BUILD_VERIFICATION_DOC, encoding="utf-8")
        print(f"  ✅ {docs_dest.relative_to(project_root)}")

    # 4) logs/checklist/ 디렉토리 보장
    (project_root / "logs" / "checklist").mkdir(parents=True, exist_ok=True)

    print("\n📦 DVC 설치 완료!")
    print(f"    프로젝트: {project_root}")
    print(f"    다음 단계:")
    print(f"      cd {project_root}")
    print(f"      python -m checklist.runner --list")
    print(f"      python -m checklist.runner --module example")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DVC 체크리스트 시스템 설치 CLI")
    parser.add_argument("project_root", help="DVC 를 설치할 프로젝트 루트 경로")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    return scaffold(root, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
