"""
[EXAMPLE] 도메인 체크리스트 템플릿.

이 파일은 새 프로젝트에 복사 후 도메인 특화 checker 의 출발점으로 사용한다.
아래 구조는 원조 Fermion `chk_display.py` 를 도메인 독립 형태로 정제한 것이다.

작성 원칙:
1. module_name 은 CLI 에서 `--module <이름>` 으로 선택되는 키
2. check_* 메서드 1개는 CASE_ID 1개에 대응 (여러 CheckResult 반환 가능)
3. scope 를 명시적으로 좁혀 false-positive 억제
4. 바이패스(# chk:skip) 존중 — 라인 매칭 후 filter_bypassed 로 제거
5. 모든 CheckResult 는 suggestion 제공 (linter 가 fixer 역할 겸함)

이름 규칙:
  chk_<domain>.py   → <Domain>Checklist 클래스 → module_name = "<domain>"
  메서드:  check_<case_id_lowercase> → CASE_ID 는 UPPER_SNAKE + 번호 suffix

@dependencies
  reads: {project_root}/src/**/*.py  (설정에 따라 다름)
"""
from __future__ import annotations

import re
from pathlib import Path

from checklist.base import BaseChecklist, CheckResult, SRC_DIR


class ExampleChecklist(BaseChecklist):
    """예시 체크리스트 — 복사 후 도메인에 맞게 재작성한다."""

    module_name = "example"

    # ── EXAMPLE_README_001: 프로젝트 README 존재 ──

    def check_example_readme_exists(self) -> CheckResult:
        """EXAMPLE_README_001: 프로젝트 루트에 README.md 가 있는지."""
        from checklist.base import PROJECT_ROOT

        readme = PROJECT_ROOT / "README.md"
        if readme.exists() and readme.stat().st_size > 100:
            return CheckResult(
                case_id="EXAMPLE_README_001",
                title="README.md 존재",
                severity="LOW",
                passed=True,
                detail=f"{readme.name} ({readme.stat().st_size} bytes)",
            )
        return CheckResult(
            case_id="EXAMPLE_README_001",
            title="README.md 누락 또는 빈약",
            severity="LOW",
            passed=False,
            detail=f"README.md 가 없거나 100 bytes 이하",
            file_path=str(readme),
            suggestion="프로젝트 개요, 설치, 사용법을 포함한 README.md 작성",
        )

    # ── EXAMPLE_PRINT_DEBUG_001: src/ 에 남은 print 디버그 탐지 ──

    # 허용: 명시적 log/output 의도, 테스트, CLI 도구
    _PRINT_ALLOW_PATTERNS = [
        r'^\s*(?:#|\"\"\"|\'\'\')',           # 주석/docstring
        r'def main\(',                         # CLI main 함수
        r'if __name__\s*==\s*[\"\']__main__', # CLI 진입점
    ]

    # 의도적 출력 파일 (로그, CLI, 리포트 생성기 등)
    _PRINT_ALLOW_FILES = {
        "runner.py",        # DVC runner 자체
        "cli.py",
        "report_gen.py",
    }

    def check_example_print_debug(self) -> list[CheckResult]:
        """EXAMPLE_PRINT_DEBUG_001: 실행 모듈에 남은 print() 디버그 추적 흔적 탐지."""
        results = []
        if not SRC_DIR.exists():
            return [CheckResult(
                case_id="EXAMPLE_PRINT_DEBUG_001",
                title="src/ 디렉토리 없음",
                severity="INFO",
                passed=True,
                detail=f"{SRC_DIR} 없음 — 건너뜀",
            )]

        py_files = self.get_all_py_files(SRC_DIR, recursive=True)

        for py_file in py_files:
            if py_file.name in self._PRINT_ALLOW_FILES:
                continue
            if py_file.name.startswith("test_"):
                continue
            if "checklist" in str(py_file):
                continue  # DVC 자체 제외

            hits = self.find_pattern_in_file(py_file, r'\bprint\s*\(')
            hits = self.filter_bypassed(py_file, hits, "EXAMPLE_PRINT_DEBUG")

            # 주석/docstring/main 허용 라인 제거
            filtered_hits = []
            text_lines = self.read_file(py_file).splitlines()
            for line_no, line_text in hits:
                skip = False
                for pat in self._PRINT_ALLOW_PATTERNS:
                    if re.search(pat, line_text):
                        skip = True
                        break
                if not skip:
                    filtered_hits.append((line_no, line_text))

            if filtered_hits:
                results.append(
                    CheckResult(
                        case_id="EXAMPLE_PRINT_DEBUG_001",
                        title=f"print() 디버그 추적 흔적: {py_file.name}",
                        severity="LOW",
                        passed=False,
                        detail=f"{len(filtered_hits)}건 — "
                               + "; ".join(f"L{ln}: {txt[:50]}" for ln, txt in filtered_hits[:3]),
                        file_path=str(py_file),
                        line_number=filtered_hits[0][0],
                        suggestion="logging 모듈로 교체 또는 `# chk:skip EXAMPLE_PRINT_DEBUG 사유` 추가",
                    )
                )

        if not results:
            results.append(
                CheckResult(
                    case_id="EXAMPLE_PRINT_DEBUG_001",
                    title="print() 디버그 흔적 점검",
                    severity="LOW",
                    passed=True,
                    detail=f"{len(py_files)}개 파일 점검 완료, print 흔적 없음",
                )
            )
        return results

    # ── EXAMPLE_GITIGNORE_001: 공통 차단 항목 탐지 ──

    _GITIGNORE_REQUIRED = [
        "__pycache__",
        ".env",
        "*.pyc",
    ]

    def check_example_gitignore_coverage(self) -> CheckResult:
        """EXAMPLE_GITIGNORE_001: .gitignore 에 공통 차단 항목이 포함되는지."""
        from checklist.base import PROJECT_ROOT

        gi = PROJECT_ROOT / ".gitignore"
        if not gi.exists():
            return CheckResult(
                case_id="EXAMPLE_GITIGNORE_001",
                title=".gitignore 없음",
                severity="MEDIUM",
                passed=False,
                detail="프로젝트 루트에 .gitignore 파일 부재",
                file_path=str(gi),
                suggestion="최소한 __pycache__, .env, *.pyc 는 무시 필요",
            )

        text = gi.read_text(encoding="utf-8", errors="ignore")
        missing = [p for p in self._GITIGNORE_REQUIRED if p not in text]

        if missing:
            return CheckResult(
                case_id="EXAMPLE_GITIGNORE_001",
                title=".gitignore 누락 항목",
                severity="LOW",
                passed=False,
                detail=f"누락: {', '.join(missing)}",
                file_path=str(gi),
                suggestion=f".gitignore 에 다음 추가: {', '.join(missing)}",
            )

        return CheckResult(
            case_id="EXAMPLE_GITIGNORE_001",
            title=".gitignore 공통 항목 점검",
            severity="LOW",
            passed=True,
            detail="__pycache__, .env, *.pyc 모두 포함됨",
        )
