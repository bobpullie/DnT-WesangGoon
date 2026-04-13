"""TEMS QMD 동기화 테스트"""
import sqlite3
import tempfile
import shutil
from pathlib import Path

from tems.fts5_memory import MemoryDB


def make_test_db(tmp_dir: Path) -> MemoryDB:
    """테스트용 DB 생성 + 샘플 규칙 3개 삽입"""
    db_path = tmp_dir / "test_error_logs.db"
    db = MemoryDB(db_path=str(db_path))

    db.commit_memory(
        context_tags=["project:dnt", "semantic-fallback"],
        action_taken="test",
        result="ok",
        correction_rule="BM25 miss 시 dense vector 폴백 검색을 수행할 것",
        keyword_trigger="BM25 dense semantic fallback",
        category="TCL",
        severity="info",
    )
    db.commit_memory(
        context_tags=["project:dnt", "subprocess"],
        action_taken="test",
        result="ok",
        correction_rule="Windows subprocess에서 bytes I/O + UTF-8 수동 디코딩 필수",
        keyword_trigger="subprocess bytes UTF-8 Windows encoding",
        category="TGL",
        severity="warning",
    )
    db.commit_memory(
        context_tags=["project:meta"],
        action_taken="test",
        result="ok",
        correction_rule="세션종료 시 핸드오버 문서 작성 (디테일 누락 금지)",
        keyword_trigger="세션종료 핸드오버 문서",
        category="TCL",
        severity="info",
    )
    return db


def test_export_per_rule_files():
    """sync_rules_to_qmd()가 규칙별 개별 .md 파일을 생성하는지 확인"""
    from tems import tems_engine

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        qmd_dir = tmp_dir / "qmd_rules"

        count = tems_engine.sync_rules_to_qmd(db, qmd_dir)

        assert count == 3, f"Expected 3 rules exported, got {count}"

        md_files = sorted(qmd_dir.glob("rule_*.md"))
        assert len(md_files) == 3, f"Expected 3 .md files, got {len(md_files)}"

        for f in md_files:
            assert f.stem.startswith("rule_"), f"Bad filename: {f.name}"
            rule_id = f.stem.split("_")[1]
            assert rule_id.isdigit(), f"Non-numeric rule ID in {f.name}"

        content = md_files[0].read_text(encoding="utf-8")
        assert "category:" in content, "Missing category in frontmatter"
        assert "rule_id:" in content, "Missing rule_id in frontmatter"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_export_removes_stale_files():
    """DB에서 삭제된 규칙의 파일이 sync 시 정리되는지 확인"""
    from tems import tems_engine

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        qmd_dir = tmp_dir / "qmd_rules"

        tems_engine.sync_rules_to_qmd(db, qmd_dir)
        assert len(list(qmd_dir.glob("rule_*.md"))) == 3

        stale = qmd_dir / "rule_9999.md"
        stale.write_text("stale", encoding="utf-8")
        assert stale.exists()

        tems_engine.sync_rules_to_qmd(db, qmd_dir)
        assert not stale.exists(), "Stale file rule_9999.md should have been removed"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_dense_search_parses_rule_id():
    """_dense_search() QMD 결과에서 rule_id를 추출하여 DB 규칙을 로드하는지 확인"""
    import json
    from unittest.mock import patch, MagicMock
    from tems.tems_engine import HybridRetriever

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        mock_qmd_output = json.dumps([
            {
                "docid": "#123",
                "score": 0.85,
                "file": "qmd://tems-wesanggoon/rule_0001.md",
                "title": "[TCL] Rule #1",
                "snippet": "BM25 miss 시 dense vector 폴백 검색을 수행할 것"
            }
        ]).encode("utf-8")

        mock_result = MagicMock()
        mock_result.stdout = mock_qmd_output
        mock_result.returncode = 0

        with patch("tems.tems_engine.subprocess.run", return_value=mock_result):
            results = retriever._dense_search("시맨틱 검색 폴백")

        assert len(results) == 1
        r = results[0]
        assert r["id"] == 1, f"Expected rule_id=1, got {r['id']}"
        assert r["category"] == "TCL"
        assert "dense vector 폴백" in r["correction_rule"]
        assert r["source"] == "qmd"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_dense_search_falls_back_on_error():
    """QMD 프로세스 실패 시 빈 리스트 반환"""
    from unittest.mock import patch
    from tems.tems_engine import HybridRetriever

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        with patch("tems.tems_engine.subprocess.run", side_effect=Exception("qmd not found")):
            results = retriever._dense_search("anything")

        assert results == []
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_commit_creates_qmd_file():
    """tems_commit 후 해당 규칙의 QMD .md 파일이 자동 생성되는지 확인"""
    from tems import tems_engine

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        qmd_dir = tmp_dir / "qmd_rules"
        qmd_dir.mkdir(parents=True, exist_ok=True)

        rule_id = db.commit_memory(
            context_tags=["project:dnt"],
            action_taken="test-commit",
            result="ok",
            correction_rule="새로운 테스트 규칙입니다",
            keyword_trigger="테스트 자동동기화",
            category="TCL",
        )

        from tems.tems_engine import sync_single_rule_to_qmd
        sync_single_rule_to_qmd(rule_id, db, qmd_dir)

        expected_file = qmd_dir / f"rule_{rule_id:04d}.md"
        assert expected_file.exists(), f"Expected {expected_file} to exist"

        content = expected_file.read_text(encoding="utf-8")
        assert "새로운 테스트 규칙입니다" in content
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_export_per_rule_files()
    print("PASS: test_export_per_rule_files")
    test_export_removes_stale_files()
    print("PASS: test_export_removes_stale_files")
    test_dense_search_parses_rule_id()
    print("PASS: test_dense_search_parses_rule_id")
    test_dense_search_falls_back_on_error()
    print("PASS: test_dense_search_falls_back_on_error")
    test_commit_creates_qmd_file()
    print("PASS: test_commit_creates_qmd_file")
    print("All tests passed.")
