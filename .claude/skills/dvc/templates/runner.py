"""
DVC 체크리스트 통합 실행기.

사용법:
  # 전체 점검
  python -m checklist.runner

  # 특정 모듈만 (chk_{module}.py)
  python -m checklist.runner --module display,config

  # JSON 출력
  python -m checklist.runner --json

  # 바이패스 주석 감사
  python -m checklist.runner --audit-bypass

  # 케이스 생명주기 분석
  python -m checklist.runner --audit-cases

자동 discovery:
  - checklist/chk_*.py 파일을 스캔
  - 각 파일에서 BaseChecklist 서브클래스를 import
  - module_name 속성으로 CLI 모듈명 등록

@dependencies
  reads: checklist/chk_*.py, checklist/cases.json
"""
from __future__ import annotations

import argparse
import datetime
import importlib
import inspect
import json
import sys
from pathlib import Path

from checklist.base import (
    BaseChecklist,
    CheckReport,
    CHECKLIST_DIR,
    PROJECT_ROOT,
)


# ── 자동 Discovery ──

def discover_checklists() -> dict[str, type]:
    """checklist/ 디렉토리에서 chk_*.py 를 스캔하여 BaseChecklist 서브클래스를 수집."""
    registry: dict[str, type] = {}
    checklist_dir = Path(__file__).parent

    for py_file in sorted(checklist_dir.glob("chk_*.py")):
        module_name = f"checklist.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"  ⚠️ {module_name} import 실패: {e}", file=sys.stderr)
            continue

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                obj is not BaseChecklist
                and issubclass(obj, BaseChecklist)
                and obj.__module__ == module_name
            ):
                key = getattr(obj, "module_name", name)
                registry[key] = obj

    return registry


def run_checklists(modules: list[str] | None = None) -> list[CheckReport]:
    """체크리스트 실행."""
    registry = discover_checklists()

    if modules:
        selected = {m: registry[m] for m in modules if m in registry}
        missing = [m for m in modules if m not in registry]
        if missing:
            print(f"  ⚠️ 등록되지 않은 모듈: {missing}", file=sys.stderr)
            print(f"  사용 가능: {sorted(registry.keys())}", file=sys.stderr)
    else:
        selected = registry

    reports = []
    for name, cls in selected.items():
        checker = cls()
        report = checker.run()
        reports.append(report)

    return reports


# ── 출력 포맷 ──

