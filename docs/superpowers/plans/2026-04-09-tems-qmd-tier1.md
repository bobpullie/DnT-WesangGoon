# TEMS + QMD Dense Vector Tier 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** TEMS HybridRetriever의 dense 검색을 세션 문서(`wesanggoon-sessions`)에서 규칙 DB 자체(`tems-wesanggoon`)로 교정하고, preflight에 시맨틱 폴백을 통합한다.

**Architecture:** 각 규칙을 개별 .md 파일로 `memory/qmd_rules/` 디렉토리에 내보내고, `tems-wesanggoon` QMD 컬렉션으로 임베딩. `_dense_search()`는 이 컬렉션을 검색하여 파일명에서 rule_id를 추출한 뒤 SQLite에서 전체 규칙을 로드. `tems_commit` 시 자동으로 해당 규칙 파일을 생성하고 QMD를 갱신.

**Tech Stack:** Python 3.12, SQLite FTS5, QMD CLI (`qmd query/search/embed/collection`), subprocess

**Spec:** `docs/superpowers/specs/2026-04-09-tems-qmd-upgrade-design.md` §5 Tier 1

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `memory/qmd_rules/` | QMD 컬렉션용 규칙 마크다운 디렉토리 |
| Create | `memory/tests/test_qmd_sync.py` | Task 1~3 테스트 |
| Modify | `memory/tems_engine.py:28` | `QMD_RULES_DIR` 경로 변경 |
| Modify | `memory/tems_engine.py:782-812` | `sync_rules_to_qmd()` per-rule 파일 리팩터 |
| Modify | `memory/tems_engine.py:90-119` | `_dense_search()` 컬렉션 교정 + 결과 파싱 |
| Modify | `memory/tems_commit.py:46-58` | 커밋 후 자동 QMD 동기화 |
| Create | `memory/tests/test_preflight_semantic.py` | Task 5~6 테스트 |
| Modify | `memory/preflight_hook.py:310-316` | 시맨틱 폴백 분기 추가 |
| Modify | `memory/tems_engine.py:121-131` | RRF 가중치 재튜닝 |

---

## Task 1: QMD 컬렉션 생성 + per-rule 내보내기 함수

**Files:**
- Create: `memory/qmd_rules/.gitkeep`
- Create: `memory/tests/__init__.py`
- Create: `memory/tests/test_qmd_sync.py`
- Modify: `memory/tems_engine.py:28`
- Modify: `memory/tems_engine.py:782-812`

- [ ] **Step 1: 디렉토리 생성 + QMD 컬렉션 등록**

```bash
mkdir -p "E:/DnT/DnT_WesangGoon/memory/qmd_rules"
touch "E:/DnT/DnT_WesangGoon/memory/qmd_rules/.gitkeep"
mkdir -p "E:/DnT/DnT_WesangGoon/memory/tests"
touch "E:/DnT/DnT_WesangGoon/memory/tests/__init__.py"
qmd collection add tems-wesanggoon "E:/DnT/DnT_WesangGoon/memory/qmd_rules"
```

Expected: `✓ Collection 'tems-wesanggoon' created successfully`

- [ ] **Step 2: `QMD_RULES_DIR` 경로 변경**

`memory/tems_engine.py:28` 수정:

```python
# Before:
QMD_RULES_DIR = Path(__file__).parent.parent / "qmd_sessions"

# After:
QMD_RULES_DIR = Path(__file__).parent / "qmd_rules"
```

- [ ] **Step 3: 테스트 작성 — `sync_rules_to_qmd()` per-rule 파일 내보내기**

`memory/tests/test_qmd_sync.py`:

