"""
DVC (Deterministic Verification Checklist) — Base classes.

프로젝트 무관 베이스. 모든 도메인별 체크리스트는 BaseChecklist 상속 후
check_* 메서드를 구현한다. 바이패스 시스템(# chk:skip CASE_ID 사유) 내장.

Paths are configurable via dvc_config.json at project root, or fall back to defaults.

@dependencies
  reads: dvc_config.json (optional)
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

SEVERITY = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


# ── DVC Config: project-specific paths ──

def _find_project_root(start: Path) -> Path:
    """상위 순회하며 dvc_config.json 또는 .git 를 찾아 프로젝트 루트 결정."""
    cur = start.resolve()
    while cur != cur.parent:
        if (cur / "dvc_config.json").exists() or (cur / ".git").exists():
            return cur
        cur = cur.parent
    return start.resolve()


def _load_config() -> dict:
    """dvc_config.json 로드. 없으면 빈 dict."""
    root = _find_project_root(Path(__file__).parent)
    cfg_path = root / "dvc_config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


_CONFIG = _load_config()
PROJECT_ROOT = _find_project_root(Path(__file__).parent)

# 설정된 경로 또는 기본값
SRC_DIR = PROJECT_ROOT / _CONFIG.get("src_dir", "src")
DATA_DIR = PROJECT_ROOT / _CONFIG.get("data_dir", "data")
LOGS_DIR = PROJECT_ROOT / _CONFIG.get("logs_dir", "logs")
CHECKLIST_DIR = LOGS_DIR / "checklist"

# 선택적으로 덮어쓰기 가능한 추가 경로
EXTRA_SCAN_DIRS = {
    name: PROJECT_ROOT / path
    for name, path in (_CONFIG.get("scan_dirs") or {}).items()
}

# 로그 디렉토리 보장
CHECKLIST_DIR.mkdir(parents=True, exist_ok=True)


# ── Result Schemas ──

@dataclass
class CheckResult:
    """단일 점검 항목 결과."""
    case_id: str            # 일반화 케이스 ID (예: DISPLAY_HUMANIZE_001)
    title: str              # 점검 항목명
    severity: SEVERITY      # 심각도
    passed: bool            # 통과 여부
    detail: str = ""        # 상세 설명 (실패 시 어디서 문제인지)
    file_path: str = ""     # 관련 파일 경로
    line_number: int = 0    # 관련 라인 번호
    suggestion: str = ""    # 수정 제안


@dataclass
class CheckReport:
    """전체 체크리스트 실행 결과."""
    module: str
    timestamp: str = ""
    results: list[CheckResult] = field(default_factory=list)
    elapsed_ms: int = 0

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def critical_failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed and r.severity in ("CRITICAL", "HIGH")]

    def summary_line(self) -> str:
        icon = "\u2705" if self.failed == 0 else "\u274c"
        return f"{icon} [{self.module}] {self.passed}/{self.total} passed ({self.elapsed_ms}ms)"

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "timestamp": self.timestamp,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "elapsed_ms": self.elapsed_ms,
            "results": [
                {
                    "case_id": r.case_id,
                    "title": r.title,
                    "severity": r.severity,
                    "passed": r.passed,
                    "detail": r.detail,
                    "file_path": r.file_path,
                    "line_number": r.line_number,
                    "suggestion": r.suggestion,
                }
                for r in self.results
            ],
        }


# ── BaseChecklist ──

class BaseChecklist:
    """모듈별 체크리스트 베이스. 상속 후 check_* 메서드를 구현한다.

    run() 이 check_ 로 시작하는 모든 메서드를 자동 수집·실행한다.
    각 check_* 메서드는 CheckResult 또는 list[CheckResult] 를 반환해야 한다.
    예외 발생 시 HIGH severity CheckResult 로 자동 포착된다.
    """

    module_name: str = "base"

    def run(self) -> CheckReport:
        import datetime

        report = CheckReport(
            module=self.module_name,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        t0 = time.time()

        methods = sorted(
            m for m in dir(self) if m.startswith("check_") and callable(getattr(self, m))
        )
        for method_name in methods:
            try:
                results = getattr(self, method_name)()
                if isinstance(results, list):
                    report.results.extend(results)
                elif isinstance(results, CheckResult):
                    report.results.append(results)
            except Exception as exc:
                report.results.append(
                    CheckResult(
                        case_id=f"{self.module_name}_ERR",
                        title=f"{method_name} 실행 오류",
                        severity="HIGH",
                        passed=False,
                        detail=str(exc),
                    )
                )

        report.elapsed_ms = int((time.time() - t0) * 1000)
        return report

    # ── 유틸리티 ──

    @staticmethod
    def read_file(path: Path) -> str:
        """파일 읽기 (없으면 빈 문자열)."""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    @staticmethod
    def find_pattern_in_file(
        path: Path, pattern: str, flags: int = 0
    ) -> list[tuple[int, str]]:
        """파일에서 정규식 패턴 매칭. [(line_no, line_text), ...] 반환."""
        hits = []
        text = BaseChecklist.read_file(path)
        if not text:
            return hits
        regex = re.compile(pattern, flags)
        for i, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                hits.append((i, line.strip()))
        return hits

    # ── 바이패스 시스템 ──
    # 소스 코드에 `# chk:skip CASE_ID 사유` 주석을 달면 해당 라인을 점검에서 제외한다.
    #
    # 예:
    #   ticker_str = f"{ticker}.KS"  # chk:skip DISPLAY_HUMANIZE yfinance API 용
    #
    # 규칙:
    # - 사유(reason) 필수. 없으면 바이패스 무효 — 왜 건너뛰는지 모르면 위험하다.
    # - CASE_ID 는 prefix 매칭. 상위/하위 호환 (DISPLAY ⊇ DISPLAY_HUMANIZE_001).
    # - 바이패스 감사: `python -m checklist.runner --audit-bypass`

    _BYPASS_RE = re.compile(r'#\s*chk:skip\s+(\S+)\s+(.*)')

    @staticmethod
    def get_bypassed_lines(path: Path) -> dict[int, tuple[str, str]]:
        """파일에서 chk:skip 주석이 있는 라인을 수집.
        Returns: {line_no: (case_id, reason)}
        """
        bypassed = {}
        text = BaseChecklist.read_file(path)
        if not text:
            return bypassed
        for i, line in enumerate(text.splitlines(), 1):
            m = BaseChecklist._BYPASS_RE.search(line)
            if m:
                case_id = m.group(1)
                reason = m.group(2).strip()
                if reason:  # 사유 없으면 바이패스 무효
                    bypassed[i] = (case_id, reason)
        return bypassed

    @staticmethod
    def is_bypassed(path: Path, line_no: int, case_id: str) -> bool:
        """특정 라인이 특정 케이스에 대해 바이패스되었는지 확인."""
        bypassed = BaseChecklist.get_bypassed_lines(path)
        if line_no in bypassed:
            bp_case, _ = bypassed[line_no]
            return case_id.startswith(bp_case) or bp_case.startswith(case_id)
        return False

    @staticmethod
    def filter_bypassed(
        path: Path, hits: list[tuple[int, str]], case_id: str
    ) -> list[tuple[int, str]]:
        """hits 에서 바이패스된 라인을 제거."""
        bypassed = BaseChecklist.get_bypassed_lines(path)
        filtered = []
        for line_no, text in hits:
            if line_no in bypassed:
                bp_case, _ = bypassed[line_no]
                if case_id.startswith(bp_case) or bp_case.startswith(case_id):
                    continue
            filtered.append((line_no, text))
        return filtered

    @staticmethod
    def get_all_py_files(directory: Path, recursive: bool = True) -> list[Path]:
        """디렉토리 내 모든 .py 파일."""
        if not directory.exists():
            return []
        pattern = "**/*.py" if recursive else "*.py"
        return sorted(directory.glob(pattern))

    @staticmethod
    def get_files_matching(directory: Path, glob_pattern: str) -> list[Path]:
        """디렉토리 내 glob 패턴 매칭 파일."""
        if not directory.exists():
            return []
        return sorted(directory.glob(glob_pattern))

    @staticmethod
    def scan_dir(name: str) -> Path | None:
        """dvc_config.json 의 scan_dirs 에 정의된 추가 디렉토리 접근."""
        return EXTRA_SCAN_DIRS.get(name)
