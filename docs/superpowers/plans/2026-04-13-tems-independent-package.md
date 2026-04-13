# TEMS Independent Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract TEMS from `E:/AgentInterface/tems_core/` into standalone `bobpullie/TEMS` git repo with PyPI package (`tems`) + Claude Code skill dual deployment.

**Architecture:** src-layout Python package. Core modules (fts5_memory, tems_engine, rebuild_from_qmd) copied as-is. scaffold.py adapted from tems_scaffold.py with `TEMS_REGISTRY_PATH` env var support. CLI entry via `tems` command (scaffold, init-skill). Templates bundled as package_data via `importlib.resources`.

**Tech Stack:** Python 3.10+, hatchling build backend, sqlite3 (stdlib), pytest, no external runtime deps.

**Source spec:** `docs/superpowers/specs/2026-04-13-tems-independent-package-design.md`

---

## File Structure

```
E:/bobpullie/TEMS/                    # New git repo
├── pyproject.toml                     # Package config (hatchling)
├── src/
│   └── tems/
│       ├── __init__.py                # Public API exports
│       ├── fts5_memory.py             # ← E:/AgentInterface/tems_core/fts5_memory.py (as-is)
│       ├── tems_engine.py             # ← E:/AgentInterface/tems_core/tems_engine.py (import fix)
│       ├── rebuild_from_qmd.py        # ← E:/AgentInterface/tems_core/rebuild_from_qmd.py (as-is)
│       ├── scaffold.py                # ← E:/AgentInterface/tems_scaffold.py (registry path refactor)
│       ├── cli.py                     # CLI dispatcher: tems scaffold / tems init-skill
│       ├── templates/                 # package_data (importlib.resources)
│       │   ├── preflight_hook.py      # ← tems_templates/ (import path updated)
│       │   ├── tems_commit.py         # ← tems_templates/ (import path updated)
│       │   └── gitignore.template     # ← tems_templates/ (as-is)
│       └── skill/                     # init-skill deployment source
│           ├── SKILL.md               # Claude Code skill definition (new)
│           └── references/
│               └── tems-architecture.md  # ← .claude/references/ (as-is)
├── tests/
│   ├── conftest.py                    # Shared fixtures (tmp_path DB, etc.)
│   ├── test_fts5_memory.py            # FTS5+BM25 unit tests
│   ├── test_scaffold.py               # Scaffold + registry tests
│   ├── test_cli.py                    # CLI integration tests
│   └── test_rebuild.py                # QMD rebuild tests
├── .gitignore
├── LICENSE
└── README.md
```

**Key decisions:**
- `fts5_memory.py`, `tems_engine.py`, `rebuild_from_qmd.py` are copied with minimal changes (only internal imports)
- `scaffold.py` is the most changed file: `REGISTRY_PATH` → `get_registry_path()` with env var
- Templates get new import paths (`from tems.` instead of `from tems_core.`)
- No tests for tems_engine.py internals in v0.1.0 — that's 2040 LOC of evolved engines; test the public surface only

---

### Task 1: Repository + pyproject.toml

**Files:**
- Create: `E:/bobpullie/TEMS/.gitignore`
- Create: `E:/bobpullie/TEMS/pyproject.toml`
- Create: `E:/bobpullie/TEMS/README.md`
- Create: `E:/bobpullie/TEMS/LICENSE`

- [ ] **Step 1: Create repo directory + git init**

```bash
mkdir -p E:/bobpullie/TEMS
cd E:/bobpullie/TEMS
git init
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tems"
version = "0.1.0"
description = "Topological Evolving Memory System — self-evolving agent memory with FTS5+BM25, topological health scoring, and hybrid retrieval"
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov"]

[project.scripts]
tems = "tems.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/tems"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: Write .gitignore**

```
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.eggs/
*.db
*.db-journal
*.db-wal
*.db-shm
.pytest_cache/
.venv/
```

- [ ] **Step 4: Write README.md**

```markdown
# TEMS — Topological Evolving Memory System

Self-evolving agent memory system with FTS5+BM25 retrieval, topological health scoring, and hybrid sparse-dense search.

## Install

```bash
pip install -e ".[dev]"
```

## CLI