```python
"""TEMS QMD 동기화 테스트"""
import sqlite3
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fts5_memory import MemoryDB


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
    from tems_engine import sync_rules_to_qmd, QMD_RULES_DIR

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        # QMD_RULES_DIR을 임시 디렉토리로 오버라이드
        import tems_engine
        original_dir = tems_engine.QMD_RULES_DIR
        tems_engine.QMD_RULES_DIR = tmp_dir / "qmd_rules"

        count = sync_rules_to_qmd(db)

        assert count == 3, f"Expected 3 rules exported, got {count}"

        rules_dir = tems_engine.QMD_RULES_DIR
        md_files = sorted(rules_dir.glob("rule_*.md"))
        assert len(md_files) == 3, f"Expected 3 .md files, got {len(md_files)}"

        # 파일명 형식 확인: rule_NNNN.md
        for f in md_files:
            assert f.stem.startswith("rule_"), f"Bad filename: {f.name}"
            rule_id = f.stem.split("_")[1]
            assert rule_id.isdigit(), f"Non-numeric rule ID in {f.name}"

        # 파일 내용에 필수 필드 존재 확인
        content = md_files[0].read_text(encoding="utf-8")
        assert "category:" in content, "Missing category in frontmatter"
        assert "rule_id:" in content, "Missing rule_id in frontmatter"
        assert "correction_rule" in content.lower() or "Rule:" in content, "Missing rule content"

        tems_engine.QMD_RULES_DIR = original_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_export_removes_stale_files():
    """DB에서 삭제된 규칙의 파일이 sync 시 정리되는지 확인"""
    from tems_engine import sync_rules_to_qmd
    import tems_engine

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        original_dir = tems_engine.QMD_RULES_DIR
        tems_engine.QMD_RULES_DIR = tmp_dir / "qmd_rules"

        # 첫 sync: 3개 파일 생성
        sync_rules_to_qmd(db)
        assert len(list((tmp_dir / "qmd_rules").glob("rule_*.md"))) == 3

        # stale 파일 하나 추가 (DB에 없는 규칙)
        stale = tmp_dir / "qmd_rules" / "rule_9999.md"
        stale.write_text("stale", encoding="utf-8")
        assert stale.exists()

        # 재sync: stale 파일이 삭제되어야 함
        sync_rules_to_qmd(db)
        assert not stale.exists(), "Stale file rule_9999.md should have been removed"

        tems_engine.QMD_RULES_DIR = original_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_export_per_rule_files()
    print("PASS: test_export_per_rule_files")
    test_export_removes_stale_files()
    print("PASS: test_export_removes_stale_files")
    print("All tests passed.")
```

- [ ] **Step 4: 테스트 실행 — 실패 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected: FAIL — `sync_rules_to_qmd()`가 아직 단일 파일(`active_rules.md`) 방식이므로 per-rule 파일 어서션 실패.

- [ ] **Step 5: `sync_rules_to_qmd()` per-rule 파일 리팩터 구현**

`memory/tems_engine.py:782-812` 전체 교체:

```python
def sync_rules_to_qmd(db: Optional[MemoryDB] = None) -> int:
    """FTS5 DB의 활성 규칙들을 QMD 인덱싱 가능한 개별 마크다운 파일로 내보내기.

    각 규칙을 rule_{id:04d}.md 파일로 생성하여 QMD가 개별 벡터로 임베딩하도록 함.
    DB에 없는 stale 파일은 삭제.
    """
    db = db or MemoryDB()
    rules = db.get_recent(200)

    QMD_RULES_DIR.mkdir(parents=True, exist_ok=True)

    # 현재 DB에 있는 rule ID 집합
    active_ids = set()

    for r in rules:
        rule_id = r["id"]
        active_ids.add(rule_id)

        rule_file = QMD_RULES_DIR / f"rule_{rule_id:04d}.md"
        content = _format_rule_markdown(r)
        rule_file.write_text(content, encoding="utf-8")

    # stale 파일 정리: DB에 없는 rule_*.md 삭제
    for f in QMD_RULES_DIR.glob("rule_*.md"):
        try:
            file_id = int(f.stem.split("_")[1])
            if file_id not in active_ids:
                f.unlink()
        except (ValueError, IndexError):
            pass

    # QMD 인덱스 갱신 (임베딩은 별도)
    try:
        subprocess.run(
            ["qmd", "update"],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass

    return len(rules)


def _format_rule_markdown(rule: dict) -> str:
    """규칙을 QMD 인덱싱에 최적화된 마크다운으로 포맷."""
    rid = rule["id"]
    cat = rule.get("category", "general")
    tags = rule.get("context_tags", "")
    trigger = rule.get("keyword_trigger", "")
    correction = rule.get("correction_rule", "")
    severity = rule.get("severity", "info")
    action = rule.get("action_taken", "")
    result = rule.get("result", "")

    lines = [
        f"---",
        f"rule_id: {rid}",
        f"category: {cat}",
        f"tags: {tags}",
        f"trigger: {trigger}",
        f"severity: {severity}",
        f"---",
        f"",
        f"# [{cat}] Rule #{rid}",
        f"",
        f"**Keywords:** {trigger}",
        f"",
        f"**Rule:** {correction}",
        f"",
        f"**Context:** {action}",
        f"",
        f"**Result:** {result}",
    ]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 6: 테스트 재실행 — 통과 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected:
```
PASS: test_export_per_rule_files
PASS: test_export_removes_stale_files
All tests passed.
```

- [ ] **Step 7: 실제 DB로 sync 실행 + QMD 임베딩**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python -c "
from tems_engine import sync_rules_to_qmd
count = sync_rules_to_qmd()
print(f'Exported {count} rules')
"
```