def format_console_report(reports: list[CheckReport]) -> str:
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  DVC 체크리스트 점검 결과")
    lines.append(f"  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    total_pass = 0
    total_fail = 0

    for report in reports:
        lines.append("")
        lines.append(report.summary_line())
        total_pass += report.passed
        total_fail += report.failed

        for r in report.results:
            if r.passed:
                icon = "\u2705"
            elif r.severity in ("CRITICAL", "HIGH"):
                icon = "\U0001f534"
            else:
                icon = "\U0001f7e1"

            lines.append(f"  {icon} [{r.case_id}] {r.title}")
            if not r.passed and r.detail:
                lines.append(f"      {r.detail}")
            if r.suggestion:
                lines.append(f"      \u27a1 {r.suggestion}")

    lines.append("")
    lines.append("-" * 60)
    total = total_pass + total_fail
    if total_fail == 0:
        lines.append(f"\u2705 전체: {total_pass}/{total} 통과 — 모든 점검 정상")
    else:
        lines.append(f"\u274c 전체: {total_pass}/{total} 통과, {total_fail}건 실패")

        critical = []
        for report in reports:
            critical.extend(report.critical_failures)
        if critical:
            lines.append("")
            lines.append("\U0001f6a8 긴급 조치 필요:")
            for r in critical:
                lines.append(f"  \U0001f534 [{r.case_id}] {r.title}")
                if r.suggestion:
                    lines.append(f"      \u27a1 {r.suggestion}")

    lines.append("=" * 60)
    return "\n".join(lines)


def save_report(reports: list[CheckReport]) -> Path:
    """체크리스트 결과를 logs/checklist/ 에 저장."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = CHECKLIST_DIR / f"checklist_{today}.json"

    data = {
        "date": today,
        "timestamp": datetime.datetime.now().isoformat(),
        "reports": [r.to_dict() for r in reports],
        "summary": {
            "total": sum(r.total for r in reports),
            "passed": sum(r.passed for r in reports),
            "failed": sum(r.failed for r in reports),
        },
    }

    report_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


# ── 바이패스 감사 ──

def audit_bypasses() -> str:
    """전체 소스에서 chk:skip 바이패스 주석을 수집하여 보고."""
    from checklist.base import BaseChecklist, SRC_DIR

    lines = []
    lines.append("\n📋 chk:skip 바이패스 감사 보고")
    lines.append("=" * 50)

    total = 0
    py_files = sorted(SRC_DIR.glob("**/*.py")) if SRC_DIR.exists() else []

    for py_file in py_files:
        bypassed = BaseChecklist.get_bypassed_lines(py_file)
        if not bypassed:
            continue
        try:
            rel = py_file.relative_to(SRC_DIR)
        except ValueError:
            rel = py_file
        for line_no, (case_id, reason) in sorted(bypassed.items()):
            lines.append(f"  {rel}:L{line_no} — [{case_id}] {reason}")
            total += 1

    lines.append("-" * 50)
    lines.append(f"총 {total}건 바이패스")
    if total > 20:
        lines.append("⚠️ 바이패스 20건 초과 — 케이스 통합 검토 필요")
    return "\n".join(lines)


# ── 케이스 생명주기 감사 ──

CASE_THRESHOLDS = {
    "consolidate_per_category": 10,   # 같은 카테고리 10개 초과 시 통합 검토
    "consolidate_total": 50,          # 전체 50개 초과 시 통합 검토
    "archive_inactive_days": 30,      # 30일간 새 탐지 없으면 폐기 후보
}


def audit_cases() -> str:
    """cases.json 의 케이스 생명주기를 분석하여 통합/폐기 제안."""
    cases_path = Path(__file__).parent / "cases.json"
    if not cases_path.exists():
        return "cases.json 없음"

    data = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])

    lines = []
    lines.append("\n📊 케이스 생명주기 분석")
    lines.append("=" * 50)
    lines.append(f"총 케이스: {len(cases)}개")

    by_category: dict[str, list] = {}
    for c in cases:
        cat = c.get("category", "unknown")
        by_category.setdefault(cat, []).append(c)

    lines.append(f"카테고리: {len(by_category)}개")
    for cat, items in sorted(by_category.items()):
        icon = "⚠️" if len(items) > CASE_THRESHOLDS["consolidate_per_category"] else "✅"
        lines.append(f"  {icon} {cat}: {len(items)}개")

    suggestions = []
    if len(cases) > CASE_THRESHOLDS["consolidate_total"]:
        suggestions.append(
            f"🔄 전체 {len(cases)}개 > {CASE_THRESHOLDS['consolidate_total']}개 임계 "
            "— 유사 케이스 통합 검토 필요"
        )
    for cat, items in by_category.items():
        if len(items) > CASE_THRESHOLDS["consolidate_per_category"]:
            suggestions.append(
                f"🔄 [{cat}] {len(items)}개 > {CASE_THRESHOLDS['consolidate_per_category']}개 "
                "— 카테고리 내 통합 검토"
            )

    auto_count = sum(1 for c in cases if c.get("auto_discover"))
    if cases:
        lines.append(f"자동탐지(auto_discover): {auto_count}/{len(cases)} "
                     f"({auto_count/len(cases)*100:.0f}%)")

    if suggestions:
        lines.append("")
        lines.append("📌 통합 제안:")
        for s in suggestions:
            lines.append(f"  {s}")
    else:
        lines.append("\n✅ 케이스 수 적정 — 통합 불필요")

    lines.append("=" * 50)
    return "\n".join(lines)


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="DVC (Deterministic Verification Checklist)")
    parser.add_argument("--module", "-m", help="점검할 모듈 (쉼표 구분)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    parser.add_argument("--save", action="store_true", default=True, help="결과 저장")
    parser.add_argument("--audit-bypass", action="store_true", help="바이패스 주석 감사")
    parser.add_argument("--audit-cases", action="store_true", help="케이스 생명주기 분석")
    parser.add_argument("--list", action="store_true", help="등록된 체크리스트 모듈 목록")

    args = parser.parse_args()

    if args.list:
        registry = discover_checklists()
        print("등록된 체크리스트 모듈:")
        for name, cls in sorted(registry.items()):
            print(f"  {name}  ({cls.__module__}.{cls.__name__})")
        return

    if args.audit_bypass:
        print(audit_bypasses())
        return

    if args.audit_cases:
        print(audit_cases())
        return

    modules = args.module.split(",") if args.module else None
    reports = run_checklists(modules=modules)

    if args.json:
        print(json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2))
    else:
        print(format_console_report(reports))

    if args.save and reports:
        path = save_report(reports)
        print(f"\n\U0001f4be 결과 저장: {path}")


if __name__ == "__main__":
    main()