```bash
tems scaffold --agent-id myagent --agent-name "My Agent" --project MyProject --cwd /path/to/agent
tems init-skill
```
```

- [ ] **Step 5: Write LICENSE (MIT)**

Standard MIT license with "Triad Chord Studio" as copyright holder, year 2026.

- [ ] **Step 6: Create src/tems/ package directory**

```bash
mkdir -p E:/bobpullie/TEMS/src/tems/templates
mkdir -p E:/bobpullie/TEMS/src/tems/skill/references
mkdir -p E:/bobpullie/TEMS/tests
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore README.md LICENSE
git commit -m "chore: init repo with pyproject.toml (hatchling, src-layout)"
```

---

### Task 2: Core modules — fts5_memory.py

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/__init__.py`
- Create: `E:/bobpullie/TEMS/src/tems/fts5_memory.py`
- Create: `E:/bobpullie/TEMS/tests/conftest.py`
- Create: `E:/bobpullie/TEMS/tests/test_fts5_memory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_fts5_memory.py
"""FTS5+BM25 MemoryDB unit tests."""

import pytest
from tems.fts5_memory import MemoryDB


class TestMemoryDB:
    def test_commit_and_search(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        rule_id = db.commit_memory(
            context_tags=["python", "test"],
            action_taken="wrote test",
            result="passed",
            correction_rule="always write tests first",
            keyword_trigger="python test TDD",
            category="TCL",
        )
        assert rule_id > 0

        results = db.search("python test")
        assert len(results) >= 1
        assert results[0]["category"] == "TCL"

    def test_commit_tcl(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        rule_id = db.commit_tcl(
            original_instruction="앞으로 테스트 먼저 작성",
            topological_rule="TDD 의무화",
            keyword_trigger="TDD test 테스트",
            context_tags=["dev", "testing"],
        )
        assert rule_id > 0
        tcls = db.get_active_tcl()
        assert len(tcls) == 1
        assert tcls[0]["category"] == "TCL"

    def test_commit_tgl(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        rule_id = db.commit_tgl(
            error_description="cp949 인코딩 에러",
            topological_case="Windows subprocess encoding",
            guard_rule="subprocess에서 bytes I/O 사용",
            keyword_trigger="subprocess encoding cp949 Windows",
            context_tags=["Windows", "encoding"],
        )
        assert rule_id > 0
        tgls = db.get_active_tgl()
        assert len(tgls) == 1
        assert tgls[0]["category"] == "TGL"

    def test_preflight(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        db.commit_tcl("instruction", "rule1", "python import", ["dev"])
        db.commit_tgl("err", "case", "guard1", "encoding error", ["dev"])

        pf = db.preflight("python encoding")
        assert "tcl_hits" in pf
        assert "tgl_hits" in pf
        assert "general_hits" in pf

    def test_stats(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        db.commit_memory(["tag"], "action", "result", category="TCL")
        db.commit_memory(["tag"], "action", "result", category="TGL")
        stats = db.stats()
        assert stats["total_records"] == 2
        assert "TCL" in stats["by_category"]
        assert "TGL" in stats["by_category"]

    def test_auto_summarize(self, tmp_path):
        db = MemoryDB(str(tmp_path / "test.db"))
        summary = db._auto_summarize("Windows subprocess 시: bytes I/O 사용하고 UTF-8로 디코딩")
        assert len(summary) > 0
        assert len(summary) <= 40
```

- [ ] **Step 2: Write conftest.py**

```python
# tests/conftest.py
"""Shared test fixtures for TEMS."""
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd E:/bobpullie/TEMS
pip install -e ".[dev]"
pytest tests/test_fts5_memory.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tems'`

- [ ] **Step 4: Write __init__.py**

```python
# src/tems/__init__.py
"""TEMS — Topological Evolving Memory System."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Copy fts5_memory.py**

Copy `E:/AgentInterface/tems_core/fts5_memory.py` → `E:/bobpullie/TEMS/src/tems/fts5_memory.py`

No changes needed — this module has no internal cross-imports.

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_fts5_memory.py -v
```

Expected: 6 PASSED

- [ ] **Step 7: Commit**

```bash
git add src/tems/__init__.py src/tems/fts5_memory.py tests/conftest.py tests/test_fts5_memory.py
git commit -m "feat: add fts5_memory module with FTS5+BM25 retrieval"
```

---

### Task 3: Core modules — tems_engine.py + rebuild_from_qmd.py

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/tems_engine.py`
- Create: `E:/bobpullie/TEMS/src/tems/rebuild_from_qmd.py`

- [ ] **Step 1: Write smoke test for tems_engine import**

Append to `tests/test_fts5_memory.py` or create new file:

```python
# tests/test_engine_smoke.py
"""Smoke test: tems_engine imports correctly and core classes are accessible."""

def test_engine_imports():
    from tems.tems_engine import HybridRetriever, HealthScorer, RuleGraph
    assert HybridRetriever is not None
    assert HealthScorer is not None
    assert RuleGraph is not None

def test_rebuild_imports():
    from tems.rebuild_from_qmd import parse_qmd_rule, rebuild
    assert parse_qmd_rule is not None
    assert rebuild is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_engine_smoke.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Copy tems_engine.py with import fix**

Copy `E:/AgentInterface/tems_core/tems_engine.py` → `E:/bobpullie/TEMS/src/tems/tems_engine.py`

**One change required** — line 27:
```python
# Before:
from .fts5_memory import MemoryDB
# After (same — relative import works in new package too):
from .fts5_memory import MemoryDB
```

No change needed. The relative import `.fts5_memory` works because the new package is also `tems/`.

- [ ] **Step 4: Copy rebuild_from_qmd.py**

Copy `E:/AgentInterface/tems_core/rebuild_from_qmd.py` → `E:/bobpullie/TEMS/src/tems/rebuild_from_qmd.py`

