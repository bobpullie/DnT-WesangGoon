"""TEMS Rule Viewer — NiceGUI + AG Grid 데스크탑 앱.

기능:
  - 모든 규칙 테이블 뷰 (TCL/TGL, status, fire/violation count)
  - 행 더블클릭 → 본문 + 코멘트 편집 모달
  - severity (info / warn / disable) — disable 은 preflight 주입에서 제외
  - soft delete (status='archive')  /  hard delete (memory_logs DELETE + .md)
  - 자동 새로고침 (5초 토글)

실행:
  python viewer/rule_viewer.py            # 네이티브 윈도우 (pywebview)
  python viewer/rule_viewer.py --browser  # 브라우저 모드 (디버그용, http://localhost:8765)

격리:
  - TEMS core 는 이 파일을 import 안 함
  - DB 의 rule_user_annotations 테이블 + user_annotations.jsonl 만 쓴다
  - 미설치 시 preflight_hook 는 빈 테이블/빈 LEFT JOIN 으로 정상 동작
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from nicegui import ui

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "memory" / "error_logs.db"
JSONL_BACKUP = ROOT / "memory" / "user_annotations.jsonl"
QMD_RULES_DIR = ROOT / "memory" / "qmd_rules"


# ─── DB Layer ─────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"TEMS DB not found: {DB_PATH}")
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def _ensure_annot_table() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS rule_user_annotations (
        rule_id      INTEGER PRIMARY KEY,
        comment      TEXT    NOT NULL DEFAULT '',
        severity     TEXT    NOT NULL DEFAULT 'info'
                     CHECK(severity IN ('info', 'warn', 'disable')),
        author       TEXT    NOT NULL DEFAULT 'jongil',
        updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (rule_id) REFERENCES memory_logs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_rule_annotations_severity
        ON rule_user_annotations(severity);
    """
    con = _connect()
    try:
        con.executescript(sql)
        con.commit()
    finally:
        con.close()