Expected: `Exported 45 rules` (현재 DB 규칙 수)

```bash
ls "E:/DnT/DnT_WesangGoon/memory/qmd_rules/" | head -10
```

Expected: `rule_0001.md`, `rule_0002.md`, ... 45개 파일

```bash
qmd embed
```

Expected: 45개 파일 임베딩 완료 (CUDA ~50초)

- [ ] **Step 8: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/qmd_rules/.gitkeep memory/tests/__init__.py memory/tests/test_qmd_sync.py memory/tems_engine.py
git commit -m "feat(tems): per-rule QMD export + tems-wesanggoon collection

sync_rules_to_qmd() now exports each rule as individual .md file
for granular QMD vector indexing. Stale files auto-cleaned."
```

---

## Task 2: `_dense_search()` 컬렉션 교정 + 결과 파싱

**Files:**
- Modify: `memory/tems_engine.py:90-119`
- Modify: `memory/tests/test_qmd_sync.py` (테스트 추가)

- [ ] **Step 1: 테스트 작성 — `_dense_search()` 결과 파싱**

`memory/tests/test_qmd_sync.py`에 추가:

```python
def test_dense_search_parses_rule_id():
    """_dense_search() QMD 결과에서 rule_id를 추출하여 DB 규칙을 로드하는지 확인"""
    import json
    from unittest.mock import patch, MagicMock
    from tems_engine import HybridRetriever

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        # QMD가 반환할 mock 결과 (rule_0001.md 매칭)
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

        with patch("tems_engine.subprocess.run", return_value=mock_result):
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
    from tems_engine import HybridRetriever

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        with patch("tems_engine.subprocess.run", side_effect=Exception("qmd not found")):
            results = retriever._dense_search("anything")

        assert results == []
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
```

테스트 `__main__` 블록에도 추가:

```python
if __name__ == "__main__":
    test_export_per_rule_files()
    print("PASS: test_export_per_rule_files")
    test_export_removes_stale_files()
    print("PASS: test_export_removes_stale_files")
    test_dense_search_parses_rule_id()
    print("PASS: test_dense_search_parses_rule_id")
    test_dense_search_falls_back_on_error()
    print("PASS: test_dense_search_falls_back_on_error")
    print("All tests passed.")
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected: FAIL — `_dense_search()`가 아직 `wesanggoon-sessions`를 검색하고 `qmd_` prefix ID를 사용하므로 `r["id"] == 1` 어서션 실패.

- [ ] **Step 3: `_dense_search()` 리팩터 구현**

`memory/tems_engine.py:90-119` 전체 교체:

```python
    def _dense_search(self, query: str, limit: int = 20) -> list[dict]:
        """QMD 벡터 검색 — tems-wesanggoon 컬렉션에서 규칙 검색.

        QMD 결과의 파일명(rule_NNNN.md)에서 rule_id를 추출하여
        SQLite DB에서 전체 규칙 데이터를 로드.
        """
        try:
            result = subprocess.run(
                ["qmd", "query", query, "-c", "tems-wesanggoon", "--json"],
                capture_output=True, timeout=8,
            )
            stdout = result.stdout.decode("utf-8", errors="replace").strip()
            if not stdout:
                return []

            qmd_results = json.loads(stdout)
            converted = []
            for item in qmd_results[:limit]:
                rule_id = self._extract_rule_id(item.get("file", ""))
                if rule_id is None:
                    continue

                # DB에서 전체 규칙 로드
                rule = self._load_rule_by_id(rule_id)
                if rule is None:
                    continue

                rule["source"] = "qmd"
                rule["qmd_score"] = item.get("score", 0)
                converted.append(rule)

            return converted
        except Exception:
            return []

    @staticmethod
    def _extract_rule_id(file_path: str) -> Optional[int]:
        """QMD 파일 경로에서 rule_id 추출. e.g. 'qmd://tems-wesanggoon/rule_0001.md' → 1"""
        try:
            # 파일명: rule_NNNN.md
            filename = file_path.rsplit("/", 1)[-1]  # rule_0001.md
            stem = filename.replace(".md", "")        # rule_0001
            return int(stem.split("_")[1])             # 1
        except (ValueError, IndexError):
            return None

    def _load_rule_by_id(self, rule_id: int) -> Optional[dict]:
        """SQLite DB에서 rule_id로 전체 규칙 데이터 로드"""
        try:
            with self.db._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM memory_logs WHERE id = ?", (rule_id,)
                ).fetchone()
                if row:
                    return dict(row)
        except Exception:
            pass
        return None
```

- [ ] **Step 4: 테스트 재실행 — 통과 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected:
```
PASS: test_export_per_rule_files
PASS: test_export_removes_stale_files
PASS: test_dense_search_parses_rule_id
PASS: test_dense_search_falls_back_on_error
All tests passed.
```

- [ ] **Step 5: 실제 QMD 검색으로 E2E 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python -c "
from tems_engine import HybridRetriever
r = HybridRetriever()
# BM25에서 잡히기 어려운 시맨틱 쿼리
results = r._dense_search('에이전트 간 메시지 전달 방법')
for hit in results[:3]:
    print(f'  Rule #{hit[\"id\"]} [{hit[\"category\"]}]: {hit[\"correction_rule\"][:60]}')
if not results:
    print('  (no dense results — QMD embed 필요할 수 있음)')
"
```

Expected: 시맨틱으로 관련된 규칙이 반환됨 (또는 `qmd embed` 필요 안내).

- [ ] **Step 6: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/tems_engine.py memory/tests/test_qmd_sync.py
git commit -m "fix(tems): _dense_search() now queries tems-wesanggoon rules collection

Extracts rule_id from QMD filename, loads full rule from SQLite.
Previously searched wesanggoon-sessions (session docs, not rules)."
```

---

## Task 3: `tems_commit` 자동 QMD 동기화

**Files:**
- Modify: `memory/tems_commit.py:46-58`
- Modify: `memory/tems_engine.py` (신규 함수 `sync_single_rule_to_qmd`)

- [ ] **Step 1: 테스트 작성 — 커밋 후 자동 파일 생성**

`memory/tests/test_qmd_sync.py`에 추가:

```python
def test_commit_creates_qmd_file():
    """tems_commit 후 해당 규칙의 QMD .md 파일이 자동 생성되는지 확인"""
    import tems_engine

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        original_dir = tems_engine.QMD_RULES_DIR
        tems_engine.QMD_RULES_DIR = tmp_dir / "qmd_rules"
        tems_engine.QMD_RULES_DIR.mkdir(parents=True, exist_ok=True)

        # 새 규칙 직접 삽입 (tems_commit 내부 로직 시뮬레이션)
        rule_id = db.commit_memory(
            context_tags=["project:dnt"],
            action_taken="test-commit",
            result="ok",
            correction_rule="새로운 테스트 규칙입니다",
            keyword_trigger="테스트 자동동기화",
            category="TCL",
        )

        # sync_single_rule_to_qmd 호출
        from tems_engine import sync_single_rule_to_qmd
        sync_single_rule_to_qmd(rule_id, db)

        expected_file = tems_engine.QMD_RULES_DIR / f"rule_{rule_id:04d}.md"
        assert expected_file.exists(), f"Expected {expected_file} to exist"

        content = expected_file.read_text(encoding="utf-8")
        assert "새로운 테스트 규칙입니다" in content

        tems_engine.QMD_RULES_DIR = original_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
```

`__main__` 블록에 추가:

```python
    test_commit_creates_qmd_file()
    print("PASS: test_commit_creates_qmd_file")
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected: FAIL — `sync_single_rule_to_qmd` 함수가 아직 없음.

- [ ] **Step 3: `sync_single_rule_to_qmd()` 구현**

`memory/tems_engine.py`, `sync_rules_to_qmd()` 함수 바로 아래에 추가:

```python
def sync_single_rule_to_qmd(rule_id: int, db: Optional[MemoryDB] = None):
    """단일 규칙을 QMD 마크다운 파일로 내보내기 (tems_commit 후 호출).

    전체 재sync 없이 해당 규칙만 빠르게 갱신.
    """
    db = db or MemoryDB()
    QMD_RULES_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with db._conn() as conn:
            row = conn.execute(
                "SELECT * FROM memory_logs WHERE id = ?", (rule_id,)
            ).fetchone()
            if not row:
                return

            rule = dict(row)
            rule_file = QMD_RULES_DIR / f"rule_{rule_id:04d}.md"
            content = _format_rule_markdown(rule)
            rule_file.write_text(content, encoding="utf-8")
    except Exception:
        pass
```

- [ ] **Step 4: `tems_commit.py`에 자동 동기화 호출 추가**

`memory/tems_commit.py:9` import 섹션에 추가:

```python
# 기존 imports 아래에:
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

`memory/tems_commit.py:57` (`conn.close()` 직후, `return` 직전)에 추가:

```python
    conn.commit()
    conn.close()

    # QMD 자동 동기화 — 새 규칙 파일 생성
    try:
        from tems_engine import sync_single_rule_to_qmd
        sync_single_rule_to_qmd(rule_id)
    except Exception:
        pass  # QMD 동기화 실패 시 규칙 등록은 유지

    return {"ok": True, "rule_id": rule_id, "category": category, "rule": rule[:80]}
```

기존 `return` 문은 삭제 (위의 블록으로 대체).

- [ ] **Step 5: 테스트 재실행 — 통과 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py
```

Expected: 모든 테스트 통과.

- [ ] **Step 6: E2E 확인 — CLI로 규칙 등록 후 파일 생성 확인**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tems_commit.py --type TCL --rule "QMD 자동동기화 E2E 테스트 규칙 (삭제 가능)" --triggers "e2e-test qmd-sync" --tags "test" --json
```

Expected: `{"ok": true, "rule_id": N, ...}`

```bash
ls "E:/DnT/DnT_WesangGoon/memory/qmd_rules/" | grep "rule_00$(printf '%02d' N)"
```

Expected: `rule_00NN.md` 파일 존재.

```bash
# 테스트 규칙 정리
cd "E:/DnT/DnT_WesangGoon/memory" && python -c "
import sqlite3
conn = sqlite3.connect('error_logs.db')
cur = conn.cursor()
cur.execute(\"DELETE FROM memory_logs WHERE correction_rule LIKE '%E2E 테스트 규칙%'\")
print(f'Deleted {cur.rowcount} test rule(s)')
conn.commit()
conn.close()
"
```

