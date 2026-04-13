"""TEMS Hybrid Retrieval 품질 비교 테스트

BM25-only vs Hybrid(BM25+QMD)를 동일 쿼리 10개로 비교.
Dense가 BM25 miss를 보완하는지 확인.
"""
import sys
from pathlib import Path

from tems.tems_engine import HybridRetriever

# 쿼리 3종: BM25에 유리한 것, Dense에 유리한 것, 중립
TEST_QUERIES = [
    # BM25 유리 (정확한 키워드)
    ("subprocess bytes UTF-8", "TGL", "keyword-exact"),
    ("preflight BM25 검색", "TCL", "keyword-exact"),
    ("git commit amend", None, "keyword-exact"),

    # Dense 유리 (의미적 유사, 키워드 불일치)
    ("프로세스 간 통신에서 인코딩 문제", "TGL", "semantic"),
    ("에이전트가 실수를 반복하지 않게 하는 방법", None, "semantic"),
    ("코드 작성 전에 과거 기록부터 확인하라", "TCL", "semantic"),
    ("큰 작업을 한번에 하면 안되는 이유", "TCL", "semantic"),

    # 중립 (둘 다 가능)
    ("세션 종료 핸드오버", "TCL", "neutral"),
    ("게임 설계 심리학", None, "neutral"),
    ("Windows 경로 문제", "TGL", "neutral"),
]


def run_comparison():
    """BM25-only vs Hybrid 비교 실행"""
    from tems.fts5_memory import MemoryDB
    db_path = Path(__file__).parent.parent / "error_logs.db"
    db = MemoryDB(db_path=str(db_path))
    retriever = HybridRetriever(db=db)

    print("=" * 70)
    print("TEMS Hybrid Retrieval Quality Comparison")
    print("=" * 70)

    sparse_wins = 0
    dense_wins = 0
    both_miss = 0

    for query, expected_cat, qtype in TEST_QUERIES:
        sparse_results = retriever.search(query, limit=5, mode="sparse")
        hybrid_results = retriever.search(query, limit=5, mode="auto")

        sparse_ids = {r.get("id") for r in sparse_results}
        hybrid_ids = {r.get("id") for r in hybrid_results}
        dense_only = hybrid_ids - sparse_ids

        has_sparse = len(sparse_results) > 0
        has_hybrid = len(hybrid_results) > 0

        status = "BOTH" if has_sparse and has_hybrid else \
                 "SPARSE-ONLY" if has_sparse else \
                 "DENSE-CATCH" if has_hybrid else "MISS"

        if not has_sparse and has_hybrid:
            dense_wins += 1
        elif has_sparse and not has_hybrid:
            sparse_wins += 1
        elif not has_sparse and not has_hybrid:
            both_miss += 1

        print(f"\n[{qtype:13s}] {query}")
        print(f"  Sparse: {len(sparse_results)} hits | Hybrid: {len(hybrid_results)} hits | Dense-only: {len(dense_only)} | {status}")

        if sparse_results:
            r = sparse_results[0]
            print(f"  Top sparse: #{r.get('id')} [{r.get('category')}] {str(r.get('correction_rule', ''))[:50]}")
        if hybrid_results:
            r = hybrid_results[0]
            print(f"  Top hybrid: #{r.get('id')} [{r.get('category')}] {str(r.get('correction_rule', ''))[:50]}")

    print(f"\n{'=' * 70}")
    print(f"Summary: Dense catches {dense_wins} BM25 misses | Sparse-only: {sparse_wins} | Both miss: {both_miss}")
    print(f"{'=' * 70}")

    if dense_wins >= 1:
        print("PASS: Dense search provides value beyond BM25")
    else:
        print("WARN: Dense search didn't catch any BM25 misses — check QMD embeddings")


if __name__ == "__main__":
    run_comparison()
