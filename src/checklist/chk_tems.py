"""
DVC TEMS Self-Audit — TEMS 인프라 회귀 방지 체크리스트.

S49/S50/S51/S52 누적 결함을 일반화한 8개 case 의 결정론적 검증.
LLM 행동 교정용 TEMS TGL 과는 분리 — 본 모듈은 build-time / cron 결정론.

매핑:
  TEMS_DIRECT_RUN_IMPORT_001         → check_tems_direct_run_import
  TEMS_RESOLVE_CANONICAL_001         → check_tems_resolve_canonical
  TEMS_HOOK_REGISTRY_FILE_EXISTS_001 → check_tems_hook_registry_file_exists
  TEMS_DB_ORPHAN_RULE_HEALTH_001     → check_tems_db_orphan_rule_health
  TEMS_HOOK_EMPTY_STDIN_GRACEFUL_001 → check_tems_hook_empty_stdin_graceful
  TEMS_THS_DEAD_COLUMN_REGRESSION_001 → check_tems_ths_dead_column_regression
  TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001 → check_tems_audit_diag_recent_failure_health
  TEMS_DECAY_TTHS_SWEEP_ALIVE_001    → check_tems_decay_ths_sweep_alive

@dependencies
  reads: memory/*.py, .claude/settings.local.json, memory/error_logs.db,
         memory/tems_diagnostics.jsonl
  runs:  python memory/decay.py --dry-run --json (subprocess, no DB write)
"""
from __future__ import annotations

import ast
import io
import json
import re
import sqlite3
import subprocess
import sys
import tokenize
from datetime import datetime, timedelta
from pathlib import Path

from checklist.base import BaseChecklist, CheckResult, PROJECT_ROOT


MEMORY_DIR = PROJECT_ROOT / "memory"
SETTINGS_PATH = PROJECT_ROOT / ".claude" / "settings.local.json"
DB_PATH = MEMORY_DIR / "error_logs.db"
DIAG_PATH = MEMORY_DIR / "tems_diagnostics.jsonl"

# 7개 hook (S52 검증 시점 정착)
HOOK_FILES = [
    "preflight_hook.py",
    "tool_gate_hook.py",
    "handover_failure_gate.py",
    "tool_failure_hook.py",
    "compliance_tracker.py",
    "retrospective_hook.py",
    "self_cognition_gate.py",
]

# audit_diagnostics_recent.py 도 SessionStart hook 에 등록되지만 stdin 처리 X (no JSON 파싱)
# memory_bridge.py 도 PostToolUse hook 이지만 본 회귀 case 의 대상 아님

# 24h failure 임계 (S52 = 2건 정착, 5건 = 위상군 즉시 추적)
DIAG_FAILURE_THRESHOLD = 5