No changes needed — this module uses only stdlib (sqlite3, pathlib, re, json).

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_engine_smoke.py -v
```

Expected: 2 PASSED

- [ ] **Step 6: Commit**

```bash
git add src/tems/tems_engine.py src/tems/rebuild_from_qmd.py tests/test_engine_smoke.py
git commit -m "feat: add tems_engine (4-phase orchestrator) and rebuild_from_qmd"
```

---

### Task 4: scaffold.py — Registry path refactor

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/scaffold.py`
- Create: `E:/bobpullie/TEMS/tests/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scaffold.py
"""Scaffold + registry tests."""

import json
import os
import pytest
from pathlib import Path
from tems.scaffold import (
    create_marker,
    create_directories,
    create_database,
    get_registry_path,
    load_registry,
    save_registry,
    update_registry,
)


class TestGetRegistryPath:
    def test_env_var_override(self, tmp_path, monkeypatch):
        reg_path = tmp_path / "custom_registry.json"
        monkeypatch.setenv("TEMS_REGISTRY_PATH", str(reg_path))
        result = get_registry_path()
        assert result == reg_path

    def test_default_fallback_missing(self, monkeypatch):
        monkeypatch.delenv("TEMS_REGISTRY_PATH", raising=False)
        # Default path E:/AgentInterface/tems_registry.json may or may not exist
        result = get_registry_path()
        # Should return Path or None (None if default doesn't exist)
        assert result is None or isinstance(result, Path)


class TestCreateMarker:
    def test_create_new(self, tmp_path):
        result = create_marker(tmp_path, "testagent", force=False)
        assert result == "marker_created"
        marker = tmp_path / ".claude" / "tems_agent_id"
        assert marker.read_text(encoding="utf-8").strip() == "testagent"

    def test_existing_same_id(self, tmp_path):
        create_marker(tmp_path, "testagent", force=False)
        result = create_marker(tmp_path, "testagent", force=False)
        assert result == "marker_exists"

    def test_existing_different_id_raises(self, tmp_path):
        create_marker(tmp_path, "agent_a", force=False)
        with pytest.raises(ValueError, match="different ID"):
            create_marker(tmp_path, "agent_b", force=False)

    def test_force_overwrite(self, tmp_path):
        create_marker(tmp_path, "agent_a", force=False)
        result = create_marker(tmp_path, "agent_b", force=True)
        assert result == "marker_created"


class TestCreateDirectories:
    def test_creates_memory_and_qmd(self, tmp_path):
        actions = create_directories(tmp_path)
        assert "memory_dir_created" in actions
        assert "qmd_rules_dir_created" in actions
        assert (tmp_path / "memory").is_dir()
        assert (tmp_path / "memory" / "qmd_rules").is_dir()


class TestCreateDatabase:
    def test_creates_db_with_full_schema(self, tmp_path):
        (tmp_path / "memory").mkdir()
        result = create_database(tmp_path, force=False)
        assert result == "db_created"

        import sqlite3
        conn = sqlite3.connect(str(tmp_path / "memory" / "error_logs.db"))
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()

        for expected in ["memory_logs", "rule_health", "exceptions",
                         "meta_rules", "rule_edges", "co_activations"]:
            assert expected in tables


class TestRegistryCRUD:
    def test_load_save_roundtrip(self, tmp_path):
        reg_path = tmp_path / "registry.json"
        registry = load_registry(reg_path)
        assert registry["version"] == 1
        registry["agents"]["test"] = {"name": "Test", "status": "active"}
        save_registry(registry, reg_path)

        loaded = load_registry(reg_path)
        assert "test" in loaded["agents"]

    def test_update_registry_new_agent(self, tmp_path):
        reg_path = tmp_path / "registry.json"
        result = update_registry(
            "testagent", "Test Agent", "TestProject",
            str(tmp_path / "memory" / "error_logs.db"),
            registry_path=reg_path,
        )
        assert result == "agent_registered"

        registry = load_registry(reg_path)
        assert "testagent" in registry["agents"]
        assert "TestProject" in registry["projects"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scaffold.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write scaffold.py**

Copy `E:/AgentInterface/tems_scaffold.py` → `E:/bobpullie/TEMS/src/tems/scaffold.py` with these changes:

**Change 1:** Replace hardcoded `REGISTRY_PATH` and `TEMPLATES_DIR` (lines 17-18):

```python
# Before:
REGISTRY_PATH = Path("E:/AgentInterface/tems_registry.json")
TEMPLATES_DIR = Path("E:/AgentInterface/tems_templates")

# After:
import importlib.resources

_DEFAULT_REGISTRY = Path("E:/AgentInterface/tems_registry.json")


def get_registry_path() -> Path | None:
    """Registry path resolution: env var → default → None."""
    env = os.environ.get("TEMS_REGISTRY_PATH")
    if env:
        return Path(env)
    if _DEFAULT_REGISTRY.exists():
        return _DEFAULT_REGISTRY
    return None


def _get_template_path(filename: str) -> Path:
    """Get template file path from package_data via importlib.resources."""
    ref = importlib.resources.files("tems") / "templates" / filename
    return Path(str(ref))
```

**Change 2:** In `copy_templates()`, replace `TEMPLATES_DIR / filename` with `_get_template_path(filename)`:

```python
def copy_templates(cwd: Path, force: bool) -> list[str]:
    actions = []
    for filename in ("preflight_hook.py", "tems_commit.py"):
        src = _get_template_path(filename)
        dst = cwd / "memory" / filename
        if dst.exists() and not force:
            actions.append(f"{filename}_exists")
            continue
        shutil.copy2(str(src), str(dst))
        actions.append(f"{filename}_copied")
    return actions
