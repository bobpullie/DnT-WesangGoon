"""Preflight 시맨틱 폴백 테스트"""
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from tems.fts5_memory import MemoryDB
from tems.tems_engine import HybridRetriever


def make_test_db(tmp_dir: Path) -> MemoryDB:
    """테스트용 DB 생성"""
    db_path = tmp_dir / "test_error_logs.db"
    db = MemoryDB(db_path=str(db_path))
    db.commit_memory(
        context_tags=["project:dnt"],
        action_taken="test",
        result="ok",
        correction_rule="프로세스 간 통신에서 인코딩 변환 주의",
        keyword_trigger="subprocess bytes UTF-8 encoding",
        category="TGL",
    )
    return db


def test_preflight_semantic_fallback():
    """BM25가 0 hits 반환 시 HybridRetriever 폴백이 작동하는지 확인"""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        # BM25에서 안 잡히는 시맨틱 쿼리
        sparse_results = retriever._sparse_search("바이트 변환 문제점")

        # Hybrid는 dense 폴백으로 잡아야 함 (mock)
        mock_qmd_output = json.dumps([{
            "docid": "#1",
            "score": 0.75,
            "file": "qmd://tems-wesanggoon/rule_0001.md",
            "title": "[TGL] Rule #1",
            "snippet": "프로세스 간 통신에서 인코딩 변환 주의"
        }]).encode("utf-8")

        mock_result = MagicMock()
        mock_result.stdout = mock_qmd_output

        with patch("tems.tems_engine.subprocess.run", return_value=mock_result):
            hybrid_results = retriever.search("바이트 변환 문제점", limit=5, mode="auto")

        assert len(hybrid_results) > 0, "Hybrid should return results via dense fallback"
        assert hybrid_results[0]["category"] == "TGL"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_preflight_semantic_fallback()
    print("PASS: test_preflight_semantic_fallback")
    print("All tests passed.")