- [ ] **Step 7: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/tems_engine.py memory/tems_commit.py memory/tests/test_qmd_sync.py
git commit -m "feat(tems): auto-sync rule to QMD on tems_commit

New rule files are created immediately after commit.
Full batch sync still available via sync_rules_to_qmd()."
```

---

## Task 4: BM25 miss → Dense catch 비교 테스트

**Files:**
- Create: `memory/tests/test_hybrid_quality.py`

이 태스크는 구현이 아닌 **검증 태스크**. Tier 1의 핵심 가치인 "BM25가 놓친 규칙을 dense가 잡는가"를 확인.

- [ ] **Step 1: 테스트 쿼리 10개 설계**

`memory/tests/test_hybrid_quality.py`:

```python
"""TEMS Hybrid Retrieval 품질 비교 테스트

BM25-only vs Hybrid(BM25+QMD)를 동일 쿼리 10개로 비교.
Dense가 BM25 miss를 보완하는지 확인.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tems_engine import HybridRetriever

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
    retriever = HybridRetriever()

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

    # 최소 기대: dense가 1개 이상의 BM25 miss를 잡아야 함
    if dense_wins >= 1:
        print("PASS: Dense search provides value beyond BM25")
    else:
        print("WARN: Dense search didn't catch any BM25 misses — check QMD embeddings")


if __name__ == "__main__":
    run_comparison()
```

- [ ] **Step 2: 비교 테스트 실행**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_hybrid_quality.py
```

Expected: Dense가 최소 1개 이상의 시맨틱 쿼리에서 BM25 miss를 보완. 결과를 기록하여 Task 6의 RRF 가중치 튜닝에 사용.

- [ ] **Step 3: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/tests/test_hybrid_quality.py
git commit -m "test(tems): hybrid retrieval quality comparison (10 queries)

BM25-only vs Hybrid(BM25+QMD) A/B test suite.
Validates dense search catches BM25 semantic misses."
```

---

## Task 5: Preflight 시맨틱 폴백 통합

**Files:**
- Create: `memory/tests/test_preflight_semantic.py`
- Modify: `memory/preflight_hook.py:308-316`

현재 preflight는 FTS5 BM25만 사용. BM25가 0 hits를 반환하면 HybridRetriever로 폴백하여 dense 검색 수행.

- [ ] **Step 1: 테스트 작성 — BM25 miss 시 Hybrid 폴백**

`memory/tests/test_preflight_semantic.py`:

```python
"""Preflight 시맨틱 폴백 테스트"""
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from fts5_memory import MemoryDB


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
    from tems_engine import HybridRetriever

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        db = make_test_db(tmp_dir)
        retriever = HybridRetriever(db=db)

        # BM25에서 안 잡히는 시맨틱 쿼리
        sparse_results = retriever._sparse_search("바이트 변환 문제점")
        # BM25는 "바이트 변환 문제점" 키워드가 없어서 miss할 수 있음

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

        with patch("tems_engine.subprocess.run", return_value=mock_result):
            hybrid_results = retriever.search("바이트 변환 문제점", limit=5, mode="auto")

        # sparse가 비었어도 hybrid에는 결과가 있어야 함
        assert len(hybrid_results) > 0, "Hybrid should return results via dense fallback"
        assert hybrid_results[0]["category"] == "TGL"

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_preflight_semantic_fallback()
    print("PASS: test_preflight_semantic_fallback")
    print("All tests passed.")
```

- [ ] **Step 2: 테스트 실행 — 통과 확인**

이 테스트는 현재 코드에서도 통과할 수 있음 (HybridRetriever.search는 이미 sparse+dense를 합산). 확인 실행:

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_preflight_semantic.py
```

Expected: PASS (HybridRetriever는 이미 양쪽을 합산)

- [ ] **Step 3: Preflight hook에 시맨틱 폴백 분기 추가**

현재 `preflight_hook.py:308-316`은 FTS5 직접 호출(`db.preflight(fts_query)`)만 사용. HybridRetriever.preflight()로 교체하여 dense 검색을 포함.

`memory/preflight_hook.py:308-328` 수정:

```python
        db = MemoryDB()

        # FTS5 prefix 쿼리 구성
        fts_query = " OR ".join(f'"{kw}"*' for kw in keywords)

        # 1단계: FTS5 BM25 기본 검색
        try:
            base_result = db.preflight(fts_query, limit=5)
        except Exception:
            base_result = {"tcl_hits": [], "tgl_hits": [], "general_hits": []}
            seen_ids = set()
            for kw in keywords[:5]:
                try:
                    partial = db.preflight(f'"{kw}"*', limit=3)
                    for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                        for hit in partial.get(cat, []):
                            if hit["id"] not in seen_ids:
                                seen_ids.add(hit["id"])
                                base_result[cat].append(hit)
                except Exception:
                    continue

        # 1-b단계: BM25가 빈약하면 HybridRetriever 시맨틱 폴백
        total_bm25 = sum(len(base_result.get(c, [])) for c in ("tcl_hits", "tgl_hits"))
        if total_bm25 < 2:
            try:
                from memory.tems_engine import HybridRetriever
                hybrid = HybridRetriever(db)
                hybrid_result = hybrid.preflight(" ".join(keywords), limit=5)
                # BM25 결과에 dense 결과 병합 (중복 제거)
                existing_ids = set()
                for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                    for hit in base_result.get(cat, []):
                        existing_ids.add(hit.get("id"))

                for cat in ("tcl_hits", "tgl_hits", "general_hits"):
                    for hit in hybrid_result.get(cat, []):
                        if hit.get("id") not in existing_ids:
                            base_result[cat].append(hit)
                            existing_ids.add(hit.get("id"))
            except Exception:
                pass
```

- [ ] **Step 4: 테스트 재실행**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_preflight_semantic.py
```

Expected: PASS

- [ ] **Step 5: 실제 preflight E2E 테스트**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && echo '{"prompt":"에이전트가 과거 실수를 반복하지 않는 방법","cwd":"E:/DnT/DnT_WesangGoon","session_id":"test"}' | python preflight_hook.py
```

Expected: `<preflight-memory-check>` 태그 출력. 시맨틱으로 관련된 규칙이 포함되어야 함.

비교 — BM25에서 잡히는 쿼리:

```bash
echo '{"prompt":"subprocess bytes UTF-8 Windows","cwd":"E:/DnT/DnT_WesangGoon","session_id":"test"}' | python preflight_hook.py
```

Expected: TGL #9 (subprocess bytes) 등 직접 키워드 매칭.

- [ ] **Step 6: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/preflight_hook.py memory/tests/test_preflight_semantic.py
git commit -m "feat(tems): semantic fallback in preflight hook

When BM25 returns < 2 TCL+TGL hits, falls back to HybridRetriever
which adds QMD dense vector results. Deduplicates by rule ID."
```

---

## Task 6: Dynamic RRF 가중치 재튜닝

**Files:**
- Modify: `memory/tems_engine.py:121-131`
- Modify: `memory/tests/test_hybrid_quality.py` (재실행)

이전까지 dense가 세션 문서를 검색했으므로 가중치가 의미 없었음. 이제 규칙 DB를 검색하므로 가중치 재조정.

- [ ] **Step 1: 현재 가중치 확인 + 변경 포인트 분석**

현재 (`tems_engine.py:129-130`):

```python
sparse_w = 0.3 + 0.5 * specificity       # 0.3 ~ 0.8
dense_w = 0.8 - 0.5 * specificity         # 0.3 ~ 0.8
```

문제: 규칙 DB는 `keyword_trigger` 필드가 잘 설계되어 BM25 정확도가 높음. Dense는 보조 역할이므로 기본 가중치를 BM25 쪽으로 편향.

- [ ] **Step 2: 가중치 재조정 구현**

`memory/tems_engine.py:129-130` 수정:

```python
        # v2: 규칙 DB 대상이므로 BM25 기본 우위 + dense 보완
        # specificity=0 (추상): sparse=0.35, dense=0.65
        # specificity=1 (구체): sparse=0.85, dense=0.15
        sparse_w = 0.35 + 0.5 * specificity      # 0.35 ~ 0.85
        dense_w = 0.65 - 0.5 * specificity        # 0.15 ~ 0.65
```

근거: 추상적 쿼리에서 dense가 더 큰 역할 (0.65), 구체적 쿼리에서 BM25가 지배 (0.85). Dense 최소값을 0.15로 설정하여 항상 시맨틱 신호를 유지.

- [ ] **Step 3: 품질 비교 재실행**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_hybrid_quality.py
```

Expected: 이전 결과 대비 시맨틱 쿼리에서 더 나은 결과 (dense catch 수 증가 또는 유지).

- [ ] **Step 4: 커밋**

```bash
cd "E:/DnT/DnT_WesangGoon"
git add memory/tems_engine.py
git commit -m "tune(tems): RRF weights for rule-DB dense search

BM25 base advantage for rule DB (keyword_trigger well-designed).
Dense weight range: 0.15~0.65 (was 0.3~0.8).
Sparse weight range: 0.35~0.85 (was 0.3~0.8)."
```

---

## Task 7: 전체 동기화 + 최종 검증

통합 검증 태스크.

- [ ] **Step 1: 전체 규칙 QMD 동기화 + 임베딩**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python -c "
from tems_engine import sync_rules_to_qmd
count = sync_rules_to_qmd()
print(f'Synced {count} rules to QMD')
"
```

```bash
qmd embed
```

Expected: 45개 규칙 임베딩 완료.

```bash
qmd collection show tems-wesanggoon
```

Expected: Files: 45

- [ ] **Step 2: 전체 테스트 스위트 실행**

```bash
cd "E:/DnT/DnT_WesangGoon/memory" && python tests/test_qmd_sync.py && python tests/test_preflight_semantic.py && python tests/test_hybrid_quality.py
```

Expected: 모든 테스트 통과 + 품질 비교 결과 양호.

- [ ] **Step 3: 실제 preflight E2E (다양한 쿼리)**

```bash
# 키워드 매칭 쿼리
echo '{"prompt":"subprocess encoding Windows bytes","cwd":"E:/DnT/DnT_WesangGoon","session_id":"test"}' | python "E:/DnT/DnT_WesangGoon/memory/preflight_hook.py"

# 시맨틱 쿼리 (BM25 miss 가능)
echo '{"prompt":"코드를 고치기 전에 먼저 해야 할 일","cwd":"E:/DnT/DnT_WesangGoon","session_id":"test"}' | python "E:/DnT/DnT_WesangGoon/memory/preflight_hook.py"

# 혼합 쿼리
echo '{"prompt":"세션 끝낼 때 빠뜨리는 것","cwd":"E:/DnT/DnT_WesangGoon","session_id":"test"}' | python "E:/DnT/DnT_WesangGoon/memory/preflight_hook.py"
```

Expected: 각 쿼리에 대해 관련 TCL/TGL이 `<preflight-memory-check>` 안에 출력됨.

- [ ] **Step 4: 최종 커밋 (있다면)**

남은 변경사항이 있으면 커밋.

```bash
cd "E:/DnT/DnT_WesangGoon" && git status
```

---

## Verification Checklist

- [ ] `qmd collection show tems-wesanggoon` → 45개 파일
- [ ] `_dense_search()` → `tems-wesanggoon` 컬렉션 검색
- [ ] `tems_commit --type TCL --rule "..." --triggers "..."` → `qmd_rules/rule_NNNN.md` 자동 생성
- [ ] `preflight_hook.py` → BM25 miss 시 HybridRetriever 폴백
- [ ] RRF 가중치 → sparse 0.35~0.85, dense 0.15~0.65
- [ ] 테스트 3개 파일 모두 통과 (`test_qmd_sync.py`, `test_preflight_semantic.py`, `test_hybrid_quality.py`)
- [ ] 기존 preflight 기능 유지 (BM25 쿼리 정상 작동)