```

**Change 3:** In `install_gitignore()`, replace `TEMPLATES_DIR / "gitignore.template"` with `_get_template_path("gitignore.template")`.

**Change 4:** In `update_registry()`, replace `REGISTRY_PATH` references with registry_path parameter:

```python
def update_registry(agent_id: str, agent_name: str, project: str, db_path: str,
                    registry_path: Path = None) -> str:
    path = registry_path or get_registry_path()
    if path is None:
        return "registry_unavailable"
    # ... rest uses path instead of REGISTRY_PATH
```

**Change 5:** In `load_registry()` and `save_registry()`, default to `get_registry_path()`:

```python
def load_registry(registry_path: Path = None) -> dict:
    path = registry_path or get_registry_path()
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"version": 1, "registry_path": str(path or ""), "projects": {}, "agents": {}}
```

**Change 6:** In `main()` argparse, remove hardcoded paths. The `scaffold` subcommand calls `update_registry()` with `registry_path=get_registry_path()`.

All other functions (`create_marker`, `create_directories`, `create_database`, `_create_tables`, `register_hook`, `add_project_to_agent`, `rename_project`, `retire_agent`, `reactivate_agent`, `restore_agent`) remain identical except replacing `REGISTRY_PATH` with `get_registry_path()`.

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_scaffold.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/tems/scaffold.py tests/test_scaffold.py
git commit -m "feat: add scaffold with TEMS_REGISTRY_PATH env var support"
```

---

### Task 5: Templates — package_data

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/templates/preflight_hook.py`
- Create: `E:/bobpullie/TEMS/src/tems/templates/tems_commit.py`
- Create: `E:/bobpullie/TEMS/src/tems/templates/gitignore.template`
- Create: `E:/bobpullie/TEMS/src/tems/templates/__init__.py`

- [ ] **Step 1: Write test for template accessibility**

```python
# tests/test_templates.py
"""Verify templates are accessible as package_data."""

import importlib.resources
from pathlib import Path


def test_templates_exist():
    """All 3 template files must be accessible via importlib.resources."""
    for name in ("preflight_hook.py", "tems_commit.py", "gitignore.template"):
        ref = importlib.resources.files("tems") / "templates" / name
        path = Path(str(ref))
        assert path.exists(), f"Template missing: {name}"


def test_preflight_uses_tems_import():
    """New template must import from 'tems' not 'tems_core'."""
    ref = importlib.resources.files("tems") / "templates" / "preflight_hook.py"
    content = Path(str(ref)).read_text(encoding="utf-8")
    assert "from tems." in content or "import tems" in content
    assert "tems_core" not in content
    assert "E:/AgentInterface" not in content


def test_tems_commit_uses_tems_import():
    """New template must import from 'tems' not 'tems_core'."""
    ref = importlib.resources.files("tems") / "templates" / "tems_commit.py"
    content = Path(str(ref)).read_text(encoding="utf-8")
    assert "from tems." in content or "import tems" in content
    assert "tems_core" not in content
    assert "E:/AgentInterface" not in content
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_templates.py -v
```

Expected: FAIL — templates don't exist yet

- [ ] **Step 3: Create templates/__init__.py**

```python
# src/tems/templates/__init__.py (empty package marker for importlib.resources)
```

- [ ] **Step 4: Copy and update preflight_hook.py**

Copy `E:/AgentInterface/tems_templates/preflight_hook.py` → `E:/bobpullie/TEMS/src/tems/templates/preflight_hook.py`

**Changes:**

Line 13-18 — Remove sys.path hack, update imports:
```python
# Before:
TEMS_CORE = Path("E:/AgentInterface")
sys.path.insert(0, str(TEMS_CORE))
from tems_core.fts5_memory import MemoryDB
from tems_core.tems_engine import EnhancedPreflight, RuleGraph, HybridRetriever

# After:
from tems.fts5_memory import MemoryDB
from tems.tems_engine import EnhancedPreflight, RuleGraph, HybridRetriever
```

Line 36 — Registry path:
```python
# Before:
REGISTRY_PATH = Path("E:/AgentInterface/tems_registry.json")

# After:
import os
_reg_env = os.environ.get("TEMS_REGISTRY_PATH")
REGISTRY_PATH = Path(_reg_env) if _reg_env else Path("E:/AgentInterface/tems_registry.json")
```

Line 379 — PredictiveTGL import:
```python
# Before:
from tems_core.tems_engine import PredictiveTGL

# After:
from tems.tems_engine import PredictiveTGL
```

All other code remains identical.

- [ ] **Step 5: Copy and update tems_commit.py**

Copy `E:/AgentInterface/tems_templates/tems_commit.py` → `E:/bobpullie/TEMS/src/tems/templates/tems_commit.py`

**Changes:**

Lines 13-15 — Remove sys.path hack:
```python
# Before:
TEMS_CORE = Path("E:/AgentInterface")
sys.path.insert(0, str(TEMS_CORE))

# After:
# (removed — tems package is pip-installed)
```

Line 78-79 — Update import:
```python
# Before:
from tems_core.tems_engine import sync_single_rule_to_qmd
from tems_core.fts5_memory import MemoryDB

