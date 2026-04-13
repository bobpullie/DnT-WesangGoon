# Atlas src-Layout Migration & Skill Packaging Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Atlas from flat `scripts/` layout to standard `src/atlas/` layout, add unified CLI and `init-skill` mechanism, making it `pip install`-able and deployable as a Claude Code skill.

**Architecture:** Standard Python src-layout (`src/atlas/`). 13 source modules move from `scripts/` to `src/atlas/`, eliminating the intermediate `scripts` package. Unified `atlas <command>` CLI via argparse subparsers. `init-skill` copies SKILL.md + references to `~/.claude/skills/atlas/`. TEMS remains an optional dependency.

**Tech Stack:** Python 3.11+, setuptools, argparse, importlib.resources, pytest

**Spec:** `docs/superpowers/specs/2026-04-12-atlas-packaging-design.md`
**Repo:** `E:/AgentInterface/skills/atlas` (HEAD: `b530cb0`, 69 tests green)

**S22 Patches Preserved:** 3-Section mandate (TGL#88), preflight hint (TGL#89), L2 keyword enrichment, Windows encoding fix (TGL#9)

---

## File Structure

### Files to Create
| Path | Responsibility |
|------|---------------|
| `src/atlas/__init__.py` | Package root, `__version__ = "1.0.0"` |
| `src/atlas/cli.py` | Unified `atlas <command>` CLI entry point |

### Files to Move (scripts/ → src/atlas/)
| From | To |
|------|-----|
| `scripts/topology.py` | `src/atlas/topology.py` |
| `scripts/render_template.py` | `src/atlas/render_template.py` |
| `scripts/anchor_detect.py` | `src/atlas/anchor_detect.py` |
| `scripts/git_analysis.py` | `src/atlas/git_analysis.py` |
| `scripts/atlas_setup.py` | `src/atlas/atlas_setup.py` |
| `scripts/atlas_backfill.py` | `src/atlas/atlas_backfill.py` |
| `scripts/atlas_check.py` | `src/atlas/atlas_check.py` |
| `scripts/atlas_split.py` | `src/atlas/atlas_split.py` |
| `scripts/atlas_collapse.py` | `src/atlas/atlas_collapse.py` |
| `scripts/atlas_promote_check.py` | `src/atlas/atlas_promote_check.py` |
| `scripts/atlas_hint.py` | `src/atlas/atlas_hint.py` |
| `scripts/tems_query.py` | `src/atlas/tems_query.py` |
| `templates/` | `src/atlas/templates/` |
| `hook_templates/` | `src/atlas/hook_templates/` |

### Files to Copy (src/atlas/ + repo root)
| Source | Also at |
|--------|---------|
| `src/atlas/SKILL.md` | `SKILL.md` (repo root, GitHub browsing) |
| `src/atlas/references/` | `references/` (repo root, GitHub browsing) |

### Files to Modify
| Path | Change |
|------|--------|
| `pyproject.toml` | Complete rewrite for src-layout |
| `tests/conftest.py` | No change needed (fixtures are generic) |
| `tests/test_*.py` (all 25 files) | `atlas.scripts.X` → `atlas.X` |

### Files to Delete
| Path | Reason |
|------|--------|
| `scripts/__init__.py` | Intermediate package eliminated |
| `scripts/` (entire directory) | Moved to src/atlas/ |

---

## Phase A: Structural Migration

Existing 69 tests serve as the safety net. No new code — just moving files and updating imports.

### Task 1: Create src/atlas/ directory structure

**Files:**
- Create: `src/atlas/__init__.py`

- [ ] **Step 1: Create directory and __init__.py**

```bash
cd E:/AgentInterface/skills/atlas
mkdir -p src/atlas
```

Write `src/atlas/__init__.py`:
```python
"""Atlas — Dynamic hierarchical documentation for agent contexts."""

__version__ = "1.0.0"
```

- [ ] **Step 2: Commit**

```bash
git add src/atlas/__init__.py
git commit -m "chore: create src/atlas/ package with __version__"
```

---

### Task 2: Move source modules from scripts/ to src/atlas/

**Files:**
- Move: all 12 `.py` modules from `scripts/` to `src/atlas/` (excluding `__init__.py`)

- [ ] **Step 1: Move all source modules**

```bash
cd E:/AgentInterface/skills/atlas
# Move each module (git mv preserves history)
git mv scripts/topology.py src/atlas/topology.py
git mv scripts/render_template.py src/atlas/render_template.py
git mv scripts/anchor_detect.py src/atlas/anchor_detect.py
git mv scripts/git_analysis.py src/atlas/git_analysis.py
git mv scripts/atlas_setup.py src/atlas/atlas_setup.py
git mv scripts/atlas_backfill.py src/atlas/atlas_backfill.py
git mv scripts/atlas_check.py src/atlas/atlas_check.py
git mv scripts/atlas_split.py src/atlas/atlas_split.py
git mv scripts/atlas_collapse.py src/atlas/atlas_collapse.py
git mv scripts/atlas_promote_check.py src/atlas/atlas_promote_check.py
git mv scripts/atlas_hint.py src/atlas/atlas_hint.py
git mv scripts/tems_query.py src/atlas/tems_query.py
```

Note: Internal relative imports (`.topology`, `.git_analysis`, etc.) remain valid because all modules are now siblings in the same `atlas` package.

- [ ] **Step 2: Remove old scripts/ directory**

```bash
rm scripts/__init__.py
rmdir scripts
# If __pycache__ lingers:
rm -rf scripts/__pycache__
rm -rf scripts
git add -A scripts/
```

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor: move scripts/*.py to src/atlas/ (eliminate intermediate package)"
```

---

### Task 3: Move data files into src/atlas/

**Files:**
- Move: `templates/` → `src/atlas/templates/`
- Move: `hook_templates/` → `src/atlas/hook_templates/`
- Copy: `SKILL.md` → `src/atlas/SKILL.md` (keep root copy)
- Copy: `references/` → `src/atlas/references/` (keep root copy)

- [ ] **Step 1: Move templates and hook_templates**

```bash
cd E:/AgentInterface/skills/atlas
git mv templates src/atlas/templates
git mv hook_templates src/atlas/hook_templates
```

- [ ] **Step 2: Copy SKILL.md and references into package**

```bash
cp SKILL.md src/atlas/SKILL.md
cp -r references src/atlas/references
git add src/atlas/SKILL.md src/atlas/references/
```

Root copies of `SKILL.md` and `references/` stay for GitHub browsing.

- [ ] **Step 3: Commit**

```bash
git commit -m "refactor: move data files into src/atlas/ package"
```

---

### Task 4: Rewrite pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Replace pyproject.toml entirely**

Write `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "atlas-docs"
version = "1.0.0"
description = "Dynamic hierarchical documentation for agent contexts"
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0",
    "python-frontmatter>=1.0",
]

[project.optional-dependencies]
tems = ["tems @ git+https://github.com/bobpullie/TEMS"]
dev = ["pytest>=7.0", "pytest-mock>=3.10"]

[project.scripts]
atlas = "atlas.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
atlas = [
    "templates/*.md",
    "hook_templates/*.tmpl",
    "SKILL.md",
    "references/*.md",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Key changes from old pyproject.toml:
- `name`: `atlas` → `atlas-docs` (PyPI conflict avoidance)
- `build-backend`: added (was missing)
- `[project.scripts]`: 7 individual entry points → 1 unified `atlas` CLI
- `pythonpath`: `[".."]` → `["src"]`
- `packages.find.where`: `["src"]` added
- `package-data`: added for templates, hooks, SKILL.md, references
- Removed `atlas-rebuild-cache` entry point (module doesn't exist)

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: rewrite pyproject.toml for src-layout and unified CLI"
```

---

### Task 5: Update all test imports

**Files:**
- Modify: all `tests/test_*.py` files (25 files)

The migration is mechanical: `atlas.scripts.X` → `atlas.X` in every import.

- [ ] **Step 1: Bulk replace imports across all test files**

Run a single sed command (or use editor) to replace across all test files:

```bash
cd E:/AgentInterface/skills/atlas
# Replace all occurrences of 'atlas.scripts.' with 'atlas.' in test files
find tests -name "test_*.py" -exec sed -i 's/atlas\.scripts\./atlas./g' {} +
```

Verify a few key files after the replacement:

`tests/test_e2e_smoke.py` imports should read:
```python
from atlas.atlas_setup import run_stage1
from atlas.atlas_backfill import run_stage2, run_stage3
from atlas.atlas_check import run_check
from atlas.atlas_promote_check import detect_rule1_local, detect_rule2_cross
```

`tests/test_atlas_hint.py` imports should read:
```python
from atlas.atlas_hint import (
    _load_skeleton_index,
    _keyword_overlap,
    atlas_hint,
    format_atlas_hint,
)
```

`tests/test_topology_frontmatter.py` should read:
```python
from atlas.topology import parse_frontmatter, write_frontmatter
```

- [ ] **Step 2: Commit**

```bash
git add tests/
git commit -m "refactor: update test imports atlas.scripts.X -> atlas.X"
```

---

### Task 6: Verify all existing tests pass

- [ ] **Step 1: Install in editable mode**

```bash
cd E:/AgentInterface/skills/atlas
pip install -e ".[dev]"
```

Expected: succeeds, `import atlas` works.

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: 69 tests PASSED. If any fail, diagnose — likely an import path missed in Task 5.

- [ ] **Step 3: Verify import from Python**

```bash
python -c "from atlas.topology import parse_frontmatter; print('OK')"
python -c "from atlas.atlas_hint import atlas_hint; print('OK')"
python -c "from atlas import __version__; print(__version__)"
```

Expected: all print OK / 1.0.0.

- [ ] **Step 4: Commit if any fixes were needed**

```bash
# Only if Task 5 missed something
git add -A
git commit -m "fix: correct remaining import paths after migration"
```

---

## Phase B: New Features (TDD)

### Task 7: Unified CLI — test first

**Files:**
- Create: `tests/test_cli.py`
- Create: `src/atlas/cli.py`

- [ ] **Step 1: Write failing test for CLI**

Write `tests/test_cli.py`:
```python
"""Tests for unified atlas CLI entry point."""
import subprocess
import sys


def test_atlas_help_shows_subcommands():
    """atlas --help should list all subcommands."""
    result = subprocess.run(
        [sys.executable, "-m", "atlas.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    for cmd in ["setup", "backfill", "check", "split", "collapse", "promote-check", "init-skill"]:
        assert cmd in result.stdout, f"Missing subcommand: {cmd}"


def test_atlas_setup_requires_root(tmp_path):
    """atlas setup without --name should fail with clear error."""
    result = subprocess.run(
        [sys.executable, "-m", "atlas.cli", "setup", str(tmp_path)],
        capture_output=True, text=True,
    )
    # argparse should complain about missing --name
    assert result.returncode != 0


def test_atlas_check_runs(tmp_path):
    """atlas check on empty dir should return report (no crash)."""
    result = subprocess.run(
        [sys.executable, "-m", "atlas.cli", "check", str(tmp_path)],
        capture_output=True, text=True,
    )
    # Should not crash — either prints report or handles gracefully
    assert result.returncode == 0


def test_atlas_init_skill_creates_files(tmp_path):
    """atlas init-skill --target <path> should copy SKILL.md + references."""
    target = tmp_path / "skill_out"
    result = subprocess.run(
        [sys.executable, "-m", "atlas.cli", "init-skill", "--target", str(target)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert (target / "SKILL.md").exists()
    assert (target / "references").is_dir()
    assert (target / "references" / "topology-invariants.md").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_cli.py -v
```

Expected: FAIL — `atlas.cli` module does not exist yet.

- [ ] **Step 3: Write cli.py implementation**

Write `src/atlas/cli.py`:
```python
"""Unified atlas CLI — single entry point for all atlas commands."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def cmd_setup(args):
    from .atlas_setup import run_stage1

    result = run_stage1(
        project_root=Path(args.root),
        project_name=args.name,
        modules=args.modules.split(","),
        confirm_anchor=not args.no_confirm,
    )
    print(json.dumps(result, indent=2, default=str))


def cmd_backfill(args):
    from .atlas_backfill import run_stage2, run_stage3

    root = Path(args.root)
    if args.stage == 2:
        result = run_stage2(root, k=args.k)
    elif args.stage == 3:
        result = run_stage3(root, use_haiku=args.use_haiku)
    else:
        print(f"Unknown stage: {args.stage}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2, default=str))


def cmd_check(args):
    from .atlas_check import run_check

    report = run_check(Path(args.root))
    print(json.dumps(report, indent=2, default=str))


def cmd_split(args):
    from .atlas_split import split_vertical

    split_vertical(
        target=Path(args.target),
        project_root=Path(args.project_root) if args.project_root else None,
    )
    print("Split complete.")


def cmd_collapse(args):
    from .atlas_collapse import collapse_level

    collapse_level(
        target=Path(args.target),
        project_root=Path(args.project_root) if args.project_root else None,
    )
    print("Collapse complete.")


def cmd_promote_check(args):
    from .atlas_promote_check import detect_rule1_local, detect_rule2_cross

    root = Path(args.root)
    r1 = detect_rule1_local(root)
    r2 = detect_rule2_cross(root)
    result = {"rule1_candidates": r1, "rule2_candidates": r2}
    print(json.dumps(result, indent=2, default=str))


def cmd_init_skill(args):
    import importlib.resources
    import shutil

    target = Path(args.target).expanduser()
    target.mkdir(parents=True, exist_ok=True)

    # Copy SKILL.md
    skill_src = importlib.resources.files("atlas") / "SKILL.md"
    with importlib.resources.as_file(skill_src) as src_path:
        shutil.copy2(src_path, target / "SKILL.md")

    # Copy references/
    ref_src = importlib.resources.files("atlas") / "references"
    with importlib.resources.as_file(ref_src) as ref_path:
        if ref_path.is_dir():
            if (target / "references").exists():
                shutil.rmtree(target / "references")
            shutil.copytree(ref_path, target / "references")

    print(f"Atlas skill installed at {target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas",
        description="Dynamic hierarchical documentation for agent contexts",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- setup ---
    p_setup = sub.add_parser("setup", help="Initialize atlas for a project")
    p_setup.add_argument("root", help="Project root directory")
    p_setup.add_argument("--name", required=True, help="Project name")
    p_setup.add_argument("--modules", required=True, help="Comma-separated module list")
    p_setup.add_argument("--no-confirm", action="store_true", help="Skip anchor confirmation")
    p_setup.set_defaults(func=cmd_setup)

    # --- backfill ---
    p_bf = sub.add_parser("backfill", help="Run backfill stage 2 or 3")
    p_bf.add_argument("root", help="Project root directory")
    p_bf.add_argument("--stage", type=int, required=True, choices=[2, 3], help="Stage number")
    p_bf.add_argument("--k", type=int, default=8, help="Top-K files for stage 2")
    p_bf.add_argument("--use-haiku", action="store_true", help="Use Haiku for stage 3")
    p_bf.set_defaults(func=cmd_backfill)

    # --- check ---
    p_check = sub.add_parser("check", help="Run all invariant checks")
    p_check.add_argument("root", nargs="?", default=".", help="Project root directory")
    p_check.set_defaults(func=cmd_check)

    # --- split ---
    p_split = sub.add_parser("split", help="Split an L1 document vertically")
    p_split.add_argument("target", help="Target L1 file to split")
    p_split.add_argument("--project-root", default=None, help="Project root directory")
    p_split.set_defaults(func=cmd_split)

    # --- collapse ---
    p_collapse = sub.add_parser("collapse", help="Collapse a level (inverse of split)")
    p_collapse.add_argument("target", help="Target file to collapse")
    p_collapse.add_argument("--project-root", default=None, help="Project root directory")
    p_collapse.set_defaults(func=cmd_collapse)

    # --- promote-check ---
    p_promo = sub.add_parser("promote-check", help="Check for promotion candidates")
    p_promo.add_argument("root", nargs="?", default=".", help="Project root directory")
    p_promo.add_argument("--threshold", type=float, default=0.5, help="Similarity threshold")
    p_promo.set_defaults(func=cmd_promote_check)

    # --- init-skill ---
    p_init = sub.add_parser("init-skill", help="Install SKILL.md + references for Claude Code")
    p_init.add_argument("--target", default="~/.claude/skills/atlas", help="Target directory")
    p_init.set_defaults(func=cmd_init_skill)

    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Run full test suite to confirm no regressions**

```bash
pytest tests/ -v
```

Expected: 73 tests PASSED (69 existing + 4 new).

- [ ] **Step 6: Commit**

```bash
git add src/atlas/cli.py tests/test_cli.py
git commit -m "feat: add unified atlas CLI with subcommands"
```

---

### Task 8: Verify CLI via entry point

- [ ] **Step 1: Reinstall package to register entry point**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 2: Test entry point**

```bash
atlas --help
atlas check .
```

Expected: `--help` shows all subcommands. `check .` runs without crash.

- [ ] **Step 3: Test init-skill end-to-end**

```bash
# Use a temp directory to avoid polluting real skill dir
atlas init-skill --target /tmp/atlas-skill-test
ls /tmp/atlas-skill-test/
# Expected: SKILL.md, references/ with 6 .md files
```

---

## Phase C: Final Cleanup & Verification

### Task 9: Clean up stale files and verify final state

- [ ] **Step 1: Verify no stale scripts/ references remain**

```bash
cd E:/AgentInterface/skills/atlas
# Should return nothing:
grep -r "atlas\.scripts\." tests/ src/
```

Expected: no matches.

- [ ] **Step 2: Verify package structure**

```bash
python -c "
import atlas
print('version:', atlas.__version__)
print('package:', atlas.__file__)
"
```

Expected: version `1.0.0`, file path inside `src/atlas/`.

- [ ] **Step 3: Verify importlib.resources works for package data**

```bash
python -c "
import importlib.resources
skill = importlib.resources.files('atlas') / 'SKILL.md'
print('SKILL.md:', skill)
refs = importlib.resources.files('atlas') / 'references'
print('references:', refs)
"
```

Expected: both paths resolve correctly.

- [ ] **Step 4: Final full test run**

```bash
pytest tests/ -v --tb=short
```

Expected: 73 tests PASSED (69 migrated + 4 new CLI tests).

- [ ] **Step 5: Commit any remaining fixes**

```bash
git add -A
git commit -m "chore: final cleanup after src-layout migration"
```

---

## Post-Migration Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| `import atlas` | `python -c "import atlas"` | No error |
| `atlas.__version__` | `python -c "from atlas import __version__; print(__version__)"` | `1.0.0` |
| `atlas --help` | `atlas --help` | Lists 7 subcommands |
| `pip install -e .` | `pip install -e ".[dev]"` | Success |
| All tests | `pytest tests/ -v` | 73 PASSED |
| No stale imports | `grep -r "atlas\.scripts\." tests/ src/` | No matches |
| SKILL.md in package | `python -c "import importlib.resources; print(importlib.resources.files('atlas') / 'SKILL.md')"` | Valid path |
| init-skill | `atlas init-skill --target /tmp/test` | Creates SKILL.md + references/ |
| S22 features preserved | `python -c "from atlas.atlas_hint import atlas_hint; print('hint OK')"` | OK |
| Windows encoding | `python -c "from atlas.git_analysis import top_k_modified_files; print('git OK')"` | OK |

---

## Risk Notes

1. **`importlib.resources` on Windows:** `as_file()` context manager is needed for reliable path access. The `cli.py` implementation uses this correctly.
2. **TEMS optional dependency:** Not tested in this migration (TEMS package not yet pip-installable). Deferred to TEMS-skill phase.
3. **Root SKILL.md + src/atlas/SKILL.md sync:** Two copies exist. The root copy is the source of truth for editing; copy into src/atlas/ before release. Consider a Makefile target or pre-commit hook (out of scope).
4. **TGL#84 (frontmatter parser):** Empty frontmatter edge case already handled in topology.py. No action needed in migration, but verify test_topology_frontmatter.py passes.
