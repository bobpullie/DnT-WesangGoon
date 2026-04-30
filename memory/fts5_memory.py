"""
위상군(WesangGoon) FTS5+BM25 장기기억 시스템 v2
================================================
SQLite FTS5 기반 오류 로그 및 진행 기록 검색 엔진.
BM25 랭킹으로 과거 실패/성공 패턴을 자동 검색합니다.

카테고리:
  - TCL (Topological Checklist Loop): 사용자 "앞으로" 지시 → 위상적 체크리스트
  - TGL (Topological Guard Loop): 실수/시행착오 → 위상적 가드 규칙
  - session: 세션 메타데이터
  - general: 일반 기록

Usage:
    from memory.fts5_memory import MemoryDB
    db = MemoryDB()
    db.commit_tcl(...)        # TCL 규칙 커밋
    db.commit_tgl(...)        # TGL 가드 커밋
    db.preflight("query")    # 작업 전 BM25 검색
    db.search("query")       # 일반 BM25 검색
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "error_logs.db"  # S49 P0: cwd 비의존


class MemoryDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            # 메인 메모리 테이블 (keyword_trigger 추가)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    context_tags TEXT NOT NULL,
                    keyword_trigger TEXT DEFAULT '',
                    action_taken TEXT NOT NULL,
                    result TEXT NOT NULL,
                    correction_rule TEXT,
                    category TEXT DEFAULT 'general',
                    severity TEXT DEFAULT 'info',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)

            # 컬럼 마이그레이션 (기존 DB 호환)
            # S56-B: temporal columns (valid_from/valid_until/superseded_by) 도 여기서 보장 —
            # search() SELECT 가 이 컬럼들을 참조하므로 fresh DB 에서도 NoSuchColumn 회피.
            # (TemporalGraph._ensure_temporal_tables 와 중복이지만 idempotent 라 안전.)
            for col, default in [
                ("keyword_trigger", "''"),
                ("summary", "''"),
                ("valid_from", "NULL"),
                ("valid_until", "NULL"),
                ("superseded_by", "NULL"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE memory_logs ADD COLUMN {col} TEXT DEFAULT {default}")
                except sqlite3.OperationalError:
                    pass  # 이미 존재

            # 기존 FTS5 테이블 드롭 후 재생성 (keyword_trigger 포함)
            conn.execute("DROP TABLE IF EXISTS memory_fts")
            conn.execute("DROP TRIGGER IF EXISTS memory_ai")
            conn.execute("DROP TRIGGER IF EXISTS memory_ad")
            conn.execute("DROP TRIGGER IF EXISTS memory_au")

            # FTS5 가상 테이블 (BM25 랭킹 내장, keyword_trigger 포함)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    context_tags,
                    keyword_trigger,
                    action_taken,
                    result,
                    correction_rule,
                    category,
                    content=memory_logs,
                    content_rowid=id,
                    tokenize='unicode61'
                )
            """)

            # 기존 데이터를 FTS5에 재색인
            conn.execute("""
                INSERT INTO memory_fts(rowid, context_tags, keyword_trigger, action_taken, result, correction_rule, category)
                SELECT id, context_tags, COALESCE(keyword_trigger, ''), action_taken, result, correction_rule, category
                FROM memory_logs
            """)

            # 자동 동기화 트리거: INSERT
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_logs BEGIN
                    INSERT INTO memory_fts(rowid, context_tags, keyword_trigger, action_taken, result, correction_rule, category)
                    VALUES (new.id, new.context_tags, new.keyword_trigger, new.action_taken, new.result, new.correction_rule, new.category);
                END
            """)

            # 자동 동기화 트리거: DELETE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory_logs BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, context_tags, keyword_trigger, action_taken, result, correction_rule, category)
                    VALUES ('delete', old.id, old.context_tags, old.keyword_trigger, old.action_taken, old.result, old.correction_rule, old.category);
                END
            """)

            # 자동 동기화 트리거: UPDATE
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory_logs BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, context_tags, keyword_trigger, action_taken, result, correction_rule, category)
                    VALUES ('delete', old.id, old.context_tags, old.keyword_trigger, old.action_taken, old.result, old.correction_rule, old.category);
                    INSERT INTO memory_fts(rowid, context_tags, keyword_trigger, action_taken, result, correction_rule, category)
                    VALUES (new.id, new.context_tags, new.keyword_trigger, new.action_taken, new.result, new.correction_rule, new.category);
                END
            """)

            conn.commit()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ─── Core CRUD ───

    @staticmethod
    def _auto_summarize(correction_rule: str, max_len: int = 40) -> str:
        """correction_rule을 자동 압축하여 summary 생성.

        첫 문장 또는 첫 절을 max_len자 이내로 자르고, 핵심 동작만 남깁니다.
        """
        if not correction_rule:
            return ""

        # (1), (2) 같은 번호 리스트가 있으면 첫 번째 항목까지만
        text = correction_rule.strip()

        # "시: " 이후의 첫 번째 핵심 내용 추출
        if "시:" in text:
            text = text.split("시:")[-1].strip()
            # (1) 이전까지
            if "(1)" in text:
                text = text.split("(1)")[0].strip()
                if not text:
                    # (1) 내용 추출
                    parts = correction_rule.split("(1)")
                    if len(parts) > 1:
                        text = parts[1].split("(2)")[0].strip()

        # 길면 자르기
        if len(text) > max_len:
            # 자연스러운 끊김점 찾기
            for sep in [".", "。", ",", "，", " — ", " - "]:
                idx = text.find(sep, max_len // 2)
                if 0 < idx <= max_len:
                    text = text[:idx]
                    break
            else:
                text = text[:max_len]

        return text.strip(" ,;:→")

    def commit_memory(
        self,
        context_tags: list[str],
        action_taken: str,
        result: str,
        correction_rule: str = "",
        keyword_trigger: str = "",
        category: str = "general",
        severity: str = "info",
        summary: str = "",
        timestamp: Optional[str] = None,
    ) -> int:
        """메모리 기록 (Memory Commit)"""
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags_str = ", ".join(context_tags)

        # summary가 없으면 자동 생성
        if not summary:
            summary = self._auto_summarize(correction_rule)

        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO memory_logs
                    (timestamp, context_tags, keyword_trigger, action_taken, result, correction_rule, summary, category, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, tags_str, keyword_trigger, action_taken, result, correction_rule, summary, category, severity),
            )
            conn.commit()
            return cursor.lastrowid

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """BM25 랭킹 기반 전문 검색.

        S56-B: valid_from/valid_until/superseded_by 칼럼 노출 — HybridRetriever.preflight 가
        supersede 된 규칙을 retrieval 단계에서 필터링할 수 있도록.
        """
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    m.id, m.timestamp, m.context_tags, m.keyword_trigger,
                    m.action_taken, m.result, m.correction_rule,
                    m.summary, m.category, m.severity,
                    m.valid_from, m.valid_until, m.superseded_by, rank
                FROM memory_fts f
                JOIN memory_logs m ON f.rowid = m.id
                WHERE memory_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── TCL: Topological Checklist Loop ───

    def commit_tcl(
        self,
        original_instruction: str,
        topological_rule: str,
        keyword_trigger: str,
        context_tags: list[str],
    ) -> int:
        """사용자의 '앞으로' 지시를 위상적 체크리스트로 변환하여 저장"""
        return self.commit_memory(
            context_tags=context_tags,
            action_taken=f"[TCL] 원문: {original_instruction}",
            result=f"위상적 변환 완료 → 규칙 활성화",
            correction_rule=topological_rule,
            keyword_trigger=keyword_trigger,
            category="TCL",
            severity="directive",
        )

    def get_active_tcl(self) -> list[dict]:
        """활성 TCL 규칙 전체 조회"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_logs WHERE category = 'TCL' ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── TGL: Topological Guard Loop ───

    def commit_tgl(
        self,
        error_description: str,
        topological_case: str,
        guard_rule: str,
        keyword_trigger: str,
        context_tags: list[str],
        severity: str = "error",
    ) -> int:
        """실수/시행착오를 위상 케이스로 변환하여 가드 규칙 저장"""
        return self.commit_memory(
            context_tags=context_tags,
            action_taken=f"[TGL] 발생: {error_description}",
            result=f"위상 케이스: {topological_case}",
            correction_rule=guard_rule,
            keyword_trigger=keyword_trigger,
            category="TGL",
            severity=severity,
        )

    def get_active_tgl(self) -> list[dict]:
        """활성 TGL 가드 규칙 전체 조회"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_logs WHERE category = 'TGL' ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── Pre-flight: 작업 전 자동 검색 ───

    def preflight(self, query: str, limit: int = 5) -> dict:
        """작업 진입 전 TCL+TGL 규칙 자동 검색 (Pre-flight BM25 Retrieval)

        Returns:
            {
                "tcl_hits": [...],   # 관련 체크리스트 규칙
                "tgl_hits": [...],   # 관련 가드 규칙
                "general_hits": [...] # 기타 관련 기록
            }
        """
        results = self.search(query, limit=limit * 3)
        return {
            "tcl_hits": [r for r in results if r["category"] == "TCL"],
            "tgl_hits": [r for r in results if r["category"] == "TGL"],
            "general_hits": [r for r in results if r["category"] not in ("TCL", "TGL")],
        }

    # ─── Utility ───

    def get_recent(self, n: int = 10, category: Optional[str] = None) -> list[dict]:
        """최근 N건의 메모리 조회"""
        with self._conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM memory_logs WHERE category = ? ORDER BY id DESC LIMIT ?",
                    (category, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memory_logs ORDER BY id DESC LIMIT ?", (n,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_correction_rules(self, tags: list[str]) -> list[dict]:
        """특정 태그와 관련된 correction_rule만 추출"""
        query = " OR ".join(tags)
        results = self.search(query, limit=20)
        return [r for r in results if r.get("correction_rule")]

    def stats(self) -> dict:
        """메모리 통계"""
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM memory_logs").fetchone()[0]
            by_category = conn.execute(
                "SELECT category, COUNT(*) as cnt FROM memory_logs GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            by_severity = conn.execute(
                "SELECT severity, COUNT(*) as cnt FROM memory_logs GROUP BY severity ORDER BY cnt DESC"
            ).fetchall()
            return {
                "total_records": total,
                "by_category": {r["category"]: r["cnt"] for r in by_category},
                "by_severity": {r["severity"]: r["cnt"] for r in by_severity},
            }

    def export_json(self) -> str:
        """전체 메모리를 JSON으로 내보내기"""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM memory_logs ORDER BY id").fetchall()
            return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


# --- CLI 인터페이스 ---
if __name__ == "__main__":
    import sys

    db = MemoryDB()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fts5_memory.py search <query>")
        print("  python fts5_memory.py preflight <query>")
        print("  python fts5_memory.py recent [n] [category]")
        print("  python fts5_memory.py tcl")
        print("  python fts5_memory.py tgl")
        print("  python fts5_memory.py stats")
        print("  python fts5_memory.py export")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "search" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        results = db.search(query)
        for r in results:
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print("---")
        if not results:
            print("(검색 결과 없음)")

    elif cmd == "preflight" and len(sys.argv) >= 3:
        query = " ".join(sys.argv[2:])
        pf = db.preflight(query)
        for label, hits in pf.items():
            if hits:
                print(f"\n=== {label} ===")
                for r in hits:
                    print(f"  [{r['severity']}] {r['correction_rule']}")
                    print(f"    triggers: {r['keyword_trigger']}")

    elif cmd == "recent":
        n = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        cat = sys.argv[3] if len(sys.argv) >= 4 else None
        for r in db.get_recent(n, cat):
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print("---")

    elif cmd == "tcl":
        for r in db.get_active_tcl():
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print("---")

    elif cmd == "tgl":
        for r in db.get_active_tgl():
            print(json.dumps(r, ensure_ascii=False, indent=2))
            print("---")

    elif cmd == "stats":
        print(json.dumps(db.stats(), ensure_ascii=False, indent=2))

    elif cmd == "export":
        print(db.export_json())

    else:
        print(f"Unknown command: {cmd}")