# After:
from tems.tems_engine import sync_single_rule_to_qmd
from tems.fts5_memory import MemoryDB
```

- [ ] **Step 6: Copy gitignore.template**

Copy `E:/AgentInterface/tems_templates/gitignore.template` → `E:/bobpullie/TEMS/src/tems/templates/gitignore.template`

No changes needed.

- [ ] **Step 7: Run test to verify it passes**

```bash
pytest tests/test_templates.py -v
```

Expected: 3 PASSED

- [ ] **Step 8: Commit**

```bash
git add src/tems/templates/
git commit -m "feat: add templates as package_data with updated import paths"
```

---

### Task 6: CLI — cli.py

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/cli.py`
- Create: `E:/bobpullie/TEMS/tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
"""CLI integration tests."""

import subprocess
import sys
import json
import pytest
from pathlib import Path


def run_tems(*args) -> subprocess.CompletedProcess:
    """Run `tems` CLI command."""
    return subprocess.run(
        [sys.executable, "-m", "tems.cli", *args],
        capture_output=True, text=True, timeout=30,
    )


class TestCLIScaffold:
    def test_scaffold_creates_agent(self, tmp_path):
        reg = tmp_path / "registry.json"
        result = run_tems(
            "scaffold",
            "--agent-id", "testagent",
            "--agent-name", "Test Agent",
            "--project", "TestProject",
            "--cwd", str(tmp_path / "agent"),
            "--registry-path", str(reg),
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["ok"] is True

        # Verify artifacts
        agent_dir = tmp_path / "agent"
        assert (agent_dir / ".claude" / "tems_agent_id").exists()
        assert (agent_dir / "memory" / "error_logs.db").exists()

    def test_scaffold_missing_args(self):
        result = run_tems("scaffold")
        assert result.returncode != 0


class TestCLIInitSkill:
    def test_init_skill_copies_files(self, tmp_path):
        target = tmp_path / "skill_target"
        result = run_tems("init-skill", "--target", str(target))
        assert result.returncode == 0
        assert (target / "SKILL.md").exists()
        assert (target / "references" / "tems-architecture.md").exists()


class TestCLIHelp:
    def test_help(self):
        result = run_tems("--help")
        assert result.returncode == 0
        assert "scaffold" in result.stdout
        assert "init-skill" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'tems.cli'`

- [ ] **Step 3: Write cli.py**

```python
"""TEMS CLI — scaffold + init-skill commands."""

import argparse
import importlib.resources
import json
import shutil
import sys
from pathlib import Path

from .scaffold import (
    create_marker,
    create_directories,
    create_database,
    install_gitignore,
    copy_templates,
    register_hook,
    update_registry,
    get_registry_path,
    restore_agent,
    add_project_to_agent,
    rename_project,
    retire_agent,
    reactivate_agent,
)


def cmd_scaffold(args):
    """New agent environment setup."""
    cwd = Path(args.cwd).resolve()
    cwd.mkdir(parents=True, exist_ok=True)
    reg_path = Path(args.registry_path) if args.registry_path else get_registry_path()

    actions = []
    try:
        actions.append(create_marker(cwd, args.agent_id, args.force))
        actions.extend(create_directories(cwd))
        actions.append(create_database(cwd, args.force))
        actions.append(install_gitignore(cwd, args.force))
        actions.extend(copy_templates(cwd, args.force))
        actions.append(register_hook(cwd))
        db_path = str(cwd / "memory" / "error_logs.db")
        actions.append(update_registry(
            args.agent_id, args.agent_name, args.project, db_path,
            registry_path=reg_path,
        ))
        result = {"ok": True, "agent_id": args.agent_id, "actions": actions}
    except Exception as e:
        result = {"ok": False, "error": str(e), "actions": actions}

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def cmd_init_skill(args):
    """Deploy SKILL.md + references to Claude Code skills directory."""
    target = Path(args.target) if args.target else Path.home() / ".claude" / "skills" / "tems"
    target.mkdir(parents=True, exist_ok=True)

    skill_src = importlib.resources.files("tems") / "skill"
    actions = []

    # Copy SKILL.md
    skill_md = Path(str(skill_src / "SKILL.md"))
    if skill_md.exists():
        shutil.copy2(str(skill_md), str(target / "SKILL.md"))
        actions.append("SKILL.md copied")

    # Copy references/
    refs_src = Path(str(skill_src / "references"))
    refs_dst = target / "references"
    refs_dst.mkdir(parents=True, exist_ok=True)
    if refs_src.is_dir():
        for f in refs_src.iterdir():
            shutil.copy2(str(f), str(refs_dst / f.name))
            actions.append(f"references/{f.name} copied")

    result = {"ok": True, "target": str(target), "actions": actions}
    print(json.dumps(result, ensure_ascii=False))
    return 0


def cmd_restore(args):
    """Restore agent from registry."""
    reg_path = Path(args.registry_path) if args.registry_path else None
    try:
        result = restore_agent(args.agent_id, registry_path=reg_path)
    except Exception as e:
        result = {"ok": False, "error": str(e)}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


def main():
    parser = argparse.ArgumentParser(prog="tems", description="TEMS — Topological Evolving Memory System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scaffold
    p_scaffold = subparsers.add_parser("scaffold", help="New agent environment setup")
    p_scaffold.add_argument("--agent-id", required=True)
    p_scaffold.add_argument("--agent-name", required=True)
    p_scaffold.add_argument("--project", required=True)
    p_scaffold.add_argument("--cwd", required=True)
    p_scaffold.add_argument("--force", action="store_true")
    p_scaffold.add_argument("--registry-path", default=None)

    # init-skill
    p_init = subparsers.add_parser("init-skill", help="Deploy Claude Code skill")
    p_init.add_argument("--target", default=None)

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore agent from registry")
    p_restore.add_argument("--agent-id", required=True)
    p_restore.add_argument("--registry-path", default=None)

    # add / rename / retire / reactivate (passthrough to scaffold.py)
    p_add = subparsers.add_parser("add", help="Add project to agent")
    p_add.add_argument("--agent-id", required=True)
    p_add.add_argument("--project", required=True)
    p_add.add_argument("--registry-path", default=None)

    p_rename = subparsers.add_parser("rename", help="Rename project")
    p_rename.add_argument("--old", required=True)
    p_rename.add_argument("--new", required=True)
    p_rename.add_argument("--registry-path", default=None)

    p_retire = subparsers.add_parser("retire", help="Retire agent")
    p_retire.add_argument("--agent-id", required=True)
    p_retire.add_argument("--registry-path", default=None)

    p_react = subparsers.add_parser("reactivate", help="Reactivate agent")
    p_react.add_argument("--agent-id", required=True)
    p_react.add_argument("--registry-path", default=None)

    args = parser.parse_args()

    handlers = {
        "scaffold": cmd_scaffold,
        "init-skill": cmd_init_skill,
        "restore": cmd_restore,
    }

    if args.command in handlers:
        sys.exit(handlers[args.command](args))

    # Simple passthrough commands
    reg_path = Path(args.registry_path) if getattr(args, "registry_path", None) else None
    if args.command == "add":
        result = add_project_to_agent(args.agent_id, args.project, reg_path)
    elif args.command == "rename":
        result = rename_project(args.old, args.new, reg_path)
    elif args.command == "retire":
        result = retire_agent(args.agent_id, reg_path)
    elif args.command == "reactivate":
        result = reactivate_agent(args.agent_id, reg_path)
    else:
        print(json.dumps({"ok": False, "error": f"Unknown command: {args.command}"}))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_cli.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/tems/cli.py tests/test_cli.py
git commit -m "feat: add CLI with scaffold + init-skill commands"
```

