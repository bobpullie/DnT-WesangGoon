# DnT KnowledgeHub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 종일군의 사고·세션 디테일·테스트 결과·교훈을 자동 축적하는 KnowledgeHub Phase 1 MVP 구축. 7종 노드 + 기록군 Subagent + 3중 누락 방지망 + Obsidian 시각화.

**Architecture:** Markdown 파일이 진실의 원본, SQLite FTS5가 인덱스. Python CLI(`/k-*`)가 쓰기 인터페이스, Obsidian이 읽기 인터페이스. 외부 프로젝트(`DnT_WesangGoon`, `MRV_DnT`, `DnT_Fermion`)의 핸드오버는 어댑터로 비파괴 미러링.

**Tech Stack:** Python 3.11+, sqlite3 (FTS5), PyYAML, python-frontmatter, click, pytest, watchdog, dataclasses

**Spec 기반:** `E:\DnT\DnT_WesangGoon\docs\superpowers\specs\2026-04-07-knowledge-hub-design.md`

**작업 위치:** `E:/KnowledgeHub/` (드라이브 루트, 어느 프로젝트에도 속하지 않는 독립 메타 프로젝트)

---

## 작업 환경 사전 준비 (Task 1 전 1회)

이 plan을 실행하기 전 사용자(또는 빌드군)는 아래 사전 작업을 한 번 수행해야 한다:

1. Python 3.11+ 설치 확인: `python --version`
2. SQLite FTS5 활성화 확인: `python -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.execute('CREATE VIRTUAL TABLE t USING fts5(x)'); print('FTS5 OK')"`
3. Obsidian 설치 (https://obsidian.md/, vault 직접 설정은 Task 22에서)
4. `E:/KnowledgeHub/` 디렉토리 위치 사용 가능 확인 (권한, 디스크 공간 ≥ 1GB 권장)

3개 모두 OK면 Task 1 시작.

---

## File Structure (전체 매핑)

```
E:/KnowledgeHub/
├── README.md                          # Task 1
├── pyproject.toml                     # Task 1
├── .gitignore                         # Task 1
│
├── .obsidian/                         # Task 22
│   ├── core-plugins.json
│   ├── community-plugins.json
│   └── workspace.json
│
├── .index/                            # Task 3 (DB 자동 생성)
│   └── wiki.db                        # gitignore 대상
│
├── khub/
│   ├── __init__.py                    # Task 1
│   ├── schema.py                      # Task 2
│   ├── frontmatter_io.py              # Task 4
│   ├── db.py                          # Task 3
│   ├── nodes.py                       # Task 5
│   ├── edges.py                       # Task 6
│   ├── search.py                      # Task 7
│   ├── adapters/
│   │   ├── __init__.py                # Task 8
│   │   ├── base.py                    # Task 8
│   │   └── claude_standard.py         # Task 9
│   ├── mirror_sync.py                 # Task 10
│   ├── indexer.py                     # Task 11
│   ├── friction.py                    # Task 12
│   ├── wiki_api.py                    # Task 13, 14
│   ├── girok.py                       # Task 18
│   ├── visualizer.py                  # Task 20
│   └── cli.py                         # Task 15, 16, 17
│
├── .agents/
│   └── girok-goon.md                  # Task 19
│
├── projects/                          # Task 21
│   ├── DnT_Game.md
│   ├── DnT_Fermion.md
│   └── Shared.md
│
├── notes/                             # 빈 폴더 (Task 1)
├── mirrors/                           # 빈 폴더 (Task 1)
│   ├── wesang/
│   ├── build/
│   └── fermion/
├── artifacts/                         # 빈 폴더 (Task 1)
│   ├── fermion/
│   ├── dnt/
│   └── shared/
│
└── tests/
    ├── __init__.py                    # Task 1
    ├── conftest.py                    # Task 3
    ├── fixtures/                      # Task 9
    │   └── sample_handovers/
    │       ├── wesang_session16.md
    │       ├── build_handoff.md
    │       └── fermion_session1.md
    ├── test_schema.py                 # Task 2
    ├── test_db.py                     # Task 3
    ├── test_frontmatter_io.py         # Task 4
    ├── test_nodes.py                  # Task 5
    ├── test_edges.py                  # Task 6
    ├── test_search.py                 # Task 7
    ├── test_adapters/
    │   ├── __init__.py                # Task 8
    │   └── test_claude_standard.py    # Task 9
    ├── test_mirror_sync.py            # Task 10
    ├── test_indexer.py                # Task 11
    ├── test_friction.py               # Task 12
    ├── test_wiki_api.py               # Task 13, 14
    ├── test_cli.py                    # Task 15, 16, 17
    ├── test_girok.py                  # Task 18
    ├── test_visualizer.py             # Task 20
    ├── test_e2e_scenario.py           # Task 24
    └── test_smoke.py                  # Task 23
```

**작업 단위 25개. 추정 소요: 4-6주.**

---

## Task 1: 프로젝트 초기화 (디렉토리 + 패키징)

**Files:**
- Create: `E:/KnowledgeHub/README.md`
- Create: `E:/KnowledgeHub/pyproject.toml`
- Create: `E:/KnowledgeHub/.gitignore`
- Create: `E:/KnowledgeHub/khub/__init__.py`
- Create: `E:/KnowledgeHub/tests/__init__.py`
- Create: 디렉토리 트리 (notes/, mirrors/, artifacts/, projects/, .agents/, .obsidian/, .index/)

- [ ] **Step 1: 디렉토리 트리 생성**

```bash
mkdir -p E:/KnowledgeHub/{khub/adapters,.agents,.obsidian,.index,projects,notes,mirrors/{wesang,build,fermion},artifacts/{fermion,dnt,shared},tests/{fixtures/sample_handovers,test_adapters}}
```

- [ ] **Step 2: pyproject.toml 작성**

```toml
# E:/KnowledgeHub/pyproject.toml
[project]
name = "knowledgehub"
version = "0.1.0"
description = "DnT KnowledgeHub - Experience-based knowledge accumulation"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "python-frontmatter>=1.0",
    "watchdog>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
]

[project.scripts]
k = "khub.cli:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

- [ ] **Step 3: .gitignore 작성**

```
# E:/KnowledgeHub/.gitignore
.index/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
*.egg-info/
mirrors/_quarantine/
```

- [ ] **Step 4: README.md 작성**

```markdown
# DnT KnowledgeHub

종일군의 사고·세션·테스트·교훈을 자동 축적하는 메타 지식 베이스.

## 사용
- 쓰기: Claude Code에서 `/k-capture`, `/k-journal`, `/k-feedback` 등
- 읽기: Obsidian에서 이 디렉토리를 vault로 열기

## 구조
- `notes/` - 7종 노드 본체
- `mirrors/` - 외부 프로젝트 핸드오버 미러 (자동 생성)
- `artifacts/` - 스크린샷, CSV, 차트 원본
- `projects/` - 프로젝트 랜딩 페이지
- `khub/` - Python CLI 및 인덱서
- `.index/` - SQLite FTS5 인덱스 (재생성 가능)

## 설정
```bash
cd E:/KnowledgeHub
pip install -e ".[dev]"
python -m khub.cli init
```

자세한 내용: `E:/DnT/DnT_WesangGoon/docs/superpowers/specs/2026-04-07-knowledge-hub-design.md`
```

- [ ] **Step 5: 빈 패키지 초기화**

```python
# E:/KnowledgeHub/khub/__init__.py
"""KnowledgeHub - DnT 지식 베이스."""
__version__ = "0.1.0"
```

```python
# E:/KnowledgeHub/tests/__init__.py
```

- [ ] **Step 6: pip 설치 및 확인**

```bash
cd E:/KnowledgeHub
pip install -e ".[dev]"
```

Expected: `Successfully installed knowledgehub-0.1.0 ...`

- [ ] **Step 7: pytest 실행 가능 확인**

```bash
cd E:/KnowledgeHub && pytest --collect-only
```

Expected: `no tests ran` (아직 테스트 없음, 에러 없이 실행되면 OK)

- [ ] **Step 8: Commit**

```bash
cd E:/KnowledgeHub
git init
git add .
git commit -m "feat: initialize KnowledgeHub project structure"
```

---

## Task 2: 노드/엣지 스키마 정의

**Files:**
- Create: `E:/KnowledgeHub/khub/schema.py`
- Test: `E:/KnowledgeHub/tests/test_schema.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_schema.py
import pytest
from datetime import datetime
from khub.schema import NodeType, EdgeRelation, Node, Edge, generate_node_id

def test_node_type_enum_has_seven_values():
    expected = {"idea", "task", "session", "test_run", "session_journal", "lesson", "feedback"}
    assert {t.value for t in NodeType} == expected

def test_edge_relation_enum_has_eight_values():
    expected = {"spawns", "executed_in", "produces", "produces_journal",
                "distilled_into", "feedback_by", "contradicts", "generalizes_into"}
    assert {r.value for r in EdgeRelation} == expected

def test_generate_node_id_format():
    nid = generate_node_id(NodeType.IDEA, datetime(2026, 4, 7, 14, 20))
    assert nid.startswith("idea-20260407-")
    assert len(nid) == len("idea-20260407-") + 6  # 6-char hash

def test_node_creation():
    n = Node(
        id="idea-20260407-a3b5c2",
        type=NodeType.IDEA,
        project="DnT_Game",
        title="ItemSlotBar 스프링 재튜닝",
        file_path="notes/2026-04-07_idea_spring.md",
        created=datetime(2026, 4, 7, 14, 20),
        updated=datetime(2026, 4, 7, 14, 20),
        agent_owner="jongil",
        tags=["motion", "spring"],
    )
    assert n.id == "idea-20260407-a3b5c2"
    assert n.type == NodeType.IDEA
    assert "motion" in n.tags

def test_edge_creation():
    e = Edge(
        source_id="idea-20260407-a3b5c2",
        target_id="task-20260407-q011xx",
        relation=EdgeRelation.SPAWNS,
    )
    assert e.relation == EdgeRelation.SPAWNS
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'khub.schema'`

- [ ] **Step 3: schema.py 구현**

```python
# E:/KnowledgeHub/khub/schema.py
"""노드/엣지 스키마 정의."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Optional
import secrets


class NodeType(str, Enum):
    IDEA = "idea"
    TASK = "task"
    SESSION = "session"
    TEST_RUN = "test_run"
    SESSION_JOURNAL = "session_journal"
    LESSON = "lesson"
    FEEDBACK = "feedback"


class EdgeRelation(str, Enum):
    SPAWNS = "spawns"
    EXECUTED_IN = "executed_in"
    PRODUCES = "produces"
    PRODUCES_JOURNAL = "produces_journal"
    DISTILLED_INTO = "distilled_into"
    FEEDBACK_BY = "feedback_by"
    CONTRADICTS = "contradicts"
    GENERALIZES_INTO = "generalizes_into"


@dataclass
class Node:
    id: str
    type: NodeType
    project: Optional[str]
    title: str
    file_path: str
    created: datetime
    updated: datetime
    agent_owner: Optional[str] = None
    agent_role: Optional[str] = None        # director|specialist|recorder|reviewer
    agent_project: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    source_path: Optional[str] = None       # 미러일 때만
    
    # 타입별 조회 가속 필드
    status: Optional[str] = None
    priority: Optional[str] = None
    test_category: Optional[str] = None
    generality: Optional[str] = None
    external_id: Optional[str] = None
    
    raw_frontmatter: dict = field(default_factory=dict)


@dataclass
class Edge:
    source_id: str
    target_id: str
    relation: EdgeRelation
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None


def generate_node_id(node_type: NodeType, when: datetime) -> str:
    """타입-날짜-짧은해시 형식의 노드 ID 생성."""
    date_str = when.strftime("%Y%m%d")
    short_hash = secrets.token_hex(3)  # 6 hex chars
    return f"{node_type.value}-{date_str}-{short_hash}"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_schema.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add khub/schema.py tests/test_schema.py
git commit -m "feat: add node/edge schema definitions"
```

---

## Task 3: SQLite DB 초기화 + 7개 테이블

**Files:**
- Create: `E:/KnowledgeHub/khub/db.py`
- Create: `E:/KnowledgeHub/tests/conftest.py`
- Test: `E:/KnowledgeHub/tests/test_db.py`

- [ ] **Step 1: conftest.py 작성 (테스트 fixtures)**

```python
# E:/KnowledgeHub/tests/conftest.py
import pytest
from pathlib import Path
from khub.db import init_db, get_connection

@pytest.fixture
def tmp_db(tmp_path):
    """임시 DB 경로 반환."""
    db_path = tmp_path / "test_wiki.db"
    init_db(db_path)
    return db_path

@pytest.fixture
def db_conn(tmp_db):
    """초기화된 DB 연결 반환."""
    conn = get_connection(tmp_db)
    yield conn
    conn.close()
```

- [ ] **Step 2: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_db.py
import sqlite3
import pytest
from khub.db import init_db, get_connection

EXPECTED_TABLES = {
    "nodes", "edges", "tags", "nodes_fts",
    "mirrors", "sync_state", "friction_patterns", "artifacts",
    # FTS5 내부 테이블 추가
    "nodes_fts_data", "nodes_fts_idx", "nodes_fts_docsize", "nodes_fts_config"
}

def test_init_db_creates_file(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    assert db_path.exists()

def test_init_db_creates_all_tables(tmp_db):
    conn = get_connection(tmp_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual = {row[0] for row in cur.fetchall()}
    missing = EXPECTED_TABLES - actual
    assert not missing, f"Missing tables: {missing}"

def test_init_db_idempotent(tmp_path):
    """init_db를 두 번 호출해도 에러 없어야 함."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    init_db(db_path)  # should not raise

def test_fts5_available(tmp_db):
    conn = get_connection(tmp_db)
    conn.execute("INSERT INTO nodes_fts(id, type, project, title, body, tags_concat) VALUES ('x', 'idea', 'p', 'hello world', 'body', 'tag1')")
    cur = conn.execute("SELECT id FROM nodes_fts WHERE nodes_fts MATCH 'hello'")
    assert cur.fetchone()[0] == 'x'
```

- [ ] **Step 3: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_db.py -v
```

Expected: FAIL (`ModuleNotFoundError: No module named 'khub.db'`)

- [ ] **Step 4: db.py 구현**

```python
# E:/KnowledgeHub/khub/db.py
"""SQLite DB 초기화 + 연결 관리."""
from __future__ import annotations
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("E:/KnowledgeHub/.index/wiki.db")

SCHEMA_SQL = """
-- 1. 노드 테이블
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    project TEXT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    created TEXT NOT NULL,
    updated TEXT NOT NULL,
    agent_owner TEXT,
    agent_role TEXT,
    agent_project TEXT,
    tags TEXT,
    status TEXT,
    priority TEXT,
    test_category TEXT,
    generality TEXT,
    external_id TEXT,
    source_path TEXT,
    raw_frontmatter TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_type_project ON nodes(type, project);
CREATE INDEX IF NOT EXISTS idx_nodes_created      ON nodes(created DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_status       ON nodes(status) WHERE status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_nodes_owner        ON nodes(agent_owner);

-- 2. 엣지 테이블
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now')),
    metadata TEXT,
    UNIQUE(source_id, target_id, relation),
    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id, relation);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id, relation);

-- 3. 태그 테이블
CREATE TABLE IF NOT EXISTS tags (
    node_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (node_id, tag),
    FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- 4. FTS5 전문검색
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    id UNINDEXED,
    type UNINDEXED,
    project UNINDEXED,
    title,
    body,
    tags_concat,
    tokenize='unicode61'
);

-- 5. 외부 미러 동기화
CREATE TABLE IF NOT EXISTS mirrors (
    source_path TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    last_synced TEXT NOT NULL,
    adapter TEXT NOT NULL,
    protected INTEGER DEFAULT 0,
    source_missing INTEGER DEFAULT 0,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

CREATE TABLE IF NOT EXISTS sync_state (
    source_root TEXT PRIMARY KEY,
    adapter_name TEXT,
    last_scan TEXT NOT NULL,
    last_file_mtime TEXT
);

-- 6. friction_patterns
CREATE TABLE IF NOT EXISTS friction_patterns (
    pattern_hash TEXT PRIMARY KEY,
    pattern_text TEXT NOT NULL,
    pattern_type TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    source_journals TEXT,
    promoted_to_tems INTEGER DEFAULT 0,
    tems_db TEXT,
    tems_rule_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_friction_count ON friction_patterns(occurrence_count DESC);

-- 7. artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    path TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    created TEXT NOT NULL,
    size_bytes INTEGER,
    description TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
CREATE INDEX IF NOT EXISTS idx_artifacts_node ON artifacts(node_id);
"""


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """DB 초기화 + 7개 테이블 생성."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """DB 연결 반환 (Foreign keys 활성화)."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_db.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add khub/db.py tests/conftest.py tests/test_db.py
git commit -m "feat: add SQLite schema with 7 tables + FTS5"
```

---

## Task 4: frontmatter I/O (YAML 파싱/직렬화)

**Files:**
- Create: `E:/KnowledgeHub/khub/frontmatter_io.py`
- Test: `E:/KnowledgeHub/tests/test_frontmatter_io.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_frontmatter_io.py
import pytest
from pathlib import Path
from khub.frontmatter_io import parse_file, write_file, FrontmatterError

SAMPLE_MD = """---
id: idea-20260407-a3b5c2
type: idea
project: DnT_Game
title: "ItemSlotBar 스프링 재튜닝"
created: 2026-04-07T14:20:00+09:00
tags: [motion, spring]
---

본문 내용입니다.
"""

def test_parse_file(tmp_path):
    p = tmp_path / "test.md"
    p.write_text(SAMPLE_MD, encoding="utf-8")
    fm, body = parse_file(p)
    assert fm["id"] == "idea-20260407-a3b5c2"
    assert fm["type"] == "idea"
    assert fm["tags"] == ["motion", "spring"]
    assert "본문 내용입니다" in body

def test_write_file(tmp_path):
    p = tmp_path / "out.md"
    fm = {
        "id": "task-20260407-q011xx",
        "type": "task",
        "project": "DnT_Game",
        "title": "Q-011",
        "tags": ["spring"],
    }
    body = "태스크 본문"
    write_file(p, fm, body)
    assert p.exists()
    fm2, body2 = parse_file(p)
    assert fm2["id"] == fm["id"]
    assert "태스크 본문" in body2

def test_parse_file_no_frontmatter(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text("그냥 텍스트만 있음", encoding="utf-8")
    with pytest.raises(FrontmatterError):
        parse_file(p)

def test_parse_file_invalid_yaml(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text("---\n[broken yaml\n---\nbody\n", encoding="utf-8")
    with pytest.raises(FrontmatterError):
        parse_file(p)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_frontmatter_io.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: frontmatter_io.py 구현**

```python
# E:/KnowledgeHub/khub/frontmatter_io.py
"""마크다운 frontmatter 읽기/쓰기."""
from __future__ import annotations
from pathlib import Path
import yaml


class FrontmatterError(Exception):
    pass


def parse_file(path: Path) -> tuple[dict, str]:
    """파일을 읽어 (frontmatter dict, body str) 반환."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise FrontmatterError(f"No frontmatter delimiter at start of {path}")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise FrontmatterError(f"Frontmatter not properly closed in {path}")
    _, fm_text, body = parts
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise FrontmatterError(f"YAML parse error in {path}: {e}") from e
    return fm, body.lstrip("\n")


def write_file(path: Path, frontmatter: dict, body: str) -> None:
    """frontmatter dict + body string을 마크다운 파일로 저장."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm_text = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    content = f"---\n{fm_text}---\n\n{body}"
    path.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_frontmatter_io.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add khub/frontmatter_io.py tests/test_frontmatter_io.py
git commit -m "feat: add frontmatter I/O with error handling"
```

---

## Task 5: 노드 CRUD

**Files:**
- Create: `E:/KnowledgeHub/khub/nodes.py`
- Test: `E:/KnowledgeHub/tests/test_nodes.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_nodes.py
import pytest
import json
from datetime import datetime
from khub.schema import Node, NodeType, generate_node_id
from khub.db import get_connection
from khub.nodes import insert_node, get_node, update_node, delete_node, list_nodes

@pytest.fixture
def sample_node():
    now = datetime(2026, 4, 7, 14, 20)
    return Node(
        id="idea-20260407-a3b5c2",
        type=NodeType.IDEA,
        project="DnT_Game",
        title="스프링 재튜닝",
        file_path="notes/2026-04-07_idea_spring.md",
        created=now,
        updated=now,
        agent_owner="jongil",
        tags=["motion", "spring"],
        raw_frontmatter={"actionability": 7, "hypothesis": "stiffness 부족"},
    )

def test_insert_and_get_node(tmp_db, sample_node):
    conn = get_connection(tmp_db)
    insert_node(conn, sample_node)
    n = get_node(conn, sample_node.id)
    assert n is not None
    assert n.id == sample_node.id
    assert n.type == NodeType.IDEA
    assert n.tags == ["motion", "spring"]
    assert n.raw_frontmatter["actionability"] == 7

def test_get_node_not_found(tmp_db):
    conn = get_connection(tmp_db)
    assert get_node(conn, "nonexistent-id") is None

def test_update_node(tmp_db, sample_node):
    conn = get_connection(tmp_db)
    insert_node(conn, sample_node)
    sample_node.title = "수정된 제목"
    update_node(conn, sample_node)
    n = get_node(conn, sample_node.id)
    assert n.title == "수정된 제목"

def test_delete_node(tmp_db, sample_node):
    conn = get_connection(tmp_db)
    insert_node(conn, sample_node)
    delete_node(conn, sample_node.id)
    assert get_node(conn, sample_node.id) is None

def test_list_nodes_by_type(tmp_db, sample_node):
    conn = get_connection(tmp_db)
    insert_node(conn, sample_node)
    results = list_nodes(conn, type=NodeType.IDEA)
    assert len(results) == 1
    assert results[0].id == sample_node.id

def test_list_nodes_by_project(tmp_db, sample_node):
    conn = get_connection(tmp_db)
    insert_node(conn, sample_node)
    results = list_nodes(conn, project="DnT_Game")
    assert len(results) == 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_nodes.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: nodes.py 구현**

```python
# E:/KnowledgeHub/khub/nodes.py
"""노드 CRUD 고수준 API."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from typing import Optional
from .schema import Node, NodeType


def _row_to_node(row: sqlite3.Row) -> Node:
    return Node(
        id=row["id"],
        type=NodeType(row["type"]),
        project=row["project"],
        title=row["title"],
        file_path=row["file_path"],
        created=datetime.fromisoformat(row["created"]),
        updated=datetime.fromisoformat(row["updated"]),
        agent_owner=row["agent_owner"],
        agent_role=row["agent_role"],
        agent_project=row["agent_project"],
        tags=row["tags"].split(" ") if row["tags"] else [],
        status=row["status"],
        priority=row["priority"],
        test_category=row["test_category"],
        generality=row["generality"],
        external_id=row["external_id"],
        source_path=row["source_path"],
        raw_frontmatter=json.loads(row["raw_frontmatter"]) if row["raw_frontmatter"] else {},
    )


def insert_node(conn: sqlite3.Connection, node: Node) -> None:
    conn.execute("""
        INSERT INTO nodes (
            id, type, project, title, file_path, created, updated,
            agent_owner, agent_role, agent_project, tags,
            status, priority, test_category, generality, external_id, source_path,
            raw_frontmatter
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        node.id, node.type.value, node.project, node.title, node.file_path,
        node.created.isoformat(), node.updated.isoformat(),
        node.agent_owner, node.agent_role, node.agent_project,
        " ".join(node.tags),
        node.status, node.priority, node.test_category, node.generality,
        node.external_id, node.source_path,
        json.dumps(node.raw_frontmatter, ensure_ascii=False),
    ))
    # 태그 테이블에도 삽입
    for tag in node.tags:
        conn.execute("INSERT OR IGNORE INTO tags (node_id, tag) VALUES (?, ?)",
                     (node.id, tag))
    conn.commit()


def get_node(conn: sqlite3.Connection, node_id: str) -> Optional[Node]:
    cur = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    row = cur.fetchone()
    return _row_to_node(row) if row else None


def update_node(conn: sqlite3.Connection, node: Node) -> None:
    node.updated = datetime.now()
    conn.execute("""
        UPDATE nodes SET
            type=?, project=?, title=?, file_path=?, updated=?,
            agent_owner=?, agent_role=?, agent_project=?, tags=?,
            status=?, priority=?, test_category=?, generality=?, external_id=?, source_path=?,
            raw_frontmatter=?
        WHERE id=?
    """, (
        node.type.value, node.project, node.title, node.file_path,
        node.updated.isoformat(),
        node.agent_owner, node.agent_role, node.agent_project,
        " ".join(node.tags),
        node.status, node.priority, node.test_category, node.generality,
        node.external_id, node.source_path,
        json.dumps(node.raw_frontmatter, ensure_ascii=False),
        node.id,
    ))
    # 태그 갱신
    conn.execute("DELETE FROM tags WHERE node_id = ?", (node.id,))
    for tag in node.tags:
        conn.execute("INSERT OR IGNORE INTO tags (node_id, tag) VALUES (?, ?)",
                     (node.id, tag))
    conn.commit()


def delete_node(conn: sqlite3.Connection, node_id: str) -> None:
    conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    conn.commit()


def list_nodes(
    conn: sqlite3.Connection,
    type: Optional[NodeType] = None,
    project: Optional[str] = None,
    agent_owner: Optional[str] = None,
    limit: int = 100,
) -> list[Node]:
    query = "SELECT * FROM nodes WHERE 1=1"
    params = []
    if type:
        query += " AND type = ?"
        params.append(type.value)
    if project:
        query += " AND project = ?"
        params.append(project)
    if agent_owner:
        query += " AND agent_owner = ?"
        params.append(agent_owner)
    query += " ORDER BY created DESC LIMIT ?"
    params.append(limit)
    cur = conn.execute(query, params)
    return [_row_to_node(row) for row in cur.fetchall()]
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_nodes.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add khub/nodes.py tests/test_nodes.py
git commit -m "feat: add node CRUD API"
```

---

## Task 6: 엣지 CRUD

**Files:**
- Create: `E:/KnowledgeHub/khub/edges.py`
- Test: `E:/KnowledgeHub/tests/test_edges.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_edges.py
import pytest
from datetime import datetime
from khub.schema import Node, NodeType, Edge, EdgeRelation
from khub.db import get_connection
from khub.nodes import insert_node
from khub.edges import insert_edge, get_edges_from, get_edges_to, delete_edge, get_neighbors

@pytest.fixture
def two_nodes(tmp_db):
    conn = get_connection(tmp_db)
    now = datetime(2026, 4, 7, 14, 20)
    n1 = Node(id="idea-1", type=NodeType.IDEA, project="DnT_Game",
              title="아이디어", file_path="notes/idea.md",
              created=now, updated=now)
    n2 = Node(id="task-1", type=NodeType.TASK, project="DnT_Game",
              title="태스크", file_path="notes/task.md",
              created=now, updated=now)
    insert_node(conn, n1)
    insert_node(conn, n2)
    return conn, n1, n2

def test_insert_and_query_edge(two_nodes):
    conn, n1, n2 = two_nodes
    e = Edge(source_id=n1.id, target_id=n2.id, relation=EdgeRelation.SPAWNS)
    insert_edge(conn, e)
    edges = get_edges_from(conn, n1.id)
    assert len(edges) == 1
    assert edges[0].relation == EdgeRelation.SPAWNS
    assert edges[0].target_id == n2.id

def test_get_edges_to(two_nodes):
    conn, n1, n2 = two_nodes
    insert_edge(conn, Edge(n1.id, n2.id, EdgeRelation.SPAWNS))
    edges = get_edges_to(conn, n2.id)
    assert len(edges) == 1
    assert edges[0].source_id == n1.id

def test_unique_constraint(two_nodes):
    """동일 (source, target, relation) 중복 삽입 시 무시."""
    conn, n1, n2 = two_nodes
    e = Edge(n1.id, n2.id, EdgeRelation.SPAWNS)
    insert_edge(conn, e)
    insert_edge(conn, e)  # 두 번째는 무시
    edges = get_edges_from(conn, n1.id)
    assert len(edges) == 1

def test_delete_edge(two_nodes):
    conn, n1, n2 = two_nodes
    insert_edge(conn, Edge(n1.id, n2.id, EdgeRelation.SPAWNS))
    delete_edge(conn, n1.id, n2.id, EdgeRelation.SPAWNS)
    assert len(get_edges_from(conn, n1.id)) == 0

def test_get_neighbors(two_nodes):
    conn, n1, n2 = two_nodes
    insert_edge(conn, Edge(n1.id, n2.id, EdgeRelation.SPAWNS))
    neighbors = get_neighbors(conn, n1.id, depth=1)
    assert n2.id in [n.id for n in neighbors]

def test_cascade_delete_on_node_deletion(two_nodes):
    """노드 삭제 시 엣지 자동 삭제."""
    from khub.nodes import delete_node
    conn, n1, n2 = two_nodes
    insert_edge(conn, Edge(n1.id, n2.id, EdgeRelation.SPAWNS))
    delete_node(conn, n1.id)
    assert len(get_edges_from(conn, n1.id)) == 0
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_edges.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: edges.py 구현**

```python
# E:/KnowledgeHub/khub/edges.py
"""엣지 CRUD + 그래프 탐색."""
from __future__ import annotations
import json
import sqlite3
from typing import Optional
from .schema import Edge, EdgeRelation, Node, NodeType
from .nodes import _row_to_node, get_node


def insert_edge(conn: sqlite3.Connection, edge: Edge) -> None:
    """엣지 삽입. 중복(UNIQUE 제약)은 무시."""
    try:
        conn.execute("""
            INSERT INTO edges (source_id, target_id, relation, weight, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            edge.source_id, edge.target_id, edge.relation.value,
            edge.weight, json.dumps(edge.metadata, ensure_ascii=False),
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # 중복 무시


def _row_to_edge(row: sqlite3.Row) -> Edge:
    from datetime import datetime
    return Edge(
        source_id=row["source_id"],
        target_id=row["target_id"],
        relation=EdgeRelation(row["relation"]),
        weight=row["weight"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
    )


def get_edges_from(
    conn: sqlite3.Connection, source_id: str, relation: Optional[EdgeRelation] = None
) -> list[Edge]:
    if relation:
        cur = conn.execute(
            "SELECT * FROM edges WHERE source_id = ? AND relation = ?",
            (source_id, relation.value),
        )
    else:
        cur = conn.execute("SELECT * FROM edges WHERE source_id = ?", (source_id,))
    return [_row_to_edge(row) for row in cur.fetchall()]


def get_edges_to(
    conn: sqlite3.Connection, target_id: str, relation: Optional[EdgeRelation] = None
) -> list[Edge]:
    if relation:
        cur = conn.execute(
            "SELECT * FROM edges WHERE target_id = ? AND relation = ?",
            (target_id, relation.value),
        )
    else:
        cur = conn.execute("SELECT * FROM edges WHERE target_id = ?", (target_id,))
    return [_row_to_edge(row) for row in cur.fetchall()]


def delete_edge(
    conn: sqlite3.Connection, source_id: str, target_id: str, relation: EdgeRelation
) -> None:
    conn.execute(
        "DELETE FROM edges WHERE source_id = ? AND target_id = ? AND relation = ?",
        (source_id, target_id, relation.value),
    )
    conn.commit()


def get_neighbors(
    conn: sqlite3.Connection,
    node_id: str,
    relation: Optional[EdgeRelation] = None,
    depth: int = 1,
    direction: str = "both",  # "out" | "in" | "both"
) -> list[Node]:
    """노드의 이웃 노드 반환 (depth 단계, 양방향)."""
    visited = {node_id}
    frontier = {node_id}
    for _ in range(depth):
        next_frontier = set()
        for nid in frontier:
            if direction in ("out", "both"):
                for e in get_edges_from(conn, nid, relation):
                    if e.target_id not in visited:
                        next_frontier.add(e.target_id)
                        visited.add(e.target_id)
            if direction in ("in", "both"):
                for e in get_edges_to(conn, nid, relation):
                    if e.source_id not in visited:
                        next_frontier.add(e.source_id)
                        visited.add(e.source_id)
        frontier = next_frontier
        if not frontier:
            break
    visited.discard(node_id)
    return [n for n in (get_node(conn, nid) for nid in visited) if n is not None]
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_edges.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add khub/edges.py tests/test_edges.py
git commit -m "feat: add edge CRUD + graph neighbors traversal"
```

---

## Task 7: FTS5 검색 (BM25)

**Files:**
- Create: `E:/KnowledgeHub/khub/search.py`
- Test: `E:/KnowledgeHub/tests/test_search.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_search.py
import pytest
from datetime import datetime
from khub.schema import Node, NodeType
from khub.db import get_connection
from khub.nodes import insert_node
from khub.search import index_node_body, search, search_filtered

@pytest.fixture
def populated_db(tmp_db):
    conn = get_connection(tmp_db)
    now = datetime(2026, 4, 7, 14, 20)
    n1 = Node(id="idea-1", type=NodeType.IDEA, project="DnT_Game",
              title="ItemSlotBar 스프링 재튜닝", file_path="notes/idea1.md",
              created=now, updated=now, tags=["motion", "spring"])
    n2 = Node(id="lesson-1", type=NodeType.LESSON, project="DnT_Game",
              title="motion baseline", file_path="notes/lesson1.md",
              created=now, updated=now, tags=["motion"])
    insert_node(conn, n1)
    insert_node(conn, n2)
    index_node_body(conn, n1.id, "스프링 stiffness 값 재조정 필요")
    index_node_body(conn, n2.id, "DnT UI 드래그는 stiffness 250~280 기본")
    return conn

def test_search_basic(populated_db):
    results = search(populated_db, "스프링")
    assert len(results) >= 1
    assert any(r["id"] == "idea-1" for r in results)

def test_search_filter_type(populated_db):
    results = search_filtered(populated_db, "stiffness", type="lesson")
    assert all(r["type"] == "lesson" for r in results)

def test_search_filter_project(populated_db):
    results = search_filtered(populated_db, "stiffness", project="DnT_Game")
    assert len(results) >= 1

def test_search_no_match(populated_db):
    results = search(populated_db, "전혀없는단어xyz")
    assert results == []
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_search.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: search.py 구현**

```python
# E:/KnowledgeHub/khub/search.py
"""FTS5 BM25 검색."""
from __future__ import annotations
import sqlite3
from typing import Optional


def index_node_body(conn: sqlite3.Connection, node_id: str, body: str) -> None:
    """노드 본문을 FTS5 인덱스에 삽입/갱신."""
    cur = conn.execute("SELECT type, project, title, tags FROM nodes WHERE id = ?", (node_id,))
    row = cur.fetchone()
    if not row:
        return
    # 기존 인덱스 제거 후 재삽입
    conn.execute("DELETE FROM nodes_fts WHERE id = ?", (node_id,))
    conn.execute("""
        INSERT INTO nodes_fts (id, type, project, title, body, tags_concat)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (node_id, row["type"], row["project"], row["title"], body, row["tags"] or ""))
    conn.commit()


def search(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[dict]:
    """기본 FTS5 BM25 검색."""
    try:
        cur = conn.execute("""
            SELECT id, type, project, title, snippet(nodes_fts, 4, '<<', '>>', '...', 32) as snippet
            FROM nodes_fts
            WHERE nodes_fts MATCH ?
            ORDER BY bm25(nodes_fts)
            LIMIT ?
        """, (query, limit))
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.OperationalError:
        return []


def search_filtered(
    conn: sqlite3.Connection,
    query: str,
    type: Optional[str] = None,
    project: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """필터 적용 FTS5 검색."""
    where = ["nodes_fts MATCH ?"]
    params: list = [query]
    if type:
        where.append("type = ?")
        params.append(type)
    if project:
        where.append("project = ?")
        params.append(project)
    sql = f"""
        SELECT id, type, project, title, snippet(nodes_fts, 4, '<<', '>>', '...', 32) as snippet
        FROM nodes_fts
        WHERE {' AND '.join(where)}
        ORDER BY bm25(nodes_fts)
        LIMIT ?
    """
    params.append(limit)
    try:
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_search.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add khub/search.py tests/test_search.py
git commit -m "feat: add FTS5 BM25 search with type/project filters"
```

---

## Task 8: BaseAdapter 인터페이스

**Files:**
- Create: `E:/KnowledgeHub/khub/adapters/__init__.py`
- Create: `E:/KnowledgeHub/khub/adapters/base.py`
- Create: `E:/KnowledgeHub/tests/test_adapters/__init__.py`

- [ ] **Step 1: adapters 패키지 초기화**

```python
# E:/KnowledgeHub/khub/adapters/__init__.py
"""외부 원본 → 미러 어댑터."""
from .base import BaseAdapter, ParsedNode

__all__ = ["BaseAdapter", "ParsedNode"]
```

```python
# E:/KnowledgeHub/tests/test_adapters/__init__.py
```

- [ ] **Step 2: base.py 구현**

```python
# E:/KnowledgeHub/khub/adapters/base.py
"""어댑터 공통 인터페이스."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ParsedNode:
    """어댑터 파싱 결과."""
    type: str                            # session | test_run | ...
    project: str
    title: str
    summary: str                         # 200자 내외 요약
    extracted_entities: dict             # {"tasks": [...], "handoffs": [...], ...}
    raw_content: str                     # 원본 본문 (FTS5 인덱싱용)
    source_metadata: dict = field(default_factory=dict)
    agent_owner: Optional[str] = None
    agent_role: Optional[str] = None


class BaseAdapter(ABC):
    """모든 어댑터가 상속할 베이스 클래스."""
    name: str = "base"
    source_roots: list[Path] = []
    file_pattern: str = "*.md"

    @abstractmethod
    def discover(self, since: Optional[datetime] = None) -> list[Path]:
        """since 이후 수정/추가된 원본 파일 탐지."""
        ...

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedNode:
        """원본 → ParsedNode."""
        ...

    def matches(self, file_path: Path) -> bool:
        """이 어댑터가 해당 파일을 처리할 수 있는지."""
        return any(
            file_path.is_relative_to(root) for root in self.source_roots
        ) and file_path.match(self.file_pattern)
```

- [ ] **Step 3: import 검증**

```bash
cd E:/KnowledgeHub && python -c "from khub.adapters import BaseAdapter, ParsedNode; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add khub/adapters/ tests/test_adapters/
git commit -m "feat: add BaseAdapter interface for external source ingestion"
```

---

## Task 9: claude_standard 어댑터 (Phase 1 통합 어댑터)

**Files:**
- Create: `E:/KnowledgeHub/khub/adapters/claude_standard.py`
- Create: `E:/KnowledgeHub/tests/fixtures/sample_handovers/wesang_session16.md`
- Create: `E:/KnowledgeHub/tests/fixtures/sample_handovers/build_handoff.md`
- Create: `E:/KnowledgeHub/tests/fixtures/sample_handovers/fermion_session1.md`
- Test: `E:/KnowledgeHub/tests/test_adapters/test_claude_standard.py`

- [ ] **Step 1: 픽스처 작성 (실제 핸드오버 발췌)**

```markdown
<!-- E:/KnowledgeHub/tests/fixtures/sample_handovers/wesang_session16.md -->
# 위상군 세션 핸드오버 — 2026-03-29 Session 16

## 세션 요약
아트 파이프라인 전면 수립 + UI 스킨 전환 + 레이아웃 리사이즈.

## 논의 및 결정

### 1. Phase A: CSS 스킨 전환 (HO-005) → 완료
- 디자인 토큰 15개 CSS 변수
- **빌드군 완료 (Q-006)**

### 2. ItemSlotBar 하단 중앙 (HO-007) → 완료
- **빌드군 완료 (Q-008)**

## 미완료 사항
| ID | 작업 | 담당 | 상태 |
|----|------|------|------|
| Q-002 | SidePanel crossfade 검증 | 빌드군 | P0 대기 |
| Q-010 | UI_ELEMENT_CATALOG 기반 P0 에셋 | 아트군 | P0 대기 |
```

```markdown
<!-- E:/KnowledgeHub/tests/fixtures/sample_handovers/build_handoff.md -->
# Build 핸드오프 HO-005

## 작업 내용
Phase A CSS 스킨 전환 완료. tokens.css 신규.

## 관련 태스크
- Q-006 완료
```

```markdown
<!-- E:/KnowledgeHub/tests/fixtures/sample_handovers/fermion_session1.md -->
# Fermion Session 1

## 요약
COMPASS V4 백테스트 진행. 수익률 87.6%, MDD -19.2%.

## 결정
- L3 weights {VIX:0.3, M2:0.4, SOXX:0.3} 유지
```

- [ ] **Step 2: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_adapters/test_claude_standard.py
import pytest
from pathlib import Path
from khub.adapters.claude_standard import ClaudeStandardAdapter

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sample_handovers"

@pytest.fixture
def adapter(tmp_path):
    return ClaudeStandardAdapter(source_roots=[tmp_path])

def test_parse_wesang_session16():
    a = ClaudeStandardAdapter(source_roots=[FIXTURES])
    parsed = a.parse(FIXTURES / "wesang_session16.md")
    assert parsed.type == "session"
    assert "아트 파이프라인" in parsed.summary or "스킨" in parsed.summary
    assert "Q-002" in parsed.extracted_entities["tasks"]
    assert "Q-010" in parsed.extracted_entities["tasks"]
    assert "HO-005" in parsed.extracted_entities["handoffs"]
    assert "HO-007" in parsed.extracted_entities["handoffs"]

def test_parse_build_handoff():
    a = ClaudeStandardAdapter(source_roots=[FIXTURES])
    parsed = a.parse(FIXTURES / "build_handoff.md")
    assert "HO-005" in parsed.title or "HO-005" in parsed.raw_content
    assert "Q-006" in parsed.extracted_entities["tasks"]

def test_parse_fermion_session1():
    a = ClaudeStandardAdapter(source_roots=[FIXTURES])
    parsed = a.parse(FIXTURES / "fermion_session1.md")
    assert "COMPASS" in parsed.raw_content

def test_discover_finds_md_files(tmp_path):
    (tmp_path / "a.md").write_text("# test", encoding="utf-8")
    (tmp_path / "b.txt").write_text("not md", encoding="utf-8")
    a = ClaudeStandardAdapter(source_roots=[tmp_path])
    found = a.discover()
    assert len(found) == 1
    assert found[0].name == "a.md"
```

- [ ] **Step 3: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_adapters/test_claude_standard.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 4: claude_standard.py 구현**

```python
# E:/KnowledgeHub/khub/adapters/claude_standard.py
"""Claude Code 표준 핸드오버 포맷 어댑터.

위상군 / 빌드군 / Fermion 핸드오버를 공통으로 처리.
"""
from __future__ import annotations
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from .base import BaseAdapter, ParsedNode


# 엔티티 추출용 정규식
TASK_PATTERN = re.compile(r"\bQ-\d+\b")
HANDOFF_PATTERN = re.compile(r"\bHO-\d+\b")
SESSION_PATTERN = re.compile(r"Session\s*(\d+)", re.IGNORECASE)


class ClaudeStandardAdapter(BaseAdapter):
    name = "claude_standard"
    file_pattern = "*.md"

    def __init__(self, source_roots: Optional[list[Path]] = None, project: str = "DnT_Game"):
        self.source_roots = source_roots or []
        self.project = project

    def discover(self, since: Optional[datetime] = None) -> list[Path]:
        found = []
        for root in self.source_roots:
            if not root.exists():
                continue
            for md_path in root.rglob(self.file_pattern):
                if since:
                    mtime = datetime.fromtimestamp(md_path.stat().st_mtime)
                    if mtime <= since:
                        continue
                found.append(md_path)
        return sorted(found)

    def parse(self, file_path: Path) -> ParsedNode:
        text = file_path.read_text(encoding="utf-8")
        # 제목 추출 (첫 # 헤딩)
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else file_path.stem

        # 요약: "## 세션 요약" 다음 첫 문단 또는 첫 200자
        summary = self._extract_summary(text)

        # 엔티티 추출
        tasks = sorted(set(TASK_PATTERN.findall(text)))
        handoffs = sorted(set(HANDOFF_PATTERN.findall(text)))
        session_match = SESSION_PATTERN.search(text)
        session_number = int(session_match.group(1)) if session_match else None

        # 노드 타입 추론: 파일명에 'session'이 있으면 session, 'handoff' 또는 'HO-'면 task
        fname = file_path.name.lower()
        if "session" in fname or session_number is not None:
            node_type = "session"
        else:
            node_type = "session"  # Phase 1은 모두 session으로 통합 미러링

        # 에이전트 추론
        agent_owner = self._infer_agent(file_path)

        return ParsedNode(
            type=node_type,
            project=self.project,
            title=title,
            summary=summary,
            extracted_entities={
                "tasks": tasks,
                "handoffs": handoffs,
                "session_number": session_number,
            },
            raw_content=text,
            agent_owner=agent_owner,
            agent_role="director" if agent_owner == "wesang_goon" else "specialist",
            source_metadata={
                "source_file": str(file_path),
                "file_size": file_path.stat().st_size,
                "mtime": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            },
        )

    def _extract_summary(self, text: str) -> str:
        match = re.search(
            r"##\s*세션\s*요약\s*\n\n?(.+?)(?=\n##|\Z)",
            text, re.DOTALL,
        )
        if match:
            summary = match.group(1).strip()
            return summary[:200]
        return text[:200].strip()

    def _infer_agent(self, file_path: Path) -> str:
        path_str = str(file_path).replace("\\", "/").lower()
        if "wesang" in path_str:
            return "wesang_goon"
        if "mrv" in path_str or "build" in path_str:
            return "build_goon"
        if "fermion" in path_str:
            return "fermion"
        if "art" in path_str:
            return "art_goon"
        if "gihak" in path_str:
            return "gihak_goon"
        if "jaemi" in path_str:
            return "jaemi_goon"
        return "unknown"
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_adapters/test_claude_standard.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add khub/adapters/claude_standard.py tests/fixtures/ tests/test_adapters/
git commit -m "feat: add claude_standard adapter for handover parsing"
```

---

## Task 10: 미러 동기화 (mirror_sync)

**Files:**
- Create: `E:/KnowledgeHub/khub/mirror_sync.py`
- Test: `E:/KnowledgeHub/tests/test_mirror_sync.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_mirror_sync.py
import pytest
from pathlib import Path
from datetime import datetime
from khub.db import get_connection
from khub.adapters.claude_standard import ClaudeStandardAdapter
from khub.mirror_sync import sync_source_root, get_source_hash, create_mirror_stub

@pytest.fixture
def fake_source(tmp_path):
    src = tmp_path / "fake_handovers"
    src.mkdir()
    (src / "session1.md").write_text("# Session 1\n\n## 세션 요약\n첫 세션\n", encoding="utf-8")
    (src / "session2.md").write_text("# Session 2\n\n## 세션 요약\n두 번째\n", encoding="utf-8")
    return src

def test_get_source_hash(fake_source):
    h1 = get_source_hash(fake_source / "session1.md")
    h2 = get_source_hash(fake_source / "session1.md")
    assert h1 == h2  # 동일 파일 동일 해시
    assert len(h1) == 64  # SHA-256

def test_create_mirror_stub(tmp_path, fake_source):
    out_dir = tmp_path / "mirrors"
    a = ClaudeStandardAdapter(source_roots=[fake_source])
    parsed = a.parse(fake_source / "session1.md")
    stub_path = create_mirror_stub(parsed, out_dir, source_path=fake_source / "session1.md", source_hash="abc")
    assert stub_path.exists()
    text = stub_path.read_text(encoding="utf-8")
    assert "source_path:" in text
    assert "source_hash: abc" in text

def test_sync_source_root(tmp_db, tmp_path, fake_source):
    conn = get_connection(tmp_db)
    out_dir = tmp_path / "mirrors"
    a = ClaudeStandardAdapter(source_roots=[fake_source])
    count = sync_source_root(conn, a, fake_source, out_dir)
    assert count == 2  # 2개 파일 동기화
    # mirrors 테이블에 행 추가 확인
    cur = conn.execute("SELECT COUNT(*) FROM mirrors")
    assert cur.fetchone()[0] == 2

def test_sync_skips_unchanged(tmp_db, tmp_path, fake_source):
    """동일 해시 파일은 재동기화 건너뛴다."""
    conn = get_connection(tmp_db)
    out_dir = tmp_path / "mirrors"
    a = ClaudeStandardAdapter(source_roots=[fake_source])
    sync_source_root(conn, a, fake_source, out_dir)
    count2 = sync_source_root(conn, a, fake_source, out_dir)
    assert count2 == 0  # 두 번째 호출 시 변경 없음
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_mirror_sync.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: mirror_sync.py 구현**

```python
# E:/KnowledgeHub/khub/mirror_sync.py
"""외부 원본 → mirrors/ 증분 동기화."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from .adapters.base import BaseAdapter, ParsedNode
from .frontmatter_io import write_file
from .schema import Node, NodeType, generate_node_id
from .nodes import insert_node, get_node, update_node
from .search import index_node_body


def get_source_hash(path: Path) -> str:
    """파일의 SHA-256 해시 (변경 감지용)."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def create_mirror_stub(
    parsed: ParsedNode,
    mirror_dir: Path,
    source_path: Path,
    source_hash: str,
) -> Path:
    """ParsedNode → mirrors/<agent>/<filename>.stub.md"""
    agent_short = (parsed.agent_owner or "unknown").replace("_goon", "")
    target_dir = mirror_dir / agent_short
    target_dir.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem
    target_file = target_dir / f"{stem}.stub.md"

    now = datetime.now()
    nid = generate_node_id(NodeType.SESSION, now)
    fm = {
        "id": nid,
        "type": parsed.type,
        "project": parsed.project,
        "title": parsed.title,
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "agent_owner": parsed.agent_owner,
        "agent_role": parsed.agent_role,
        "source_path": str(source_path),
        "source_hash": source_hash,
        "imported_at": now.isoformat(),
        "summary": parsed.summary,
        "extracted_entities": parsed.extracted_entities,
    }
    body = (
        f"## 미러 요약\n\n{parsed.summary}\n\n"
        f"전체 본문 검색은 SQLite FTS5가 담당.\n"
        f"원본 열람: `{source_path}`\n"
    )
    write_file(target_file, fm, body)
    return target_file


def sync_source_root(
    conn: sqlite3.Connection,
    adapter: BaseAdapter,
    source_root: Path,
    mirror_dir: Path,
) -> int:
    """source_root의 모든 파일을 어댑터로 파싱하여 미러 생성. 동기화된 파일 수 반환."""
    synced = 0
    files = adapter.discover()
    for src_file in files:
        current_hash = get_source_hash(src_file)
        # mirrors 테이블 조회
        cur = conn.execute(
            "SELECT source_hash FROM mirrors WHERE source_path = ?",
            (str(src_file),),
        )
        row = cur.fetchone()
        if row and row["source_hash"] == current_hash:
            continue  # 변경 없음
        if row and row["source_hash"] != current_hash:
            # 사용자가 직접 편집했는지 확인 (protected 플래그)
            cur2 = conn.execute("SELECT protected FROM mirrors WHERE source_path = ?",
                                (str(src_file),))
            r2 = cur2.fetchone()
            if r2 and r2["protected"]:
                continue  # protected 미러는 건너뛰기

        # 파싱 + 미러 생성
        try:
            parsed = adapter.parse(src_file)
        except Exception as e:
            # 파싱 실패는 quarantine
            quarantine = mirror_dir / "_quarantine"
            quarantine.mkdir(parents=True, exist_ok=True)
            (quarantine / f"{src_file.stem}.error.txt").write_text(
                f"Parse error in {src_file}: {e}", encoding="utf-8"
            )
            continue

        stub_path = create_mirror_stub(parsed, mirror_dir, src_file, current_hash)

        # nodes 테이블에 노드 삽입
        now = datetime.now()
        node_id = generate_node_id(NodeType.SESSION, now)
        node = Node(
            id=node_id,
            type=NodeType.SESSION,
            project=parsed.project,
            title=parsed.title,
            file_path=str(stub_path.relative_to(mirror_dir.parent)),
            created=now,
            updated=now,
            agent_owner=parsed.agent_owner,
            agent_role=parsed.agent_role,
            source_path=str(src_file),
            raw_frontmatter={
                "summary": parsed.summary,
                "extracted_entities": parsed.extracted_entities,
            },
        )
        insert_node(conn, node)
        index_node_body(conn, node_id, parsed.raw_content)

        # mirrors 테이블 갱신
        conn.execute("""
            INSERT OR REPLACE INTO mirrors
                (source_path, node_id, source_hash, last_synced, adapter, protected, source_missing)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (
            str(src_file), node_id, current_hash, datetime.now().isoformat(), adapter.name,
        ))
        synced += 1

    # sync_state 갱신
    conn.execute("""
        INSERT OR REPLACE INTO sync_state (source_root, adapter_name, last_scan, last_file_mtime)
        VALUES (?, ?, ?, ?)
    """, (str(source_root), adapter.name, datetime.now().isoformat(), None))
    conn.commit()
    return synced
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_mirror_sync.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add khub/mirror_sync.py tests/test_mirror_sync.py
git commit -m "feat: add incremental mirror sync with hash-based change detection"
```

---

## Task 11: notes/ 인덱서

**Files:**
- Create: `E:/KnowledgeHub/khub/indexer.py`
- Test: `E:/KnowledgeHub/tests/test_indexer.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_indexer.py
import pytest
from pathlib import Path
from datetime import datetime
from khub.db import get_connection
from khub.indexer import index_notes_dir, index_single_note
from khub.frontmatter_io import write_file
from khub.nodes import get_node

@pytest.fixture
def notes_dir(tmp_path):
    notes = tmp_path / "notes"
    notes.mkdir()
    write_file(notes / "2026-04-07_idea_test.md", {
        "id": "idea-20260407-aaa111",
        "type": "idea",
        "project": "DnT_Game",
        "title": "테스트 아이디어",
        "created": "2026-04-07T14:20:00",
        "updated": "2026-04-07T14:20:00",
        "agent_owner": "jongil",
        "tags": ["test"],
    }, "본문 내용")
    return notes

def test_index_single_note(tmp_db, notes_dir):
    conn = get_connection(tmp_db)
    note_path = notes_dir / "2026-04-07_idea_test.md"
    index_single_note(conn, note_path)
    n = get_node(conn, "idea-20260407-aaa111")
    assert n is not None
    assert n.title == "테스트 아이디어"

def test_index_notes_dir(tmp_db, notes_dir):
    conn = get_connection(tmp_db)
    count = index_notes_dir(conn, notes_dir)
    assert count == 1

def test_index_handles_missing_id(tmp_db, tmp_path):
    """ID가 없는 노트는 건너뛴다."""
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "bad.md").write_text("# no frontmatter", encoding="utf-8")
    conn = get_connection(tmp_db)
    count = index_notes_dir(conn, notes)
    assert count == 0  # bad.md는 건너뛴다
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_indexer.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: indexer.py 구현**

```python
# E:/KnowledgeHub/khub/indexer.py
"""notes/ 디렉토리 → SQLite 동기화."""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path
from .frontmatter_io import parse_file, FrontmatterError
from .schema import Node, NodeType, Edge, EdgeRelation
from .nodes import insert_node, get_node, update_node
from .edges import insert_edge
from .search import index_node_body


def index_single_note(conn: sqlite3.Connection, note_path: Path) -> bool:
    """단일 노트 파일을 DB에 반영. 성공 시 True."""
    try:
        fm, body = parse_file(note_path)
    except FrontmatterError:
        return False

    node_id = fm.get("id")
    node_type_str = fm.get("type")
    if not node_id or not node_type_str:
        return False

    try:
        node_type = NodeType(node_type_str)
    except ValueError:
        return False

    created = datetime.fromisoformat(fm["created"]) if "created" in fm else datetime.now()
    updated = datetime.fromisoformat(fm["updated"]) if "updated" in fm else created

    node = Node(
        id=node_id,
        type=node_type,
        project=fm.get("project"),
        title=fm.get("title", note_path.stem),
        file_path=str(note_path),
        created=created,
        updated=updated,
        agent_owner=fm.get("agent_owner"),
        agent_role=fm.get("agent_role"),
        agent_project=fm.get("agent_project"),
        tags=fm.get("tags", []),
        status=fm.get("status"),
        priority=fm.get("priority"),
        test_category=fm.get("test_category"),
        generality=fm.get("generality"),
        external_id=fm.get("task_id"),
        source_path=fm.get("source_path"),
        raw_frontmatter=fm,
    )

    existing = get_node(conn, node_id)
    if existing:
        update_node(conn, node)
    else:
        insert_node(conn, node)

    index_node_body(conn, node_id, body)

    # frontmatter links → edges
    links = fm.get("links", {})
    for rel_str, targets in links.items():
        if not targets:
            continue
        try:
            rel = EdgeRelation(rel_str)
        except ValueError:
            continue
        for target_id in (targets if isinstance(targets, list) else [targets]):
            insert_edge(conn, Edge(source_id=node_id, target_id=target_id, relation=rel))

    return True


def index_notes_dir(conn: sqlite3.Connection, notes_dir: Path) -> int:
    """notes/ 전체 스캔 후 인덱싱. 처리된 파일 수 반환."""
    if not notes_dir.exists():
        return 0
    count = 0
    for md_file in notes_dir.rglob("*.md"):
        if index_single_note(conn, md_file):
            count += 1
    return count
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_indexer.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add khub/indexer.py tests/test_indexer.py
git commit -m "feat: add notes/ directory indexer"
```

---

## Task 12: friction_patterns 카운터

**Files:**
- Create: `E:/KnowledgeHub/khub/friction.py`
- Test: `E:/KnowledgeHub/tests/test_friction.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_friction.py
import pytest
from khub.db import get_connection
from khub.friction import (
    record_friction, get_pattern_count, list_promotion_candidates, hash_pattern
)

def test_hash_pattern_normalizes():
    """공백, 대소문자 정규화."""
    h1 = hash_pattern("  EADDRINUSE port 3000  ")
    h2 = hash_pattern("eaddrinuse port 3000")
    assert h1 == h2

def test_record_friction_first_time(tmp_db):
    conn = get_connection(tmp_db)
    record_friction(conn, "EADDRINUSE port 3000", "repeated_error", "journal-1")
    count = get_pattern_count(conn, "EADDRINUSE port 3000")
    assert count == 1

def test_record_friction_increments(tmp_db):
    conn = get_connection(tmp_db)
    record_friction(conn, "EADDRINUSE port 3000", "repeated_error", "journal-1")
    record_friction(conn, "EADDRINUSE port 3000", "repeated_error", "journal-2")
    record_friction(conn, "EADDRINUSE port 3000", "repeated_error", "journal-3")
    count = get_pattern_count(conn, "EADDRINUSE port 3000")
    assert count == 3

def test_list_promotion_candidates(tmp_db):
    conn = get_connection(tmp_db)
    for i in range(3):
        record_friction(conn, "patternA", "repeated_error", f"j-{i}")
    record_friction(conn, "patternB", "dead_end", "j-x")
    candidates = list_promotion_candidates(conn, threshold=2)
    assert len(candidates) == 1  # patternA만 임계값 도달
    assert candidates[0]["pattern_text"] == "patternA"
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_friction.py -v
```

Expected: FAIL

- [ ] **Step 3: friction.py 구현**

```python
# E:/KnowledgeHub/khub/friction.py
"""반복 마찰 패턴 카운터."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Optional


def hash_pattern(text: str) -> str:
    """패턴 텍스트를 정규화하여 SHA-256 해시 반환."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def record_friction(
    conn: sqlite3.Connection,
    pattern_text: str,
    pattern_type: str,
    journal_node_id: Optional[str] = None,
) -> int:
    """마찰 패턴 1회 기록. 누적 발생 횟수 반환."""
    h = hash_pattern(pattern_text)
    now = datetime.now().isoformat()

    cur = conn.execute(
        "SELECT occurrence_count, source_journals FROM friction_patterns WHERE pattern_hash = ?",
        (h,),
    )
    row = cur.fetchone()
    if row:
        new_count = row["occurrence_count"] + 1
        existing_journals = json.loads(row["source_journals"]) if row["source_journals"] else []
        if journal_node_id and journal_node_id not in existing_journals:
            existing_journals.append(journal_node_id)
        conn.execute("""
            UPDATE friction_patterns
            SET occurrence_count = ?, last_seen = ?, source_journals = ?
            WHERE pattern_hash = ?
        """, (new_count, now, json.dumps(existing_journals), h))
    else:
        new_count = 1
        journals = [journal_node_id] if journal_node_id else []
        conn.execute("""
            INSERT INTO friction_patterns
                (pattern_hash, pattern_text, pattern_type, first_seen, last_seen,
                 occurrence_count, source_journals)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (h, pattern_text, pattern_type, now, now, json.dumps(journals)))
    conn.commit()
    return new_count


def get_pattern_count(conn: sqlite3.Connection, pattern_text: str) -> int:
    h = hash_pattern(pattern_text)
    cur = conn.execute(
        "SELECT occurrence_count FROM friction_patterns WHERE pattern_hash = ?", (h,)
    )
    row = cur.fetchone()
    return row["occurrence_count"] if row else 0


def list_promotion_candidates(conn: sqlite3.Connection, threshold: int = 3) -> list[dict]:
    """임계값 이상 반복된 패턴 (TEMS 승격 후보) 반환."""
    cur = conn.execute("""
        SELECT pattern_hash, pattern_text, pattern_type, occurrence_count, last_seen
        FROM friction_patterns
        WHERE occurrence_count >= ? AND promoted_to_tems = 0
        ORDER BY occurrence_count DESC
    """, (threshold,))
    return [dict(row) for row in cur.fetchall()]
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_friction.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add khub/friction.py tests/test_friction.py
git commit -m "feat: add friction pattern counter for TEMS promotion candidates"
```

---

## Task 13: WikiAPI - 검색·그래프 (search, get_neighbors, get_history, find_similar)

**Files:**
- Create: `E:/KnowledgeHub/khub/wiki_api.py`
- Test: `E:/KnowledgeHub/tests/test_wiki_api.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_wiki_api.py
import pytest
from datetime import datetime
from khub.schema import Node, NodeType, Edge, EdgeRelation
from khub.db import get_connection
from khub.nodes import insert_node
from khub.edges import insert_edge
from khub.search import index_node_body
from khub.wiki_api import WikiAPI

@pytest.fixture
def api(tmp_db):
    return WikiAPI(db_path=tmp_db)

@pytest.fixture
def populated(tmp_db):
    conn = get_connection(tmp_db)
    now = datetime(2026, 4, 7)
    nodes = [
        Node(id="idea-1", type=NodeType.IDEA, project="DnT_Game",
             title="스프링", file_path="notes/i1.md", created=now, updated=now),
        Node(id="task-1", type=NodeType.TASK, project="DnT_Game",
             title="Q-011", file_path="notes/t1.md", created=now, updated=now,
             status="pending", priority="P1"),
        Node(id="lesson-1", type=NodeType.LESSON, project="DnT_Game",
             title="motion baseline", file_path="notes/l1.md", created=now, updated=now),
    ]
    for n in nodes:
        insert_node(conn, n)
    insert_edge(conn, Edge("idea-1", "task-1", EdgeRelation.SPAWNS))
    index_node_body(conn, "idea-1", "스프링 stiffness 재조정")
    index_node_body(conn, "lesson-1", "DnT UI 드래그 stiffness 250-280")
    conn.close()
    return tmp_db

def test_search(populated):
    api = WikiAPI(db_path=populated)
    results = api.search("stiffness")
    assert len(results) >= 2

def test_search_with_filter(populated):
    api = WikiAPI(db_path=populated)
    results = api.search("stiffness", filters={"type": "lesson"})
    assert all(r["type"] == "lesson" for r in results)

def test_get_neighbors(populated):
    api = WikiAPI(db_path=populated)
    neighbors = api.get_neighbors("idea-1", depth=1)
    assert "task-1" in [n.id for n in neighbors]

def test_get_history_returns_chain(populated):
    api = WikiAPI(db_path=populated)
    history = api.get_history("idea-1")
    assert len(history) >= 1
    assert any(n.id == "task-1" for n in history)

def test_find_similar(populated):
    api = WikiAPI(db_path=populated)
    results = api.find_similar("스프링")
    assert len(results) >= 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_wiki_api.py::test_search -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: wiki_api.py 구현 (검색·그래프 부분)**

```python
# E:/KnowledgeHub/khub/wiki_api.py
"""진행자/에이전트가 사용할 위키 조회·기록 API."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional
from .db import get_connection, DEFAULT_DB_PATH
from .schema import Node, NodeType, Edge, EdgeRelation, generate_node_id
from .nodes import insert_node, get_node, update_node, list_nodes
from .edges import insert_edge, get_neighbors as _get_neighbors
from .search import search as _search, search_filtered
from .friction import list_promotion_candidates


class WikiAPI:
    """KnowledgeHub의 통합 조회·기록 API."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path

    def _conn(self):
        return get_connection(self.db_path)

    # ─── 검색 ─────────────────────────────
    def search(self, query: str, filters: Optional[dict] = None, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            if filters:
                return search_filtered(
                    conn, query,
                    type=filters.get("type"),
                    project=filters.get("project"),
                    limit=limit,
                )
            return _search(conn, query, limit)

    def search_by_tag(self, tag: str, project: Optional[str] = None) -> list[Node]:
        with self._conn() as conn:
            sql = """
                SELECT n.* FROM nodes n
                JOIN tags t ON n.id = t.node_id
                WHERE t.tag = ?
            """
            params = [tag]
            if project:
                sql += " AND n.project = ?"
                params.append(project)
            from .nodes import _row_to_node
            cur = conn.execute(sql, params)
            return [_row_to_node(row) for row in cur.fetchall()]

    # ─── 그래프 조회 ──────────────────────
    def get_neighbors(
        self, node_id: str, relation: Optional[EdgeRelation] = None, depth: int = 1
    ) -> list[Node]:
        with self._conn() as conn:
            return _get_neighbors(conn, node_id, relation=relation, depth=depth)

    def get_history(self, node_id: str) -> list[Node]:
        """노드와 연결된 전체 그래프 (depth 5)."""
        with self._conn() as conn:
            return _get_neighbors(conn, node_id, depth=5)

    def find_similar(self, pattern: str, type: Optional[str] = None) -> list[dict]:
        """패턴 텍스트로 FTS5 검색."""
        with self._conn() as conn:
            return search_filtered(conn, pattern, type=type, limit=10)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_wiki_api.py::test_search tests/test_wiki_api.py::test_search_with_filter tests/test_wiki_api.py::test_get_neighbors tests/test_wiki_api.py::test_get_history_returns_chain tests/test_wiki_api.py::test_find_similar -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add khub/wiki_api.py tests/test_wiki_api.py
git commit -m "feat: add WikiAPI search and graph methods"
```

---

## Task 14: WikiAPI - 프로젝트·기록 (timeline, pending_tasks, add_node, add_edge, update_node, friction_candidates)

**Files:**
- Modify: `E:/KnowledgeHub/khub/wiki_api.py` (메서드 추가)
- Modify: `E:/KnowledgeHub/tests/test_wiki_api.py` (테스트 추가)

- [ ] **Step 1: 새 테스트 추가**

```python
# E:/KnowledgeHub/tests/test_wiki_api.py 끝에 추가
def test_get_pending_tasks(populated):
    api = WikiAPI(db_path=populated)
    tasks = api.get_pending_tasks(project="DnT_Game")
    assert len(tasks) == 1
    assert tasks[0].id == "task-1"
    assert tasks[0].status == "pending"

def test_add_node_creates(populated):
    api = WikiAPI(db_path=populated)
    new_id = api.add_node(
        type="idea",
        frontmatter={"project": "DnT_Game", "title": "새 아이디어"},
        body="본문",
    )
    assert new_id.startswith("idea-")
    fetched = api.get_node(new_id)
    assert fetched is not None
    assert fetched.title == "새 아이디어"

def test_add_edge_creates(populated):
    api = WikiAPI(db_path=populated)
    api.add_edge("task-1", "lesson-1", "distilled_into")
    neighbors = api.get_neighbors("task-1")
    assert "lesson-1" in [n.id for n in neighbors]

def test_get_project_timeline(populated):
    api = WikiAPI(db_path=populated)
    timeline = api.get_project_timeline("DnT_Game", since="2026-04-01")
    assert len(timeline) >= 3

def test_get_friction_candidates(tmp_db):
    from khub.friction import record_friction
    conn = get_connection(tmp_db)
    for i in range(4):
        record_friction(conn, "patternX", "repeated_error", f"j-{i}")
    conn.close()
    api = WikiAPI(db_path=tmp_db)
    candidates = api.get_friction_candidates(threshold=3)
    assert len(candidates) == 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_wiki_api.py::test_get_pending_tasks -v
```

Expected: FAIL (`AttributeError: 'WikiAPI' object has no attribute 'get_pending_tasks'`)

- [ ] **Step 3: wiki_api.py에 메서드 추가**

```python
# E:/KnowledgeHub/khub/wiki_api.py 끝에 추가 (WikiAPI 클래스 안)

    # ─── 프로젝트 단위 ────────────────────
    def get_project_timeline(
        self, project: str, since: str, until: Optional[str] = None
    ) -> list[Node]:
        with self._conn() as conn:
            sql = "SELECT * FROM nodes WHERE project = ? AND created >= ?"
            params = [project, since]
            if until:
                sql += " AND created <= ?"
                params.append(until)
            sql += " ORDER BY created DESC"
            from .nodes import _row_to_node
            cur = conn.execute(sql, params)
            return [_row_to_node(row) for row in cur.fetchall()]

    def get_pending_tasks(
        self, project: Optional[str] = None, owner: Optional[str] = None
    ) -> list[Node]:
        with self._conn() as conn:
            sql = "SELECT * FROM nodes WHERE type = 'task' AND status != 'done'"
            params = []
            if project:
                sql += " AND project = ?"
                params.append(project)
            if owner:
                sql += " AND agent_owner = ?"
                params.append(owner)
            sql += " ORDER BY priority ASC, created DESC"
            from .nodes import _row_to_node
            cur = conn.execute(sql, params)
            return [_row_to_node(row) for row in cur.fetchall()]

    def get_recent_lessons(self, since: str) -> list[Node]:
        with self._conn() as conn:
            sql = "SELECT * FROM nodes WHERE type = 'lesson' AND created >= ? ORDER BY created DESC"
            from .nodes import _row_to_node
            cur = conn.execute(sql, (since,))
            return [_row_to_node(row) for row in cur.fetchall()]

    # ─── 기록 ─────────────────────────────
    def add_node(self, type: str, frontmatter: dict, body: str = "") -> str:
        """새 노드 생성 후 ID 반환. notes/ 파일과 DB 양쪽에 반영."""
        from .frontmatter_io import write_file
        from .indexer import index_single_note
        nt = NodeType(type)
        now = datetime.now()
        node_id = generate_node_id(nt, now)
        slug = frontmatter.get("title", "untitled").replace(" ", "-")[:30]
        fname = f"{now.strftime('%Y-%m-%d')}_{type}_{slug}.md"
        notes_dir = self.db_path.parent.parent / "notes"
        note_path = notes_dir / fname
        full_fm = {
            "id": node_id,
            "type": type,
            "created": now.isoformat(),
            "updated": now.isoformat(),
            **frontmatter,
        }
        write_file(note_path, full_fm, body)
        with self._conn() as conn:
            index_single_note(conn, note_path)
        return node_id

    def get_node(self, node_id: str) -> Optional[Node]:
        with self._conn() as conn:
            return get_node(conn, node_id)

    def add_edge(self, source: str, target: str, relation: str) -> None:
        with self._conn() as conn:
            insert_edge(conn, Edge(source, target, EdgeRelation(relation)))

    def update_node(self, node_id: str, updates: dict) -> None:
        with self._conn() as conn:
            n = get_node(conn, node_id)
            if not n:
                return
            for key, val in updates.items():
                if hasattr(n, key):
                    setattr(n, key, val)
            update_node(conn, n)

    # ─── 메타 ─────────────────────────────
    def get_friction_candidates(self, threshold: int = 3) -> list[dict]:
        with self._conn() as conn:
            return list_promotion_candidates(conn, threshold=threshold)

    def get_metaknowledge_suggestions(self) -> list[dict]:
        """Phase 3 — 현재는 빈 리스트."""
        return []
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_wiki_api.py -v
```

Expected: 10 passed (5 from Task 13 + 5 new)

- [ ] **Step 5: Commit**

```bash
git add khub/wiki_api.py tests/test_wiki_api.py
git commit -m "feat: complete WikiAPI with project queries and write methods"
```

---

## Task 15: CLI - 기본 구조 + /k-capture

**Files:**
- Create: `E:/KnowledgeHub/khub/cli.py`
- Test: `E:/KnowledgeHub/tests/test_cli.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_cli.py
import pytest
from click.testing import CliRunner
from pathlib import Path
from khub.cli import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def tmp_hub(tmp_path, monkeypatch):
    """임시 KnowledgeHub 디렉토리."""
    hub = tmp_path / "hub"
    hub.mkdir()
    (hub / ".index").mkdir()
    (hub / "notes").mkdir()
    monkeypatch.setenv("KHUB_ROOT", str(hub))
    return hub

def test_cli_init(runner, tmp_hub):
    result = runner.invoke(cli, ["init"])
    assert result.exit_code == 0
    assert (tmp_hub / ".index" / "wiki.db").exists()

def test_capture_idea(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, [
        "capture", "idea", "테스트 아이디어",
        "--project", "DnT_Game",
        "--hypothesis", "가설 X"
    ])
    assert result.exit_code == 0
    assert "idea-" in result.output  # 노드 ID 출력

def test_capture_task(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, [
        "capture", "task", "Q-011 스프링 튜닝",
        "--task-id", "Q-011",
        "--priority", "P1",
        "--assigned-to", "build_goon"
    ])
    assert result.exit_code == 0
    assert "task-" in result.output
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: cli.py 구현 (init + capture)**

```python
# E:/KnowledgeHub/khub/cli.py
"""KnowledgeHub CLI — /k-* 슬래시 커맨드."""
from __future__ import annotations
import os
import click
from pathlib import Path
from datetime import datetime
from .db import init_db, get_connection
from .wiki_api import WikiAPI


def get_hub_root() -> Path:
    """KHUB_ROOT 환경변수 또는 기본 경로 반환."""
    return Path(os.environ.get("KHUB_ROOT", "E:/KnowledgeHub"))


def get_db_path() -> Path:
    return get_hub_root() / ".index" / "wiki.db"


@click.group()
def cli():
    """KnowledgeHub CLI — /k-* 슬래시 커맨드."""
    pass


@cli.command()
def init():
    """KnowledgeHub DB와 디렉토리 초기화."""
    root = get_hub_root()
    for sub in ["notes", "mirrors", "artifacts", "projects", ".index", ".agents"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    init_db(get_db_path())
    click.echo(f"KnowledgeHub initialized at {root}")


@cli.group()
def capture():
    """노드 생성 (idea/task/testrun/session/feedback)."""
    pass


@capture.command("idea")
@click.argument("title")
@click.option("--project", default="DnT_Game")
@click.option("--hypothesis", default="")
@click.option("--actionability", type=int, default=5)
def capture_idea(title, project, hypothesis, actionability):
    api = WikiAPI(db_path=get_db_path())
    nid = api.add_node(
        type="idea",
        frontmatter={
            "project": project,
            "title": title,
            "agent_owner": "jongil",
            "actionability": actionability,
            "hypothesis": hypothesis,
            "status": "raw",
        },
        body=hypothesis or "",
    )
    click.echo(nid)


@capture.command("task")
@click.argument("title")
@click.option("--task-id", required=True)
@click.option("--project", default="DnT_Game")
@click.option("--priority", type=click.Choice(["P0", "P1", "P2"]), default="P1")
@click.option("--assigned-to", default="build_goon")
@click.option("--spawned-by", default=None)
def capture_task(title, task_id, project, priority, assigned_to, spawned_by):
    api = WikiAPI(db_path=get_db_path())
    fm = {
        "project": project,
        "title": title,
        "task_id": task_id,
        "priority": priority,
        "assigned_to": assigned_to,
        "status": "pending",
        "agent_owner": "wesang_goon",
    }
    if spawned_by:
        fm["links"] = {"spawned_by": [spawned_by]}
    nid = api.add_node(type="task", frontmatter=fm, body="")
    if spawned_by:
        api.add_edge(spawned_by, nid, "spawns")
    click.echo(nid)


@capture.command("testrun")
@click.argument("title")
@click.option("--category", required=True,
              type=click.Choice(["backtest", "playtest", "unit_test", "integration_test"]))
@click.option("--project", default="DnT_Game")
@click.option("--artifact", multiple=True)
def capture_testrun(title, category, project, artifact):
    api = WikiAPI(db_path=get_db_path())
    nid = api.add_node(
        type="test_run",
        frontmatter={
            "project": project,
            "title": title,
            "test_category": category,
            "artifacts": list(artifact),
        },
    )
    click.echo(nid)


@capture.command("session")
@click.option("--owner", default="wesang_goon")
@click.option("--number", type=int, default=None)
def capture_session(owner, number):
    api = WikiAPI(db_path=get_db_path())
    nid = api.add_node(
        type="session",
        frontmatter={
            "title": f"Session {number or '?'}",
            "session_owner": owner,
            "session_number": number,
        },
    )
    click.echo(nid)


@capture.command("feedback")
@click.argument("notes")
@click.option("--target", required=True)
@click.option("--rating", type=int)
@click.option("--decision", default="keep",
              type=click.Choice(["keep", "revise", "discard", "pivot"]))
def capture_feedback(notes, target, rating, decision):
    api = WikiAPI(db_path=get_db_path())
    nid = api.add_node(
        type="feedback",
        frontmatter={
            "title": notes[:60],
            "target_node": target,
            "from_user": "jongil",
            "rating": rating,
            "decision": decision,
        },
        body=notes,
    )
    api.add_edge(nid, target, "feedback_by")
    click.echo(nid)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add khub/cli.py tests/test_cli.py
git commit -m "feat: add CLI skeleton with /k-capture (idea/task/testrun/session/feedback)"
```

---

## Task 16: CLI - /k-journal + /k-search

**Files:**
- Modify: `E:/KnowledgeHub/khub/cli.py`
- Modify: `E:/KnowledgeHub/tests/test_cli.py`

- [ ] **Step 1: 새 테스트 추가**

```python
# tests/test_cli.py 에 추가

def test_journal_creates_friction(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    result = runner.invoke(cli, [
        "journal", "EADDRINUSE port 3000",
        "--type", "repeated_error",
        "--count", "3",
    ])
    assert result.exit_code == 0
    # 두 번째 호출 시 카운터 증가
    runner.invoke(cli, ["journal", "EADDRINUSE port 3000", "--type", "repeated_error"])
    # friction_patterns 테이블 검증은 wiki_api로

def test_search_command(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["capture", "idea", "스프링 튜닝"])
    result = runner.invoke(cli, ["search", "스프링"])
    assert result.exit_code == 0
    assert "스프링" in result.output or "idea-" in result.output
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py::test_journal_creates_friction -v
```

Expected: FAIL (No such command 'journal')

- [ ] **Step 3: cli.py에 명령 추가**

```python
# khub/cli.py 에 추가

from .friction import record_friction


@cli.command("journal")
@click.argument("pattern")
@click.option("--type", "ftype",
              type=click.Choice(["repeated_error", "dead_end", "parameter_sweep", "tool_misuse", "uncertain"]),
              default="uncertain")
@click.option("--count", type=int, default=1)
@click.option("--duration-min", type=int, default=0)
@click.option("--resolved-by", default="")
def journal(pattern, ftype, count, duration_min, resolved_by):
    """SessionJournal에 마찰 이벤트 추가."""
    conn = get_connection(get_db_path())
    new_count = record_friction(conn, pattern, ftype)
    conn.close()
    click.echo(f"Recorded ({ftype}, count={new_count}): {pattern}")
    if new_count >= 3:
        click.echo(click.style("⚠️ TEMS 승격 후보 (count >= 3)", fg="yellow"))


@cli.command("search")
@click.argument("query")
@click.option("--type", "ntype", default=None)
@click.option("--project", default=None)
@click.option("--limit", type=int, default=10)
def search_cmd(query, ntype, project, limit):
    """FTS5 BM25 검색."""
    api = WikiAPI(db_path=get_db_path())
    filters = {}
    if ntype:
        filters["type"] = ntype
    if project:
        filters["project"] = project
    results = api.search(query, filters=filters, limit=limit)
    if not results:
        click.echo("(no results)")
        return
    for r in results:
        click.echo(f"[{r['type']}] {r['id']} — {r['title']}")
        if r.get("snippet"):
            click.echo(f"    {r['snippet']}")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add khub/cli.py tests/test_cli.py
git commit -m "feat: add /k-journal and /k-search commands"
```

---

## Task 17: CLI - /k-link + /k-index + /k-graph + /k-girok

**Files:**
- Modify: `E:/KnowledgeHub/khub/cli.py`
- Modify: `E:/KnowledgeHub/tests/test_cli.py`

- [ ] **Step 1: 새 테스트 추가**

```python
# tests/test_cli.py 에 추가

def test_link_command(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    r1 = runner.invoke(cli, ["capture", "idea", "아이디어"])
    idea_id = r1.output.strip()
    r2 = runner.invoke(cli, ["capture", "task", "태스크", "--task-id", "Q-001"])
    task_id = r2.output.strip()
    result = runner.invoke(cli, ["link", idea_id, task_id, "spawns"])
    assert result.exit_code == 0

def test_index_command(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    runner.invoke(cli, ["capture", "idea", "테스트"])
    result = runner.invoke(cli, ["index"])
    assert result.exit_code == 0
    assert "indexed" in result.output.lower() or "complete" in result.output.lower()

def test_graph_command(runner, tmp_hub):
    runner.invoke(cli, ["init"])
    r = runner.invoke(cli, ["capture", "idea", "아이디어"])
    nid = r.output.strip()
    result = runner.invoke(cli, ["graph", "node", nid])
    assert result.exit_code == 0
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py::test_link_command -v
```

Expected: FAIL (No such command 'link')

- [ ] **Step 3: cli.py에 명령 추가**

```python
# khub/cli.py 에 추가

from .indexer import index_notes_dir


@cli.command("link")
@click.argument("source")
@click.argument("target")
@click.argument("relation",
                type=click.Choice(["spawns", "executed_in", "produces", "produces_journal",
                                   "distilled_into", "feedback_by", "contradicts", "generalizes_into"]))
def link_cmd(source, target, relation):
    """수동 엣지 추가."""
    api = WikiAPI(db_path=get_db_path())
    api.add_edge(source, target, relation)
    click.echo(f"linked: {source} --{relation}--> {target}")


@cli.command("index")
@click.option("--full", is_flag=True, help="전체 재인덱싱")
@click.option("--source", default=None, help="특정 소스만")
def index_cmd(full, source):
    """notes/ + mirrors/ 재인덱싱."""
    notes_dir = get_hub_root() / "notes"
    conn = get_connection(get_db_path())
    if full:
        conn.execute("DELETE FROM nodes")
        conn.execute("DELETE FROM nodes_fts")
        conn.commit()
    count = index_notes_dir(conn, notes_dir)
    conn.close()
    click.echo(f"indexed: {count} notes")


@cli.command("graph")
@click.argument("kind", type=click.Choice(["node", "project"]))
@click.argument("identifier")
@click.option("--depth", type=int, default=2)
def graph_cmd(kind, identifier, depth):
    """그래프 조회 (CLI 텍스트 출력)."""
    api = WikiAPI(db_path=get_db_path())
    if kind == "node":
        center = api.get_node(identifier)
        if not center:
            click.echo(f"node not found: {identifier}")
            return
        click.echo(f"● {center.id} [{center.type.value}] {center.title}")
        neighbors = api.get_neighbors(identifier, depth=depth)
        for n in neighbors:
            click.echo(f"  ├─ {n.id} [{n.type.value}] {n.title}")
    elif kind == "project":
        timeline = api.get_project_timeline(identifier, since="2026-01-01")
        click.echo(f"Project: {identifier}")
        for n in timeline[:20]:
            click.echo(f"  · {n.created.date()} [{n.type.value}] {n.title}")


@cli.command("girok")
@click.argument("instruction", required=False, default="")
def girok_cmd(instruction):
    """기록군 수동 호출 (Phase 1: stub)."""
    click.echo("기록군 호출됨")
    click.echo(f"지시: {instruction or '(없음)'}")
    click.echo("(Phase 1: 자동화 로직은 girok.py 모듈 참조)")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_cli.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add khub/cli.py tests/test_cli.py
git commit -m "feat: add /k-link /k-index /k-graph /k-girok commands"
```

---

## Task 18: 기록군 자동 호출 로직 (girok.py)

**Files:**
- Create: `E:/KnowledgeHub/khub/girok.py`
- Test: `E:/KnowledgeHub/tests/test_girok.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_girok.py
import pytest
from pathlib import Path
from khub.db import get_connection, init_db
from khub.girok import GirokAgent

@pytest.fixture
def hub(tmp_path):
    root = tmp_path / "hub"
    for sub in ["notes", "mirrors/wesang", "mirrors/build", "mirrors/fermion", ".index"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    init_db(root / ".index" / "wiki.db")
    return root

def test_girok_init(hub):
    g = GirokAgent(hub_root=hub)
    assert g.db_path.exists()

def test_girok_session_end_creates_session_node(hub):
    g = GirokAgent(hub_root=hub)
    sid = g.on_session_end(
        agent_owner="wesang_goon",
        session_number=16,
        summary="아트 파이프라인 수립",
    )
    assert sid.startswith("session-")

def test_girok_sync_external_sources(hub, tmp_path):
    """외부 소스 디렉토리를 미러링 가능한가."""
    fake_handover_dir = tmp_path / "fake_wesang"
    fake_handover_dir.mkdir()
    (fake_handover_dir / "session1.md").write_text(
        "# Session 1\n\n## 세션 요약\n첫 세션 요약\n",
        encoding="utf-8",
    )
    g = GirokAgent(hub_root=hub)
    count = g.sync_external_sources([fake_handover_dir])
    assert count == 1

def test_girok_friction_review_returns_candidates(hub):
    from khub.friction import record_friction
    conn = get_connection(hub / ".index" / "wiki.db")
    for i in range(3):
        record_friction(conn, "patternA", "repeated_error", f"j-{i}")
    conn.close()
    g = GirokAgent(hub_root=hub)
    candidates = g.friction_review(threshold=3)
    assert len(candidates) == 1
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_girok.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: girok.py 구현**

```python
# E:/KnowledgeHub/khub/girok.py
"""기록군 자동 호출 로직.

Stop hook, 파일 watcher, 일정 트리거에서 호출되는 진입점들.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Optional
from .db import get_connection
from .wiki_api import WikiAPI
from .friction import list_promotion_candidates
from .adapters.claude_standard import ClaudeStandardAdapter
from .mirror_sync import sync_source_root


class GirokAgent:
    """기록군 — 위키 자동화 큐레이터."""

    def __init__(self, hub_root: Path):
        self.hub_root = hub_root
        self.db_path = hub_root / ".index" / "wiki.db"
        self.api = WikiAPI(db_path=self.db_path)

    def on_session_end(
        self,
        agent_owner: str,
        session_number: Optional[int] = None,
        summary: str = "",
    ) -> str:
        """세션 종료 시 Session 노드 생성."""
        title = f"{agent_owner} Session {session_number}" if session_number else f"{agent_owner} Session"
        return self.api.add_node(
            type="session",
            frontmatter={
                "title": title,
                "session_number": session_number,
                "agent_owner": agent_owner,
                "agent_role": "director" if "wesang" in agent_owner else "specialist",
                "summary": summary,
            },
            body=summary,
        )

    def sync_external_sources(self, source_roots: list[Path]) -> int:
        """외부 핸드오버 소스들을 미러링."""
        adapter = ClaudeStandardAdapter(source_roots=source_roots)
        mirror_dir = self.hub_root / "mirrors"
        total = 0
        with get_connection(self.db_path) as conn:
            for root in source_roots:
                total += sync_source_root(conn, adapter, root, mirror_dir)
        return total

    def friction_review(self, threshold: int = 3) -> list[dict]:
        """반복 마찰 패턴 중 TEMS 승격 후보 반환."""
        with get_connection(self.db_path) as conn:
            return list_promotion_candidates(conn, threshold=threshold)

    def daily_check(self) -> dict:
        """일 1회 자동 검사: 누락 감지 + 승격 후보 수집."""
        candidates = self.friction_review(threshold=3)
        return {
            "ran_at": datetime.now().isoformat(),
            "promotion_candidates": candidates,
            "candidate_count": len(candidates),
        }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_girok.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add khub/girok.py tests/test_girok.py
git commit -m "feat: add girok agent automation entry points"
```

---

## Task 19: 기록군 Subagent 정의 파일

**Files:**
- Create: `E:/KnowledgeHub/.agents/girok-goon.md`

- [ ] **Step 1: 정의 파일 작성**

```markdown
<!-- E:/KnowledgeHub/.agents/girok-goon.md -->
---
name: girok-goon
description: DnT KnowledgeHub 전속 큐레이터. 세션 기록, 교훈 추출, 마찰 감지, 미러링, 시각화 자동 관리.
model: sonnet
tools: Read, Write, Edit, Glob, Grep, Bash
---

# 기록군 (GirokGoon) — Knowledge Curator

당신은 **DnT KnowledgeHub** (`E:/KnowledgeHub/`)의 전속 관리자다.

## 페르소나
- 종일군에게는 말 없는 사관(史官)
- 다른 에이전트와는 협력자, 단 산출물 정리만 담당
- 흐름을 만들지 않고 기록만 한다

## 책임
1. **세션 종료 시 자가 호출**: 현재 세션의 주요 이벤트를 스캔하여
   Session/TestRun/SessionJournal 노드를 생성한다.
   - 호출 방식: `python -m khub.cli girok "지난 세션 정리"`
2. **외부 원본 미러링**: 파일 watcher가 감지한 새 핸드오버를
   `claude_standard` 어댑터로 파싱하여 `mirrors/`에 스텁을 생성한다.
3. **반복 패턴 감지**: `friction_patterns` 테이블을 모니터링하여
   임계값 초과 시 종일군에게 TEMS 승격을 제안한다.
4. **시각화 자동 생성**: 주간 요약 Dataview 쿼리, Mermaid 타임라인,
   `projects/*.md` 랜딩 페이지 갱신.
5. (Phase 3) 메타지식 후보 제안: 크로스 프로젝트 패턴 발견.

## 절대 금지
- 외부 프로젝트 원본 파일 수정 금지 (`mirrors/`만 씀)
- `Idea` / `Feedback` 노드 수정 금지 (종일군 전유)
- 설계·구현·기획 관여 금지 (기록·정리만)

## 자동 트리거
- **Stop hook 시**: 현재 세션 요약 생성
- **파일 watcher 이벤트 시**: 해당 파일 어댑터 파싱
- **일 1회 (자정)**: friction_patterns 리뷰, 랜딩 페이지 갱신
- **주 1회 (월요일)**: 주간 요약 + Mermaid 타임라인

## 조회 API (다른 에이전트가 호출)
Python 모듈 `khub.wiki_api.WikiAPI` 사용:
- `search(query, filters)` → FTS5 BM25 결과
- `get_neighbors(node_id, depth)` → 그래프 이웃
- `get_history(node_id)` → 전체 타임라인
- `find_similar(pattern)` → 유사 과거 사례
- `get_friction_candidates()` → 승격 후보 리스트
- `add_node(type, frontmatter, body)` → 노드 생성
- `add_edge(source, target, relation)` → 엣지 추가

## 작업 흐름 예시
종일군이 `/k-girok "지난 세션 정리"` 호출 시:
1. 현재 세션 컨텍스트(어느 에이전트, 어느 시간대)를 파악
2. `WikiAPI.search()`로 관련 노드 조회
3. 주요 이벤트 (TestRun, 마찰, 결과)를 자동 추출
4. `add_node()`로 Session/TestRun/SessionJournal 생성
5. `add_edge()`로 그래프 연결
6. 종일군에게 한 줄 요약 보고
```

- [ ] **Step 2: 파일 검증**

```bash
cd E:/KnowledgeHub && cat .agents/girok-goon.md | head -5
```

Expected: frontmatter `name: girok-goon` 포함된 출력

- [ ] **Step 3: Commit**

```bash
git add .agents/girok-goon.md
git commit -m "feat: add girok-goon subagent definition"
```

---

## Task 20: 시각화 (Dataview 쿼리 카탈로그 + Mermaid 생성)

**Files:**
- Create: `E:/KnowledgeHub/khub/visualizer.py`
- Test: `E:/KnowledgeHub/tests/test_visualizer.py`

- [ ] **Step 1: 실패 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_visualizer.py
import pytest
from datetime import datetime
from khub.schema import Node, NodeType, Edge, EdgeRelation
from khub.db import get_connection
from khub.nodes import insert_node
from khub.edges import insert_edge
from khub.visualizer import (
    generate_session_mermaid,
    render_dataview_query,
    DATAVIEW_QUERIES,
)

def test_dataview_queries_count():
    assert len(DATAVIEW_QUERIES) == 10
    assert "Q1" in DATAVIEW_QUERIES
    assert "Q10" in DATAVIEW_QUERIES

def test_render_dataview_query():
    rendered = render_dataview_query("Q1")
    assert "```dataview" in rendered
    assert "FROM \"notes\"" in rendered

def test_generate_session_mermaid(tmp_db):
    conn = get_connection(tmp_db)
    now = datetime(2026, 4, 7)
    nodes = [
        Node(id="idea-1", type=NodeType.IDEA, project="DnT_Game",
             title="스프링", file_path="notes/i.md", created=now, updated=now),
        Node(id="task-1", type=NodeType.TASK, project="DnT_Game",
             title="Q-011", file_path="notes/t.md", created=now, updated=now),
        Node(id="session-1", type=NodeType.SESSION, project="DnT_Game",
             title="Session 16", file_path="notes/s.md", created=now, updated=now),
    ]
    for n in nodes:
        insert_node(conn, n)
    insert_edge(conn, Edge("idea-1", "task-1", EdgeRelation.SPAWNS))
    insert_edge(conn, Edge("task-1", "session-1", EdgeRelation.EXECUTED_IN))

    mermaid = generate_session_mermaid(conn, "session-1")
    assert "graph" in mermaid.lower()
    assert "session-1" in mermaid
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_visualizer.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: visualizer.py 구현**

```python
# E:/KnowledgeHub/khub/visualizer.py
"""Dataview 쿼리 카탈로그 + Mermaid 다이어그램 생성."""
from __future__ import annotations
import sqlite3
from .edges import get_edges_from, get_edges_to
from .nodes import get_node


DATAVIEW_QUERIES = {
    "Q1": """\
TABLE 
  type AS "타입",
  agent_owner AS "담당",
  summary AS "요약"
FROM "notes"
WHERE created >= date(today) - dur(7 days)
SORT created DESC""",

    "Q2": """\
TABLE
  task_id AS "ID",
  priority AS "P",
  status AS "상태",
  assigned_to AS "담당",
  file.link AS "노트"
FROM "notes"
WHERE type = "task" AND project = this.project AND status != "done"
SORT priority ASC, created DESC""",

    "Q3": """\
TABLE
  date AS "날짜",
  parameters.compass_l3_weights AS "L3 가중치",
  results.return_rate AS "수익률(%)",
  results.mdd AS "MDD(%)",
  results.sharpe AS "샤프"
FROM "notes"
WHERE type = "test_run" 
  AND project = "DnT_Fermion" 
  AND test_category = "backtest"
SORT date DESC
LIMIT 10""",

    "Q4": """\
LIST
  "**" + evt.type + "**: " + evt.pattern + " (×" + evt.count + ")"
FROM "notes"
WHERE type = "session_journal" 
  AND created >= date(today) - dur(30 days)
FLATTEN friction_events AS evt
WHERE evt.count >= 2""",

    "Q5": """\
TABLE
  occurrence_count AS "발생수",
  pattern_text AS "패턴"
FROM "notes"
WHERE type = "lesson" 
  AND tems.promoted = false
SORT occurrence_count DESC
LIMIT 10""",

    "Q6": """\
TABLE
  target_node AS "대상",
  rating AS "평점",
  notes AS "노트"
FROM "notes"
WHERE type = "feedback"
SORT created DESC
LIMIT 10""",

    "Q7": """\
LIST lesson_text
FROM "notes"
WHERE type = "lesson"
GROUP BY generality
SORT generality""",

    "Q8": """\
TABLE
  actionability AS "구체성",
  hypothesis AS "가설",
  file.link AS "노트"
FROM "notes"
WHERE type = "idea" 
  AND status != "promoted_to_task" 
  AND status != "abandoned"
SORT actionability DESC""",

    "Q9": """\
TABLE
  status AS "상태",
  links.executed_in AS "세션",
  links.distilled_into AS "교훈"
FROM "notes"
WHERE type = "task"
SORT created DESC
LIMIT 10""",

    "Q10": """\
TABLE WITHOUT ID
  type AS "타입",
  length(rows) AS "개수"
FROM "notes"
WHERE created >= date(today) - dur(30 days)
GROUP BY type
SORT length(rows) DESC""",
}


# 노드 타입별 이모지
TYPE_ICON = {
    "idea": "💡",
    "task": "📋",
    "session": "📅",
    "test_run": "🟢",
    "session_journal": "🟠",
    "lesson": "🔴",
    "feedback": "🟣",
}


def render_dataview_query(qid: str) -> str:
    """Dataview 쿼리를 마크다운 코드 블록으로 감싸 반환."""
    if qid not in DATAVIEW_QUERIES:
        raise ValueError(f"Unknown query ID: {qid}")
    return f"```dataview\n{DATAVIEW_QUERIES[qid]}\n```"


def generate_session_mermaid(conn: sqlite3.Connection, session_id: str) -> str:
    """세션 노드를 중심으로 그래프 Mermaid 다이어그램 생성."""
    visited = set()
    edges_str = []

    def add_node_label(nid: str) -> str:
        n = get_node(conn, nid)
        if not n:
            return f"{nid}[{nid}]"
        icon = TYPE_ICON.get(n.type.value, "")
        return f'{nid}["{icon} {n.title[:30]}"]'

    def walk(nid: str, depth: int = 0):
        if nid in visited or depth > 3:
            return
        visited.add(nid)
        for e in get_edges_from(conn, nid):
            edges_str.append(f"  {add_node_label(e.source_id)} -->|{e.relation.value}| {add_node_label(e.target_id)}")
            walk(e.target_id, depth + 1)
        for e in get_edges_to(conn, nid):
            if e.source_id not in visited:
                edges_str.append(f"  {add_node_label(e.source_id)} -->|{e.relation.value}| {add_node_label(e.target_id)}")
                walk(e.source_id, depth + 1)

    walk(session_id)
    if not edges_str:
        return f"```mermaid\ngraph TD\n  {add_node_label(session_id)}\n```"
    return "```mermaid\ngraph TD\n" + "\n".join(edges_str) + "\n```"
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd E:/KnowledgeHub && pytest tests/test_visualizer.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add khub/visualizer.py tests/test_visualizer.py
git commit -m "feat: add Dataview query catalog and Mermaid session graph generator"
```

---

## Task 21: 프로젝트 랜딩 페이지

**Files:**
- Create: `E:/KnowledgeHub/projects/DnT_Game.md`
- Create: `E:/KnowledgeHub/projects/DnT_Fermion.md`
- Create: `E:/KnowledgeHub/projects/Shared.md`

- [ ] **Step 1: DnT_Game.md 작성**

```markdown
<!-- E:/KnowledgeHub/projects/DnT_Game.md -->
---
project: DnT_Game
type: project_landing
last_updated: auto
---

# DnT_Game 프로젝트 상태

> 이 페이지는 기록군이 일 1회 자동 갱신합니다.

## 진행자
- **위상군** (`E:/DnT/DnT_WesangGoon`)
- 도메인: 게임 시스템 설계, 나선형 파이프라인

## 협력 에이전트
- 빌드군 (`E:/DnT/MRV_DnT`) — 코드 구현
- 아트군 (`E:/DnT/DnT_ArtGoon`) — UI/스프라이트 에셋
- 기획군 (`E:/QuantProject/DNT_GihakGoon`) — UX/심리 기획

## 📊 이번 주 활동

```dataview
TABLE 
  type AS "타입",
  agent_owner AS "담당",
  summary AS "요약"
FROM "notes"
WHERE project = "DnT_Game" AND created >= date(today) - dur(7 days)
SORT created DESC
```

## 🚀 진행 중 태스크

```dataview
TABLE
  task_id AS "ID",
  priority AS "P",
  status AS "상태",
  assigned_to AS "담당"
FROM "notes"
WHERE type = "task" AND project = "DnT_Game" AND status != "done"
SORT priority ASC, created DESC
```

## 🎓 최근 교훈

```dataview
TABLE lesson_text AS "교훈", generality AS "일반성"
FROM "notes"
WHERE type = "lesson" AND project = "DnT_Game"
SORT created DESC
LIMIT 5
```

## ⚠️ 미해결 마찰 패턴

```dataview
LIST
  "**" + evt.type + "**: " + evt.pattern + " (×" + evt.count + ")"
FROM "notes"
WHERE type = "session_journal" AND project = "DnT_Game"
FLATTEN friction_events AS evt
WHERE evt.count >= 2
```
```

- [ ] **Step 2: DnT_Fermion.md 작성**

```markdown
<!-- E:/KnowledgeHub/projects/DnT_Fermion.md -->
---
project: DnT_Fermion
type: project_landing
last_updated: auto
---

# DnT_Fermion 프로젝트 상태

> 이 페이지는 기록군이 일 1회 자동 갱신합니다.

## 진행자
- (별도 진행자 에이전트 — 추후 결정)
- 임시: 종일군 직접 + Fermion 에이전트

## 협력 에이전트
- 재미군 (`E:/QuantProject/DNT_JaemiGoon`) — 시뮬레이터 검증
- 기획군 (`E:/QuantProject/DNT_GihakGoon`) — 메타포 번역

## 📊 백테스트 결과 추이

```dataview
TABLE
  date AS "날짜",
  results.return_rate AS "수익률(%)",
  results.mdd AS "MDD(%)",
  results.sharpe AS "샤프"
FROM "notes"
WHERE type = "test_run" AND project = "DnT_Fermion" AND test_category = "backtest"
SORT date DESC
LIMIT 10
```

## 🚀 진행 중 태스크

```dataview
TABLE task_id, priority, status, assigned_to
FROM "notes"
WHERE type = "task" AND project = "DnT_Fermion" AND status != "done"
SORT priority ASC
```

## 🎓 교훈

```dataview
LIST lesson_text
FROM "notes"
WHERE type = "lesson" AND project = "DnT_Fermion"
SORT created DESC
```
```

- [ ] **Step 3: Shared.md 작성**

```markdown
<!-- E:/KnowledgeHub/projects/Shared.md -->
---
project: Shared
type: project_landing
last_updated: auto
---

# Shared (범용 교훈)

크로스 프로젝트 메타지식과 일반화된 교훈.

## 🌐 범용 교훈

```dataview
LIST lesson_text
FROM "notes"
WHERE type = "lesson" AND (generality = "universal" OR generality = "cross-project")
SORT confidence DESC
```

## 🔗 프로젝트 횡단 패턴

(Phase 3에서 자동 채워짐)
```

- [ ] **Step 4: Commit**

```bash
git add projects/
git commit -m "feat: add project landing pages with Dataview queries"
```

---

## Task 22: Obsidian Vault 설정

**Files:**
- Create: `E:/KnowledgeHub/.obsidian/core-plugins.json`
- Create: `E:/KnowledgeHub/.obsidian/community-plugins.json`
- Create: `E:/KnowledgeHub/.obsidian/app.json`

- [ ] **Step 1: core-plugins.json**

```json
[
  "file-explorer",
  "global-search",
  "switcher",
  "graph",
  "backlink",
  "outgoing-link",
  "tag-pane",
  "page-preview",
  "templates",
  "outline",
  "word-count"
]
```

- [ ] **Step 2: community-plugins.json**

```json
[
  "dataview"
]
```

- [ ] **Step 3: app.json (기본 설정)**

```json
{
  "alwaysUpdateLinks": true,
  "newLinkFormat": "shortest",
  "useMarkdownLinks": false,
  "attachmentFolderPath": "artifacts",
  "showLineNumber": true
}
```

- [ ] **Step 4: 사용자 안내 메시지 작성 (README에 추가)**

`E:/KnowledgeHub/README.md`에 다음 섹션 추가:

```markdown
## Obsidian 첫 설정

1. Obsidian 실행 → "Open folder as vault" → `E:/KnowledgeHub` 선택
2. Settings → Community plugins → Turn on
3. Community plugins → Browse → "Dataview" 검색 → Install + Enable
4. (선택) "Charts", "Templater", "Kanban" 검색 → Install + Enable
5. Settings → Files & Links → Default location: `notes`
6. Graph view 열기 → 색상 그룹 추가:
   - `tag:#type/idea` → 노란색
   - `tag:#type/task` → 파란색
   - `tag:#type/lesson` → 빨간색
   - 등등 (또는 frontmatter 기반)
```

- [ ] **Step 5: Commit**

```bash
git add .obsidian/ README.md
git commit -m "feat: add Obsidian vault configuration files"
```

---

## Task 23: Smoke Test

**Files:**
- Create: `E:/KnowledgeHub/tests/test_smoke.py`

- [ ] **Step 1: smoke 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_smoke.py
"""end-to-end smoke test — DB 초기화부터 검색까지 한 번에 검증."""
import pytest
from click.testing import CliRunner
from khub.cli import cli

def test_smoke_full_pipeline(tmp_path, monkeypatch):
    """전체 파이프라인 동작 확인."""
    hub = tmp_path / "smoke_hub"
    hub.mkdir()
    monkeypatch.setenv("KHUB_ROOT", str(hub))
    runner = CliRunner()

    # 1. Init
    r1 = runner.invoke(cli, ["init"])
    assert r1.exit_code == 0
    assert (hub / ".index" / "wiki.db").exists()

    # 2. Capture idea
    r2 = runner.invoke(cli, [
        "capture", "idea", "스프링 튜닝",
        "--project", "DnT_Game",
        "--hypothesis", "stiffness 부족"
    ])
    assert r2.exit_code == 0
    idea_id = r2.output.strip()
    assert idea_id.startswith("idea-")

    # 3. Capture task linked to idea
    r3 = runner.invoke(cli, [
        "capture", "task", "Q-011 스프링 튜닝",
        "--task-id", "Q-011",
        "--priority", "P1",
        "--spawned-by", idea_id,
    ])
    assert r3.exit_code == 0
    task_id = r3.output.strip()

    # 4. Journal
    r4 = runner.invoke(cli, [
        "journal", "EADDRINUSE port 3000",
        "--type", "repeated_error", "--count", "1"
    ])
    assert r4.exit_code == 0

    # 5. Search
    r5 = runner.invoke(cli, ["search", "스프링"])
    assert r5.exit_code == 0
    assert "스프링" in r5.output or idea_id in r5.output

    # 6. Graph
    r6 = runner.invoke(cli, ["graph", "node", idea_id])
    assert r6.exit_code == 0

    # 7. Link
    r7 = runner.invoke(cli, ["capture", "feedback", "OK",
                              "--target", task_id, "--rating", "8"])
    assert r7.exit_code == 0

    # 8. Index
    r8 = runner.invoke(cli, ["index"])
    assert r8.exit_code == 0
```

- [ ] **Step 2: smoke 테스트 실행**

```bash
cd E:/KnowledgeHub && pytest tests/test_smoke.py -v
```

Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add end-to-end smoke test"
```

---

## Task 24: end-to-end 시나리오 테스트 (모션 스프링 튜닝)

**Files:**
- Create: `E:/KnowledgeHub/tests/test_e2e_scenario.py`

- [ ] **Step 1: 시나리오 테스트 작성**

```python
# E:/KnowledgeHub/tests/test_e2e_scenario.py
"""스펙 Section 13 모션 스프링 튜닝 시나리오 통합 테스트."""
import pytest
from datetime import datetime
from pathlib import Path
from khub.db import get_connection, init_db
from khub.wiki_api import WikiAPI
from khub.girok import GirokAgent
from khub.friction import record_friction

@pytest.fixture
def hub(tmp_path):
    root = tmp_path / "hub"
    for sub in ["notes", "mirrors", "artifacts/dnt", ".index"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    init_db(root / ".index" / "wiki.db")
    return root

def test_motion_spring_scenario_full_cycle(hub):
    """Day 1-2 전체 흐름 재현."""
    api = WikiAPI(db_path=hub / ".index" / "wiki.db")
    girok = GirokAgent(hub_root=hub)

    # Day 1 14:20 — 종일군 아이디어 캡처
    idea_id = api.add_node(
        type="idea",
        frontmatter={
            "project": "DnT_Game",
            "title": "ItemSlotBar 스프링 재튜닝",
            "agent_owner": "jongil",
            "actionability": 7,
            "hypothesis": "stiffness 부족으로 bounce 큼",
            "tags": ["motion", "spring"],
        },
        body="ItemSlotBar 드래그 감이 너무 탄력적",
    )
    assert idea_id.startswith("idea-")

    # Day 1 14:25 — Task 변환
    task_id = api.add_node(
        type="task",
        frontmatter={
            "project": "DnT_Game",
            "title": "Q-011 ItemSlotBar 스프링 튜닝",
            "task_id": "Q-011",
            "priority": "P1",
            "status": "pending",
            "assigned_to": "build_goon",
        },
    )
    api.add_edge(idea_id, task_id, "spawns")

    # Day 1 16:00-18:00 — 빌드군 작업 (3 시도 + 마찰)
    # 마찰 기록
    record_friction(
        get_connection(hub / ".index" / "wiki.db"),
        "ItemSlotBar TargetDragger ref 공유",
        "repeated_error",
    )

    # 18:00 — 기록군이 Session/TestRun/Journal 자동 생성
    session_id = girok.on_session_end(
        agent_owner="build_goon",
        session_number=16,
        summary="Q-011 스프링 튜닝 완료",
    )
    api.add_edge(task_id, session_id, "executed_in")

    testrun_id = api.add_node(
        type="test_run",
        frontmatter={
            "project": "DnT_Game",
            "title": "Spring tuning playtest",
            "test_category": "playtest",
            "build": {"version": "v3.0.8", "commit": "abc123def"},
            "parameters": {"stiffness": 250, "damping": 25},
            "results": {"feel": "stable, 조작감 양호"},
            "screenshots": {
                "current": "artifacts/dnt/2026-04-07_현재_stiff250.png",
            },
        },
    )
    api.add_edge(session_id, testrun_id, "produces")

    journal_id = api.add_node(
        type="session_journal",
        frontmatter={
            "project": "DnT_Game",
            "title": "Session 16 Journal",
            "session_ref": session_id,
            "friction_events": [
                {"type": "dead_end", "attempt": "stiffness=300", "why_abandoned": "너무 딱딱"},
                {"type": "repeated_error", "pattern": "ref 공유", "count": 1},
            ],
        },
    )
    api.add_edge(session_id, journal_id, "produces_journal")

    # Day 1 20:00 — 종일군 피드백
    feedback_id = api.add_node(
        type="feedback",
        frontmatter={
            "project": "DnT_Game",
            "title": "Spring approval",
            "target_node": testrun_id,
            "from_user": "jongil",
            "rating": 8,
            "decision": "keep",
            "notes": "좋은데 더 단단해도 OK",
        },
    )
    api.add_edge(feedback_id, testrun_id, "feedback_by")

    # Day 2 09:00 — 기록군 Lesson 정제
    lesson_id = api.add_node(
        type="lesson",
        frontmatter={
            "project": "DnT_Game",
            "title": "Motion spring baseline",
            "generality": "project",
            "lesson_text": "DnT UI 드래그는 stiffness 250~280 기본",
            "evidence": [testrun_id, journal_id],
            "confidence": 0.8,
        },
    )
    api.add_edge(testrun_id, lesson_id, "distilled_into")
    api.add_edge(journal_id, lesson_id, "distilled_into")

    # 검증: 6개 노드 + 7개 엣지 그래프 형성
    all_nodes = [idea_id, task_id, session_id, testrun_id, journal_id, feedback_id, lesson_id]
    assert len(set(all_nodes)) == 7  # 모두 unique

    # 검색 검증
    results = api.search("스프링")
    assert any(r["id"] == idea_id for r in results)

    # 그래프 탐색 검증 (idea에서 시작해서 lesson까지 도달)
    history = api.get_history(idea_id)
    history_ids = {n.id for n in history}
    assert task_id in history_ids
    assert session_id in history_ids
    assert lesson_id in history_ids
```

- [ ] **Step 2: 시나리오 테스트 실행**

```bash
cd E:/KnowledgeHub && pytest tests/test_e2e_scenario.py -v
```

Expected: 1 passed

- [ ] **Step 3: Commit**

```bash
git add tests/test_e2e_scenario.py
git commit -m "test: add end-to-end motion spring scenario"
```

---

## Task 25: Hooks 통합 + 실행 가이드

**Files:**
- Create: `E:/KnowledgeHub/docs/HOOKS_INTEGRATION.md`
- Modify: `E:/DnT/DnT_WesangGoon/.claude/settings.local.json` (수동 안내)

- [ ] **Step 1: HOOKS_INTEGRATION.md 작성**

```markdown
<!-- E:/KnowledgeHub/docs/HOOKS_INTEGRATION.md -->
# Claude Code Hook 통합 가이드

KnowledgeHub의 기록군을 Claude Code 세션 종료 시 자동 호출하려면
각 에이전트 프로젝트의 `.claude/settings.local.json`에 hook을 추가합니다.

## Stop Hook 추가 (위상군 예시)

`E:/DnT/DnT_WesangGoon/.claude/settings.local.json`의 `hooks.Stop` 배열에 추가:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python -m khub.girok_hook on_session_end --owner wesang_goon",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

`girok_hook.py` 파일도 작성 (KnowledgeHub의 khub/ 아래):

```python
# E:/KnowledgeHub/khub/girok_hook.py
"""Stop hook 진입점."""
import sys
import argparse
from pathlib import Path
from .girok import GirokAgent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["on_session_end", "daily_check"])
    parser.add_argument("--owner", default="unknown")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    hub_root = Path("E:/KnowledgeHub")
    g = GirokAgent(hub_root=hub_root)

    if args.action == "on_session_end":
        nid = g.on_session_end(agent_owner=args.owner, summary=args.summary)
        print(f"기록군: Session 노드 생성 — {nid}")
    elif args.action == "daily_check":
        result = g.daily_check()
        print(f"기록군 일일 검사 — 승격 후보 {result['candidate_count']}건")

if __name__ == "__main__":
    main()
```

## Tier 1 — 전문 에이전트 의무 조항

각 에이전트의 CLAUDE.md / agent prompt에 다음 조항 추가:

```markdown
## 작업 종료 의무 (Knowledge Recording Duty)

모든 작업 단위 완료 시 다음을 호출한다:
- `python -m khub.cli capture testrun "Q-XXX 결과" --category playtest --artifact ...`
- 실패한 시도가 있었다면: `python -m khub.cli journal "패턴" --type dead_end`

이는 위상군이나 기록군이 잡지 못할 수 있는 디테일을 보존하기 위함이다.
"잡힐 거다"고 가정하지 말 것.
```

## 파일 Watcher 실행 (장기 실행)

별도 터미널에서:

```bash
cd E:/KnowledgeHub
python -m khub.watcher --sources E:/DnT/DnT_WesangGoon/handover_doc E:/DnT/MRV_DnT/handover_doc
```

(Phase 1 후반에 watcher.py 추가, 또는 cron/스케줄러 사용)

## 미감지 패턴 알림 — daily_check

매일 00:00 cron 또는 schedule로:

```bash
python -m khub.girok_hook daily_check
```
```

- [ ] **Step 2: girok_hook.py 작성**

`HOOKS_INTEGRATION.md`에 포함된 코드 그대로 `E:/KnowledgeHub/khub/girok_hook.py`로 작성.

```python
# E:/KnowledgeHub/khub/girok_hook.py
"""Stop hook 진입점."""
import argparse
from pathlib import Path
from .girok import GirokAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["on_session_end", "daily_check"])
    parser.add_argument("--owner", default="unknown")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    hub_root = Path("E:/KnowledgeHub")
    g = GirokAgent(hub_root=hub_root)

    if args.action == "on_session_end":
        nid = g.on_session_end(agent_owner=args.owner, summary=args.summary)
        print(f"기록군: Session 노드 생성 — {nid}")
    elif args.action == "daily_check":
        result = g.daily_check()
        print(f"기록군 일일 검사 — 승격 후보 {result['candidate_count']}건")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 실행 가능 검증**

```bash
cd E:/KnowledgeHub && python -m khub.girok_hook daily_check
```

Expected: `기록군 일일 검사 — 승격 후보 0건` (또는 비슷한 출력)

- [ ] **Step 4: Commit**

```bash
git add docs/HOOKS_INTEGRATION.md khub/girok_hook.py
git commit -m "feat: add hook integration guide and entry point"
```

---

## Task 26: Phase 1 합격 기준 검증 (수동)

이건 코드 변경이 아니라 **체크리스트 실행**이다. 모든 Task 완료 후 종일군이 직접 검증.

- [ ] **Step 1: 자동 합격 기준 (테스트로 검증)**

```bash
cd E:/KnowledgeHub && pytest -v --tb=short
```

Expected: 모든 테스트 통과 (60+ passed)

- [ ] **Step 2: 위상군 핸드오버 1주일치 미러링 검증**

```bash
cd E:/KnowledgeHub && python -m khub.cli init  # 이미 했으면 skip
python -c "
from pathlib import Path
from khub.adapters.claude_standard import ClaudeStandardAdapter
from khub.mirror_sync import sync_source_root
from khub.db import get_connection

src = Path('E:/DnT/DnT_WesangGoon/handover_doc')
adapter = ClaudeStandardAdapter(source_roots=[src], project='DnT_Game')
conn = get_connection(Path('E:/KnowledgeHub/.index/wiki.db'))
count = sync_source_root(conn, adapter, src, Path('E:/KnowledgeHub/mirrors'))
print(f'wesang 미러: {count}건')
"
```

Expected: `wesang 미러: N건` (N >= 1)

- [ ] **Step 3: Obsidian Graph View 수동 검증**

1. Obsidian 실행 → `E:/KnowledgeHub` vault 열기
2. Graph View 열기
3. 6노드 시나리오 클러스터(Task 24의 시나리오)가 시각화되는지 확인

- [ ] **Step 4: 10개 Dataview 쿼리 수동 검증**

`projects/DnT_Game.md` 열어서 각 쿼리가 정상 렌더링되는지 확인.

- [ ] **Step 5: 종일군 일주일 사용 (최종 합격 기준)**

종일군이 일주일간 노션 대신 KnowledgeHub로:
- 아이디어 캡처 (`/k-capture idea`)
- 태스크 생성 (`/k-capture task`)
- 마찰 기록 (`/k-journal`)
- 피드백 (`/k-capture feedback`)
- 검색 (`/k-search`)

일주일 후 종일군 판단: **"이걸로 가능"**이면 Phase 1 완료.

---

# Self-Review

## 1. Spec Coverage

스펙의 각 섹션을 plan과 매핑:

| 스펙 섹션 | Plan Task |
|---|---|
| §1 배경 | (Task 없음, 동기) |
| §2 목표/비목표 | 전체 plan이 목표 1-8 충족 |
| §3 설계 원칙 | 모든 task에 반영 |
| §4 아키텍처 개요 | Task 1, 3 |
| §5 파일 시스템 레이아웃 | Task 1 (디렉토리), 21, 22 |
| §6.1-6.4 노드/엣지 | Task 2 |
| §6.5 SQLite 스키마 | Task 3 |
| §6.6 파일 네이밍 | Task 14 (add_node 내부) |
| §7 누락 방지 3-Tier | Task 18 (girok), Task 25 (Tier 1 의무 조항 가이드) |
| §8.1 BaseAdapter | Task 8 |
| §8.2-8.4 claude_standard | Task 9 |
| §8.5 인덱싱 파이프라인 | Task 10, 11 |
| §8.6 증분 감지 | Task 10 |
| §8.7 충돌 처리 | Task 10 (protected 플래그) |
| §9 슬래시 커맨드 8개 | Task 15, 16, 17 |
| §10 기록군 Subagent | Task 18, 19 |
| §11 진행자 인터페이스 | Task 13, 14 |
| §12.1 Vault 설정 | Task 22 |
| §12.2 Graph View | Task 22 (안내) |
| §12.3 Dataview 쿼리 10개 | Task 20 |
| §12.4 랜딩 페이지 | Task 21 |
| §12.5 Mermaid | Task 20 |
| §13 사용 시나리오 검증 | Task 24 |
| §14 에러 처리 | Task 10 (parse error quarantine) |
| §15 테스트 전략 | Task 23, 24 + 각 Task의 단위 테스트 |
| §16 합격 기준 | Task 26 |
| §17 Phase 2/3 로드맵 | (out of scope) |

**누락 없음. 모든 스펙 요구사항이 task로 매핑됨.**

## 2. Placeholder 스캔
- ✅ TBD/TODO 표시 없음
- ✅ "implement later", "fill in details" 없음
- ✅ 모든 step에 실제 코드/명령
- ✅ 함수 시그니처 모두 정의됨

## 3. 타입 일관성
- ✅ `NodeType` enum 7값 일관 (`idea`, `task`, `session`, `test_run`, `session_journal`, `lesson`, `feedback`)
- ✅ `EdgeRelation` 8값 일관
- ✅ `WikiAPI.add_node(type, frontmatter, body)` 시그니처 일관
- ✅ `Node` dataclass 필드 모든 task에서 동일하게 사용
- ✅ `friction_patterns` 테이블 컬럼명 schema(Task 3)와 친구 모듈(Task 12) 일치

## 4. 모호성
- ✅ 함수명 일관: `record_friction()`, `get_neighbors()`, `add_node()` 등 전체 plan에서 동일
- ✅ 파일 경로 모두 절대경로
- ✅ enum 값 모두 명시 (`status`, `priority`, `generality` 등)

**Self-review 통과. 수정 사항 없음.**

---

# Execution Handoff

Plan complete and saved to `E:/DnT/DnT_WesangGoon/docs/superpowers/plans/2026-04-07-knowledge-hub.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — 각 Task마다 fresh subagent 디스패치, task 사이에 리뷰, 빠른 반복

**2. Inline Execution** — 이 세션에서 superpowers:executing-plans 사용, 체크포인트 단위 배치 실행

**Which approach?**