def load_rules() -> list[dict]:
    con = _connect()
    try:
        rows = con.execute(
            """
            SELECT
                m.id            AS id,
                m.category      AS category,
                m.context_tags  AS tags,
                m.correction_rule AS rule,
                m.summary       AS summary,
                m.keyword_trigger AS triggers,
                m.severity      AS rule_severity,
                m.created_at    AS created_at,
                COALESCE(rh.status, 'warm')           AS status,
                COALESCE(rh.fire_count, 0)            AS fire,
                COALESCE(rh.violation_count, 0)       AS viol,
                COALESCE(rh.compliance_count, 0)      AS comp,
                COALESCE(rh.ths_score, 0.5)           AS ths,
                COALESCE(ua.comment, '')              AS user_comment,
                COALESCE(ua.severity, 'info')         AS user_severity,
                ua.updated_at                         AS comment_updated_at
            FROM memory_logs m
            LEFT JOIN rule_health rh           ON rh.rule_id = m.id
            LEFT JOIN rule_user_annotations ua ON ua.rule_id = m.id
            ORDER BY m.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        con.close()


def upsert_annotation(rule_id: int, comment: str, severity: str) -> None:
    if severity not in {"info", "warn", "disable"}:
        raise ValueError(f"invalid severity: {severity}")
    now = datetime.now().isoformat()
    con = _connect()
    try:
        con.execute(
            """
            INSERT INTO rule_user_annotations (rule_id, comment, severity, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                comment = excluded.comment,
                severity = excluded.severity,
                updated_at = excluded.updated_at
            """,
            (rule_id, comment, severity, now),
        )
        con.commit()
    finally:
        con.close()
    _backup_jsonl({
        "action": "upsert", "rule_id": rule_id,
        "comment": comment, "severity": severity, "updated_at": now,
    })


def delete_annotation(rule_id: int) -> None:
    now = datetime.now().isoformat()
    con = _connect()
    try:
        con.execute("DELETE FROM rule_user_annotations WHERE rule_id = ?", (rule_id,))
        con.commit()
    finally:
        con.close()
    _backup_jsonl({"action": "delete_annotation", "rule_id": rule_id, "updated_at": now})


def archive_rule(rule_id: int) -> None:
    now = datetime.now().isoformat()
    con = _connect()
    try:
        con.execute(
            """
            INSERT INTO rule_health (rule_id, status, status_changed_at, ths_score, created_at)
            VALUES (?, 'archive', ?, 0.0, ?)
            ON CONFLICT(rule_id) DO UPDATE SET
                status = 'archive',
                status_changed_at = excluded.status_changed_at
            """,
            (rule_id, now, now),
        )
        con.commit()
    finally:
        con.close()
    _backup_jsonl({"action": "archive", "rule_id": rule_id, "updated_at": now})


def hard_delete_rule(rule_id: int) -> None:
    now = datetime.now().isoformat()
    con = _connect()
    try:
        con.execute("DELETE FROM memory_fts WHERE rowid = ?", (rule_id,))
        con.execute("DELETE FROM memory_logs WHERE id = ?", (rule_id,))
        con.execute("DELETE FROM rule_health WHERE rule_id = ?", (rule_id,))
        con.execute("DELETE FROM rule_user_annotations WHERE rule_id = ?", (rule_id,))
        con.commit()
    finally:
        con.close()
    md_file = QMD_RULES_DIR / f"rule_{rule_id:04d}.md"
    if md_file.exists():
        md_file.unlink()
    _backup_jsonl({"action": "hard_delete", "rule_id": rule_id, "updated_at": now})


def _backup_jsonl(record: dict) -> None:
    JSONL_BACKUP.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_BACKUP.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ─── UI Layer ─────────────────────────────────────────────────────────

def _build_grid_rows(rules: list[dict]) -> list[dict]:
    out = []
    for r in rules:
        sev_emoji = {"info": "💬", "warn": "⚠️", "disable": "🚫"}.get(r["user_severity"], "")
        comment_preview = r["user_comment"][:50] + ("…" if len(r["user_comment"]) > 50 else "")
        out.append({
            "id": r["id"],
            "category": r["category"] or "",
            "status": r["status"],
            "fire": r["fire"],
            "vc": f"{r['viol']}/{r['comp']}",
            "ths": f"{r['ths']:.2f}",
            "rule_preview": (r["rule"] or r["summary"] or "")[:120],
            "comment": (f"{sev_emoji} {comment_preview}").strip() if (sev_emoji or comment_preview) else "",
        })
    return out


@ui.page("/")
def index_page() -> None:
    try:
        initial_rules = load_rules()
    except Exception as exc:
        print(f"[ERR] initial load_rules failed: {exc}", flush=True)
        initial_rules = []
    initial_grid_rows = _build_grid_rows(initial_rules)
    state = {"filter": "all", "search": "", "rules": initial_rules}

    def apply_filter() -> None:
        rows = state["rules"]
        f = state["filter"]
        if f == "tcl":
            rows = [r for r in rows if r["category"] == "TCL"]
        elif f == "tgl":
            rows = [r for r in rows if r["category"] == "TGL"]
        elif f == "hot":
            rows = [r for r in rows if r["status"] == "hot"]
        elif f == "warm":
            rows = [r for r in rows if r["status"] == "warm"]
        elif f == "cold":
            rows = [r for r in rows if r["status"] == "cold"]
        elif f == "archive":
            rows = [r for r in rows if r["status"] == "archive"]
        elif f == "commented":
            rows = [r for r in rows if r["user_comment"] or r["user_severity"] == "disable"]
        elif f == "disabled":
            rows = [r for r in rows if r["user_severity"] == "disable"]

        q = state["search"].strip().lower()
        if q:
            rows = [
                r for r in rows
                if q in str(r.get("rule", "")).lower()
                or q in str(r.get("tags", "")).lower()
                or q in str(r.get("triggers", "")).lower()
                or q in str(r.get("user_comment", "")).lower()
            ]

        grid_rows = _build_grid_rows(rows)
        grid.rows = grid_rows
        grid.update()
        count_label.text = f"{len(grid_rows)} rules"
        count_label.update()
        print(f"[DEBUG] grid populated: {len(grid_rows)} rows pushed to ui.table.rows", flush=True)

    def refresh_data() -> None:
        try:
            state["rules"] = load_rules()
            print(f"[DEBUG] refresh_data: loaded {len(state['rules'])} rules from DB", flush=True)
        except Exception as exc:
            import traceback
            print(f"[DEBUG] refresh_data EXC: {exc}\n{traceback.format_exc()}", flush=True)
            ui.notify(f"DB load error: {exc}", type="negative")
            state["rules"] = []
        apply_filter()
        print(f"[DEBUG] apply_filter done: filter={state['filter']!r} grid_rows displayed", flush=True)

    def open_edit_dialog(rule: dict) -> None:
        with ui.dialog() as dialog, ui.card().style("min-width: 720px; max-width: 90vw;"):
            ui.label(f"Rule #{rule['id']} — [{rule['category']}] status: {rule['status']}").classes("text-h6")
            ui.label(f"tags: {rule['tags']}").classes("text-caption text-grey-7")
            with ui.row().classes("w-full gap-4 text-caption"):
                ui.label(f"fire: {rule['fire']}")
                ui.label(f"viol: {rule['viol']}")
                ui.label(f"comp: {rule['comp']}")
                ui.label(f"ths: {rule['ths']:.2f}")

            ui.separator()
            ui.label("Rule").classes("text-subtitle2")
            ui.label(rule["rule"] or "(empty)").classes("text-body2").style(
                "white-space: pre-wrap; padding: 8px; background: #f5f5f5; border-radius: 4px;"
            )

            if rule["triggers"]:
                ui.label("Keywords").classes("text-subtitle2 q-mt-md")
                ui.label(rule["triggers"]).classes("text-caption text-grey-8")

            ui.separator()
            ui.label("종일군 코멘트").classes("text-subtitle2 q-mt-sm")
            comment_input = ui.textarea(
                value=rule["user_comment"],
                placeholder="이 규칙에 대한 코멘트... (저장 시 향후 preflight 에서 에이전트에게 함께 주입됨)",
            ).props("autogrow outlined").classes("w-full")

            severity_radio = ui.radio(
                ["info", "warn", "disable"],
                value=rule["user_severity"],
            ).props("inline")
            ui.label(
                "info=힌트로 부드럽게 / warn=강조 / disable=preflight 주입에서 완전히 제외 (소프트 비활성화)"
            ).classes("text-caption text-grey-6")

            ui.separator()

            def do_save():
                upsert_annotation(rule["id"], comment_input.value, severity_radio.value)
                ui.notify(f"#{rule['id']} 코멘트 저장됨", type="positive")
                dialog.close()
                refresh_data()

            def do_clear():
                delete_annotation(rule["id"])
                ui.notify(f"#{rule['id']} 코멘트 삭제됨", type="info")
                dialog.close()
                refresh_data()

            def do_archive():
                with ui.dialog() as cd, ui.card():
                    ui.label(f"#{rule['id']} 을 archive 처리하시겠습니까?").classes("text-h6")
                    ui.label("status='archive' 로 마킹됩니다 (preflight 자동 제외, TEMS lifecycle 종착).")
                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button("Cancel", on_click=cd.close).props("flat")

                        def do_archive_confirm():
                            archive_rule(rule["id"])
                            ui.notify(f"#{rule['id']} archived", type="warning")
                            cd.close()
                            dialog.close()
                            refresh_data()
                        ui.button("Archive", color="orange", on_click=do_archive_confirm)
                cd.open()

            def do_hard_delete():
                with ui.dialog() as cd, ui.card():
                    ui.label(f"#{rule['id']} 을 영구 삭제하시겠습니까?").classes("text-h6 text-negative")
                    ui.label("memory_logs / rule_health / qmd_rules/rule_*.md 모두 제거됩니다. 비가역.").classes("text-body2")
                    ui.label("(soft delete = Archive 권장)").classes("text-caption text-grey-7")
                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button("Cancel", on_click=cd.close).props("flat")

                        def do_hard_confirm():
                            hard_delete_rule(rule["id"])
                            ui.notify(f"#{rule['id']} permanently deleted", type="negative")
                            cd.close()
                            dialog.close()
                            refresh_data()
                        ui.button("DELETE", color="negative", on_click=do_hard_confirm)
                cd.open()

            with ui.row().classes("w-full justify-between q-mt-md"):
                with ui.row().classes("gap-2"):
                    ui.button("Save", icon="save", on_click=do_save).props("color=primary")
                    ui.button("Clear comment", icon="backspace", on_click=do_clear).props("flat color=grey")
                with ui.row().classes("gap-2"):
                    ui.button("Archive (soft)", icon="inventory_2", on_click=do_archive).props("color=orange")
                    ui.button("Hard Delete", icon="delete_forever", on_click=do_hard_delete).props("color=negative outline")
                    ui.button("Close", on_click=dialog.close).props("flat")
        dialog.open()

    def on_row_double_click(e) -> None:
        args = e.args
        row = None
        if isinstance(args, list) and len(args) >= 2:
            row = args[1] if isinstance(args[1], dict) else None
        elif isinstance(args, dict):
            row = args.get("row") or args.get("data") or args
        if not row:
            return
        rid = row.get("id")
        full = next((r for r in state["rules"] if r["id"] == rid), None)
        if full:
            open_edit_dialog(full)

    # ─── 헤더 ───
    with ui.header().classes("bg-primary"):
        ui.label("TEMS Rule Viewer").classes("text-h5 text-white q-mr-md")
        count_label = ui.label(f"{len(initial_grid_rows)} rules").classes("text-white q-mr-md")
        ui.button(icon="refresh", on_click=lambda: refresh_data()).props("flat color=white dense").tooltip("Refresh")

    # ─── 필터 바 ───
    with ui.row().classes("w-full items-center gap-2 q-pa-sm bg-grey-2"):
        ui.label("Filter:").classes("text-weight-medium")

        def make_filter_handler(k: str):
            def handler():
                state["filter"] = k
                apply_filter()
            return handler

        for key, label in [
            ("all", "All"), ("tcl", "TCL"), ("tgl", "TGL"),
            ("hot", "🔥 hot"), ("warm", "warm"), ("cold", "cold"), ("archive", "archive"),
            ("commented", "💬 commented"), ("disabled", "🚫 disabled"),
        ]:
            ui.button(label, on_click=make_filter_handler(key)).props("flat dense")

        ui.space()

        def on_search(e):
            state["search"] = e.value or ""
            apply_filter()

        ui.input(
            placeholder="Search rule / tags / comment...",
            on_change=on_search,
        ).props("dense outlined clearable").style("width: 280px;")

    # ─── Quasar Table (ui.table) — AG Grid v32 + NiceGUI 3.x race 회피 ───
    columns = [
        {"name": "id", "label": "ID", "field": "id", "sortable": True, "align": "right",
         "tooltip": "memory_logs.id — TEMS DB 의 규칙 고유 번호"},
        {"name": "category", "label": "Cat", "field": "category", "sortable": True, "align": "left",
         "tooltip": "TCL = 좁은 명시적 규칙 (사용자가 '앞으로/항상' 직접 정한 케이스). TGL = 누적 실수에서 추출한 넓은 위상 패턴. 자세히는 docs/wiki/concepts/TCL_vs_TGL.md"},
        {"name": "status", "label": "Status", "field": "status", "sortable": True, "align": "left",
         "tooltip": "규칙 lifecycle 단계 — warm(기본,활발) / hot(매우 자주 매칭) / cold(30일 0회 발동, 자동 전환) / archive(90일 0회, 또는 수동 archive 버튼). archive 는 preflight 에서 자동 제외."},
        {"name": "fire", "label": "Fire", "field": "fire", "sortable": True, "align": "right",
         "tooltip": "발동 카운트 — preflight_hook 가 매칭해서 컨텍스트에 주입한 누적 횟수. 자주 등장하는 규칙일수록 ↑."},
        {"name": "vc", "label": "Viol/Comp", "field": "vc", "align": "right",
         "tooltip": "Violation / Compliance — 발동된 뒤 결과. Viol = 규칙이 주입됐는데도 어긴 횟수. Comp = 잘 따른 횟수. 비율이 규칙 효용도의 직접 지표."},
        {"name": "ths", "label": "THS", "field": "ths", "sortable": True, "align": "right",
         "tooltip": "Topological Health Score (0~1, 기본 0.5). 산식: 0.25*log(fire) + 0.30*comp/(comp+viol) + 0.20*centrality - 0.10*mod_entropy - 0.15*age_decay. SessionStart hook 의 decay sweep 에서 24h 마다 자동 갱신 (S49~). 0.5 default 행은 (a) memory_logs orphan health row 또는 (b) sweep 미실행 상태."},
        {"name": "rule_preview", "label": "Rule", "field": "rule_preview", "align": "left", "classes": "rule-cell",
         "tooltip": "correction_rule (없으면 summary) 의 첫 120자. 더블클릭하면 전체 본문 + 코멘트 편집 모달."},
        {"name": "comment", "label": "코멘트", "field": "comment", "align": "left",
         "tooltip": "종일군이 viewer 에서 직접 단 코멘트 + severity (💬info / ⚠️warn / 🚫disable). 'disable' 은 preflight 주입에서 소프트 제외됨."},
    ]
    grid = ui.table(
        columns=columns,
        rows=initial_grid_rows,
        row_key="id",
        pagination={"rowsPerPage": 50, "sortBy": "id", "descending": True},
    ).classes("w-full").style("flex: 1 1 auto; min-height: 0;")
    grid.on("rowDblclick", on_row_double_click)

    # 헤더 슬롯 커스터마이즈 — col.tooltip 을 q-tooltip 으로 표출
    grid.add_slot("header", r"""
        <q-tr :props="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
            <q-tooltip v-if="col.tooltip" :delay="200" max-width="420px"
              class="bg-grey-9 text-white text-caption q-pa-sm" style="font-size:12px;line-height:1.4;">
              {{ col.tooltip }}
            </q-tooltip>
          </q-th>
        </q-tr>
    """)

    ui.add_head_html(
        """
        <style>
          /* viewport 잠금 */
          html, body { height: 100%; margin: 0; overflow: hidden; }
          /* body 의 Vue mount wrapper (class 없는 div) — flex column 으로 chain 시작 */
          body > div { height: 100vh; display: flex; flex-direction: column; min-height: 0; }
          /* q-layout: Quasar 가 display:block 기본. flex column 으로 강제 + 100vh */
          .nicegui-layout, .q-layout { height: 100vh !important; display: flex !important; flex-direction: column !important; min-height: 0 !important; }
          /* q-page-container: q-layout 의 자식. block 기본 → flex chain 으로 합류 + 남은 영역 채움 */
          .q-page-container { flex: 1 1 auto !important; min-height: 0 !important; display: flex !important; flex-direction: column !important; }
          /* q-page: q-page-container 의 자식. flex chain 합류 */
          .q-page-container > .q-page { flex: 1 1 auto !important; min-height: 0 !important; display: flex !important; flex-direction: column !important; }
          /* nicegui-content: q-page 안 user-content wrapper */
          .q-page > .nicegui-content { flex: 1 1 auto !important; min-height: 0 !important; padding: 0 !important; }
          /* q-table 내부: container = flex col (Quasar 기본 적용됨), middle 스크롤, top/bottom 고정 */
          .q-table__container { min-height: 0; }
          .q-table__middle { flex: 1 1 auto; min-height: 0; overflow: auto; }
          .q-table__top, .q-table__bottom { flex: 0 0 auto; }
          .rule-cell { max-width: 480px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        </style>
        """
    )

    # ─── 푸터 / 자동 새로고침 / THS sweep ───
    auto_state = {"on": False}

    def trigger_ths_sweep() -> None:
        try:
            if str(ROOT) not in sys.path:
                sys.path.insert(0, str(ROOT))
            from memory.decay import apply_decay
            result = apply_decay(dry_run=False)
        except Exception as exc:
            ui.notify(f"THS sweep 실패: {exc}", type="negative")
            return
        if not result.get("ok"):
            ui.notify(f"THS sweep ok=False: {result.get('error', '?')}", type="negative")
            return
        msg = (
            f"THS sweep 완료 — recomputed={result.get('ths_recomputed', 0)}"
            f" / transitions={result.get('transitions', 0)}"
            f" (cold+{result.get('to_cold', 0)} archive+{result.get('to_archive', 0)})"
        )
        ui.notify(msg, type="positive")
        refresh_data()

    with ui.footer().classes("bg-grey-3 text-black"):
        with ui.row().classes("items-center gap-3"):
            switch = ui.switch("Auto-refresh (5s)", value=False)

            def toggle(_):
                auto_state["on"] = switch.value

            switch.on_value_change(toggle)
            ui.button("Refresh THS now", icon="bolt", on_click=trigger_ths_sweep).props(
                "color=primary outline dense"
            ).tooltip(
                "decay.apply_decay(dry_run=False) 호출 — 전 규칙 ths_score 재계산 + "
                "60일/90일 status 전이. 24h 가드 무시 (수동 트리거)."
            )
            ui.label(f"DB: {DB_PATH}").classes("text-caption text-grey-8")

    ui.timer(5.0, lambda: refresh_data() if auto_state["on"] else None)
    # 초기 데이터는 construction time 에 이미 grid 에 박혔음 — 여기서 refresh 호출 안 함
    # (AG Grid v32 + NiceGUI 3.x race 회피)


# ─── Entrypoint ────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="TEMS Rule Viewer")
    parser.add_argument("--browser", action="store_true", help="브라우저 모드 (디버그용)")
    args, _ = parser.parse_known_args()

    if not DB_PATH.exists():
        print(f"[ERR] TEMS DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    _ensure_annot_table()

    if args.browser:
        ui.run(title="TEMS Rule Viewer", reload=False, port=8765, show=True)
    else:
        ui.run(
            title="TEMS Rule Viewer",
            native=True,
            window_size=(1280, 800),
            reload=False,
        )
    return 0


if __name__ == "__main__":
    # __mp_main__ 제거 — NiceGUI native_mode 가 mp.Process 로 _open_window 자식 spawn 시
    # 자식이 이 스크립트를 spawn import 하면 (실제로는 nicegui.native.native_mode 만 import 하지만,
    # 가드 누수 방지) main() 재진입 → ui.run(native=True) 중첩 호출 → 윈도우 즉시 종료. S52 진단.
    sys.exit(main())