---

### Task 7: Skill content — SKILL.md + references

**Files:**
- Create: `E:/bobpullie/TEMS/src/tems/skill/SKILL.md`
- Create: `E:/bobpullie/TEMS/src/tems/skill/references/tems-architecture.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: tems
description: TEMS (Topological Evolving Memory System) — agent self-evolving memory. Use when committing rules (TCL/TGL), debugging preflight, or checking rule health.
---

# TEMS — Topological Evolving Memory System

## Overview
4-Phase self-evolving memory:
1. **Hybrid Retrieval** — FTS5 BM25 (sparse) + QMD vector (dense) + RRF fusion
2. **Health Scoring** — THS lifecycle (hot → warm → cold → archive)
3. **Anomaly Certification** — Exception classification + rule promotion
4. **Meta-Rule Engine** — Godel Agent self-modification

## Rule Types
- **TCL** (Topological Checklist Loop): "앞으로/이제부터" → proactive checklist
- **TGL** (Topological Guard Loop): errors/mistakes → defensive guard rule

## Rule Registration
```bash
python memory/tems_commit.py --type TCL --rule "규칙 내용" --triggers "키워드" --tags "태그"
python memory/tems_commit.py --type TGL --rule "규칙 내용" --triggers "키워드" --tags "태그"
```

## Preflight
Automatically triggered via UserPromptSubmit hook. Injects `<preflight-memory-check>` with relevant TCL/TGL rules.

## DB Schema (10 tables)
- `memory_logs` — core rule storage
- `rule_health` — THS score + lifecycle status
- `exceptions` — anomaly classification
- `meta_rules` — self-modification audit
- `rule_edges` — topological connections
- `co_activations` — co-firing patterns
- `tgl_sequences` — temporal predecessor chains
- `trigger_misses` — keyword expansion learning
- `rule_versions` — evolution history
- `memory_fts` — FTS5 virtual table

## Troubleshooting
- **DB corruption:** `python -m tems.rebuild_from_qmd --agent-root <path>`
- **Missing rules:** Check `memory/qmd_rules/` (source of truth for rebuild)
- **Preflight silent:** Check `.claude/settings.local.json` hook registration
```

- [ ] **Step 2: Copy tems-architecture.md**

Copy `E:/DnT/DnT_WesangGoon/.claude/references/tems-architecture.md` → `E:/bobpullie/TEMS/src/tems/skill/references/tems-architecture.md`

No changes needed.

- [ ] **Step 3: Verify init-skill test still passes**

```bash
pytest tests/test_cli.py::TestCLIInitSkill -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/tems/skill/
git commit -m "feat: add SKILL.md and references for Claude Code skill deployment"
```

---

### Task 8: QMD rebuild tests

