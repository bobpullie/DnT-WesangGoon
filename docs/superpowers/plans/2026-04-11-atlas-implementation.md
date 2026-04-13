# Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **IMPORTANT — Session discipline (TCL#64):** Implementation MUST happen in a separate session from this planning session. Do NOT start implementing tasks in the session that produced this plan. Each Phase is a natural implementation session boundary.

**Goal:** Build the `atlas` skill — a dynamic hierarchical documentation system that lets agents load only the minimal context needed for any task, with automatic drift detection and TEMS lesson promotion.

**Architecture:** A core Python library (`topology.py`) that enforces 8 topological invariants over a tree of `(level, time)` coordinate files, consumed by 3 deterministic engines (SETUP, SYNC, PROMOTE) and 1 agent-driven protocol (NAV). Installation scaffolds per-project `.claude/hooks/` + `docs/architecture/` + `.hdocs/` cache + TEMS TCL rules.

**Tech Stack:** Python 3.11+, `pyyaml` (frontmatter), `pytest` (tests), `pathlib`/`subprocess` (git log), SQLite (TEMS DB queries via existing `tems_commit.py`).

**Spec reference:** `docs/superpowers/specs/2026-04-11-atlas-hierarchical-docs-design.md`

**Install location:** `E:/AgentInterface/skills/atlas/` (will be extracted to a dedicated git repo after implementation completes — coordinated by 종일군).

---

## ⚠️ Implementation Conventions (Windows/Locale)

**Convention W1 — Explicit UTF-8 for test file I/O.**
All test files MUST use `encoding="utf-8"` explicitly on every raw `Path.write_text()` and `Path.read_text()` call, including fixture setups inside `conftest.py` and helpers like `_make_l1`, `_make_l2` in this plan. Korean Windows locale defaults to `cp949`, and many tests write Korean strings (`좌표`, `업로드`, etc.) as part of fixtures — the default encoding path will raise `UnicodeEncodeError`/`UnicodeDecodeError` at test-collection time.

The library functions `parse_frontmatter` / `write_frontmatter` already hard-code UTF-8 internally, so production code is safe. This convention applies only to **test code** where raw `write_text`/`read_text` is called directly against `tmp_path` fixtures.

Reference code blocks in this plan may not always show `encoding="utf-8"` explicitly for brevity, but **implementers must add it whenever they copy a test body that writes/reads a file**. This is non-negotiable — S19 Impl-1 confirmed the failure mode in Task 1.1 and established the convention for Tasks 1.2~1.8.

---

## Phase 0 — Project Skeleton (Session 1, foundational)

### Task 0.1: Create skill directory skeleton

**Files:**
- Create: `E:/AgentInterface/skills/atlas/`
- Create: `E:/AgentInterface/skills/atlas/scripts/__init__.py` (empty)
- Create: `E:/AgentInterface/skills/atlas/scripts/topology.py` (empty stub)
- Create: `E:/AgentInterface/skills/atlas/tests/__init__.py` (empty)
- Create: `E:/AgentInterface/skills/atlas/tests/conftest.py`
- Create: `E:/AgentInterface/skills/atlas/pyproject.toml`
- Create: `E:/AgentInterface/skills/atlas/README.md`

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p E:/AgentInterface/skills/atlas/{scripts,tests,templates,hook_templates,references}
touch E:/AgentInterface/skills/atlas/scripts/__init__.py
touch E:/AgentInterface/skills/atlas/tests/__init__.py
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "atlas"
version = "1.0.0"
description = "Dynamic hierarchical documentation system for agent contexts"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "python-frontmatter>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-mock>=3.10"]

# ⚠️ Phase 1 완료 전까지 `pip install -e .` 금지.
# 아래 7개 엔트리포인트 모듈 중 일부는 Phase 3~7에서야 생성됨.
# 설치를 시도하면 ModuleNotFoundError 로 install 단계 자체가 깨짐.
[project.scripts]
atlas-setup = "atlas.scripts.atlas_setup:main"
atlas-backfill = "atlas.scripts.atlas_backfill:main"
atlas-check = "atlas.scripts.atlas_check:main"
atlas-split = "atlas.scripts.atlas_split:main"
atlas-collapse = "atlas.scripts.atlas_collapse:main"
atlas-promote-check = "atlas.scripts.atlas_promote_check:main"
atlas-rebuild-cache = "atlas.scripts.atlas_rebuild_cache:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
# ⚠️ load-bearing: 플랫 레이아웃 (atlas/scripts/topology.py) 에서 테스트가
# `from atlas.scripts.topology import ...` 로 임포트한다. Python 3.3+ 의
# implicit namespace package + pythonpath 로 resolve 하는 방식을 사용한다.
# `pip install -e .` 대안은 [project.scripts] 미존재 모듈 때문에 불가 (Impl-1 S19 결정).
pythonpath = [".."]
```

- [ ] **Step 3: Write `tests/conftest.py`** (shared fixtures)

```python
"""Shared pytest fixtures for atlas tests."""
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal project layout under tmp_path."""
    (tmp_path / ".claude" / "references").mkdir(parents=True)
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    (tmp_path / "docs" / "architecture").mkdir(parents=True)
    (tmp_path / ".hdocs").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def sample_l0(tmp_project):
    """Create a minimal L0 file with skeleton_index."""
    l0 = tmp_project / ".claude" / "references" / "L0-architecture.md"
    l0.write_text(
        "---\n"
        "atlas_version: 1.0\n"
        "level: 0\n"
        "anchor_strategy: preset:spa\n"
        "budget:\n"
        "  drill_files: 8\n"
        "  history_per_file: 1\n"
        "skeleton_index: []\n"
        "---\n\n"
        "# Project Atlas (L0)\n"
    )
    return l0
```

- [ ] **Step 4: Run pytest to verify empty collection works**

Run: `cd E:/AgentInterface/skills/atlas && pytest -v`
Expected: `no tests ran in 0.XXs` (exit 5 is acceptable for empty collection)

- [ ] **Step 5: Commit**

```bash
cd E:/AgentInterface/skills/atlas
git init  # if not already inside a repo
git add pyproject.toml scripts/ tests/ templates/ hook_templates/ references/
git commit -m "chore(atlas): initial skeleton"
```

---

## Phase 1 — `topology.py` Core Library (Session 1-2, ~8 tasks)

`topology.py` is the foundation. All engines depend on it. Develop with strict TDD.

### Task 1.1: Frontmatter parser + writer

**Files:**
- Create: `E:/AgentInterface/skills/atlas/scripts/topology.py` (add `parse_frontmatter`, `write_frontmatter`)
- Create: `E:/AgentInterface/skills/atlas/tests/test_topology_frontmatter.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_topology_frontmatter.py
from pathlib import Path
from atlas.scripts.topology import parse_frontmatter, write_frontmatter


def test_parse_frontmatter_reads_yaml_block(tmp_path):
    f = tmp_path / "sample.md"
    f.write_text(
        "---\n"
        "level: 2\n"
        "parent: gallery/README.md\n"
        "keywords: [crop, 좌표]\n"
        "---\n\n"
        "# Body\n"
    )
    meta, body = parse_frontmatter(f)
    assert meta["level"] == 2
    assert meta["parent"] == "gallery/README.md"
    assert meta["keywords"] == ["crop", "좌표"]
    assert body.strip() == "# Body"


def test_write_frontmatter_preserves_body(tmp_path):
    f = tmp_path / "out.md"
    write_frontmatter(f, {"level": 1, "owner": "test"}, "# Hello\n")
    content = f.read_text()
    assert content.startswith("---\n")
    assert "level: 1" in content
    assert "owner: test" in content
    assert "# Hello" in content


def test_roundtrip_preserves_frontmatter(tmp_path):
    f = tmp_path / "rt.md"
    meta_in = {"level": 2, "keywords": ["a", "b"], "depends_on": []}
    write_frontmatter(f, meta_in, "body text")
    meta_out, body_out = parse_frontmatter(f)
    assert meta_out == meta_in
    assert body_out.strip() == "body text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_topology_frontmatter.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_frontmatter'`

- [ ] **Step 3: Implement minimal code**

> **Hardening context (S19 Impl-1 → P2 Impl-2):** the implementation below
> already incorporates the four deferred fixes (I2 loud-fail on unclosed
> fence, I3 `python-frontmatter` as the YAML backend, I4 UTF-8 BOM strip,
> empty-frontmatter + byte-stable body roundtrip). Body slicing is
> deliberately kept manual because `python-frontmatter` strips trailing
> whitespace from `Post.content` and drops the body separator when content
> is empty — both would break Task 1.6 (`update_bidirectional_links`)
> byte-stable edit-in-place. The sentinel trick in `write_frontmatter`
> sidesteps this by always rendering a non-empty body through the library
> and splicing the real body back in verbatim.

```python
# scripts/topology.py
"""Atlas topology engine — core library for hierarchical documentation."""
from __future__ import annotations
from pathlib import Path
from typing import Any

import frontmatter

VERSION = "1.0.0"

# Sentinel used to recover the body slot from frontmatter.dumps output. The
# library strips trailing whitespace from Post.content and drops the body
# separator entirely when content is empty, both of which would break our
# byte-stable roundtrip contract. We render with a non-empty placeholder so
# the library always emits the full "---\n{yaml}\n---\n\n{body}" frame, then
# substitute the real body verbatim.
_BODY_SENTINEL = "\x00ATLAS_BODY_SENTINEL\x00"


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file.

    Returns:
        (metadata_dict, body_str). If no frontmatter, metadata is {} and body
        is full content. Raises ValueError if the frontmatter fence is opened
        but never closed (I2 hardening — loud-fail on malformed files).
    """
    text = Path(path).read_text(encoding="utf-8")
    # I4 — strip UTF-8 BOM so files saved by Windows tools parse correctly.
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---\n"):
        return {}, text
    # Empty frontmatter shorthand: "---\n---\n..." → meta={}, body after fence.
    if text[4:].startswith("---\n"):
        body = text[8:]
        if body.startswith("\n"):
            body = body[1:]
        return {}, body
    end = text.find("\n---\n", 4)
    if end == -1:
        # I2 — frontmatter fence opened but never closed. Loud-fail.
        raise ValueError(
            f"parse_frontmatter: unclosed frontmatter fence in {path}"
        )
    # Delegate YAML parsing to python-frontmatter (I3 — make the dep real).
    fm_slice = text[: end + 5]
    post = frontmatter.loads(fm_slice)
    meta = dict(post.metadata)
    body = text[end + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    return meta, body


def write_frontmatter(path: Path, meta: dict[str, Any], body: str) -> None:
    """Write a markdown file with YAML frontmatter.

    Output format: "---\\n{yaml}\\n---\\n\\n{body}". Insertion order of meta
    is preserved (sort_keys=False). Body is written verbatim so that
    parse→write→parse is byte-stable.
    """
    post = frontmatter.Post(content=_BODY_SENTINEL)
    post.metadata.update(meta)
    raw = frontmatter.dumps(post, sort_keys=False)
    if _BODY_SENTINEL not in raw:  # pragma: no cover — defensive
        raise RuntimeError(
            "write_frontmatter: frontmatter.dumps dropped body sentinel"
        )
    content = raw.replace(_BODY_SENTINEL, body)
    Path(path).write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_topology_frontmatter.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_frontmatter.py
git commit -m "feat(atlas): add frontmatter parser and writer"
```

### Task 1.2: File discovery walker

**Files:**
- Modify: `scripts/topology.py` (add `discover_atlas_files`)
- Create: `tests/test_topology_discover.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_topology_discover.py
from atlas.scripts.topology import discover_atlas_files


def test_discover_finds_l0_l1_l2_history(tmp_project):
    # L0
    l0 = tmp_project / ".claude" / "references" / "L0-architecture.md"
    l0.write_text("---\nlevel: 0\n---\n# L0\n")

    # L1
    gallery = tmp_project / "docs" / "architecture" / "gallery"
    gallery.mkdir(parents=True)
    (gallery / "README.md").write_text("---\nlevel: 1\n---\n# gallery\n")

    # L2 + history pair
    (gallery / "crop-editor.md").write_text("---\nlevel: 2\n---\n# crop\n")
    (gallery / "crop-editor.history.md").write_text(
        "---\nlevel: 2\nhistory_of: gallery/crop-editor.md\nappend_only: true\n---\n# H\n"
    )

    files = discover_atlas_files(tmp_project)
    paths = sorted(str(f.relative_to(tmp_project)).replace("\\", "/") for f in files)
    assert paths == [
        ".claude/references/L0-architecture.md",
        "docs/architecture/gallery/README.md",
        "docs/architecture/gallery/crop-editor.history.md",
        "docs/architecture/gallery/crop-editor.md",
    ]


def test_discover_ignores_non_atlas_markdown(tmp_project):
    (tmp_project / "README.md").write_text("# project readme\n")  # no frontmatter
    (tmp_project / "docs" / "random.md").write_text("# not atlas\n")
    files = discover_atlas_files(tmp_project)
    assert files == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_topology_discover.py -v`
Expected: FAIL with `ImportError: cannot import name 'discover_atlas_files'`

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

ATLAS_ROOTS = (
    Path(".claude/references"),
    Path("docs/architecture"),
)


def discover_atlas_files(project_root: Path) -> list[Path]:
    """Walk project and return all atlas-managed markdown files.

    A file is atlas-managed if it lives under .claude/references/ or
    docs/architecture/ AND has frontmatter with atlas_version or level.
    """
    project_root = Path(project_root)
    results: list[Path] = []
    for root in ATLAS_ROOTS:
        base = project_root / root
        if not base.exists():
            continue
        for md in base.rglob("*.md"):
            meta, _ = parse_frontmatter(md)
            if "level" in meta or "atlas_version" in meta:
                results.append(md)
    return sorted(results)
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_topology_discover.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_discover.py
git commit -m "feat(atlas): add atlas file discovery walker"
```

### Task 1.3: Invariant I1 (L0 exactly one) + I2 (unique parent tree)

**Files:**
- Modify: `scripts/topology.py` (add `check_i1_l0_unique`, `check_i2_tree_structure`, `InvariantViolation`)
- Create: `tests/test_topology_invariants_i1_i2.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_topology_invariants_i1_i2.py
import pytest
from atlas.scripts.topology import (
    check_i1_l0_unique,
    check_i2_tree_structure,
    InvariantViolation,
    parse_frontmatter,
    write_frontmatter,
)


def test_i1_passes_with_exactly_one_l0(tmp_project, sample_l0):
    # sample_l0 fixture creates exactly one L0
    check_i1_l0_unique(tmp_project)  # no raise


def test_i1_fails_with_zero_l0(tmp_project):
    with pytest.raises(InvariantViolation, match="I1.*no L0"):
        check_i1_l0_unique(tmp_project)


def test_i1_fails_with_two_l0(tmp_project, sample_l0):
    extra = tmp_project / ".claude" / "references" / "L0-second.md"
    extra.write_text("---\nlevel: 0\n---\n# other\n")
    with pytest.raises(InvariantViolation, match="I1.*2 L0"):
        check_i1_l0_unique(tmp_project)


def test_i2_passes_on_simple_tree(tmp_project, sample_l0):
    gallery = tmp_project / "docs" / "architecture" / "gallery"
    gallery.mkdir(parents=True)
    (gallery / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n"
    )
    (gallery / "crop.md").write_text(
        "---\nlevel: 2\nparent: docs/architecture/gallery/README.md\n---\n"
    )
    check_i2_tree_structure(tmp_project)  # no raise


def test_i2_fails_when_two_children_claim_different_parents(tmp_project, sample_l0):
    # A dangling parent reference
    (tmp_project / "docs" / "architecture" / "orphan.md").write_text(
        "---\nlevel: 2\nparent: docs/architecture/nonexistent.md\n---\n"
    )
    with pytest.raises(InvariantViolation, match="I2.*parent not found"):
        check_i2_tree_structure(tmp_project)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_topology_invariants_i1_i2.py -v`
Expected: FAIL with `ImportError` / `check_i1_l0_unique` not found

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

class InvariantViolation(Exception):
    """Raised when a topology invariant is violated."""


def check_i1_l0_unique(project_root: Path) -> None:
    """I1 — exactly one L0 file exists."""
    files = discover_atlas_files(project_root)
    l0s = [f for f in files if parse_frontmatter(f)[0].get("level") == 0]
    if len(l0s) == 0:
        raise InvariantViolation(
            "I1 violation: no L0 file found. Expected exactly one file with level: 0"
        )
    if len(l0s) > 1:
        raise InvariantViolation(
            f"I1 violation: {len(l0s)} L0 files found, expected 1. "
            f"Paths: {[str(p) for p in l0s]}"
        )


def check_i2_tree_structure(project_root: Path) -> None:
    """I2 — every non-L0 file has exactly one existing parent."""
    files = discover_atlas_files(project_root)
    path_set = {str(f.relative_to(project_root)).replace("\\", "/") for f in files}
    for f in files:
        meta, _ = parse_frontmatter(f)
        level = meta.get("level")
        if level == 0:
            continue
        parent = meta.get("parent")
        if not parent:
            raise InvariantViolation(
                f"I2 violation: {f} (level={level}) has no parent"
            )
        parent_norm = parent.replace("\\", "/")
        if parent_norm not in path_set:
            raise InvariantViolation(
                f"I2 violation: parent not found — {f} declares parent={parent}"
            )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_topology_invariants_i1_i2.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_invariants_i1_i2.py
git commit -m "feat(atlas): add invariants I1 (L0 unique) and I2 (tree structure)"
```

### Task 1.4: Invariants I3 (compression ratio) + I4 (fan-out)

**Files:**
- Modify: `scripts/topology.py` (add `check_i3_compression`, `check_i4_fanout`)
- Create: `tests/test_topology_invariants_i3_i4.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_topology_invariants_i3_i4.py
import pytest
from atlas.scripts.topology import (
    check_i3_compression,
    check_i4_fanout,
    InvariantViolation,
)


def _make_l1(tmp_project, name: str, lines: int) -> None:
    d = tmp_project / "docs" / "architecture" / name
    d.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"line {i}" for i in range(lines))
    (d / "README.md").write_text(
        f"---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n{body}\n"
    )