class TEMSChecklist(BaseChecklist):
    module_name = "tems"

    # ─────────────────────────────────────────────────────────
    # case 1: TEMS_DIRECT_RUN_IMPORT_001
    # ─────────────────────────────────────────────────────────
    def check_tems_direct_run_import(self) -> list[CheckResult]:
        """memory/*.py 직접 실행 호환 정적 분석.

        탐지: top-level 'from memory.X import Y' AND 'if __name__ == \"__main__\"'
              둘 다 가지면서 sys.path 보강 코드가 없으면 ModuleNotFoundError.
        """
        results: list[CheckResult] = []
        py_files = sorted(MEMORY_DIR.glob("*.py"))

        offenders = []
        for py in py_files:
            text = self.read_file(py)
            if not text:
                continue
            has_main = bool(re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', text))
            if not has_main:
                continue  # 직접 실행 의도 없음
            top_lines = self._top_level_lines(text)
            has_abs_import = any(
                re.match(r'\s*from\s+memory\.', line) or re.match(r'\s*import\s+memory\.', line)
                for line in top_lines
            )
            if not has_abs_import:
                continue
            # sys.path.insert(...) 또는 sys.path.append(...) 가 어떤 형태로든 .parent 또는
            # PROJECT_ROOT 와 같은 모듈에 함께 등장하면 보강된 것으로 인정.
            has_path_fix = bool(re.search(r'sys\.path\.(insert|append)', text)) and bool(
                re.search(r'\.resolve\(\)\.parent|MEMORY_DIR\.parent|PROJECT_ROOT|__file__', text)
            )
            # bypass support
            if self.is_bypassed(py, 1, "TEMS_DIRECT_RUN_IMPORT"):
                continue
            if not has_path_fix:
                offenders.append(py)

        if offenders:
            for py in offenders:
                results.append(CheckResult(
                    case_id="TEMS_DIRECT_RUN_IMPORT_001",
                    title=f"직접 실행 호환 누락: {py.name}",
                    severity="MEDIUM",
                    passed=False,
                    detail="top-level 절대 import + __main__ block 존재, sys.path 보강 누락 → 직접 실행 시 ModuleNotFoundError",
                    file_path=str(py),
                    suggestion='top-level 에 `import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` 추가, 또는 `# chk:skip TEMS_DIRECT_RUN_IMPORT 사유` bypass',
                ))
        else:
            results.append(CheckResult(
                case_id="TEMS_DIRECT_RUN_IMPORT_001",
                title="memory/*.py 직접 실행 호환",
                severity="MEDIUM",
                passed=True,
                detail=f"{len(py_files)}개 파일 점검, 직접 실행 호환 위반 0건",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 2: TEMS_RESOLVE_CANONICAL_001
    # ─────────────────────────────────────────────────────────
    def check_tems_resolve_canonical(self) -> list[CheckResult]:
        """memory/*.py 의 Path(__file__).parent 가 .resolve() 와 함께 사용되는지.

        S49 P0 정정 패턴. Path(__file__).resolve().parent 또는 .resolve() 호출이
        같은 표현식 chain 안에 있어야 한다. 단순 Path(__file__).parent (no resolve)
        는 cwd 의존 회귀 위험.
        """
        results: list[CheckResult] = []
        py_files = sorted(MEMORY_DIR.glob("*.py"))

        # 위반 패턴: Path(__file__).parent 직후 .resolve() 가 없는 경우
        # 정상: Path(__file__).resolve().parent  또는  .parent.resolve()
        offenders: list[tuple[Path, int, str]] = []
        for py in py_files:
            text = self.read_file(py)
            if not text:
                continue
            # tokenize 로 주석/docstring 영역 식별 — false positive 차단
            skip_lines = self._docstring_and_comment_lines(text)
            for i, line in enumerate(text.splitlines(), 1):
                if i in skip_lines:
                    continue
                code_part = line.split("#", 1)[0]
                if re.search(r'Path\(__file__\)\.parent', code_part) and not re.search(r'\.resolve\(\)', code_part):
                    if not self.is_bypassed(py, i, "TEMS_RESOLVE_CANONICAL"):
                        offenders.append((py, i, line.strip()[:100]))

        if offenders:
            for py, line_no, snippet in offenders:
                results.append(CheckResult(
                    case_id="TEMS_RESOLVE_CANONICAL_001",
                    title=f".resolve() 누락: {py.name}:L{line_no}",
                    severity="HIGH",
                    passed=False,
                    detail=f"L{line_no}: {snippet}",
                    file_path=str(py),
                    line_number=line_no,
                    suggestion="`Path(__file__).resolve().parent` 패턴 강제. cwd 의존 제거.",
                ))
        else:
            results.append(CheckResult(
                case_id="TEMS_RESOLVE_CANONICAL_001",
                title=".resolve() canonical 적용",
                severity="HIGH",
                passed=True,
                detail=f"{len(py_files)}개 파일 점검, Path(__file__).parent .resolve() 누락 0건",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 3: TEMS_HOOK_REGISTRY_FILE_EXISTS_001
    # ─────────────────────────────────────────────────────────
    def check_tems_hook_registry_file_exists(self) -> list[CheckResult]:
        """settings.local.json 의 hook command 가 가리키는 파일 실재 검증."""
        results: list[CheckResult] = []
        if not SETTINGS_PATH.exists():
            results.append(CheckResult(
                case_id="TEMS_HOOK_REGISTRY_FILE_EXISTS_001",
                title="settings.local.json 부재",
                severity="HIGH",
                passed=False,
                detail=f"{SETTINGS_PATH} 가 존재하지 않음",
                suggestion="settings.local.json 생성 또는 경로 확인",
            ))
            return results

        try:
            cfg = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            results.append(CheckResult(
                case_id="TEMS_HOOK_REGISTRY_FILE_EXISTS_001",
                title="settings.local.json 파싱 실패",
                severity="HIGH",
                passed=False,
                detail=str(e),
                file_path=str(SETTINGS_PATH),
                suggestion="JSON 문법 검증",
            ))
            return results

        hooks = cfg.get("hooks") or {}
        offenders: list[tuple[str, str, str]] = []  # (event, command, missing_path)
        py_path_re = re.compile(r'python\s+["\']?([A-Za-z]:[/\\][^"\'\s]+\.py)["\']?')

        registered_count = 0
        for event_name, entries in hooks.items():
            for entry in entries or []:
                for h in entry.get("hooks", []) or []:
                    cmd = h.get("command", "")
                    m = py_path_re.search(cmd)
                    if not m:
                        continue
                    registered_count += 1
                    target = Path(m.group(1))
                    if not target.exists():
                        offenders.append((event_name, cmd[:80], str(target)))

        if offenders:
            for event, cmd, miss in offenders:
                results.append(CheckResult(
                    case_id="TEMS_HOOK_REGISTRY_FILE_EXISTS_001",
                    title=f"hook 파일 부재: {Path(miss).name} ({event})",
                    severity="HIGH",
                    passed=False,
                    detail=f"command={cmd}... → 부재: {miss}",
                    file_path=str(SETTINGS_PATH),
                    suggestion="settings.local.json 의 command 경로 정정 또는 누락 파일 복원",
                ))
        else:
            results.append(CheckResult(
                case_id="TEMS_HOOK_REGISTRY_FILE_EXISTS_001",
                title="settings.local.json hook 파일 실재",
                severity="HIGH",
                passed=True,
                detail=f"{registered_count}개 hook command 검증, 모두 파일 실재",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 4: TEMS_DB_ORPHAN_RULE_HEALTH_001
    # ─────────────────────────────────────────────────────────
    def check_tems_db_orphan_rule_health(self) -> list[CheckResult]:
        """rule_health.rule_id 가 memory_logs.id 에 없는 orphan 검출."""
        results: list[CheckResult] = []
        if not DB_PATH.exists():
            results.append(CheckResult(
                case_id="TEMS_DB_ORPHAN_RULE_HEALTH_001",
                title="error_logs.db 부재",
                severity="MEDIUM",
                passed=False,
                detail=f"{DB_PATH} 부재 — TEMS 미초기화",
                suggestion="python memory/tems_commit.py --type TCL --rule '...' 로 첫 규칙 등록",
            ))
            return results

        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            orphans = c.execute(
                "SELECT rh.rule_id FROM rule_health rh "
                "LEFT JOIN memory_logs ml ON rh.rule_id=ml.id "
                "WHERE ml.id IS NULL"
            ).fetchall()
            conn.close()
        except sqlite3.DatabaseError as e:
            results.append(CheckResult(
                case_id="TEMS_DB_ORPHAN_RULE_HEALTH_001",
                title="error_logs.db 쿼리 실패",
                severity="HIGH",
                passed=False,
                detail=str(e),
                file_path=str(DB_PATH),
                suggestion="DB 무결성 검사 (sqlite3 .schema)",
            ))
            return results

        if orphans:
            ids = ", ".join(str(r[0]) for r in orphans)
            results.append(CheckResult(
                case_id="TEMS_DB_ORPHAN_RULE_HEALTH_001",
                title=f"orphan rule_health {len(orphans)}건",
                severity="MEDIUM",
                passed=False,
                detail=f"orphan rule_ids: {ids}",
                file_path=str(DB_PATH),
                suggestion=f"DELETE FROM rule_health WHERE rule_id IN ({ids})",
            ))
        else:
            results.append(CheckResult(
                case_id="TEMS_DB_ORPHAN_RULE_HEALTH_001",
                title="rule_health orphan 0건",
                severity="MEDIUM",
                passed=True,
                detail="rule_health.rule_id 모두 memory_logs.id 에 존재",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 5: TEMS_HOOK_EMPTY_STDIN_GRACEFUL_001
    # ─────────────────────────────────────────────────────────
    def check_tems_hook_empty_stdin_graceful(self) -> list[CheckResult]:
        """7개 hook 이 empty stdin 으로 호출되어도 traceback 누출 없이 graceful exit.

        TGL #100 적용 — 본 검증은 jsonl 에 noise 적재할 수 있다. self-trigger 회피를 위해
        검증 표식 환경변수 DVC_TEMS_AUDIT=1 설정 후 호출. 각 hook 은 이를 보고 jsonl 적재 skip
        해야 함 (현재 구현 X 라 본 case 는 advisory). 일단 stdout/stderr 누출 여부만 검증.
        """
        results: list[CheckResult] = []
        offenders: list[tuple[str, str]] = []  # (hook_name, traceback_line)

        for hook_name in HOOK_FILES:
            hook_path = MEMORY_DIR / hook_name
            if not hook_path.exists():
                offenders.append((hook_name, "FILE_NOT_FOUND"))
                continue
            try:
                proc = subprocess.run(
                    [sys.executable, str(hook_path)],
                    input="",
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding="utf-8",
                    errors="replace",
                    env={"DVC_TEMS_AUDIT": "1", **__import__("os").environ},
                )
                # Traceback 누출 = stderr 또는 stdout 에 'Traceback (most recent call last):'
                combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
                if "Traceback (most recent call last):" in combined:
                    # 위치 추출
                    first_tb_line = next(
                        (ln for ln in combined.splitlines() if "Traceback" in ln), ""
                    )
                    offenders.append((hook_name, first_tb_line[:80]))
            except subprocess.TimeoutExpired:
                offenders.append((hook_name, "TIMEOUT > 10s"))
            except Exception as e:
                offenders.append((hook_name, f"INVOKE_FAILED: {e}"))

        if offenders:
            for hook_name, reason in offenders:
                results.append(CheckResult(
                    case_id="TEMS_HOOK_EMPTY_STDIN_GRACEFUL_001",
                    title=f"empty stdin 누출: {hook_name}",
                    severity="MEDIUM",
                    passed=False,
                    detail=reason,
                    file_path=str(MEMORY_DIR / hook_name),
                    suggestion="hook main() 에 try: data=json.loads(sys.stdin.read() or '{}') except: data={} graceful 처리",
                ))
        else:
            results.append(CheckResult(
                case_id="TEMS_HOOK_EMPTY_STDIN_GRACEFUL_001",
                title="7개 hook empty stdin graceful",
                severity="MEDIUM",
                passed=True,
                detail=f"{len(HOOK_FILES)}개 hook 모두 traceback 누출 0건",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 6: TEMS_THS_DEAD_COLUMN_REGRESSION_001
    # ─────────────────────────────────────────────────────────
    def check_tems_ths_dead_column_regression(self) -> list[CheckResult]:
        """tems_engine.py 의 compute_ths 메서드가 dead column 을 input 으로 사용하지 않는지.

        Dead columns (S49 정정 대상): activation_count, correction_success/total, last_activated.
        Alive sources: fire_count, compliance_count, violation_count, last_fired.
        """
        results: list[CheckResult] = []
        engine = MEMORY_DIR / "tems_engine.py"
        if not engine.exists():
            results.append(CheckResult(
                case_id="TEMS_THS_DEAD_COLUMN_REGRESSION_001",
                title="tems_engine.py 부재",
                severity="HIGH",
                passed=False,
                detail=f"{engine} 부재",
            ))
            return results

        text = self.read_file(engine)
        # compute_ths 메서드 추출 (다음 def 까지)
        m = re.search(r'def compute_ths\(self.*?(?=\n    def |\nclass )', text, re.DOTALL)
        if not m:
            results.append(CheckResult(
                case_id="TEMS_THS_DEAD_COLUMN_REGRESSION_001",
                title="compute_ths 메서드 부재",
                severity="HIGH",
                passed=False,
                detail="tems_engine.py 에 compute_ths(self, ...) 메서드 미발견",
                file_path=str(engine),
                suggestion="HealthScorer.compute_ths 복원",
            ))
            return results

        body = m.group(0)
        # dead column 직접 dict 접근 (h.get("X") 또는 h["X"])
        dead_col_re = re.compile(
            r'h\.get\(\s*["\'](?P<col>activation_count|correction_success|correction_total|last_activated)["\']'
        )
        violations = []
        for line_no, line in enumerate(body.splitlines(), 1):
            mm = dead_col_re.search(line)
            if mm:
                violations.append((line_no, line.strip()[:100], mm.group("col")))

        # 단, last_activated 는 fallback chain 에서만 허용 (h.get("last_fired") or h.get("last_activated"))
        # 이 경우는 violation 아님 → 같은 라인에 last_fired 도 함께 있으면 OK
        filtered = []
        for line_no, snippet, col in violations:
            if col == "last_activated" and "last_fired" in snippet:
                continue  # legitimate fallback
            filtered.append((line_no, snippet, col))

        if filtered:
            for line_no, snippet, col in filtered:
                results.append(CheckResult(
                    case_id="TEMS_THS_DEAD_COLUMN_REGRESSION_001",
                    title=f"dead column 사용: {col}",
                    severity="HIGH",
                    passed=False,
                    detail=f"compute_ths 내 L{line_no}: {snippet}",
                    file_path=str(engine),
                    suggestion={
                        "activation_count": "fire_count 사용",
                        "correction_success": "compliance_count 사용",
                        "correction_total": "compliance_count + violation_count 사용",
                        "last_activated": "last_fired or last_activated fallback chain 사용",
                    }.get(col, "alive source 로 swap"),
                ))
        else:
            results.append(CheckResult(
                case_id="TEMS_THS_DEAD_COLUMN_REGRESSION_001",
                title="compute_ths dead column 회귀 없음",
                severity="HIGH",
                passed=True,
                detail="fire_count / compliance / violation / last_fired 사용 정착",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 7: TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001
    # ─────────────────────────────────────────────────────────
    def check_tems_audit_diag_recent_failure_health(self) -> list[CheckResult]:
        """tems_diagnostics.jsonl 의 24h *_failure 누적 임계 검증."""
        results: list[CheckResult] = []
        if not DIAG_PATH.exists():
            results.append(CheckResult(
                case_id="TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001",
                title="tems_diagnostics.jsonl 부재",
                severity="LOW",
                passed=True,
                detail=f"{DIAG_PATH} 부재 — 정상 (failure 0건)",
            ))
            return results

        cutoff = datetime.now() - timedelta(hours=24)
        failures = []
        try:
            with DIAG_PATH.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    event = obj.get("event", "")
                    if not event.endswith("_failure"):
                        continue
                    ts_str = obj.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except ValueError:
                        continue
                    if ts >= cutoff:
                        failures.append((ts.isoformat(), event, obj.get("exc_type", "")))
        except Exception as e:
            results.append(CheckResult(
                case_id="TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001",
                title="jsonl 읽기 실패",
                severity="MEDIUM",
                passed=False,
                detail=str(e),
                file_path=str(DIAG_PATH),
            ))
            return results

        count = len(failures)
        if count >= DIAG_FAILURE_THRESHOLD:
            sample = ", ".join(f"{ts[:19]} {ev}" for ts, ev, _ in failures[:5])
            results.append(CheckResult(
                case_id="TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001",
                title=f"24h failure 임계 초과: {count}건",
                severity="MEDIUM",
                passed=False,
                detail=f"임계 {DIAG_FAILURE_THRESHOLD}건 이상. 샘플: {sample}",
                file_path=str(DIAG_PATH),
                suggestion=f"python memory/audit_diagnostics_recent.py --hours 24 로 root cause 추적, fix 후 본 case 재실행",
            ))
        else:
            results.append(CheckResult(
                case_id="TEMS_AUDIT_DIAG_RECENT_FAILURE_HEALTH_001",
                title=f"24h failure {count}건 (임계 {DIAG_FAILURE_THRESHOLD} 이하)",
                severity="MEDIUM",
                passed=True,
                detail=f"24h 내 *_failure 이벤트 {count}건 — 정상 범위",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 8: TEMS_DECAY_TTHS_SWEEP_ALIVE_001
    # ─────────────────────────────────────────────────────────
    def check_tems_decay_ths_sweep_alive(self) -> list[CheckResult]:
        """python memory/decay.py --json 실행 시 ths_recomputed == total_rules ∧ ths_errors == 0.

        TGL #100 회피 — --dry-run 사용 시 ths_recomputed=0 (의도). non-dry-run 호출은
        DB 갱신 발생하므로 본 case 는 dry-run 으로 module-load + transitions 계산만 검증.
        실제 sweep alive 는 별도 cron (1일 1회) 에서 검증 권장.
        """
        results: list[CheckResult] = []
        decay = MEMORY_DIR / "decay.py"
        if not decay.exists():
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay.py 부재",
                severity="HIGH",
                passed=False,
                detail=f"{decay} 부재",
            ))
            return results

        try:
            proc = subprocess.run(
                [sys.executable, str(decay), "--dry-run", "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
                cwd=str(PROJECT_ROOT),
            )
        except subprocess.TimeoutExpired:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay.py timeout > 30s",
                severity="HIGH",
                passed=False,
                detail="decay --dry-run 이 30초 안에 끝나지 않음",
                file_path=str(decay),
            ))
            return results
        except Exception as e:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay.py 호출 실패",
                severity="HIGH",
                passed=False,
                detail=str(e),
                file_path=str(decay),
            ))
            return results

        if proc.returncode != 0:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay.py 비정상 종료",
                severity="HIGH",
                passed=False,
                detail=f"returncode={proc.returncode} stderr={proc.stderr[:200]}",
                file_path=str(decay),
                suggestion="python memory/decay.py --dry-run 직접 실행해 traceback 확인",
            ))
            return results

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay.py JSON 파싱 실패",
                severity="HIGH",
                passed=False,
                detail=f"stdout 첫 200자: {proc.stdout[:200]}",
                file_path=str(decay),
            ))
            return results

        # dry-run 에서는 ths_recomputed = 0 정상 (DB write skip).
        # 본 case 는 module load + total_rules > 0 + ok=True 만 검증.
        ok = data.get("ok", False)
        total = data.get("total_rules", 0)

        if not ok:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay 실행 ok=False",
                severity="HIGH",
                passed=False,
                detail=f"data={data}",
                file_path=str(decay),
            ))
        elif total == 0:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title="decay total_rules=0",
                severity="MEDIUM",
                passed=False,
                detail="rule_health 에 1건도 없음. TEMS 가 비어있는 상태",
                file_path=str(decay),
                suggestion="python memory/tems_commit.py 로 첫 규칙 등록",
            ))
        else:
            results.append(CheckResult(
                case_id="TEMS_DECAY_TTHS_SWEEP_ALIVE_001",
                title=f"decay sweep alive (dry-run, {total} rules)",
                severity="HIGH",
                passed=True,
                detail=f"ok=True / total_rules={total} / transitions={data.get('transitions', 0)}",
            ))
        return results

    # ─────────────────────────────────────────────────────────
    # case 9: TEMS_PATH_ORPHAN_001
    # ─────────────────────────────────────────────────────────
    def check_tems_path_orphan(self) -> list[CheckResult]:
        """TEMS A→B 마이그레이션 잔존 caller 검출.

        A: E:/AgentInterface/tems_core (legacy raw 사본)
        B: E:/bobpullie/TEMS (packaged 'tems' v0.3+, GitHub canonical)

        검출 대상:
          1. legacy tems_core 경로 직접 참조 (`E:[/\\\\]AgentInterface[/\\\\]tems_core`)
          2. AutoMemory cross-project 절대경로
             (`C:[/\\\\]Users[/\\\\]<user>[/\\\\].claude[/\\\\]projects[/\\\\]*AgentInterface*`)

        scope: memory/*.py + memory/README.md + .claude/(skills|agents|agent-templates)/*.md
               + .claude/settings.local.json (hook command 라인)

        제외: _backup_*, __pycache__, docs/session_archive, handover_doc, qmd_drive,
              docs/wiki/postmortems (역사 기록물 — 의도적 ref). 본 chk_tems.py 자기 자신도 제외 (regex 리터럴).

        bypass: `# chk:skip TEMS_PATH_ORPHAN 사유` 또는 `<!-- chk:skip TEMS_PATH_ORPHAN 사유 -->`
        """
        results: list[CheckResult] = []

        legacy_patterns: list[tuple[re.Pattern, str, str]] = [
            (
                re.compile(r"E:[/\\]AgentInterface[/\\]tems_core", re.IGNORECASE),
                "tems_core_engine_path",
                "'tems' 패키지로 교체 (pip install git+https://github.com/bobpullie/TEMS.git → import tems / tems CLI)",
            ),
            (
                re.compile(r"E:[/\\]AgentInterface[/\\]memory[/\\]", re.IGNORECASE),
                "agentinterface_memory_dead_path",
                "E:/AgentInterface/memory/ 경로는 실재하지 않음. 각 에이전트 자체 memory/error_logs.db 참조 (TEMS_DB_PATH env 또는 marker walk)",
            ),
            (
                re.compile(
                    r"C:[/\\]Users[/\\][^/\\]+[/\\]\.claude[/\\]projects[/\\][^/\\]*AgentInterface",
                    re.IGNORECASE,
                ),
                "automemory_cross_project_abs",
                "TEMS_MEMORY_DIR env var + marker walk 사용 (canonical templates/memory_bridge.py 의 _resolve_memory_dir 패턴)",
            ),
        ]

        excluded_substrings = (
            "_backup",
            "__pycache__",
            "session_archive",
            "handover_doc",
            "qmd_drive",
            "postmortems",
            "tems_diagnostics.jsonl",
            "Claude-Sessions",
        )

        scan_targets: list[Path] = []
        scan_targets.extend(sorted((PROJECT_ROOT / "memory").glob("*.py")))
        readme = PROJECT_ROOT / "memory" / "README.md"
        if readme.exists():
            scan_targets.append(readme)
        for sub in ("skills", "agents", "agent-templates"):
            d = PROJECT_ROOT / ".claude" / sub
            if d.exists():
                scan_targets.extend(sorted(d.glob("*.md")))

        # 자기 자신 (chk_tems.py) 은 regex 리터럴 매칭 회피 위해 명시적 제외
        self_path = Path(__file__).resolve()

        offenders: list[tuple[Path, int, str, str, str]] = []
        for target in scan_targets:
            target_str = str(target.resolve()).replace("\\", "/")
            if target.resolve() == self_path:
                continue
            if any(ex in target_str for ex in excluded_substrings):
                continue
            text = self.read_file(target)
            if not text:
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                for pattern, kind, suggestion in legacy_patterns:
                    if pattern.search(line):
                        if self.is_bypassed(target, line_no, "TEMS_PATH_ORPHAN"):
                            continue
                        offenders.append(
                            (target, line_no, line.strip()[:120], kind, suggestion)
                        )
                        break  # 한 라인에 두 패턴 동시 매칭은 첫 패턴만 보고

        # settings.local.json — hook command 가 legacy 경로 (tems_core / AgentInterface/memory) 가리키면 violation.
        # tems_registry.json env 와 tems_templates 는 합법 — 분리 매칭.
        settings = PROJECT_ROOT / ".claude" / "settings.local.json"
        if settings.exists():
            text = self.read_file(settings)
            for line_no, line in enumerate(text.splitlines(), 1):
                if re.search(r"AgentInterface[/\\]tems_core", line, re.IGNORECASE):
                    offenders.append(
                        (
                            settings,
                            line_no,
                            line.strip()[:120],
                            "settings_hook_legacy_tems_core",
                            "'tems' CLI (TEMS_REGISTRY_PATH env) 또는 패키지 import 로 교체",
                        )
                    )
                elif re.search(r"AgentInterface[/\\]memory[/\\]", line, re.IGNORECASE):
                    offenders.append(
                        (
                            settings,
                            line_no,
                            line.strip()[:120],
                            "settings_hook_dead_memory_path",
                            "각 에이전트 자체 memory/ 디렉토리 참조 (E:/AgentInterface/memory/ 실재하지 않음)",
                        )
                    )

        if offenders:
            for path, ln, snippet, kind, sug in offenders:
                results.append(
                    CheckResult(
                        case_id="TEMS_PATH_ORPHAN_001",
                        title=f"legacy path orphan: {path.name}:L{ln} ({kind})",
                        severity="HIGH",
                        passed=False,
                        detail=f"L{ln}: {snippet}",
                        file_path=str(path),
                        line_number=ln,
                        suggestion=sug,
                    )
                )
        else:
            results.append(
                CheckResult(
                    case_id="TEMS_PATH_ORPHAN_001",
                    title="TEMS A→B 마이그레이션 caller 잔존 0건",
                    severity="HIGH",
                    passed=True,
                    detail=f"{len(scan_targets)}개 파일 점검, legacy tems_core / AutoMemory cross-link 참조 0건",
                )
            )
        return results

    # ─────────────────────────────────────────────────────────
    # 헬퍼
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _docstring_and_comment_lines(text: str) -> set[int]:
        """tokenize 로 docstring(STRING constants at module/class/function level)과
        주석 라인 번호 집합 반환. ast 로 docstring 위치를 정확 추출한 뒤 그 구간을 포함.
        """
        skip: set[int] = set()
        # 1) AST 로 docstring 노드 찾기
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return skip
        DOCSTRING_HOLDERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        for node in ast.walk(tree):
            if not isinstance(node, DOCSTRING_HOLDERS):
                continue
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                start = first.lineno
                end = getattr(first, "end_lineno", start)
                for ln in range(start, end + 1):
                    skip.add(ln)
        # 2) tokenize 로 주석-only 라인
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type == tokenize.COMMENT:
                    # 라인 자체에 코드가 있으면 검출 대상이지만, 위 split('#') 로 처리하므로 skip 안 함
                    pass
        except tokenize.TokenizeError:
            pass
        return skip

    @staticmethod
    def _top_level_lines(text: str) -> list[str]:
        """모듈의 top-level (function/class body 밖) 라인만 추출.

        간이 검출: 들여쓰기 0 인 라인 + multi-line string 제외.
        """
        lines = text.splitlines()
        result = []
        in_triple = False
        triple_quote = None
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # triple-quoted string 회피
            for q in ('"""', "'''"):
                if q in line:
                    if not in_triple:
                        in_triple = True
                        triple_quote = q
                    elif triple_quote == q:
                        in_triple = False
                        triple_quote = None
            if in_triple:
                continue
            # top-level (no indent)
            if line[:1] in (" ", "\t"):
                continue
            result.append(line)
        return result