**Files:**
- Create: `E:/bobpullie/TEMS/tests/test_rebuild.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_rebuild.py
"""QMD rebuild tests — verify rule_*.md → DB restoration."""

import sqlite3
from pathlib import Path
from tems.rebuild_from_qmd import parse_qmd_rule, rebuild, resolve_agent_paths


class TestParseQmdRule:
    def test_valid_rule(self, tmp_path):
        rule_file = tmp_path / "rule_0001.md"
        rule_file.write_text("""---
rule_id: 1
category: TCL
tags: dev, testing
severity: directive
---

**Keywords:** TDD test pytest

**Rule:** Always write tests before implementation.

**Context:** [TCL] 원문: 앞으로 테스트 먼저 작성

**Result:** 위상적 변환 완료 → 규칙 활성화
""", encoding="utf-8")
        result = parse_qmd_rule(rule_file)
        assert result is not None
        assert result["rule_id"] == 1
        assert result["category"] == "TCL"
        assert "TDD" in result["keyword_trigger"]

    def test_invalid_no_frontmatter(self, tmp_path):
        rule_file = tmp_path / "rule_0002.md"
        rule_file.write_text("No frontmatter here", encoding="utf-8")
        result = parse_qmd_rule(rule_file)
        assert result is None

    def test_invalid_zero_id(self, tmp_path):
        rule_file = tmp_path / "rule_0000.md"
        rule_file.write_text("""---
rule_id: 0
category: TGL
---

**Keywords:** test
**Rule:** test rule
""", encoding="utf-8")
        result = parse_qmd_rule(rule_file)
        assert result is None


class TestResolveAgentPaths:
    def test_resolves_correctly(self, tmp_path):
        db_path, qmd_dir = resolve_agent_paths(tmp_path)
        assert db_path == tmp_path / "memory" / "error_logs.db"
        assert qmd_dir == tmp_path / "memory" / "qmd_rules"


class TestRebuild:
    def test_rebuild_empty_dir(self, tmp_path):
        qmd_dir = tmp_path / "qmd_rules"
        qmd_dir.mkdir()
        db_path = tmp_path / "test.db"
        result = rebuild(db_path, qmd_dir, dry_run=False)
        assert result["ok"] is True
        assert result["parsed"] == 0

    def test_rebuild_dry_run(self, tmp_path):
        qmd_dir = tmp_path / "qmd_rules"
        qmd_dir.mkdir()
        rule = qmd_dir / "rule_0001.md"
        rule.write_text("""---
rule_id: 1
category: TCL
tags: dev
severity: info
---

**Keywords:** test
**Rule:** test rule
**Context:** context
**Result:** result
""", encoding="utf-8")

        result = rebuild(tmp_path / "test.db", qmd_dir, dry_run=True)
        assert result["ok"] is True
        assert result["parsed"] == 1
        assert result["dry_run"] is True
        assert len(result["rules_preview"]) == 1

    def test_rebuild_inserts_into_db(self, tmp_path):
        # Create DB with schema first
        from tems.scaffold import create_directories, create_database
        create_directories(tmp_path)
        create_database(tmp_path, force=False)

        qmd_dir = tmp_path / "memory" / "qmd_rules"
        rule = qmd_dir / "rule_0001.md"
        rule.write_text("""---
rule_id: 1
category: TGL
tags: encoding
severity: error
---

**Keywords:** subprocess encoding cp949

**Rule:** Use bytes I/O for Windows subprocess

**Context:** [TGL] cp949 encoding crash

**Result:** Fixed with bytes mode
""", encoding="utf-8")

        db_path = tmp_path / "memory" / "error_logs.db"
        result = rebuild(db_path, qmd_dir, dry_run=False)
        assert result["ok"] is True
        assert result["inserted"] == 1

        # Verify in DB
        conn = sqlite3.connect(str(db_path))
        row = conn.execute("SELECT * FROM memory_logs WHERE id = 1").fetchone()
        conn.close()
        assert row is not None
```

- [ ] **Step 2: Run test to verify it passes**

```bash
pytest tests/test_rebuild.py -v
```