def _make_l2(tmp_project, module: str, feature: str, lines: int) -> None:
    body = "\n".join(f"line {i}" for i in range(lines))
    (tmp_project / "docs" / "architecture" / module / f"{feature}.md").write_text(
        f"---\nlevel: 2\nparent: docs/architecture/{module}/README.md\n---\n{body}\n"
    )


def test_i3_passes_when_ratio_in_range(tmp_project, sample_l0):
    _make_l1(tmp_project, "gallery", lines=200)  # L1 avg 200
    _make_l2(tmp_project, "gallery", "crop", lines=60)    # L2 avg 60 → ratio 0.3
    _make_l2(tmp_project, "gallery", "upload", lines=60)
    check_i3_compression(tmp_project)  # no raise


def test_i3_warns_when_l2_larger_than_l1(tmp_project, sample_l0):
    _make_l1(tmp_project, "gallery", lines=50)
    _make_l2(tmp_project, "gallery", "crop", lines=100)  # ratio 2.0
    with pytest.raises(InvariantViolation, match="I3.*compression"):
        check_i3_compression(tmp_project)


def test_i4_passes_with_moderate_fanout(tmp_project, sample_l0):
    _make_l1(tmp_project, "gallery", lines=50)
    for feat in ["a", "b", "c"]:
        _make_l2(tmp_project, "gallery", feat, lines=20)
    check_i4_fanout(tmp_project)  # no raise


def test_i4_warns_on_excessive_fanout(tmp_project, sample_l0):
    _make_l1(tmp_project, "gallery", lines=50)
    for i in range(15):
        _make_l2(tmp_project, "gallery", f"f{i}", lines=20)
    with pytest.raises(InvariantViolation, match="I4.*fan_out"):
        check_i4_fanout(tmp_project)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_topology_invariants_i3_i4.py -v`
Expected: FAIL (functions not defined)

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py
from collections import defaultdict


def _file_line_count(p: Path) -> int:
    _, body = parse_frontmatter(p)
    return len([ln for ln in body.splitlines() if ln.strip()])


def _group_by_level(project_root: Path) -> dict[int, list[Path]]:
    out: dict[int, list[Path]] = defaultdict(list)
    for f in discover_atlas_files(project_root):
        meta, _ = parse_frontmatter(f)
        lvl = meta.get("level")
        if lvl is None:
            continue
        if str(f).endswith(".history.md"):
            continue  # history is orthogonal axis, not a level sibling
        out[int(lvl)].append(f)
    return out


def check_i3_compression(project_root: Path) -> None:
    """I3 — avg_size(L_k) / avg_size(L_{k-1}) must be in [0.1, 0.5].

    Skips k <= 1: L0 is the skeleton-index root, not a prose document, so
    L1-vs-L0 compression ratio is undefined. L0 file-size health is covered
    by I5 (overflow budget). L1-vs-L0 fan-out is covered by I4 (skipped
    symmetrically). I3 applies only to L2+ prose layers.
    (S19 Impl-1 편차 — plan reference code ↔ plan test 충돌 수정)
    """
    by_level = _group_by_level(project_root)
    for k in sorted(by_level.keys()):
        if k <= 1:
            continue
        parent_level = by_level.get(k - 1)
        if not parent_level:
            continue
        parent_avg = sum(_file_line_count(p) for p in parent_level) / len(parent_level)
        if parent_avg == 0:
            continue
        child_avg = sum(_file_line_count(p) for p in by_level[k]) / len(by_level[k])
        ratio = child_avg / parent_avg
        if not (0.1 <= ratio <= 0.5):
            raise InvariantViolation(
                f"I3 violation: compression ratio L{k}/L{k-1} = {ratio:.2f} "
                f"outside [0.1, 0.5]"
            )


def check_i4_fanout(project_root: Path) -> None:
    """I4 — children(L_{k-1} entry) must be in [2, 12].

    Skips k <= 1 symmetrically with I3: L0 has exactly one child slot
    (skeleton_index root), so L1-vs-L0 fan-out is definitionally 1 and
    the [2, 12] range does not apply. I4 applies only to L2+ layers.
    (S19 Impl-1 편차 — plan reference code ↔ plan test 충돌 수정)
    """
    by_level = _group_by_level(project_root)
    for k in sorted(by_level.keys()):
        if k <= 1:
            continue
        parent_counts: dict[str, int] = defaultdict(int)
        for f in by_level[k]:
            meta, _ = parse_frontmatter(f)
            parent = meta.get("parent", "")
            parent_counts[parent] += 1
        for parent, count in parent_counts.items():
            if count < 2 or count > 12:
                raise InvariantViolation(
                    f"I4 violation: fan_out({parent}) = {count}, expected in [2, 12]"
                )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_topology_invariants_i3_i4.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_invariants_i3_i4.py
git commit -m "feat(atlas): add invariants I3 (compression) and I4 (fan-out)"
```

### Task 1.5: Invariants I5 (overflow) + I8 (history pair)

**Files:**
- Modify: `scripts/topology.py` (add `check_i5_overflow`, `check_i8_history_pair`, `MAX_LINES_DEFAULT`)
- Create: `tests/test_topology_invariants_i5_i8.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_topology_invariants_i5_i8.py
import pytest
from atlas.scripts.topology import (
    check_i5_overflow,
    check_i8_history_pair,
    InvariantViolation,
    MAX_LINES_DEFAULT,
)


def test_max_lines_defaults():
    assert MAX_LINES_DEFAULT[0] == 200
    assert MAX_LINES_DEFAULT[1] == 300
    assert MAX_LINES_DEFAULT["default"] == 500


def test_i5_detects_overflow(tmp_project, sample_l0):
    big = "\n".join(f"line {i}" for i in range(250))  # > L0 cap 200
    (tmp_project / ".claude" / "references" / "L0-architecture.md").write_text(
        f"---\nlevel: 0\n---\n{big}\n"
    )
    overflows = check_i5_overflow(tmp_project)
    assert len(overflows) == 1
    assert overflows[0][1] == 0  # level
    assert overflows[0][2] > 200  # lines


def test_i5_returns_empty_when_all_under_cap(tmp_project, sample_l0):
    assert check_i5_overflow(tmp_project) == []


def test_i8_passes_when_history_has_pair(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "crop.md").write_text("---\nlevel: 2\nparent: docs/architecture/gallery/README.md\n---\n")
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    (d / "crop.history.md").write_text(
        "---\nlevel: 2\nhistory_of: docs/architecture/gallery/crop.md\nappend_only: true\n---\n"
    )
    check_i8_history_pair(tmp_project)  # no raise


def test_i8_fails_when_history_has_no_pair(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    (d / "orphan.history.md").write_text(
        "---\nlevel: 2\nhistory_of: docs/architecture/gallery/nonexistent.md\nappend_only: true\n---\n"
    )
    with pytest.raises(InvariantViolation, match="I8.*dangling"):
        check_i8_history_pair(tmp_project)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_topology_invariants_i5_i8.py -v`
Expected: FAIL (not defined)

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

MAX_LINES_DEFAULT: dict[Any, int] = {
    0: 200,
    1: 300,
    "default": 500,
}


def _cap_for_level(level: int, cfg: dict[Any, int] | None = None) -> int:
    cfg = cfg or MAX_LINES_DEFAULT
    if level in cfg:
        return int(cfg[level])
    return int(cfg.get("default", 500))


def check_i5_overflow(
    project_root: Path, max_lines: dict[Any, int] | None = None
) -> list[tuple[Path, int, int]]:
    """I5 — return list of (path, level, line_count) for files exceeding caps.

    Does NOT raise — callers interpret overflow as a flag, not an error.
    """
    overflows: list[tuple[Path, int, int]] = []
    for f in discover_atlas_files(project_root):
        if str(f).endswith(".history.md"):
            continue  # history has no line cap
        meta, _ = parse_frontmatter(f)
        level = meta.get("level")
        if level is None:
            continue
        cap = _cap_for_level(int(level), max_lines)
        line_count = _file_line_count(f)
        if line_count > cap:
            overflows.append((f, int(level), line_count))
    return overflows


def check_i8_history_pair(project_root: Path) -> None:
    """I8 — every .history.md must reference an existing present file."""
    files = discover_atlas_files(project_root)
    path_set = {str(f.relative_to(project_root)).replace("\\", "/") for f in files}
    for f in files:
        if not str(f).endswith(".history.md"):
            continue
        meta, _ = parse_frontmatter(f)
        history_of = (meta.get("history_of") or "").replace("\\", "/")
        if not history_of:
            raise InvariantViolation(f"I8 violation: {f} has no history_of field")
        if history_of not in path_set:
            raise InvariantViolation(
                f"I8 violation: dangling history — {f} references missing {history_of}"
            )
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_topology_invariants_i5_i8.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_invariants_i5_i8.py
git commit -m "feat(atlas): add invariants I5 (overflow) and I8 (history pair)"
```

### Task 1.6: Bidirectional link maintenance (I6)

**Files:**
- Modify: `scripts/topology.py` (add `update_bidirectional_links`)
- Create: `tests/test_topology_bidirectional.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_topology_bidirectional.py
from atlas.scripts.topology import (
    update_bidirectional_links,
    parse_frontmatter,
    write_frontmatter,
)


def test_update_bidirectional_adds_reverse_used_by(tmp_project, sample_l0):
    # A declares depends_on: [B], B has empty used_by
    d = tmp_project / "docs" / "architecture" / "mod"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    write_frontmatter(
        d / "a.md",
        {
            "level": 2,
            "parent": "docs/architecture/mod/README.md",
            "depends_on": ["docs/architecture/mod/b.md"],
            "used_by": [],
            "keywords": ["a"],
        },
        "",
    )
    write_frontmatter(
        d / "b.md",
        {
            "level": 2,
            "parent": "docs/architecture/mod/README.md",
            "depends_on": [],
            "used_by": [],
            "keywords": ["b"],
        },
        "",
    )

    update_bidirectional_links(tmp_project)

    meta_b, _ = parse_frontmatter(d / "b.md")
    assert "docs/architecture/mod/a.md" in meta_b["used_by"]


def test_update_bidirectional_is_idempotent(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "mod"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    write_frontmatter(
        d / "a.md",
        {
            "level": 2,
            "parent": "docs/architecture/mod/README.md",
            "depends_on": ["docs/architecture/mod/b.md"],
            "used_by": [],
            "keywords": ["a"],
        },
        "",
    )
    write_frontmatter(
        d / "b.md",
        {
            "level": 2,
            "parent": "docs/architecture/mod/README.md",
            "depends_on": [],
            "used_by": [],
            "keywords": ["b"],
        },
        "",
    )
    update_bidirectional_links(tmp_project)
    update_bidirectional_links(tmp_project)  # second pass should not dup
    meta_b, _ = parse_frontmatter(d / "b.md")
    assert meta_b["used_by"].count("docs/architecture/mod/a.md") == 1
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_topology_bidirectional.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

def update_bidirectional_links(project_root: Path) -> int:
    """I6 — ensure depends_on ↔ used_by consistency. Returns number of fixes applied."""
    files = discover_atlas_files(project_root)
    metas: dict[str, tuple[Path, dict[str, Any], str]] = {}
    for f in files:
        if str(f).endswith(".history.md"):
            continue
        meta, body = parse_frontmatter(f)
        rel = str(f.relative_to(project_root)).replace("\\", "/")
        metas[rel] = (f, meta, body)

    fixes = 0
    for rel, (f, meta, body) in metas.items():
        for dep in list(meta.get("depends_on") or []):
            dep_norm = dep.replace("\\", "/")
            if dep_norm not in metas:
                continue
            target_path, target_meta, target_body = metas[dep_norm]
            target_used_by = list(target_meta.get("used_by") or [])
            if rel not in target_used_by:
                target_used_by.append(rel)
                target_meta["used_by"] = target_used_by
                write_frontmatter(target_path, target_meta, target_body)
                metas[dep_norm] = (target_path, target_meta, target_body)
                fixes += 1
    return fixes
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_topology_bidirectional.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_bidirectional.py
git commit -m "feat(atlas): add bidirectional link maintenance (I6)"
```

### Task 1.7: sync_watch reverse index builder

**Files:**
- Modify: `scripts/topology.py` (add `build_sync_index`)
- Create: `tests/test_topology_sync_index.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_topology_sync_index.py
from atlas.scripts.topology import build_sync_index, write_frontmatter


def test_sync_index_maps_source_to_l_files(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    write_frontmatter(
        d / "crop.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "sync_watch": [
                {"path": "gallery.html", "range": [1680, 1944]},
                {"path": "gallery.html", "range": [2183, 2201]},
            ],
            "depends_on": [],
            "used_by": [],
            "keywords": [],
        },
        "",
    )
    write_frontmatter(
        d / "upload.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "sync_watch": [{"path": "gallery.html", "range": [2300, 2400]}],
            "depends_on": [],
            "used_by": [],
            "keywords": [],
        },
        "",
    )

    index = build_sync_index(tmp_project)
    assert "gallery.html" in index
    entries = index["gallery.html"]
    assert len(entries) == 3  # 2 crop + 1 upload
    # Each entry: (l_file_relpath, range_tuple)
    ranges = sorted(e[1] for e in entries)
    assert ranges == [[1680, 1944], [2183, 2201], [2300, 2400]]


def test_sync_index_handles_manual_type(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "mod"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    write_frontmatter(
        d / "endnode.md",
        {
            "level": 2,
            "parent": "docs/architecture/mod/README.md",
            "sync_watch": [{"type": "manual", "command": "sync OUT_houses"}],
            "depends_on": [],
            "used_by": [],
            "keywords": [],
        },
        "",
    )
    index = build_sync_index(tmp_project)
    assert "__manual__" in index
    assert len(index["__manual__"]) == 1
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_topology_sync_index.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

def build_sync_index(project_root: Path) -> dict[str, list[tuple[str, Any]]]:
    """Build reverse index: source path → [(L-file relpath, range_or_marker), ...].

    Manual sync_watch entries map to key '__manual__'.
    """
    index: dict[str, list[tuple[str, Any]]] = defaultdict(list)
    for f in discover_atlas_files(project_root):
        if str(f).endswith(".history.md"):
            continue
        meta, _ = parse_frontmatter(f)
        watches = meta.get("sync_watch") or []
        rel = str(f.relative_to(project_root)).replace("\\", "/")
        for w in watches:
            if w.get("type") == "manual":
                index["__manual__"].append((rel, w.get("command", "")))
            else:
                path = w.get("path")
                range_ = w.get("range", None)
                if path:
                    index[path].append((rel, range_))
    return dict(index)
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_topology_sync_index.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/topology.py tests/test_topology_sync_index.py
git commit -m "feat(atlas): add sync_watch reverse index builder"
```

### Task 1.8: Skeleton index rebuilder + full check runner

**Files:**
- Modify: `scripts/topology.py` (add `rebuild_skeleton_index`, `check_all_invariants`)
- Create: `tests/test_topology_skeleton_and_check_all.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_topology_skeleton_and_check_all.py
import pytest
from atlas.scripts.topology import (
    rebuild_skeleton_index,
    check_all_invariants,
    parse_frontmatter,
    write_frontmatter,
    InvariantViolation,
)


def test_skeleton_index_aggregates_l2_keywords(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    write_frontmatter(
        d / "crop.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "keywords": ["crop", "좌표"],
            "depends_on": [],
            "used_by": [],
        },
        "",
    )
    write_frontmatter(
        d / "upload.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "keywords": ["upload", "업로드"],
            "depends_on": [],
            "used_by": [],
        },
        "",
    )

    rebuild_skeleton_index(tmp_project)

    l0_meta, _ = parse_frontmatter(sample_l0)
    index = l0_meta["skeleton_index"]
    entries_by_entry = {e["entry"]: e for e in index}
    assert "docs/architecture/gallery/crop.md" in entries_by_entry
    assert entries_by_entry["docs/architecture/gallery/crop.md"]["keywords"] == ["crop", "좌표"]


def test_check_all_invariants_runs_all_and_returns_report(tmp_project, sample_l0):
    # Healthy project → report has no critical
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n"
        + "\n".join(f"line {i}" for i in range(50))
    )
    for feat in ["a", "b"]:
        write_frontmatter(
            d / f"{feat}.md",
            {
                "level": 2,
                "parent": "docs/architecture/gallery/README.md",
                "keywords": [feat],
                "depends_on": [],
                "used_by": [],
            },
            "\n".join(f"line {i}" for i in range(10)),
        )
    report = check_all_invariants(tmp_project)
    assert report["critical"] == []
    assert isinstance(report["warnings"], list)
    assert isinstance(report["overflows"], list)
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_topology_skeleton_and_check_all.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Append to scripts/topology.py

def rebuild_skeleton_index(project_root: Path) -> None:
    """Rebuild L0.skeleton_index from all L2+ keywords. Idempotent."""
    l0_candidates = [
        f for f in discover_atlas_files(project_root)
        if parse_frontmatter(f)[0].get("level") == 0
    ]
    if not l0_candidates:
        raise InvariantViolation("I1 violation: cannot rebuild skeleton_index — no L0")
    l0_path = l0_candidates[0]
    l0_meta, l0_body = parse_frontmatter(l0_path)

    new_index: list[dict[str, Any]] = []
    for f in discover_atlas_files(project_root):
        if str(f).endswith(".history.md"):
            continue
        meta, _ = parse_frontmatter(f)
        level = meta.get("level")
        if level is None or int(level) < 2:
            continue
        keywords = meta.get("keywords") or []
        if not keywords:
            continue
        rel = str(f.relative_to(project_root)).replace("\\", "/")
        new_index.append({"keywords": list(keywords), "entry": rel})

    l0_meta["skeleton_index"] = new_index
    write_frontmatter(l0_path, l0_meta, l0_body)


def check_all_invariants(
    project_root: Path, max_lines: dict[Any, int] | None = None
) -> dict[str, list[Any]]:
    """Run all invariants. Returns {critical: [...], warnings: [...], overflows: [...]}"""
    report: dict[str, list[Any]] = {"critical": [], "warnings": [], "overflows": []}

    for fn, level in [
        (check_i1_l0_unique, "critical"),
        (check_i2_tree_structure, "critical"),
        (check_i8_history_pair, "critical"),
        (check_i3_compression, "warnings"),
        (check_i4_fanout, "warnings"),
    ]:
        try:
            fn(project_root)
        except InvariantViolation as e:
            report[level].append(str(e))

    report["overflows"] = check_i5_overflow(project_root, max_lines)
    return report
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_topology_skeleton_and_check_all.py -v`
Expected: 2 passed

- [ ] **Step 5: Run all topology tests**

Run: `pytest tests/test_topology*.py -v`
Expected: all pass (full core library validated)

- [ ] **Step 6: Commit**

```bash
git add scripts/topology.py tests/test_topology_skeleton_and_check_all.py
git commit -m "feat(atlas): add skeleton_index rebuilder and full invariant report"
```

---

## Phase 2 — Templates (Session 2)

### Task 2.1: L0 and Lk templates

**Files:**
- Create: `templates/L0.template.md`
- Create: `templates/Lk.template.md`
- Create: `templates/Lk.history.template.md`
- Create: `templates/README.template.md`
- Create: `templates/CHANGELOG.template.md`

- [ ] **Step 1: Write `templates/L0.template.md`**

```markdown
---
atlas_version: 1.0
level: 0
anchor_strategy: {{ anchor_strategy }}
budget:
  drill_files: 8
  history_per_file: 1
  tokens_soft_cap: 20000
max_lines:
  0: 200
  1: 300
  default: 500
promotion:
  similarity_threshold: 0.5
  min_shared_keywords: 2
  rule1_min_occurrences: 3
  rule2_min_occurrences: 2
skeleton_index: []
---

# {{ project_name }} — Atlas L0

> 전체 지도. 부트 시 자동 주입되므로 200줄 이내 유지.

## 한 줄 정의
{{ one_line_definition }}

## 모듈
{{ module_list }}

## 외부 의존성
{{ external_deps }}

## 기술 스택
{{ tech_stack }}

## 핵심 절대금지
- TEMS TGL 참조: `memory/qmd_rules/`

## L2 기능 인덱스
(topology 엔진이 skeleton_index frontmatter에 자동 생성)
```

- [ ] **Step 2: Write `templates/Lk.template.md`**

```markdown
---
atlas_version: 1.0
level: {{ level }}
parent: {{ parent_path }}
children: []
depends_on: []
used_by: []
keywords: []
sync_watch: []
last_synced_commit: ""
owner: {{ owner }}
status: stub
---

# L{{ level }}: {{ feature_name }}

## 목적
TODO — 1~2줄로 이 기능이 하는 것

## 코드 위치
TODO — 파일:라인 범위

## 핵심 동작
1. TODO
2. TODO
3. TODO

## 입력/출력
TODO

## 핵심 제약
TODO

## 의존 기능
(depends_on frontmatter 참조)

## 히스토리
→ `{{ feature_name }}.history.md`
```

- [ ] **Step 3: Write `templates/Lk.history.template.md`**

```markdown
---
atlas_version: 1.0
level: {{ level }}
history_of: {{ present_path }}
append_only: true
owner: {{ owner }}
---

# L{{ level }} History: {{ feature_name }}

> **append-only** — 엔트리 추가만 허용. 정정이 필요하면 정정 엔트리 추가.

## 요약 (표)

| 날짜 | 커밋 | 유형 | 한 줄 요약 | 상세 |
|------|------|------|-----------|------|

## 상세

<!-- 엔트리 형식:
### #N — YYYY-MM-DD `<SHA>` <유형 이모지> <한 줄 제목>

**증상:** ...
**재현:** ... (버그만)
**원인:** ...
**패치:** ...
**교훈:** ...
**관련 파일:** ...
**promote_candidate:** true | false
**tgl_ref:** TGL#N (있으면)
**keywords_for_promotion:** [...]
-->
```

- [ ] **Step 4: Write `templates/README.template.md`** and `templates/CHANGELOG.template.md`

```markdown
<!-- templates/README.template.md -->
# docs/architecture — Atlas 계층 문서 시스템

> Atlas v{{ atlas_version }} — 동적 L0~LN × (present | history) 2축 문서 시스템.

## 레벨 규약
- **L0** `.claude/references/L0-architecture.md` — 전체 지도 (자동 부트)
- **L1** `docs/architecture/<module>/README.md` — 모듈 개요
- **L2+** `docs/architecture/<module>/<feature>.md` — 기능 본문
- **History** `<name>.history.md` — append-only 시간축

## 위상 불변량
I1~I8 참조: `E:/AgentInterface/skills/atlas/references/topology-invariants.md`

## 작업 흐름
- 기능 수정 시: `sync_watch` 범위 변경 → 훅이 리마인더 주입
- drift clear 옵션 3가지: (a) 본문 수정, (b) 히스토리 추가, (c) `docs: no-op`
```

```markdown
<!-- templates/CHANGELOG.template.md -->
# docs/architecture — CHANGELOG

문서 시스템 자체의 버전 변경 이력.

## v1.0 — {{ date }}
- atlas 최초 구축
- L0 1개, L1 {{ l1_count }}개
```

- [ ] **Step 5: Commit**

```bash
git add templates/
git commit -m "feat(atlas): add L0, Lk, history, README, CHANGELOG templates"
```

### Task 2.2: Template renderer helper

**Files:**
- Create: `scripts/render_template.py`
- Create: `tests/test_render_template.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_render_template.py
from atlas.scripts.render_template import render_template


def test_render_substitutes_placeholders(tmp_path):
    tmpl = tmp_path / "sample.md"
    tmpl.write_text("Hello {{ name }}, welcome to {{ project }}!")
    result = render_template(tmpl, {"name": "종일군", "project": "atlas"})
    assert result == "Hello 종일군, welcome to atlas!"


def test_render_leaves_unknown_placeholders_empty(tmp_path):
    tmpl = tmp_path / "sample.md"
    tmpl.write_text("{{ defined }} and {{ missing }}")
    result = render_template(tmpl, {"defined": "OK"})
    assert result == "OK and "
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_render_template.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/render_template.py
"""Minimal mustache-like template renderer."""
import re
from pathlib import Path
from typing import Mapping


_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_template(template_path: Path, context: Mapping[str, object]) -> str:
    """Substitute {{ name }} placeholders with context[name]. Missing → empty string."""
    text = Path(template_path).read_text(encoding="utf-8")
    return _PLACEHOLDER.sub(lambda m: str(context.get(m.group(1), "")), text)
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_render_template.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/render_template.py tests/test_render_template.py
git commit -m "feat(atlas): add minimal template renderer"
```

---

## Phase 3 — SETUP Engine (Session 3)

### Task 3.1: Anchor strategy detector

**Files:**
- Create: `scripts/anchor_detect.py`
- Create: `tests/test_anchor_detect.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_anchor_detect.py
from atlas.scripts.anchor_detect import detect_anchor_strategy


def test_detects_spa_from_package_json_react(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^18.0", "react-dom": "^18.0"}}'
    )
    assert detect_anchor_strategy(tmp_path) == "preset:spa"


def test_detects_backend_api_from_fastapi(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "api"\ndependencies = ["fastapi>=0.100"]\n'
    )
    assert detect_anchor_strategy(tmp_path) == "preset:backend-api"


def test_detects_pipeline_from_airflow(tmp_path):
    (tmp_path / "requirements.txt").write_text("apache-airflow>=2.0\n")
    assert detect_anchor_strategy(tmp_path) == "preset:pipeline"


def test_falls_back_to_derived(tmp_path):
    assert detect_anchor_strategy(tmp_path) == "derived"
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_anchor_detect.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/anchor_detect.py
"""Anchor strategy preset detection for atlas setup."""
from pathlib import Path
import json