Expected: 6 PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/test_rebuild.py
git commit -m "test: add QMD rebuild tests"
```

---

### Task 9: Full integration test + pip install verification

**Files:**
- Create: `E:/bobpullie/TEMS/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""End-to-end integration: scaffold → commit → preflight → rebuild cycle."""

import json
import subprocess
import sys
from pathlib import Path
from tems.fts5_memory import MemoryDB
from tems.scaffold import create_marker, create_directories, create_database, copy_templates


def test_full_lifecycle(tmp_path):
    """scaffold → commit rule → search → rebuild cycle."""
    agent_dir = tmp_path / "test_agent"
    agent_dir.mkdir()

    # 1. Scaffold
    create_marker(agent_dir, "integration_test", force=False)
    create_directories(agent_dir)
    create_database(agent_dir, force=False)

    # 2. Commit rules via MemoryDB
    db_path = agent_dir / "memory" / "error_logs.db"
    db = MemoryDB(str(db_path))

    tcl_id = db.commit_tcl(
        original_instruction="앞으로 TDD 필수",
        topological_rule="모든 구현 전 테스트 작성",
        keyword_trigger="TDD test 테스트 구현",
        context_tags=["dev", "testing"],
    )
    assert tcl_id > 0

    tgl_id = db.commit_tgl(
        error_description="subprocess cp949 crash",
        topological_case="Windows encoding boundary",
        guard_rule="bytes I/O + manual UTF-8 decode",
        keyword_trigger="subprocess encoding Windows cp949",
        context_tags=["Windows", "subprocess"],
    )
    assert tgl_id > 0

    # 3. Preflight search
    pf = db.preflight("테스트 subprocess Windows")
    all_hits = pf["tcl_hits"] + pf["tgl_hits"] + pf["general_hits"]
    assert len(all_hits) >= 1

    # 4. Stats
    stats = db.stats()
    assert stats["total_records"] == 2


def test_cli_scaffold_e2e(tmp_path):
    """CLI scaffold creates working agent environment."""
    agent_dir = tmp_path / "cli_agent"
    reg_path = tmp_path / "registry.json"

    result = subprocess.run(
        [sys.executable, "-m", "tems.cli",
         "scaffold",
         "--agent-id", "e2e_test",
         "--agent-name", "E2E Test",
         "--project", "TestProject",
         "--cwd", str(agent_dir),
         "--registry-path", str(reg_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True

    # Verify DB is usable
    db = MemoryDB(str(agent_dir / "memory" / "error_logs.db"))
    rid = db.commit_memory(["test"], "test action", "test result")
    assert rid > 0

    # Verify registry
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    assert "e2e_test" in registry["agents"]
```

- [ ] **Step 2: Run all tests**

```bash
cd E:/bobpullie/TEMS
pytest tests/ -v --tb=short
```

Expected: all tests PASS

- [ ] **Step 3: Verify pip install works**

```bash
pip install -e ".[dev]"
tems --help
```

Expected: help output showing `scaffold` and `init-skill` subcommands.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add full lifecycle integration tests"
```

---

### Task 10: __init__.py public API + py.typed

**Files:**
- Modify: `E:/bobpullie/TEMS/src/tems/__init__.py`
- Create: `E:/bobpullie/TEMS/src/tems/py.typed`

- [ ] **Step 1: Update __init__.py with public exports**

```python
# src/tems/__init__.py
"""TEMS — Topological Evolving Memory System.

Self-evolving agent memory with FTS5+BM25, topological health scoring,
and hybrid sparse-dense retrieval.
"""

__version__ = "0.1.0"

from .fts5_memory import MemoryDB
from .tems_engine import (
    HybridRetriever,
    HealthScorer,
    AnomalyCertifier,
    MetaRuleEngine,
    RuleGraph,
    PredictiveTGL,
    AdaptiveTrigger,
    TemporalGraph,
    EnhancedPreflight,
    sync_rules_to_qmd,
    sync_single_rule_to_qmd,
)
from .rebuild_from_qmd import parse_qmd_rule, rebuild
from .scaffold import get_registry_path

__all__ = [
    "MemoryDB",
    "HybridRetriever",
    "HealthScorer",
    "AnomalyCertifier",
    "MetaRuleEngine",
    "RuleGraph",
    "PredictiveTGL",
    "AdaptiveTrigger",
    "TemporalGraph",
    "EnhancedPreflight",
    "sync_rules_to_qmd",
    "sync_single_rule_to_qmd",
    "parse_qmd_rule",
    "rebuild",
    "get_registry_path",
]
```

- [ ] **Step 2: Create py.typed marker**

```bash
touch E:/bobpullie/TEMS/src/tems/py.typed
```

Empty file — PEP 561 marker for type checker support.

- [ ] **Step 3: Test public API imports**

```python
# Add to tests/test_engine_smoke.py:
def test_public_api():
    """All public API symbols importable from tems package."""
    from tems import (
        MemoryDB, HybridRetriever, HealthScorer,
        RuleGraph, EnhancedPreflight, get_registry_path,
        __version__,
    )
    assert __version__ == "0.1.0"
```

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/tems/__init__.py src/tems/py.typed tests/test_engine_smoke.py
git commit -m "feat: expose public API in __init__.py + py.typed marker"
```

---

### Task 11: Final verification + tag

- [ ] **Step 1: Run full test suite**

```bash
cd E:/bobpullie/TEMS
pytest tests/ -v --tb=short
```

Expected: all tests green.

- [ ] **Step 2: Verify clean pip install**

```bash
pip install -e ".[dev]"
python -c "from tems import MemoryDB, __version__; print(f'TEMS {__version__} OK')"
tems --help
```

Expected: `TEMS 0.1.0 OK` + help output.

- [ ] **Step 3: Verify tems scaffold works end-to-end**

```bash
tems scaffold --agent-id verify_test --agent-name "Verify" --project Test --cwd /tmp/tems_verify
```

Expected: JSON output with `"ok": true`.

- [ ] **Step 4: Tag v0.1.0**

```bash
git tag -a v0.1.0 -m "v0.1.0: initial TEMS package release"
```

- [ ] **Step 5: Final commit if any loose files**

```bash
git status
# If any untracked files remain, add and commit
```

---

## Post-Implementation (Not in this plan)

These are follow-up tasks for future sessions:

1. **위상군 import 전환** — `E:/DnT/DnT_WesangGoon/memory/` preflight_hook.py를 새 패키지 import로 교체
2. **Atlas optional dependency** — `atlas-docs` pyproject.toml에 `tems = ["tems"]` 추가
3. **나머지 에이전트 마이그레이션** — 빌드군, 코드군, 관리군 등 순차 전환
4. **GitHub remote 연결** — `bobpullie/TEMS` GitHub 레포 생성 + push
5. **AgentInterface 정리** — 전 에이전트 전환 후 `tems_core/` deprecated