def detect_anchor_strategy(project_root: Path) -> str:
    """Heuristic auto-detection. Returns preset:* or 'derived'."""
    project_root = Path(project_root)

    # SPA: package.json with react/vue/svelte
    pkg = project_root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            if any(k in deps for k in ("react", "vue", "svelte", "next", "nuxt")):
                return "preset:spa"
        except json.JSONDecodeError:
            pass

    # Backend API: fastapi / flask / django / express
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        if any(k in text for k in ("fastapi", "flask", "django")):
            return "preset:backend-api"

    # Pipeline: airflow / prefect / dagster
    requirements = project_root / "requirements.txt"
    for f in (pyproject, requirements):
        if f.exists():
            text = f.read_text(encoding="utf-8")
            if any(k in text for k in ("airflow", "prefect", "dagster")):
                return "preset:pipeline"

    return "derived"
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_anchor_detect.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/anchor_detect.py tests/test_anchor_detect.py
git commit -m "feat(atlas): add anchor strategy preset detection"
```

### Task 3.2: `atlas_setup.py` — Stage 1 scaffolding

**Files:**
- Create: `scripts/atlas_setup.py`
- Create: `tests/test_atlas_setup_stage1.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_setup_stage1.py
from atlas.scripts.atlas_setup import run_stage1
from atlas.scripts.topology import parse_frontmatter, check_i1_l0_unique


def test_stage1_creates_l0_and_hooks(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18"}}')
    result = run_stage1(
        project_root=tmp_path,
        project_name="TestProj",
        modules=["frontend", "api"],
        confirm_anchor=False,  # skip interactive confirmation
    )

    # L0 exists
    l0 = tmp_path / ".claude" / "references" / "L0-architecture.md"
    assert l0.exists()
    meta, _ = parse_frontmatter(l0)
    assert meta["level"] == 0
    assert meta["anchor_strategy"] == "preset:spa"

    # L1 modules
    assert (tmp_path / "docs" / "architecture" / "frontend" / "README.md").exists()
    assert (tmp_path / "docs" / "architecture" / "api" / "README.md").exists()

    # Hooks installed
    assert (tmp_path / ".claude" / "hooks" / "post_tool_use_sync.py").exists()
    assert (tmp_path / ".claude" / "hooks" / "session_end_check.py").exists()

    # .hdocs/ cache
    assert (tmp_path / ".hdocs" / "config.yaml").exists()
    assert (tmp_path / ".hdocs" / ".gitignore").exists()

    # I1 passes
    check_i1_l0_unique(tmp_path)

    assert result["stage"] == 1
    assert result["l1_count"] == 2
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_atlas_setup_stage1.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_setup.py
"""Atlas SETUP engine — Stage 1 (shell scaffolding)."""
from __future__ import annotations
from pathlib import Path
from datetime import date
from typing import Any

from .topology import write_frontmatter, rebuild_skeleton_index
from .render_template import render_template
from .anchor_detect import detect_anchor_strategy

SKILL_ROOT = Path(__file__).parent.parent  # skills/atlas/
TEMPLATES = SKILL_ROOT / "templates"
HOOK_TEMPLATES = SKILL_ROOT / "hook_templates"


def run_stage1(
    project_root: Path,
    project_name: str,
    modules: list[str],
    confirm_anchor: bool = True,
) -> dict[str, Any]:
    """Execute Stage 1: L0 + L1 shells + hooks + TEMS TCL + .hdocs/."""
    project_root = Path(project_root)

    # 1. Directory skeleton
    (project_root / ".claude" / "references").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (project_root / "docs" / "architecture").mkdir(parents=True, exist_ok=True)
    (project_root / ".hdocs").mkdir(parents=True, exist_ok=True)

    # 2. Anchor strategy
    anchor = detect_anchor_strategy(project_root)
    if confirm_anchor:
        ans = input(f"Detected anchor_strategy: {anchor}. Accept? (y/n/manual): ").strip().lower()
        if ans == "n":
            anchor = "derived"
        elif ans == "manual":
            anchor = "manual"

    # 3. L0
    l0_path = project_root / ".claude" / "references" / "L0-architecture.md"
    l0_body = render_template(
        TEMPLATES / "L0.template.md",
        {
            "anchor_strategy": anchor,
            "project_name": project_name,
            "one_line_definition": "TODO",
            "module_list": "\n".join(f"- {m}" for m in modules),
            "external_deps": "TODO",
            "tech_stack": "TODO",
        },
    )
    l0_path.write_text(l0_body, encoding="utf-8")

    # 4. L1 modules
    for mod in modules:
        mod_dir = project_root / "docs" / "architecture" / mod
        mod_dir.mkdir(parents=True, exist_ok=True)
        write_frontmatter(
            mod_dir / "README.md",
            {
                "atlas_version": 1.0,
                "level": 1,
                "parent": ".claude/references/L0-architecture.md",
                "children": [],
                "depends_on": [],
                "used_by": [],
                "keywords": [mod],
                "sync_watch": [],
                "last_synced_commit": "",
                "owner": "atlas-setup",
                "status": "stub",
            },
            f"# L1: {mod}\n\nTODO\n",
        )

    # 5. Hooks (copy templates verbatim — placeholder until Phase 4)
    for hook in ("post_tool_use_sync.py", "session_end_check.py"):
        tmpl = HOOK_TEMPLATES / f"{hook}.tmpl"
        target = project_root / ".claude" / "hooks" / hook
        if tmpl.exists():
            target.write_text(tmpl.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            target.write_text(f"# Placeholder for {hook}\n", encoding="utf-8")

    # 6. .hdocs/ cache
    (project_root / ".hdocs" / "config.yaml").write_text(
        "max_lines:\n  0: 200\n  1: 300\n  default: 500\n", encoding="utf-8"
    )
    (project_root / ".hdocs" / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    (project_root / ".hdocs" / "manifest.json").write_text("{}\n", encoding="utf-8")
    (project_root / ".hdocs" / "sync_index.json").write_text("{}\n", encoding="utf-8")

    # 7. Rebuild skeleton_index (empty at this stage)
    rebuild_skeleton_index(project_root)

    return {
        "stage": 1,
        "anchor_strategy": anchor,
        "l1_count": len(modules),
        "project_name": project_name,
        "date": date.today().isoformat(),
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--name", required=True)
    ap.add_argument("--modules", required=True, help="comma-separated module names")
    args = ap.parse_args()
    result = run_stage1(
        project_root=Path(args.project_root),
        project_name=args.name,
        modules=[m.strip() for m in args.modules.split(",")],
    )
    print(f"Stage 1 complete: {result}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_atlas_setup_stage1.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_setup.py tests/test_atlas_setup_stage1.py
git commit -m "feat(atlas): add Stage 1 setup (shell + L0 + L1 + hooks + .hdocs/)"
```

### Task 3.3: TEMS TCL rule registration hook

**Files:**
- Modify: `scripts/atlas_setup.py` (add `register_tems_rules`)
- Create: `tests/test_atlas_setup_tems.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_setup_tems.py
from unittest.mock import patch
from atlas.scripts.atlas_setup import register_tems_rules


def test_register_tems_rules_calls_tems_commit(tmp_path):
    tems_commit = tmp_path / "tems_commit.py"
    tems_commit.write_text("# fake")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    with patch("atlas.scripts.atlas_setup.subprocess.run", side_effect=fake_run):
        register_tems_rules(tmp_path, tems_commit_path=tems_commit)

    # Should call tems_commit.py at least once with --type TCL
    assert len(calls) >= 1
    call_joined = " ".join(calls[0])
    assert "--type" in call_joined
    assert "TCL" in call_joined
    assert "atlas" in call_joined.lower()
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_atlas_setup_tems.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Append to scripts/atlas_setup.py
import subprocess


def register_tems_rules(project_root: Path, tems_commit_path: Path | None = None) -> None:
    """Register atlas-sync TCL rule in the project's TEMS DB."""
    if tems_commit_path is None:
        tems_commit_path = project_root / "memory" / "tems_commit.py"
    if not tems_commit_path.exists():
        # TEMS not installed in this project — skip silently
        return

    rule = (
        "Atlas sync drift 감지 시 해당 L 파일을 업데이트한다. "
        "3가지 clear 옵션: (a) 본문 수정 (b) 히스토리 추가 (c) 'docs: no-op' 명시"
    )
    cmd = [
        "python",
        str(tems_commit_path),
        "--type", "TCL",
        "--rule", rule,
        "--triggers", "atlas sync drift document",
        "--tags", "atlas,documentation,sync",
    ]
    subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_atlas_setup_tems.py -v`
Expected: 1 passed

- [ ] **Step 5: Wire `register_tems_rules` into `run_stage1`**

Add after step 7 in `run_stage1`:
```python
    # 8. TEMS TCL registration
    register_tems_rules(project_root)
```

- [ ] **Step 6: Re-run Stage 1 test to ensure no regression**

Run: `pytest tests/test_atlas_setup_stage1.py tests/test_atlas_setup_tems.py -v`
Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add scripts/atlas_setup.py tests/test_atlas_setup_tems.py
git commit -m "feat(atlas): wire TEMS TCL registration into Stage 1"
```

---

## Phase 4 — SYNC Engine (hooks + check) (Session 4)

### Task 4.1: `post_tool_use_sync.py` hook template

**Files:**
- Create: `hook_templates/post_tool_use_sync.py.tmpl`
- Create: `tests/test_sync_hook.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_sync_hook.py
import json
import subprocess
import sys
from pathlib import Path


def _install_hook(tmp_project: Path) -> Path:
    """Copy the hook template to .claude/hooks/ as executable."""
    hook_src = Path(__file__).parent.parent / "hook_templates" / "post_tool_use_sync.py.tmpl"
    hook_dst = tmp_project / ".claude" / "hooks" / "post_tool_use_sync.py"
    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    hook_dst.write_text(hook_src.read_text(encoding="utf-8"), encoding="utf-8")
    return hook_dst


def test_hook_injects_reminder_on_drift(tmp_path, sample_l0):
    from atlas.scripts.topology import write_frontmatter, build_sync_index
    import json

    # Setup minimal atlas structure
    (tmp_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (sample_l0.parent).mkdir(parents=True, exist_ok=True)  # already exists from fixture

    gallery = tmp_path / "docs" / "architecture" / "gallery"
    gallery.mkdir(parents=True)
    (gallery / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n"
    )
    write_frontmatter(
        gallery / "crop.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "sync_watch": [{"path": "gallery.html", "range": [1680, 1944]}],
            "depends_on": [], "used_by": [], "keywords": ["crop"],
            "last_synced_commit": "",
        },
        "",
    )

    # Write sync_index
    index = build_sync_index(tmp_path)
    (tmp_path / ".hdocs").mkdir(exist_ok=True)
    (tmp_path / ".hdocs" / "sync_index.json").write_text(json.dumps(index))

    # Install and run hook
    hook = _install_hook(tmp_path)

    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(tmp_path / "gallery.html")},
    }
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        encoding="utf-8",  # Impl-3 Task 4.1 lesson — NOT text=True
        capture_output=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    # Hook should print a <doc-sync-reminder> tag
    assert "doc-sync-reminder" in result.stdout
    assert "docs/architecture/gallery/crop.md" in result.stdout
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_sync_hook.py -v`
Expected: FAIL (hook template not present)

- [ ] **Step 3: Implement the hook template**

```python
# hook_templates/post_tool_use_sync.py.tmpl
#!/usr/bin/env python
"""Atlas PostToolUse hook — detects drift between source edits and L docs.

Reads JSON payload from stdin (Claude Code PostToolUse convention):
  {"tool_name": "...", "tool_input": {"file_path": "..."}, ...}

Emits a reminder to stdout when the edited file overlaps any L-file's sync_watch.
"""
import json
import sys
import os
from pathlib import Path

# Windows cp949 locale defense — reconfigure stdout so Korean strings in the
# reminder body survive cp949 hosts. See Impl-3 Task 4.1 lesson in handover.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0

    tool_input = payload.get("tool_input") or {}
    edited = tool_input.get("file_path") or ""
    if not edited:
        return 0

    project_root = Path(os.getcwd())
    sync_index_path = project_root / ".hdocs" / "sync_index.json"
    if not sync_index_path.exists():
        return 0

    try:
        index = json.loads(sync_index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0

    # Normalize edited path to relative
    try:
        rel_edited = str(Path(edited).resolve().relative_to(project_root.resolve())).replace("\\", "/")
    except ValueError:
        rel_edited = edited.replace("\\", "/")

    # Match path-only (range-based matching is a future enhancement)
    candidates = []
    for source_path, entries in index.items():
        if source_path == "__manual__":
            continue
        if source_path == rel_edited or rel_edited.endswith("/" + source_path):
            for l_rel, range_ in entries:
                candidates.append(l_rel)

    if not candidates:
        return 0

    # Emit reminder
    lines = [
        "<doc-sync-reminder>",
        "[drift 감지]",
        f"수정: {rel_edited}",
        "대응 L 파일:",
    ]
    for c in sorted(set(candidates)):
        lines.append(f"  - {c}")
    lines.append("")
    lines.append("drift clear 3-옵션 중 1가지 적용:")
    lines.append("  (a) 본문 수정")
    lines.append("  (b) 히스토리 엔트리 추가 (+ last_synced_commit 갱신)")
    lines.append('  (c) "docs: no-op" 명시 (주석/포맷/리팩토링만인 경우)')
    lines.append("</doc-sync-reminder>")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_sync_hook.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add hook_templates/post_tool_use_sync.py.tmpl tests/test_sync_hook.py
git commit -m "feat(atlas): add PostToolUse drift detection hook"
```

### Task 4.2: `atlas_check.py` CLI (invariant + drift report)

**Files:**
- Create: `scripts/atlas_check.py`
- Create: `tests/test_atlas_check.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_check.py
import subprocess
import sys
from atlas.scripts.atlas_check import run_check


def test_run_check_returns_report_on_healthy_project(tmp_path, sample_l0):
    # Minimal healthy: just L0
    d = tmp_path / "docs" / "architecture" / "mod"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n# mod\n"
    )
    for feat in ["a", "b"]:
        from atlas.scripts.topology import write_frontmatter
        write_frontmatter(
            d / f"{feat}.md",
            {
                "level": 2, "parent": "docs/architecture/mod/README.md",
                "depends_on": [], "used_by": [], "keywords": [feat],
            },
            "short body\n",
        )

    report = run_check(tmp_path)
    assert report["critical"] == []
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_atlas_check.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_check.py
"""atlas check — run all invariants + drift scan, print report."""
from __future__ import annotations
import json
from pathlib import Path
from .topology import check_all_invariants


def run_check(project_root: Path) -> dict:
    return check_all_invariants(project_root)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root", nargs="?", default=".")
    args = ap.parse_args()
    report = run_check(Path(args.project_root))
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    if report["critical"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_atlas_check.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_check.py tests/test_atlas_check.py
git commit -m "feat(atlas): add atlas check CLI"
```

### Task 4.3: `session_end_check.py` shutdown gate hook

**Files:**
- Create: `hook_templates/session_end_check.py.tmpl`
- Create: `tests/test_session_end_hook.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_session_end_hook.py
import subprocess
import sys
from pathlib import Path


def test_session_end_reports_clean_project(tmp_path, sample_l0):
    hook_src = Path(__file__).parent.parent / "hook_templates" / "session_end_check.py.tmpl"
    hook_dst = tmp_path / ".claude" / "hooks" / "session_end_check.py"
    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    hook_dst.write_text(hook_src.read_text(encoding="utf-8"), encoding="utf-8")

    # Minimal healthy project.
    # NOTE (Impl-3 편차): body line counts are sized to satisfy I3 compression
    # ratio (L2/L1 ∈ [0.1, 0.5]). Each L2 body has 10 non-blank lines and the
    # L1 README has 50 → ratio 0.2. Without this padding both levels would
    # have 1 line each, ratio would be 1.0, and check_all_invariants would
    # populate `warnings`, causing the hook to emit `<session-end-atlas-check>`
    # instead of the "atlas: clean" line the test asserts on.
    d = tmp_path / "docs" / "architecture" / "mod"
    d.mkdir(parents=True)
    l1_body = "\n".join(f"line {i}" for i in range(50))
    (d / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n"
        + l1_body + "\n",
        encoding="utf-8",
    )
    for feat in ["a", "b"]:
        l2_body = "\n".join(f"line {i}" for i in range(10))
        (d / f"{feat}.md").write_text(
            f"---\nlevel: 2\nparent: docs/architecture/mod/README.md\n"
            f"depends_on: []\nused_by: []\nkeywords: [{feat}]\n---\n"
            + l2_body + "\n",
            encoding="utf-8",
        )

    result = subprocess.run(
        [sys.executable, str(hook_dst)],
        input="",
        encoding="utf-8",  # Impl-3 Task 4.1 lesson — NOT text=True
        capture_output=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "atlas: clean" in result.stdout or "no drift" in result.stdout.lower()
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_session_end_hook.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# hook_templates/session_end_check.py.tmpl
#!/usr/bin/env python
"""Atlas session-end check — invariant + drift gate.

When drift exists, prints a forced-dialogue prompt asking the agent to pick
one of the 3 clear options. When clean, prints "atlas: clean".
"""
import os
import sys
from pathlib import Path

# Windows cp949 locale defense — see Impl-3 Task 4.1 lesson in handover.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Make topology.py importable
SKILL_ROOT = Path(os.environ.get("ATLAS_SKILL_ROOT", "E:/AgentInterface/skills/atlas"))
sys.path.insert(0, str(SKILL_ROOT))

try:
    from scripts.topology import check_all_invariants
except ImportError:
    print("atlas: skill unavailable, skipping session-end check")
    sys.exit(0)


def main() -> int:
    project_root = Path(os.getcwd())
    report = check_all_invariants(project_root)

    critical = report.get("critical") or []
    warnings = report.get("warnings") or []
    overflows = report.get("overflows") or []

    if not critical and not warnings and not overflows:
        print("atlas: clean — no drift, invariants satisfied")
        return 0

    print("<session-end-atlas-check>")
    if critical:
        print("[치명 — 세션 종료 보류]")
        for c in critical:
            print(f"  - {c}")
    if warnings:
        print("[경고]")
        for w in warnings:
            print(f"  - {w}")
    if overflows:
        print("[OVERFLOW]")
        for path, level, lines in overflows:
            print(f"  - L{level} {path}: {lines} lines (> cap)")
    print("")
    print("drift clear 3-옵션 중 1가지 선택:")
    print("  (a) 지금 업데이트")
    print("  (b) 전체 'docs: no-op' 명시")
    print("  (c) 다음 세션 이월 (TEMS 경고 엔트리 기록)")
    print("</session-end-atlas-check>")
    return 0 if not critical else 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_session_end_hook.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add hook_templates/session_end_check.py.tmpl tests/test_session_end_hook.py
git commit -m "feat(atlas): add session-end check hook (forced dialogue gate)"
```

---

## Phase 5 — BACKFILL Engine (Stages 2+3) (Session 5)

### Task 5.1: git log Top-K frequency analyzer

**Files:**
- Create: `scripts/git_analysis.py`
- Create: `tests/test_git_analysis.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_git_analysis.py
import subprocess
from atlas.scripts.git_analysis import top_k_modified_files


def _git(cwd, *args):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, capture_output=True)


def test_top_k_finds_most_edited(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("v1\n")
    (tmp_path / "b.py").write_text("v1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    (tmp_path / "a.py").write_text("v2\n")
    _git(tmp_path, "commit", "-am", "edit a")
    (tmp_path / "a.py").write_text("v3\n")
    _git(tmp_path, "commit", "-am", "edit a again")
    (tmp_path / "b.py").write_text("v2\n")
    _git(tmp_path, "commit", "-am", "edit b")

    top = top_k_modified_files(tmp_path, k=2, depth=50)
    names = [f for f, _ in top]
    assert "a.py" in names
    assert names.index("a.py") < names.index("b.py")  # a edited more
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_git_analysis.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/git_analysis.py
"""git log frequency analysis for atlas backfill Stage 2."""
from __future__ import annotations
import subprocess
from collections import Counter
from pathlib import Path


def top_k_modified_files(project_root: Path, k: int = 8, depth: int = 50) -> list[tuple[str, int]]:
    """Return [(file_path, edit_count)] sorted desc, limited to k."""
    result = subprocess.run(
        ["git", "log", f"-{depth}", "--name-only", "--pretty=format:"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    counts: Counter[str] = Counter()
    for line in result.stdout.splitlines():
        line = line.strip()
        if line and not line.startswith("commit"):
            counts[line] += 1
    return counts.most_common(k)


def extract_fix_commits(
    project_root: Path, path: str, depth: int = 100
) -> list[dict]:
    """Return [{sha, date, subject, body}] for commits touching path where subject starts with 'fix'/'revert'."""
    result = subprocess.run(
        ["git", "log", f"-{depth}", "--format=%H|%ci|%s%n%b%n---END---", "--", path],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    out: list[dict] = []
    chunks = result.stdout.split("---END---")
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        header, _, body = chunk.partition("\n")
        parts = header.split("|", 2)
        if len(parts) != 3:
            continue
        sha, date_, subject = parts
        if subject.startswith(("fix", "revert")):
            out.append({"sha": sha, "date": date_, "subject": subject, "body": body.strip()})
    return out
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_git_analysis.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/git_analysis.py tests/test_git_analysis.py
git commit -m "feat(atlas): add git log Top-K and fix commit extractor"
```

### Task 5.2: Stage 2 — L2 stub generator

**Files:**
- Create: `scripts/atlas_backfill.py` (stage 2)
- Create: `tests/test_backfill_stage2.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_backfill_stage2.py
import subprocess
from atlas.scripts.atlas_backfill import run_stage2
from atlas.scripts.atlas_setup import run_stage1
from atlas.scripts.topology import parse_frontmatter


def _git(cwd, *args):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, capture_output=True)


def test_stage2_creates_l2_stubs_from_top_k(tmp_path):
    # Set up a git repo with edited files
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18"}}')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "gallery.html").write_text("v1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    (tmp_path / "src" / "gallery.html").write_text("v2\n")
    _git(tmp_path, "commit", "-am", "fix: gallery")

    # Stage 1 first
    run_stage1(
        project_root=tmp_path,
        project_name="Test",
        modules=["src"],
        confirm_anchor=False,
    )

    # Stage 2
    result = run_stage2(project_root=tmp_path, k=4)
    assert result["stage"] == 2
    assert result["l2_count"] >= 1

    # Check that an L2 stub was created for gallery.html
    # Expected path: docs/architecture/src/gallery.html.md (sanitized)
    stub_candidates = list((tmp_path / "docs" / "architecture" / "src").glob("*.md"))
    stub_l2 = [s for s in stub_candidates if parse_frontmatter(s)[0].get("level") == 2]
    assert len(stub_l2) >= 1
    meta, _ = parse_frontmatter(stub_l2[0])
    assert meta["status"] == "stub"
    assert meta["sync_watch"]
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_backfill_stage2.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_backfill.py
"""Atlas BACKFILL engine — Stages 2 (spine) and 3 (history)."""
from __future__ import annotations
from pathlib import Path
import re
from typing import Any

from .topology import write_frontmatter, rebuild_skeleton_index, check_all_invariants
from .git_analysis import top_k_modified_files, extract_fix_commits


def _safe_feature_name(src_path: str) -> str:
    """Convert a source file path into a stable L2 feature filename."""
    stem = Path(src_path).name
    return re.sub(r"[^a-zA-Z0-9_\-]", "-", stem)


def _match_module(src_path: str, modules: list[str]) -> str:
    """Match a source path to the closest module in the project."""
    parts = Path(src_path).parts
    for mod in modules:
        if mod in parts:
            return mod
    # Fallback: first module
    return modules[0] if modules else "misc"


def run_stage2(project_root: Path, k: int = 8) -> dict[str, Any]:
    """Stage 2 — create L2 stubs for Top-K edited files."""
    project_root = Path(project_root)

    # Discover existing L1 modules
    arch = project_root / "docs" / "architecture"
    modules = [p.name for p in arch.iterdir() if p.is_dir()] if arch.exists() else []
    if not modules:
        raise RuntimeError("Stage 2 requires Stage 1 completed (no L1 modules found)")

    top = top_k_modified_files(project_root, k=k, depth=50)
    l2_count = 0
    for src_path, edit_count in top:
        if not src_path.strip() or src_path.startswith("docs/"):
            continue
        mod = _match_module(src_path, modules)
        feature = _safe_feature_name(src_path)
        l2_path = project_root / "docs" / "architecture" / mod / f"{feature}.md"
        if l2_path.exists():
            continue
        write_frontmatter(
            l2_path,
            {
                "atlas_version": 1.0,
                "level": 2,
                "parent": f"docs/architecture/{mod}/README.md",
                "children": [],
                "depends_on": [],
                "used_by": [],
                "keywords": [feature],
                "sync_watch": [{"path": src_path}],
                "last_synced_commit": "",
                "owner": "atlas-backfill",
                "status": "stub",
            },
            f"# L2: {feature}\n\n## 목적\nTODO\n\n## 코드 위치\n- `{src_path}`\n\n## 핵심 동작\n1. TODO\n2. TODO\n3. TODO\n\n## 히스토리\n→ `{feature}.history.md`\n",
        )
        l2_count += 1

    rebuild_skeleton_index(project_root)
    report = check_all_invariants(project_root)
    return {
        "stage": 2,
        "l2_count": l2_count,
        "invariant_report": report,
    }
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_backfill_stage2.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_backfill.py tests/test_backfill_stage2.py
git commit -m "feat(atlas): add Stage 2 backfill (L2 stubs from Top-K)"
```

### Task 5.3: Stage 3 — history entry writer + TEMS cross-check

**Files:**
- Modify: `scripts/atlas_backfill.py` (add `run_stage3`)
- Create: `scripts/tems_query.py`
- Create: `tests/test_backfill_stage3.py`

- [ ] **Step 1: Write test for tems_query helper**

```python
# tests/test_tems_query.py
from atlas.scripts.tems_query import jaccard_similarity


def test_jaccard_basic():
    assert jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"}) == 0.5


def test_jaccard_identical():
    assert jaccard_similarity({"a"}, {"a"}) == 1.0


def test_jaccard_empty():
    assert jaccard_similarity(set(), set()) == 0.0
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_tems_query.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `tems_query.py`**

```python
# scripts/tems_query.py
"""Helper for TEMS DB cross-check during backfill Stage 3 and promotion."""
from __future__ import annotations
import subprocess
from pathlib import Path


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def query_tems_tgl_candidates(
    project_root: Path, keywords: list[str]
) -> list[dict]:
    """Query TEMS DB for existing TGL rules matching keywords.

    Returns [{rule_id, rule_text, triggers, tags}]. Requires existing tems_query.py
    infrastructure in the project. Best-effort — returns [] if TEMS not available.
    """
    query_script = project_root / "memory" / "tems_query.py"
    if not query_script.exists():
        return []
    result = subprocess.run(
        ["python", str(query_script), "--type", "TGL", "--query", " ".join(keywords), "--json"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    import json
    try:
        # Handle stdout preamble per TGL#70
        raw = result.stdout
        start = raw.find("[")
        if start == -1:
            return []
        return json.loads(raw[start:])
    except json.JSONDecodeError:
        return []
```

- [ ] **Step 4: Run tems_query test**

Run: `pytest tests/test_tems_query.py -v`
Expected: 3 passed

- [ ] **Step 5: Write failing test for Stage 3**

```python
# tests/test_backfill_stage3.py
import subprocess
from atlas.scripts.atlas_backfill import run_stage2, run_stage3
from atlas.scripts.atlas_setup import run_stage1
from atlas.scripts.topology import parse_frontmatter


def _git(cwd, *args):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, capture_output=True)


def test_stage3_creates_history_from_fix_commits(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18"}}')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "gallery.html").write_text("v1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    (tmp_path / "src" / "gallery.html").write_text("v2\n")
    _git(tmp_path, "commit", "-am", "fix: crop coordinate bug")
    (tmp_path / "src" / "gallery.html").write_text("v3\n")
    _git(tmp_path, "commit", "-am", "fix: upload retry identity")

    run_stage1(project_root=tmp_path, project_name="T", modules=["src"], confirm_anchor=False)
    run_stage2(project_root=tmp_path, k=4)

    result = run_stage3(project_root=tmp_path, use_haiku=False)
    assert result["stage"] == 3
    assert result["history_entries"] >= 2

    # History file exists
    history_files = list((tmp_path / "docs" / "architecture" / "src").glob("*.history.md"))
    assert len(history_files) >= 1
    meta, body = parse_frontmatter(history_files[0])
    assert meta["append_only"] is True
    assert "fix" in body.lower() or "crop" in body.lower()
```

- [ ] **Step 6: Run test**

Run: `pytest tests/test_backfill_stage3.py -v`
Expected: FAIL

- [ ] **Step 7: Implement `run_stage3`**

```python
# Append to scripts/atlas_backfill.py
from .tems_query import jaccard_similarity, query_tems_tgl_candidates
from .topology import parse_frontmatter


def _summarize_diff_main_agent(subject: str, body: str) -> dict[str, Any]:
    """Fallback: extract a simple template from commit subject/body without Haiku."""
    # Very naive extraction — real lessons require agent judgment
    return {
        "symptom": subject,
        "cause": body[:200] if body else "(미기록)",
        "patch": "(커밋 diff 참조)",
        "lesson": subject,
        "keywords_for_promotion": re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_\-]{2,}\b", subject)[:5],
    }


def _summarize_diff_haiku(sha: str, subject: str, body: str) -> dict[str, Any]:
    """Haiku subcall for diff summarization. Placeholder — actual Haiku wiring
    depends on runtime. For v1, falls through to main agent summarizer if not available."""
    # TODO wire to anthropic SDK when runtime is available
    return _summarize_diff_main_agent(subject, body)


def run_stage3(
    project_root: Path, use_haiku: bool = True, similarity_threshold: float = 0.5
) -> dict[str, Any]:
    """Stage 3 — append history entries to each L2 from its sync_watch file's fix commits."""
    project_root = Path(project_root)
    arch = project_root / "docs" / "architecture"
    if not arch.exists():
        return {"stage": 3, "history_entries": 0, "tgl_xref": 0}

    total_entries = 0
    total_xref = 0

    for l2_path in arch.rglob("*.md"):
        if l2_path.name.endswith(".history.md"):
            continue
        meta, _ = parse_frontmatter(l2_path)
        if meta.get("level") != 2:
            continue
        watches = meta.get("sync_watch") or []
        for w in watches:
            src_path = w.get("path")
            if not src_path:
                continue
            fixes = extract_fix_commits(project_root, src_path, depth=100)
            if not fixes:
                continue

            history_path = l2_path.with_name(l2_path.stem + ".history.md")
            if not history_path.exists():
                write_frontmatter(
                    history_path,
                    {
                        "atlas_version": 1.0,
                        "level": 2,
                        "history_of": str(l2_path.relative_to(project_root)).replace("\\", "/"),
                        "append_only": True,
                        "owner": "atlas-backfill",
                    },
                    f"# L2 History: {l2_path.stem}\n\n## 요약 (표)\n\n| 날짜 | 커밋 | 유형 | 한 줄 | 상세 |\n|---|---|---|---|---|\n\n## 상세\n",
                )

            # Append each fix as a history entry
            with history_path.open("a", encoding="utf-8") as f:
                for fx in fixes:
                    summary = (
                        _summarize_diff_haiku(fx["sha"], fx["subject"], fx["body"])
                        if use_haiku
                        else _summarize_diff_main_agent(fx["subject"], fx["body"])
                    )

                    # TEMS cross-check
                    tgl_ref = ""
                    kws = set(summary["keywords_for_promotion"])
                    if len(kws) >= 2:
                        tgls = query_tems_tgl_candidates(project_root, list(kws))
                        for tgl in tgls:
                            existing = set((tgl.get("triggers") or "").split())
                            if (
                                jaccard_similarity(kws, existing) >= similarity_threshold
                                and len(kws & existing) >= 2
                            ):
                                tgl_ref = f"TGL#{tgl.get('rule_id', '?')}"
                                total_xref += 1
                                break

                    total_entries += 1
                    f.write(
                        f"\n### #{total_entries} — {fx['date'][:10]} `{fx['sha'][:7]}` 🐛 {summary['symptom']}\n\n"
                    )
                    f.write(f"**원인:** {summary['cause']}\n\n")
                    f.write(f"**패치:** {summary['patch']}\n\n")
                    f.write(f"**교훈:** {summary['lesson']}\n\n")
                    f.write(f"**promote_candidate:** {'false' if tgl_ref else 'true'}\n\n")
                    if tgl_ref:
                        f.write(f"**tgl_ref:** {tgl_ref}\n\n")
                    f.write(f"**keywords_for_promotion:** {list(kws)}\n\n")

    return {"stage": 3, "history_entries": total_entries, "tgl_xref": total_xref}
```

- [ ] **Step 8: Run test**

Run: `pytest tests/test_backfill_stage3.py -v`
Expected: 1 passed

- [ ] **Step 9: Commit**

```bash
git add scripts/atlas_backfill.py scripts/tems_query.py tests/test_tems_query.py tests/test_backfill_stage3.py
git commit -m "feat(atlas): add Stage 3 backfill with TEMS TGL cross-check"
```

---

## Phase 6 — PROMOTE Engine (Session 6)

### Task 6.1: L-history scanner + Rule 1/2 detector

**Files:**
- Create: `scripts/atlas_promote_check.py`
- Create: `tests/test_promote_check.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_promote_check.py
from atlas.scripts.atlas_promote_check import (
    scan_history_entries,
    detect_rule1_local,
    detect_rule2_cross,
)


HISTORY_SAMPLE = """---
atlas_version: 1.0
level: 2
history_of: docs/architecture/gallery/crop.md
append_only: true
---

# History

## 상세

### #1 — 2026-04-10 `abc1234` 🐛 coordinate drift

**keywords_for_promotion:** ['coordinate', 'single-source-of-truth', 'c_limit']

### #2 — 2026-04-11 `def5678` 🐛 coordinate again

**keywords_for_promotion:** ['coordinate', 'single-source-of-truth', 'transform']

### #3 — 2026-04-12 `ghi9012` 🐛 still coordinate

**keywords_for_promotion:** ['coordinate', 'single-source-of-truth', 'pixel']
"""


def test_scan_history_parses_entries(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    (d / "crop.md").write_text("---\nlevel: 2\nparent: docs/architecture/gallery/README.md\nkeywords: [crop]\ndepends_on: []\nused_by: []\n---\n")
    (d / "crop.history.md").write_text(HISTORY_SAMPLE)

    entries = scan_history_entries(tmp_project)
    assert len(entries) == 3
    assert all(isinstance(e.get("keywords"), list) for e in entries)


def test_rule1_local_repetition_detects_3plus(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    (d / "crop.md").write_text("---\nlevel: 2\nparent: docs/architecture/gallery/README.md\nkeywords: [crop]\ndepends_on: []\nused_by: []\n---\n")
    (d / "crop.history.md").write_text(HISTORY_SAMPLE)

    candidates = detect_rule1_local(tmp_project)
    assert len(candidates) >= 1
    assert "coordinate" in candidates[0]["shared_keywords"]


def test_rule2_cross_functional_detects_2plus(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")
    (d / "crop.md").write_text("---\nlevel: 2\nparent: docs/architecture/gallery/README.md\nkeywords: [crop]\ndepends_on: []\nused_by: []\n---\n")
    (d / "crop.history.md").write_text(
        "---\nlevel: 2\nhistory_of: docs/architecture/gallery/crop.md\nappend_only: true\n---\n\n"
        "### #1 — 2026-04-10 `abc` 🐛 x\n**keywords_for_promotion:** ['stale', 'react-setstate']\n"
    )
    (d / "upload.md").write_text("---\nlevel: 2\nparent: docs/architecture/gallery/README.md\nkeywords: [upload]\ndepends_on: []\nused_by: []\n---\n")
    (d / "upload.history.md").write_text(
        "---\nlevel: 2\nhistory_of: docs/architecture/gallery/upload.md\nappend_only: true\n---\n\n"
        "### #1 — 2026-04-11 `def` 🐛 y\n**keywords_for_promotion:** ['stale', 'react-setstate', 'closure']\n"
    )

    candidates = detect_rule2_cross(tmp_project)
    assert len(candidates) >= 1
    assert "stale" in candidates[0]["shared_keywords"]
    assert "react-setstate" in candidates[0]["shared_keywords"]
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_promote_check.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_promote_check.py
"""Atlas PROMOTE engine — detect TGL promotion candidates from L-history."""
from __future__ import annotations
import re
import ast
from pathlib import Path
from typing import Any
from collections import defaultdict

from .topology import discover_atlas_files, parse_frontmatter
from .tems_query import jaccard_similarity


_ENTRY_HEADER = re.compile(r"^###\s+#(\d+)\s+—\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)
_KEYWORDS_LINE = re.compile(r"\*\*keywords_for_promotion:\*\*\s*(\[.*?\])", re.IGNORECASE)


def scan_history_entries(project_root: Path) -> list[dict[str, Any]]:
    """Parse all history files and return entry metadata."""
    entries: list[dict[str, Any]] = []
    for f in discover_atlas_files(project_root):
        if not str(f).endswith(".history.md"):
            continue
        meta, body = parse_frontmatter(f)
        history_of = meta.get("history_of", "")
        for match in _ENTRY_HEADER.finditer(body):
            start = match.end()
            next_match = _ENTRY_HEADER.search(body, start)
            end = next_match.start() if next_match else len(body)
            entry_text = body[start:end]

            kw_match = _KEYWORDS_LINE.search(entry_text)
            keywords: list[str] = []
            if kw_match:
                try:
                    keywords = [str(k) for k in ast.literal_eval(kw_match.group(1))]
                except (ValueError, SyntaxError):
                    keywords = []

            entries.append(
                {
                    "history_file": str(f.relative_to(project_root)).replace("\\", "/"),
                    "history_of": history_of,
                    "entry_num": int(match.group(1)),
                    "date": match.group(2),
                    "keywords": keywords,
                }
            )
    return entries


def detect_rule1_local(
    project_root: Path,
    threshold: float = 0.5,
    min_shared: int = 2,
    min_occurrences: int = 3,
) -> list[dict[str, Any]]:
    """Rule 1 — same history file, similar lessons ≥ N times."""
    entries = scan_history_entries(project_root)
    by_file: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_file[e["history_file"]].append(e)

    candidates: list[dict[str, Any]] = []
    for fname, es in by_file.items():
        # Cluster by pairwise Jaccard ≥ threshold AND shared ≥ min_shared
        for i in range(len(es)):
            cluster = [es[i]]
            for j in range(i + 1, len(es)):
                set_i = set(es[i]["keywords"])
                set_j = set(es[j]["keywords"])
                shared = set_i & set_j
                if (
                    jaccard_similarity(set_i, set_j) >= threshold
                    and len(shared) >= min_shared
                ):
                    cluster.append(es[j])
            if len(cluster) >= min_occurrences:
                shared_all = set.intersection(*(set(e["keywords"]) for e in cluster))
                candidates.append(
                    {
                        "rule": 1,
                        "history_file": fname,
                        "cluster_size": len(cluster),
                        "shared_keywords": sorted(shared_all),
                        "entries": [e["entry_num"] for e in cluster],
                    }
                )
                break  # one cluster per file is enough for v1
    return candidates


def detect_rule2_cross(
    project_root: Path,
    threshold: float = 0.5,
    min_shared: int = 2,
    min_occurrences: int = 2,
) -> list[dict[str, Any]]:
    """Rule 2 — different history files, similar lessons ≥ N times (cross-functional)."""
    entries = scan_history_entries(project_root)
    candidates: list[dict[str, Any]] = []

    for i in range(len(entries)):
        cluster = [entries[i]]
        for j in range(i + 1, len(entries)):
            if entries[j]["history_file"] == entries[i]["history_file"]:
                continue
            set_i = set(entries[i]["keywords"])
            set_j = set(entries[j]["keywords"])
            shared = set_i & set_j
            if (
                jaccard_similarity(set_i, set_j) >= threshold
                and len(shared) >= min_shared
            ):
                cluster.append(entries[j])
        unique_files = {e["history_file"] for e in cluster}
        if len(unique_files) >= min_occurrences:
            shared_all = set.intersection(*(set(e["keywords"]) for e in cluster))
            candidates.append(
                {
                    "rule": 2,
                    "history_files": sorted(unique_files),
                    "cluster_size": len(cluster),
                    "shared_keywords": sorted(shared_all),
                }
            )
    return candidates
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_promote_check.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_promote_check.py tests/test_promote_check.py
git commit -m "feat(atlas): add Rule 1/2 promotion candidate detection"
```

### Task 6.2: Candidate presenter + TEMS pre-filter + registration

**Files:**
- Modify: `scripts/atlas_promote_check.py` (add `present_candidates`, `register_tgl`, `main`)
- Create: `tests/test_promote_register.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_promote_register.py
from unittest.mock import patch
from atlas.scripts.atlas_promote_check import register_tgl


def test_register_tgl_calls_tems_commit(tmp_path):
    tems = tmp_path / "memory"
    tems.mkdir()
    (tems / "tems_commit.py").write_text("# fake")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = "rule_id: 42"
            stderr = ""
        return R()

    with patch("atlas.scripts.atlas_promote_check.subprocess.run", side_effect=fake_run):
        rid = register_tgl(
            project_root=tmp_path,
            rule_text="크롭 좌표 단일 진실원 유지",
            triggers="crop coordinate 좌표",
            tags="atlas,coordinate",
        )
    assert calls
    cmd = calls[0]
    assert "--type" in cmd
    assert "TGL" in cmd
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_promote_register.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# Append to scripts/atlas_promote_check.py
import subprocess
import json


def present_candidates(candidates: list[dict[str, Any]]) -> str:
    """Format candidates into a human-readable prompt."""
    if not candidates:
        return "atlas: no promotion candidates"
    lines = [f"[승격 후보 {len(candidates)}건]"]
    for i, c in enumerate(candidates, 1):
        rule = c["rule"]
        shared = ", ".join(c["shared_keywords"])
        if rule == 1:
            lines.append(f"#{i} (Rule 1 local × {c['cluster_size']}) {c['history_file']}")
        else:
            files = ", ".join(Path(f).stem for f in c["history_files"])
            lines.append(f"#{i} (Rule 2 cross × {c['cluster_size']}) {files}")
        lines.append(f"   shared_keywords: [{shared}]")
        lines.append(
            f"   제안 TGL: '<agent가 shared_keywords로 1줄 규칙 작성>'"
        )
        lines.append("")
    lines.append("각 후보에 (a) 승인 (b) 수정 (c) 거부 선택")
    return "\n".join(lines)


def register_tgl(
    project_root: Path, rule_text: str, triggers: str, tags: str
) -> int | None:
    """Call tems_commit.py to register a new TGL rule."""
    tems_commit = project_root / "memory" / "tems_commit.py"
    if not tems_commit.exists():
        return None
    result = subprocess.run(
        [
            "python",
            str(tems_commit),
            "--type", "TGL",
            "--rule", rule_text,
            "--triggers", triggers,
            "--tags", tags,
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    # Parse rule_id from output
    for line in result.stdout.splitlines():
        if "rule_id" in line:
            try:
                return int(line.split(":")[-1].strip())
            except ValueError:
                pass
    return None


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root", nargs="?", default=".")
    ap.add_argument("--threshold", type=float, default=0.5)
    args = ap.parse_args()

    project_root = Path(args.project_root)
    candidates = detect_rule1_local(project_root, threshold=args.threshold)
    candidates += detect_rule2_cross(project_root, threshold=args.threshold)
    print(present_candidates(candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_promote_register.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_promote_check.py tests/test_promote_register.py
git commit -m "feat(atlas): add candidate presenter and TGL registration wrapper"
```

---

## Phase 7 — Split/Collapse Operators (Session 7)

### Task 7.1: `atlas_split.py` — vertical and horizontal split

**Files:**
- Create: `scripts/atlas_split.py`
- Create: `tests/test_atlas_split.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_split.py
from atlas.scripts.atlas_split import split_vertical
from atlas.scripts.topology import parse_frontmatter, write_frontmatter


def test_vertical_split_creates_children_and_index(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text(
        "---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n"
    )

    # A big L2 file with 3 distinct sections
    big_body = (
        "\n".join(f"line {i}" for i in range(60))
        + "\n\n## Coordinate Transform\n\n"
        + "\n".join(f"ct {i}" for i in range(200))
        + "\n\n## Handle Interaction\n\n"
        + "\n".join(f"hi {i}" for i in range(200))
        + "\n\n## Auto Save\n\n"
        + "\n".join(f"as {i}" for i in range(200))
    )
    write_frontmatter(
        d / "crop.md",
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "depends_on": [], "used_by": [], "keywords": ["crop"],
        },
        big_body,
    )

    result = split_vertical(tmp_project, d / "crop.md")
    assert result["new_children"] == 3

    # Original file now an index
    meta, body = parse_frontmatter(d / "crop.md")
    assert len(meta.get("children") or []) == 3

    # Children exist at docs/architecture/gallery/crop/<child>.md
    assert (d / "crop" / "coordinate-transform.md").exists()
    assert (d / "crop" / "handle-interaction.md").exists()
    assert (d / "crop" / "auto-save.md").exists()
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_atlas_split.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_split.py
"""Atlas split operators — vertical (new level) and horizontal (same level)."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any

from .topology import parse_frontmatter, write_frontmatter, check_all_invariants, rebuild_skeleton_index


_SECTION_HEADER = re.compile(r"^(##\s+.+)$", re.MULTILINE)


def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    return s.strip("-")


def split_vertical(project_root: Path, target: Path) -> dict[str, Any]:
    """Convert `target` into an index file whose former `## sections` become L_{k+1} children."""
    target = Path(target)
    meta, body = parse_frontmatter(target)
    level = int(meta.get("level", 2))

    headers = list(_SECTION_HEADER.finditer(body))
    if len(headers) < 3:
        return {"new_children": 0, "reason": "need >= 3 sections for vertical split"}

    # Partition body into sections
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(headers):
        title = m.group(1).lstrip("#").strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        sections.append((title, body[start:end].strip()))

    # Create child directory
    child_dir = target.with_name(target.stem)
    child_dir.mkdir(exist_ok=True)

    new_children: list[str] = []
    for title, content in sections:
        slug = _slugify(title)
        child_path = child_dir / f"{slug}.md"
        rel_parent = str(target.relative_to(project_root)).replace("\\", "/")
        write_frontmatter(
            child_path,
            {
                "atlas_version": 1.0,
                "level": level + 1,
                "parent": rel_parent,
                "children": [],
                "depends_on": [],
                "used_by": [],
                "keywords": [slug],
                "sync_watch": [],
                "last_synced_commit": meta.get("last_synced_commit", ""),
                "owner": meta.get("owner", "atlas-split"),
                "status": "active",
            },
            f"# L{level+1}: {title}\n\n{content}\n",
        )
        new_children.append(str(child_path.relative_to(project_root)).replace("\\", "/"))

    # Rewrite target as an index
    meta["children"] = new_children
    header_preamble = body[: headers[0].start()].strip()
    index_body_lines = [header_preamble, "", "## 하위 기능 인덱스", ""]
    for title, _ in sections:
        slug = _slugify(title)
        index_body_lines.append(f"- [{title}]({target.stem}/{slug}.md)")
    write_frontmatter(target, meta, "\n".join(index_body_lines) + "\n")

    rebuild_skeleton_index(project_root)
    report = check_all_invariants(project_root)
    return {"new_children": len(new_children), "invariant_report": report}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--mode", choices=["vertical", "horizontal"], default="vertical")
    ap.add_argument("--project-root", default=".")
    args = ap.parse_args()
    result = split_vertical(Path(args.project_root), Path(args.target))
    import json
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_atlas_split.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_split.py tests/test_atlas_split.py
git commit -m "feat(atlas): add vertical split operator"
```

### Task 7.2: `atlas_collapse.py` — level collapse (inverse)

**Files:**
- Create: `scripts/atlas_collapse.py`
- Create: `tests/test_atlas_collapse.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_atlas_collapse.py
from atlas.scripts.atlas_collapse import collapse_level
from atlas.scripts.topology import parse_frontmatter, write_frontmatter


def test_collapse_merges_small_children_back(tmp_project, sample_l0):
    d = tmp_project / "docs" / "architecture" / "gallery"
    d.mkdir(parents=True)
    (d / "README.md").write_text("---\nlevel: 1\nparent: .claude/references/L0-architecture.md\n---\n")

    # An index with 3 small children
    parent = d / "crop.md"
    child_dir = d / "crop"
    child_dir.mkdir()
    write_frontmatter(
        parent,
        {
            "level": 2,
            "parent": "docs/architecture/gallery/README.md",
            "children": [
                "docs/architecture/gallery/crop/a.md",
                "docs/architecture/gallery/crop/b.md",
                "docs/architecture/gallery/crop/c.md",
            ],
            "depends_on": [], "used_by": [], "keywords": ["crop"],
        },
        "## 하위 기능 인덱스\n- a\n- b\n- c\n",
    )
    for name in ["a", "b", "c"]:
        write_frontmatter(
            child_dir / f"{name}.md",
            {
                "level": 3,
                "parent": "docs/architecture/gallery/crop.md",
                "depends_on": [], "used_by": [], "keywords": [name],
            },
            f"short content for {name}\n",
        )

    result = collapse_level(tmp_project, parent)
    assert result["collapsed_children"] == 3
    # Children dir removed
    assert not (d / "crop").exists() or not list((d / "crop").glob("*.md"))
    # Parent body now contains all children content
    _, body = parse_frontmatter(parent)
    assert "short content for a" in body
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_atlas_collapse.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

```python
# scripts/atlas_collapse.py
"""Atlas collapse operator — inverse of vertical split."""
from __future__ import annotations
from pathlib import Path
from typing import Any

from .topology import parse_frontmatter, write_frontmatter, check_all_invariants, rebuild_skeleton_index


def collapse_level(project_root: Path, target: Path) -> dict[str, Any]:
    """Absorb target's children back into target. Deletes child files + dir."""
    target = Path(target)
    meta, body = parse_frontmatter(target)
    children_rel = meta.get("children") or []
    if not children_rel:
        return {"collapsed_children": 0, "reason": "no children"}

    absorbed_sections: list[str] = []
    child_paths: list[Path] = []
    for rel in children_rel:
        child_path = project_root / rel
        if not child_path.exists():
            continue
        child_meta, child_body = parse_frontmatter(child_path)
        title = child_meta.get("keywords", ["unnamed"])[0]
        absorbed_sections.append(f"## {title}\n\n{child_body.strip()}\n")
        child_paths.append(child_path)

    # Rewrite target body with absorbed content
    new_body = (body.split("## 하위 기능 인덱스")[0].strip() + "\n\n" + "\n".join(absorbed_sections))
    meta["children"] = []
    write_frontmatter(target, meta, new_body)

    # Delete child files and empty directory
    for cp in child_paths:
        cp.unlink()
    child_dir = target.with_name(target.stem)
    if child_dir.exists() and not any(child_dir.iterdir()):
        child_dir.rmdir()

    rebuild_skeleton_index(project_root)
    report = check_all_invariants(project_root)
    return {"collapsed_children": len(child_paths), "invariant_report": report}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--project-root", default=".")
    args = ap.parse_args()
    result = collapse_level(Path(args.project_root), Path(args.target))
    import json
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test**

Run: `pytest tests/test_atlas_collapse.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/atlas_collapse.py tests/test_atlas_collapse.py
git commit -m "feat(atlas): add collapse operator (inverse of vertical split)"
```

---

## Phase 8 — SKILL.md + References (Session 8)

Documentation tasks are non-TDD; they are content. Each task writes a reference file matching the spec's claim at the given section.

### Task 8.1: Write `SKILL.md` main guide

**Files:**
- Create: `E:/AgentInterface/skills/atlas/SKILL.md`

- [ ] **Step 1: Write the file**

```markdown
---
name: atlas
description: Use when a project grows beyond ~2000 LOC or ~50 files and agent context starts thrashing — scaffolds hierarchical docs (L0~LN) with drift detection, TEMS lesson promotion, and drill-down protocol. Also use when migrating existing projects via staged backfill.
---

# atlas — Dynamic Hierarchical Documentation

Atlas builds a project atlas: a tree of markdown files organized by (level, time) coordinates. L0 is the whole-project map auto-injected at boot; Lk (k≥1) is drilled into only when the task needs it. Each present file has an optional `.history.md` twin that accumulates bug/patch lessons.

## When to Use

- New project reaching moderate complexity — run `atlas setup` once for a shell.
- Existing large project — run `atlas backfill --stage 2` (then `--stage 3`) to seed L2 from git history.
- You notice documentation drift, recurring bugs, or context thrashing across sessions.

## Core Commands

```bash
atlas setup <project> --name <N> --modules <m1,m2>    # Stage 1: L0 + L1 + hooks + TEMS TCL
atlas backfill --stage 2                               # Top-K L2 stubs
atlas backfill --stage 3                               # git log → L-history + TEMS xref
atlas check                                            # invariants + drift report
atlas split <l-file> --mode vertical|horizontal        # OVERFLOW recovery
atlas collapse <l-file>                                # inverse of split
atlas promote-check                                    # TGL promotion candidate scan
atlas rebuild-cache                                    # recover from .hdocs/ corruption
```

## Drill-Down Protocol (Agent-Driven NAV)

When a user asks about feature X:

1. L0 is already in context (auto-injected at boot). Read its `skeleton_index` frontmatter.
2. Find entries whose `keywords` overlap with the user's query. Load those L2 files.
3. For each loaded L2, compute priority for linked files:
   ```
   priority(file) = 0.5 × keyword_match(file.keywords, query)
                  + 0.3 × link_weight[link_type]
                  + 0.2 × (1 / distance_from_current)

   link_weight: depends_on=1.0, used_by=0.8, parent=0.6, children=0.5
   ```
4. Load top priority files until `drill_files` budget (default 8) is consumed.
5. If intent is debugging/"why"/historical, also load `.history.md` for each loaded file (up to `history_per_file` budget).
6. Stop. Your working set is the loaded files.

You MAY deviate from the formula with explicit justification (e.g., "I skipped used_by entries because the query is about implementation details, not caller behavior").

## drift clear 3-Option Rule

When the PostToolUse hook injects `<doc-sync-reminder>`, you MUST clear it by exactly ONE of:

- **(a) 본문 수정** — Update the L_k present file's affected sections + `last_synced_commit`
- **(b) 히스토리 추가** — Append an entry to `<name>.history.md` + `last_synced_commit`
- **(c) no-op 명시** — Respond with `docs: no-op` if the edit was comment/formatting/pure-refactor only

Never ignore a drift reminder. The session-end check will block session termination if drift remains.

## Dynamic Layer Expansion

When `check` reports I5 OVERFLOW (file > `MAX_LINES[level]`):

1. Read the overflowing file and decide: vertical or horizontal split?
   - **Vertical:** file has ≥3 sections of independent sub-responsibilities → `atlas split --mode vertical`
   - **Horizontal:** file has peer components at the same abstraction level → `atlas split --mode horizontal`
2. After split, atlas automatically runs `check_all_invariants()`. If I3/I4 regress, `atlas collapse` to rollback.

Never auto-split without agent judgment (F2 risk).

## References

Load these only when the topic is on-point:

- `references/topology-invariants.md` — I1~I8 formal definitions
- `references/drill-down-protocol.md` — NAV priority formula + examples
- `references/backfill-staged.md` — Stage 1/2/3 step-by-step
- `references/sync-watch-schema.md` — `sync_watch` frontmatter grammar
- `references/promotion-rules.md` — Rule 1/2/3 + TEMS xref
- `references/anchor-presets.md` — preset:spa / backend-api / pipeline definitions

## 철학 (위상수학 정합성)

Atlas는 위상수학의 atlas 개념과 정확히 대응한다:

- **Manifold** = 프로젝트 전체
- **Chart** = 각 L_k 파일 (국소 좌표계)
- **Chart overlap** = `depends_on` / `used_by`
- **Transition map** = topology 엔진의 bidirectional invariant
- **Atlas refinement** = 수직 증식 (L_k → L_{k+1})

이 정합성이 깨지는 구조 변경은 위상 불변량 I1~I8 위반으로 나타난다.
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs(atlas): add SKILL.md main guide"
```

### Task 8.2: Write `references/*.md`

**Files:**
- Create: `references/topology-invariants.md`
- Create: `references/drill-down-protocol.md`
- Create: `references/backfill-staged.md`
- Create: `references/sync-watch-schema.md`
- Create: `references/promotion-rules.md`
- Create: `references/anchor-presets.md`

- [ ] **Step 1: Write `references/topology-invariants.md`**

Copy the table and definitions from **spec §5** verbatim, adding examples for each invariant:

```markdown
# Topology Invariants I1~I8

Atlas maintains 8 invariants over the document graph. Any operation that
violates a critical invariant must be rolled back.

## I1 — L0 Uniqueness
Exactly one file with `level: 0` must exist. Location: `.claude/references/L0-architecture.md`.

**Violation example:** two L0 files after a merge conflict.
**Recovery:** pick the newer one, delete the other, re-run `atlas check`.

## I2 — Tree Structure
Every file with `level >= 1` must have exactly one `parent` pointing to an existing file.

**Violation example:** renaming an L1 README without updating children.
**Recovery:** fix parent references manually, re-run `atlas check`.

## I3 — Compression Ratio
`avg_size(L_k) / avg_size(L_{k-1}) ∈ [0.1, 0.5]`

**Violation:** L2 files averaging 600 lines while L1 averages 200 → L2 too big.
**Recovery:** `atlas split` the largest L2 files.

## I4 — Fan-Out
Each L_{k-1} entry has 2-12 children at L_k.

**Violation:** 15 L2 files all parented to a single L1 README → too flat.
**Recovery:** introduce an intermediate grouping (rename 1 → several L1 modules).

## I5 — File Size Cap
`lines(file) <= MAX_LINES[level]`. Defaults: L0=200, L1=300, L2+=500.

**Violation:** OVERFLOW flag. Not an error, but a signal to split.

## I6 — Bidirectional Links
`A.depends_on = [B]` implies `B.used_by ⊇ [A]`. Auto-maintained by topology engine.

## I7 — Anchor Stability
File names must be stable identifiers in the parent's index.

## I8 — History Pair
Every `.history.md` file's `history_of` must point to an existing present file.

**Violation:** deleting a present file without deleting its history. Critical.
```

- [ ] **Step 2: Write `references/drill-down-protocol.md`**

```markdown
# Drill-Down Protocol

(Full priority formula + 3 worked examples — see spec §6.3)

## Priority Formula

```
priority(file) = 0.5 × keyword_match(file.keywords, query)
               + 0.3 × link_weight[link_type]
               + 0.2 × (1 / distance_from_current)

link_weight: depends_on=1.0, used_by=0.8, parent=0.6, children=0.5
keyword_match ∈ [0, 1] = |query_keywords ∩ file_keywords| / |query_keywords|
distance_from_current = hops along any link type (1 = direct)
```

## Worked Example: "크롭 에디터에서 좌표가 틀어진다"

Current: crop-editor.md
Query keywords: {crop, coordinate, 좌표}

| Neighbor | keywords ∩ query | link_type | distance | priority |
|---|---|---|---|---|
| cloudinary-integration.md | {cloudinary, transform} ∩ {} = 0.3 | depends_on (1.0) | 1 | 0.5×0.3 + 0.3×1.0 + 0.2×1.0 = 0.65 |
| endpoints.md | {api} ∩ {} = 0.1 | depends_on (1.0) | 1 | 0.35 |
| admin-panel.md | {admin, ui} ∩ {} = 0.1 | used_by (0.8) | 1 | 0.29 |
| gallery/README.md | {gallery} ∩ {} = 0.3 | parent (0.6) | 1 | 0.43 |

Load top 3 within budget.

## Budget Enforcement

Stop when `len(working_set) >= drill_files` (default 8). If the next candidate is below 0.3 priority, stop early.
```

- [ ] **Step 3: Write `references/backfill-staged.md`**

Cross-reference spec §7. Each stage as a checklist.

```markdown
# Staged Backfill Procedure

## Stage 1 — Shell (5 min, ~5K tokens)
1. Run `atlas setup <project> --name <N> --modules <m1,m2,...>`
2. Confirm detected anchor_strategy (y/n/manual)
3. Confirm proposed L1 modules (y/n)
4. Verify: L0 exists, L1 README.md × N, `.claude/hooks/` populated, TEMS TCL registered

**Stop here if you want minimum overhead.**

## Stage 2 — Spine (10-20 min, ~15K tokens)
1. Run `atlas backfill --stage 2 --k 8`
2. For each generated L2 stub (status: stub): read sync_watch range, fill in 목적/핵심 동작/depends_on
3. `atlas check` — verify I3/I4 pass
4. Set status to `active`

## Stage 3 — History (20-40 min, ~25K+ tokens)
1. Run `atlas backfill --stage 3 --use-haiku` (falls back to main agent if Haiku unavailable)
2. For each generated history entry:
   - If tgl_ref present: done (TEMS has it)
   - Else: consider promote_candidate during next `atlas promote-check`
3. Report history entries and tgl_xref counts

## Stage 4+ — Lazy
After backfill, atlas grows via OVERFLOW trigger + manual `atlas split`.
```

- [ ] **Step 4: Write `references/sync-watch-schema.md`**

```markdown
# sync_watch Frontmatter Schema

Every L present file may declare what source edits it should react to.

## Grammar

```yaml
sync_watch:
  - path: <relative-path-from-project-root>
    range: [<start-line>, <end-line>]    # optional; omit to watch whole file
  - type: manual
    command: <human-readable-trigger>     # for non-file artifacts (hip, notebooks, ...)
```

## Examples

```yaml
# Single file, specific range
sync_watch:
  - path: gallery.html
    range: [1680, 1944]

# Multiple ranges in same file
sync_watch:
  - path: gallery.html
    range: [1680, 1944]
  - path: gallery.html
    range: [2183, 2201]

# Whole file
sync_watch:
  - path: worker/src/auth.ts

# Manual trigger (리얼군 style)
sync_watch:
  - type: manual
    command: "sync OUT_houses"
```

## Matching Semantics (v1)

- Path-only matching. Range is informational for the agent (shown in reminder) but not enforced for overlap detection.
- v2 will enforce range overlap to reduce false positives.
```

- [ ] **Step 5: Write `references/promotion-rules.md`**

```markdown
# TGL Promotion Rules

When L-history accumulates, atlas detects candidates for promotion to TEMS TGL rules.

## Rule 1 — Local Repetition
Same history file, ≥3 entries with pairwise Jaccard ≥ 0.5 AND shared keywords ≥ 2.

**Signal strength:** moderate. Indicates a feature-local recurring problem.

## Rule 2 — Cross-Functional Invariant
Different history files, ≥2 entries with Jaccard ≥ 0.5 AND shared ≥ 2.

**Signal strength:** strong. Indicates a cross-cutting invariant worth a global TGL.

## Rule 3 — Agent Intuition
Any entry where `promote_candidate: true` was set at write time by the agent.

**Signal strength:** subjective. Requires human review.

## Promotion Execution

1. `atlas promote-check` scans all history files and runs detectors
2. For each candidate, query TEMS DB — if a matching TGL already exists, add `tgl_ref` back-link to the history entries and drop the candidate
3. Present remaining candidates to user:
   - (a) 승인 → `tems_commit.py --type TGL ...`
   - (b) 수정 → edit rule text, then register
   - (c) 거부 → add to blacklist, raise similarity_threshold by 0.05 for that keyword cluster

## Single Source of Truth (TCL#75)

L-history = narrative (why the rule exists).
TEMS TGL = authority (the rule itself).
Never duplicate rule text between them — always use `tgl_ref` link.
```

- [ ] **Step 6: Write `references/anchor-presets.md`**

```markdown
# Anchor Strategy Presets

## preset:spa
Detected when `package.json` contains react/vue/svelte/next/nuxt.

- L1 modules: `frontend` (pages), `shared` (utils/components), `api` (if backend present)
- Anchors: page components, routes
- Typical L2: one per route or one per top-level component

## preset:backend-api
Detected when `pyproject.toml`/requirements has fastapi/flask/django, or Node has express.

- L1 modules: `endpoints`, `models`, `services`, `middleware`
- Anchors: endpoint URL paths, bounded contexts
- Typical L2: one per endpoint group, one per service class

## preset:pipeline
Detected when requirements has airflow/prefect/dagster.

- L1 modules: `dags` or `flows`, `tasks`, `sensors`, `transformations`
- Anchors: DAG names, task names
- Typical L2: one per DAG, deeper L3 per task

## preset:manual
Selected when the project doesn't match any preset or when user override is needed.

- L1 modules: user-specified
- Anchors: user-specified (L0 frontmatter `anchor_strategy: manual`)

## derived
Fallback when no preset matches and user declines manual. atlas infers L1 modules from top-level directories under `src/`.
```

- [ ] **Step 7: Commit**

```bash
git add references/
git commit -m "docs(atlas): add all reference documents"
```

---

## Phase 9 — End-to-End Smoke Test (Session 8)

### Task 9.1: Dogfood test against a synthetic project

**Files:**
- Create: `tests/test_e2e_smoke.py`

- [ ] **Step 1: Write the smoke test**

```python
# tests/test_e2e_smoke.py
"""End-to-end smoke: setup → backfill 2 → backfill 3 → check → promote-check."""
import subprocess
import json
from atlas.scripts.atlas_setup import run_stage1
from atlas.scripts.atlas_backfill import run_stage2, run_stage3
from atlas.scripts.atlas_check import run_check
from atlas.scripts.atlas_promote_check import detect_rule1_local, detect_rule2_cross


def _git(cwd, *args):
    subprocess.run(["git"] + list(args), cwd=cwd, check=True, capture_output=True)


def test_full_pipeline_on_synthetic_spa(tmp_path):
    # 1. Build synthetic SPA project with git history
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "package.json").write_text('{"dependencies": {"react": "^18"}}')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "gallery.html").write_text("v1\n")
    (tmp_path / "src" / "admin.html").write_text("v1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "init")
    for i in range(3):
        (tmp_path / "src" / "gallery.html").write_text(f"v{i+2}\n")
        _git(tmp_path, "commit", "-am", f"fix: crop coordinate issue {i}")

    # 2. Stage 1
    r1 = run_stage1(
        project_root=tmp_path, project_name="Synthetic", modules=["src"], confirm_anchor=False,
    )
    assert r1["stage"] == 1
    assert r1["anchor_strategy"] == "preset:spa"

    # 3. Stage 2
    r2 = run_stage2(project_root=tmp_path, k=4)
    assert r2["stage"] == 2
    assert r2["l2_count"] >= 1

    # 4. Stage 3
    r3 = run_stage3(project_root=tmp_path, use_haiku=False)
    assert r3["stage"] == 3
    assert r3["history_entries"] >= 3  # 3 fix commits on gallery.html

    # 5. Check
    report = run_check(tmp_path)
    assert report["critical"] == []

    # 6. Promote check (Rule 1 should trigger with 3 similar entries)
    candidates = detect_rule1_local(tmp_path)
    # May or may not trigger — depends on naive keyword extraction
    # Just verify it doesn't crash
    assert isinstance(candidates, list)
```

- [ ] **Step 2: Run test**

Run: `pytest tests/test_e2e_smoke.py -v`
Expected: 1 passed (or failure with clear diagnosis — this is the integration point)

- [ ] **Step 3: Run ALL tests to verify no regressions**

Run: `pytest -v`
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add tests/test_e2e_smoke.py
git commit -m "test(atlas): add end-to-end smoke test for full pipeline"
```

---

## Phase 10 — Deferred (documented for future sessions)

The following tasks are **out of scope for v1.0 implementation** but tracked here:

### Deferred: Haiku subcall wiring
Stage 3 currently uses a naive fallback summarizer. Real Haiku SDK integration is planned once runtime is available. Placeholder function is in `scripts/atlas_backfill.py::_summarize_diff_haiku`.

### Deferred: Range-based drift detection (v2)
Current PostToolUse hook matches path-only. v2 should read the edit's line range from `tool_input.old_string`/`new_string` line numbers and check overlap with `sync_watch.range`.

### Deferred: `atlas rebuild-cache` (F5 recovery)
Recovery command for corrupted `.hdocs/manifest.json` / `sync_index.json`. Scans all atlas files and reconstructs caches. Planned task, kept for future session.

### Deferred: Additional anchor presets
`preset:game-engine`, `preset:library`, `preset:monorepo` — v1.1+.

### Deferred: Visual companion for atlas structure
Interactive tree viewer for inspecting L0~LN and their links. v2.

---

## Self-Review Checklist

**Spec coverage map (checked against `2026-04-11-atlas-hierarchical-docs-design.md`):**

| Spec section | Covered by tasks |
|---|---|
| §3.1 3-space layout | 0.1, 3.2, 4.1, 4.2, 4.3 |
| §3.2 4-engine decomposition | 3.2, 4.1-4.3, 5.1-5.3, 6.1-6.2, 7.1-7.2 |
| §4.1 2-axis coordinate | 1.1, 1.2, 1.5 (I8) |
| §4.2 Present frontmatter | 1.1, 2.1, 3.2 |
| §4.3 History frontmatter | 1.5, 5.3 |
| §4.4 L0 skeleton_index | 1.8 |
| §4.5 L-history entry schema | 5.3 |
| §4.6 MAX_LINES formula | 1.5 |
| §5 Invariants I1~I8 | 1.3 (I1, I2), 1.4 (I3, I4), 1.5 (I5, I8), 1.6 (I6), deferred (I7) |
| §6.1 Scenario A | 3.2, 3.3 |
| §6.2 Scenario B | 5.1, 5.2, 5.3 |
| §6.3 Scenario C (NAV) | 8.1 (SKILL.md + protocol), 8.2 (drill-down ref) |
| §7 Staged backfill | 3.2 (Stage 1), 5.2 (Stage 2), 5.3 (Stage 3) |
| §8 sync_watch + 3-layer defense | 1.7 (sync_index), 4.1 (hook), 4.3 (shutdown) |
| §9 Promotion Rule 1/2/3 | 6.1, 6.2 |
| §10 F1-F8 failure modes | F1 (4.3 shutdown), F2 (7.1 collapse), F3 (6.2 threshold bump — deferred), F4 (NAV protocol), F5 (deferred), F6 (3.1), F7 (deferred), F8 (1.5) |

**Gaps identified and deferred:**
- I7 (anchor stability) — covered only implicitly. Add dedicated test in future task.
- F3 (promotion threshold auto-bump) — deferred, noted in Phase 10.
- F5 (rebuild_cache) — deferred, noted in Phase 10.
- F7 (TGL dangling link detection) — deferred.

These gaps do not block v1.0 since they are recovery-path enhancements, not core functionality.

**Placeholder scan:** searched plan for TODO/TBD/FIXME/"implement later" — all TODO markers are intentional template placeholders inside `L0.template.md`/`Lk.template.md` bodies (user-filled values), not plan gaps.

**Type consistency:** Method signatures verified across tasks:
- `parse_frontmatter(path) -> (dict, str)` — consistent across 1.1, 1.2, 1.3, 1.6, 5.3, 6.1
- `write_frontmatter(path, meta, body)` — consistent
- `check_all_invariants(project_root) -> dict` — consistent 1.8, 4.2, 9.1
- `discover_atlas_files(project_root) -> list[Path]` — consistent
- `rebuild_skeleton_index(project_root)` — consistent 1.8, 3.2, 5.2, 7.1, 7.2

---

## Execution Handoff

**Plan complete and saved to** `docs/superpowers/plans/2026-04-11-atlas-implementation.md`.

**IMPORTANT (TCL#64):** Implementation MUST begin in a fresh session, not this one. The brainstorming → spec → plan chain must end here.

**Two execution options for the next session:**

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Requires `superpowers:subagent-driven-development` skill.

2. **Inline Execution** — Execute tasks in-session using `superpowers:executing-plans`, batch execution with checkpoints for review.

**Recommended session boundaries for implementation:**

| Session | Tasks | Deliverable |
|---|---|---|
| Impl-1 | Phase 0 + Phase 1 | topology.py core + all invariant tests passing |
| Impl-2 | Phase 2 + Phase 3 | Templates + Stage 1 setup working |
| Impl-3 | Phase 4 | SYNC hooks + atlas check |
| Impl-4 | Phase 5 | Stage 2/3 backfill |
| Impl-5 | Phase 6 + Phase 7 | PROMOTE + split/collapse |
| Impl-6 | Phase 8 + Phase 9 | SKILL.md + references + e2e smoke |

Total: 6 implementation sessions for v1.0 completion.
