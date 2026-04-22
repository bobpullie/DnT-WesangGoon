# 세션 산출물 자동 인덱싱 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 위상군 세션 산출물(`docs/wiki/**` + `docs/session_archive/**` + `handover_doc/**` + `qmd_drive/recaps/**`)에 frontmatter 를 자동 주입하고, Obsidian Dataview 쿼리로 "최근 작성 10 / 최근 수정 10" 타임라인을 `docs/session_artifacts.md` 에 노출한 뒤 기존 `docs/wiki/index.md` 에 embed.

**Architecture:** 직교하는 2 메커니즘 — (1) `scripts/normalize_session_frontmatter.py` 가 3 폴더를 idempotent 하게 스캔하여 누락 frontmatter 주입, (2) `docs/session_artifacts.md` 의 Dataview 쿼리 2개가 4 폴더 전체를 실시간 인덱싱. 세션 종료 lifecycle step 5.5 로 자동화.

**Tech Stack:** Python 3 (argparse · pathlib · re · PyYAML) · pytest · Obsidian Dataview · YAML frontmatter.

**Spec:** `docs/superpowers/specs/2026-04-22-session-artifacts-auto-indexing-design.md`

---

## File Structure

- **Create:**
  - `scripts/normalize_session_frontmatter.py` — frontmatter 주입 스크립트 (단일 파일, ~250 LOC 예상)
  - `tests/__init__.py` — 빈 파일 (pytest 패키지)
  - `tests/test_normalize_session_frontmatter.py` — 단위 테스트
  - `docs/session_artifacts.md` — Dataview 쿼리 인덱스 페이지
  - `pytest.ini` — pytest 설정 (기존 없음)

- **Modify:**
  - `docs/wiki/index.md` — `## 세션 산출물 (통합)` 섹션 신설, `![[../session_artifacts]]` embed
  - `wiki.config.json` — `obsidian.cssclasses` 에 `raw`/`handover`/`recap`/`timeline` 추가
  - `.obsidian/snippets/twk.css` — 4 신규 cssclass 최소 스타일
  - `.claude/rules/session-lifecycle.md` — step 5.5 추가

- **Auto-modified (script apply):**
  - `docs/session_archive/*.md` (6개) · `handover_doc/*.md` (다수) · `qmd_drive/recaps/*.md` (다수) — 누락 frontmatter 보충

---

### Task 1: pytest 스캐폴딩

**Files:**
- Create: `tests/__init__.py`
- Create: `pytest.ini`

- [ ] **Step 1: 빈 `tests/__init__.py` 생성**

빈 파일 1개. 내용 없음.

- [ ] **Step 2: `pytest.ini` 생성**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

- [ ] **Step 3: pytest 기동 확인**

Run: `python -m pytest --collect-only`
Expected: 0 테스트 수집, 에러 없음.

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py pytest.ini
git commit -m "test: add pytest scaffolding for normalize_session_frontmatter"
```

---

### Task 2: frontmatter 파싱/직렬화 (read 방향)

**Files:**
- Create: `scripts/normalize_session_frontmatter.py` (초기 스켈레톤)
- Create: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 작성 — frontmatter 없음**

`tests/test_normalize_session_frontmatter.py` 에 추가:

```python
import pytest
from scripts.normalize_session_frontmatter import parse_frontmatter


def test_parse_frontmatter_empty_content():
    meta, body = parse_frontmatter("")
    assert meta == {}
    assert body == ""


def test_parse_frontmatter_no_frontmatter_block():
    content = "# 제목\n본문\n"
    meta, body = parse_frontmatter(content)
    assert meta == {}
    assert body == content


def test_parse_frontmatter_with_block():
    content = "---\ndate: 2026-04-22\ntags: [a, b]\n---\n# 제목\n"
    meta, body = parse_frontmatter(content)
    assert meta == {"date": "2026-04-22", "tags": ["a", "b"]}
    assert body == "# 제목\n"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: `ModuleNotFoundError: No module named 'scripts.normalize_session_frontmatter'`

- [ ] **Step 3: `scripts/normalize_session_frontmatter.py` 초기 구현**

```python
"""세션 산출물 frontmatter 자동 정규화.

3 폴더(docs/session_archive · handover_doc · qmd_drive/recaps)의 .md 파일에
누락된 frontmatter 필드(date · type · cssclass · tags · session)를 idempotent
하게 주입한다. docs/wiki/** 는 검증만.

위상군 로컬 전용 (TCL #93). 세션 종료 lifecycle step 5.5 에서 호출.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """markdown 문자열을 (frontmatter dict, body) 로 분리.

    frontmatter 가 없으면 ({}, content) 반환.
    """
    if not content:
        return {}, ""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    meta = yaml.safe_load(m.group(1)) or {}
    body = content[m.end():]
    return meta, body
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: parse_frontmatter — YAML frontmatter 분리 파서"
```

---

### Task 3: frontmatter 직렬화

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import serialize_frontmatter


def test_serialize_frontmatter_empty_meta_keeps_body():
    result = serialize_frontmatter({}, "# 제목\n")
    assert result == "# 제목\n"


def test_serialize_frontmatter_scalar_fields():
    meta = {"date": "2026-04-22", "type": "raw"}
    result = serialize_frontmatter(meta, "# 제목\n")
    assert result.startswith("---\n")
    assert "date: 2026-04-22" in result
    assert "type: raw" in result
    assert result.endswith("---\n\n# 제목\n")


def test_serialize_frontmatter_flow_style_tags():
    """tags 는 flow style ([a, b, c]) 로 출력 (wiki.config.json 규약)."""
    meta = {"tags": ["session", "raw"]}
    result = serialize_frontmatter(meta, "")
    assert "tags: [session, raw]" in result
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py::test_serialize_frontmatter_scalar_fields -v`
Expected: `ImportError` (serialize_frontmatter 미정의)

- [ ] **Step 3: 구현 추가**

`scripts/normalize_session_frontmatter.py` 에 추가:

```python
FLOW_STYLE_KEYS = {"tags", "aliases"}


def serialize_frontmatter(meta: dict, body: str) -> str:
    """(meta, body) 를 markdown 문자열로 합성.

    meta 가 비면 body 만 반환. tags/aliases 는 flow style (인라인) 로 출력.
    """
    if not meta:
        return body
    lines = []
    for key, value in meta.items():
        if key in FLOW_STYLE_KEYS and isinstance(value, list):
            joined = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{joined}]")
        elif isinstance(value, list):
            joined = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{joined}]")
        else:
            # yaml.safe_dump 으로 escape 처리 후 trailing newline 제거
            dumped = yaml.safe_dump({key: value}, allow_unicode=True, default_flow_style=False)
            lines.append(dumped.rstrip())
    fm = "---\n" + "\n".join(lines) + "\n---\n"
    if body and not body.startswith("\n"):
        fm += "\n"
    return fm + body
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 6 passed.

- [ ] **Step 5: round-trip 테스트 추가**

```python
def test_parse_serialize_roundtrip():
    original_meta = {"date": "2026-04-22", "type": "recap", "tags": ["a", "b"], "session": "S41"}
    serialized = serialize_frontmatter(original_meta, "# body\n")
    parsed_meta, parsed_body = parse_frontmatter(serialized)
    assert parsed_meta == original_meta
    assert parsed_body == "# body\n"
```

Run: `python -m pytest tests/test_normalize_session_frontmatter.py::test_parse_serialize_roundtrip -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: serialize_frontmatter — flow-style tags 지원"
```

---

### Task 4: 파일명에서 date 추출

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import extract_date_from_filename


def test_extract_date_yyyymmdd_format():
    """docs/session_archive/20260420_session1_raw.md → 2026-04-20"""
    assert extract_date_from_filename("20260420_session1_raw.md") == "2026-04-20"


def test_extract_date_dashed_format():
    """handover_doc/2026-04-21_session40.md → 2026-04-21"""
    assert extract_date_from_filename("2026-04-21_session40.md") == "2026-04-21"


def test_extract_date_no_date_returns_none():
    assert extract_date_from_filename("irregular_name.md") is None


def test_extract_date_ignores_year_in_middle():
    """파일명 중간의 숫자열이 년도로 오인되면 안 됨."""
    assert extract_date_from_filename("foo_123456_bar.md") is None
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py::test_extract_date_yyyymmdd_format -v`
Expected: `ImportError`.

- [ ] **Step 3: 구현 추가**

```python
# 파일명 맨 앞에서만 매칭 (중간 숫자 오인 방지)
DATE_PATTERNS = [
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})"),   # 2026-04-21
    re.compile(r"^(\d{4})(\d{2})(\d{2})"),     # 20260420
]


def extract_date_from_filename(name: str) -> str | None:
    """파일명 맨 앞에서 YYYY-MM-DD 또는 YYYYMMDD 를 추출.

    성공 시 'YYYY-MM-DD' 문자열, 실패 시 None.
    """
    for pat in DATE_PATTERNS:
        m = pat.match(name)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            return f"{y}-{mo}-{d}"
    return None
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: extract_date_from_filename — YYYYMMDD/YYYY-MM-DD 파싱"
```

---

### Task 5: 파일명에서 session 번호 추출

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import extract_session_from_filename


def test_extract_session_word_format():
    assert extract_session_from_filename("20260420_session1_raw.md") == "S1"


def test_extract_session_multi_digit():
    assert extract_session_from_filename("2026-04-21_session40.md") == "S40"


def test_extract_session_not_present():
    assert extract_session_from_filename("2026-04-22_note.md") is None


def test_extract_session_sN_shortform():
    """sN 형식도 허용 (혹시 미래에 사용될 경우)."""
    assert extract_session_from_filename("20260421_s3_raw.md") == "S3"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -k extract_session -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
SESSION_PATTERN = re.compile(r"[_-]s(?:ession)?(\d+)", re.IGNORECASE)


def extract_session_from_filename(name: str) -> str | None:
    """파일명에서 'session{N}' 또는 's{N}' 패턴으로 session 번호 추출.

    성공 시 'S{N}', 실패 시 None.
    """
    m = SESSION_PATTERN.search(name)
    if m:
        return f"S{m.group(1)}"
    return None
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: extract_session_from_filename — S{N} 추출"
```

---

### Task 6: mtime fallback

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import mtime_date
from pathlib import Path
import os
import time


def test_mtime_date_format(tmp_path: Path):
    """file.mtime 을 YYYY-MM-DD 로 변환."""
    p = tmp_path / "test.md"
    p.write_text("x", encoding="utf-8")
    # 특정 시각으로 mtime 고정: 2026-04-01 00:00:00
    fixed = time.mktime(time.strptime("2026-04-01", "%Y-%m-%d"))
    os.utime(p, (fixed, fixed))
    assert mtime_date(p) == "2026-04-01"
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py::test_mtime_date_format -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
import datetime


def mtime_date(path: Path) -> str:
    """파일 mtime 의 날짜 부분을 YYYY-MM-DD 로 반환."""
    ts = path.stat().st_mtime
    return datetime.date.fromtimestamp(ts).strftime("%Y-%m-%d")
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: mtime_date — filesystem mtime fallback"
```

---

### Task 7: frontmatter 병합 — 스칼라 skip + 배열 union

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import merge_frontmatter


def test_merge_scalar_injects_when_missing():
    existing = {}
    template = {"date": "2026-04-22", "type": "recap"}
    result, changed = merge_frontmatter(existing, template)
    assert result == {"date": "2026-04-22", "type": "recap"}
    assert changed is True


def test_merge_scalar_preserves_when_present():
    """기존 스칼라 값은 덮어쓰지 않는다."""
    existing = {"date": "2026-04-15", "type": "recap"}
    template = {"date": "2026-04-22", "type": "handover"}
    result, changed = merge_frontmatter(existing, template)
    assert result == {"date": "2026-04-15", "type": "recap"}
    assert changed is False


def test_merge_tags_union_append_missing():
    existing = {"tags": ["custom"]}
    template = {"tags": ["session", "recap"]}
    result, changed = merge_frontmatter(existing, template)
    assert result["tags"] == ["custom", "session", "recap"]
    assert changed is True


def test_merge_tags_union_no_change_when_superset():
    existing = {"tags": ["custom", "session", "recap", "extra"]}
    template = {"tags": ["session", "recap"]}
    result, changed = merge_frontmatter(existing, template)
    assert result["tags"] == ["custom", "session", "recap", "extra"]
    assert changed is False


def test_merge_tags_created_when_missing():
    existing = {}
    template = {"tags": ["session", "handover"]}
    result, changed = merge_frontmatter(existing, template)
    assert result["tags"] == ["session", "handover"]
    assert changed is True


def test_merge_mixed_scalar_and_array():
    existing = {"date": "2026-04-15", "tags": ["custom"]}
    template = {"date": "2026-04-22", "type": "recap", "tags": ["session", "recap"]}
    result, changed = merge_frontmatter(existing, template)
    assert result == {
        "date": "2026-04-15",
        "type": "recap",
        "tags": ["custom", "session", "recap"],
    }
    assert changed is True
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -k merge_ -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
ARRAY_KEYS = {"tags", "aliases"}


def merge_frontmatter(existing: dict, template: dict) -> tuple[dict, bool]:
    """template 값을 existing 에 병합.

    규칙:
      - 스칼라: 기존 값 있으면 skip, 없을 때만 주입
      - 배열(tags/aliases): union 병합. 기존 순서 보존 + 누락분 append.

    Returns:
        (merged_dict, changed_flag)
    """
    result = dict(existing)
    changed = False
    for key, new_value in template.items():
        if key in ARRAY_KEYS:
            current = result.get(key, [])
            if not isinstance(current, list):
                current = [current]
            additions = [v for v in new_value if v not in current]
            if additions:
                result[key] = current + additions
                changed = True
            elif key not in result:
                result[key] = current
                changed = True
        else:
            if key not in result:
                result[key] = new_value
                changed = True
    return result, changed
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 21 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: merge_frontmatter — 스칼라 skip · 배열 union"
```

---

### Task 8: 폴더 → 템플릿 매핑 + build_template

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import build_template, FOLDER_CONFIG


def test_build_template_session_archive():
    tpl = build_template("docs/session_archive", "20260420_session1_raw.md", None)
    assert tpl["date"] == "2026-04-20"
    assert tpl["type"] == "raw"
    assert tpl["cssclass"] == "twk-raw"
    assert tpl["session"] == "S1"
    assert set(tpl["tags"]) == {"session", "raw", "L2"}


def test_build_template_handover():
    tpl = build_template("handover_doc", "2026-04-21_session40.md", None)
    assert tpl["date"] == "2026-04-21"
    assert tpl["type"] == "handover"
    assert tpl["cssclass"] == "twk-handover"
    assert tpl["session"] == "S40"
    assert set(tpl["tags"]) == {"session", "handover"}


def test_build_template_recap():
    tpl = build_template("qmd_drive/recaps", "2026-04-22_session41.md", None)
    assert tpl["type"] == "recap"
    assert tpl["cssclass"] == "twk-recap"
    assert tpl["session"] == "S41"


def test_build_template_filename_parse_fails_uses_mtime(tmp_path: Path):
    """파일명 파싱 실패 시 date 는 mtime fallback, session 은 생략."""
    p = tmp_path / "irregular_name.md"
    p.write_text("x", encoding="utf-8")
    fixed = time.mktime(time.strptime("2026-01-15", "%Y-%m-%d"))
    os.utime(p, (fixed, fixed))
    tpl = build_template("handover_doc", "irregular_name.md", p)
    assert tpl["date"] == "2026-01-15"
    assert "session" not in tpl
    assert tpl["type"] == "handover"


def test_build_template_unknown_folder_raises():
    with pytest.raises(KeyError):
        build_template("unknown/folder", "foo.md", None)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -k build_template -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
FOLDER_CONFIG = {
    "docs/session_archive": {
        "type": "raw",
        "cssclass": "twk-raw",
        "tags": ["session", "raw", "L2"],
    },
    "handover_doc": {
        "type": "handover",
        "cssclass": "twk-handover",
        "tags": ["session", "handover"],
    },
    "qmd_drive/recaps": {
        "type": "recap",
        "cssclass": "twk-recap",
        "tags": ["session", "recap"],
    },
}


def build_template(folder_key: str, filename: str, path: Path | None) -> dict:
    """폴더 config + 파일명 파싱 결과로 template dict 구성.

    Args:
        folder_key: FOLDER_CONFIG 의 키 (e.g. "handover_doc")
        filename: 파일 이름 (basename)
        path: mtime fallback 용 Path (없으면 mtime fallback 불가 — date 생략)

    Raises:
        KeyError: folder_key 가 FOLDER_CONFIG 에 없을 때
    """
    if folder_key not in FOLDER_CONFIG:
        raise KeyError(f"unknown folder: {folder_key}")
    base = FOLDER_CONFIG[folder_key]
    tpl: dict = {}
    date = extract_date_from_filename(filename)
    if date is None and path is not None:
        date = mtime_date(path)
    if date is not None:
        tpl["date"] = date
    tpl["type"] = base["type"]
    tpl["cssclass"] = base["cssclass"]
    tpl["tags"] = list(base["tags"])
    session = extract_session_from_filename(filename)
    if session:
        tpl["session"] = session
    return tpl
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 26 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: build_template — 폴더 config + 파일명 파싱 결합"
```

---

### Task 9: process_file — end-to-end + idempotency

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import process_file


def test_process_file_injects_into_missing_frontmatter(tmp_path: Path):
    p = tmp_path / "2026-04-21_session40.md"
    p.write_text("# 제목\n본문\n", encoding="utf-8")
    action = process_file(p, "handover_doc", dry_run=False)
    assert action in {"added", "updated"}
    content = p.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "date: 2026-04-21" in content
    assert "type: handover" in content
    assert "# 제목" in content  # 본문 보존


def test_process_file_preserves_existing_scalar(tmp_path: Path):
    p = tmp_path / "2026-04-21_session40.md"
    p.write_text("---\ndate: 2026-04-01\n---\n# 제목\n", encoding="utf-8")
    process_file(p, "handover_doc", dry_run=False)
    content = p.read_text(encoding="utf-8")
    assert "date: 2026-04-01" in content  # 기존 값 보존
    assert "date: 2026-04-21" not in content


def test_process_file_idempotent(tmp_path: Path):
    """2회 apply 결과 동일."""
    p = tmp_path / "2026-04-21_session40.md"
    p.write_text("# 제목\n", encoding="utf-8")
    process_file(p, "handover_doc", dry_run=False)
    first = p.read_text(encoding="utf-8")
    process_file(p, "handover_doc", dry_run=False)
    second = p.read_text(encoding="utf-8")
    assert first == second


def test_process_file_dry_run_no_write(tmp_path: Path):
    p = tmp_path / "2026-04-21_session40.md"
    original = "# 제목\n"
    p.write_text(original, encoding="utf-8")
    process_file(p, "handover_doc", dry_run=True)
    assert p.read_text(encoding="utf-8") == original


def test_process_file_tags_union(tmp_path: Path):
    p = tmp_path / "2026-04-21_session40.md"
    p.write_text("---\ntags: [custom]\n---\n", encoding="utf-8")
    process_file(p, "handover_doc", dry_run=False)
    content = p.read_text(encoding="utf-8")
    assert "tags: [custom, session, handover]" in content
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -k process_file -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
def process_file(path: Path, folder_key: str, dry_run: bool) -> str:
    """단일 파일에 frontmatter 병합 적용.

    Returns:
        "kept" | "updated" | "added" | "dry-run"
    """
    content = path.read_text(encoding="utf-8")
    existing_meta, body = parse_frontmatter(content)
    template = build_template(folder_key, path.name, path)
    merged_meta, changed = merge_frontmatter(existing_meta, template)

    if not changed:
        return "kept"
    if dry_run:
        return "dry-run"

    new_content = serialize_frontmatter(merged_meta, body)
    path.write_text(new_content, encoding="utf-8")
    return "added" if not existing_meta else "updated"
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 31 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: process_file — frontmatter 주입 + idempotent 보장"
```

---

### Task 10: docs/wiki 검증 모드

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`
- Modify: `tests/test_normalize_session_frontmatter.py`

- [ ] **Step 1: 실패 테스트 추가**

```python
from scripts.normalize_session_frontmatter import validate_wiki_file


def test_validate_wiki_file_passes(tmp_path: Path):
    p = tmp_path / "concept.md"
    p.write_text("---\ndate: 2026-04-20\nstatus: Active\n---\n# X\n", encoding="utf-8")
    warnings = validate_wiki_file(p)
    assert warnings == []


def test_validate_wiki_file_missing_date(tmp_path: Path):
    p = tmp_path / "concept.md"
    p.write_text("---\nstatus: Active\n---\n", encoding="utf-8")
    warnings = validate_wiki_file(p)
    assert any("date" in w for w in warnings)


def test_validate_wiki_file_missing_status(tmp_path: Path):
    p = tmp_path / "concept.md"
    p.write_text("---\ndate: 2026-04-20\n---\n", encoding="utf-8")
    warnings = validate_wiki_file(p)
    assert any("status" in w for w in warnings)


def test_validate_wiki_file_no_frontmatter(tmp_path: Path):
    p = tmp_path / "concept.md"
    p.write_text("# X\n", encoding="utf-8")
    warnings = validate_wiki_file(p)
    assert len(warnings) >= 2  # date, status 둘 다 누락
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -k validate_wiki -v`
Expected: ImportError.

- [ ] **Step 3: 구현 추가**

```python
WIKI_REQUIRED_FIELDS = ["date", "status"]


def validate_wiki_file(path: Path) -> list[str]:
    """docs/wiki/** 파일의 필수 필드 검증. 수정 없음.

    Returns:
        누락 필드별 warning 메시지 리스트. 이상 없으면 [].
    """
    content = path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)
    warnings = []
    for field in WIKI_REQUIRED_FIELDS:
        if field not in meta:
            warnings.append(f"{path.name}: '{field}' 누락")
    return warnings
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 35 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py tests/test_normalize_session_frontmatter.py
git commit -m "feat: validate_wiki_file — docs/wiki 필수 필드 검증"
```

---

### Task 11: CLI 진입점 (main + argparse)

**Files:**
- Modify: `scripts/normalize_session_frontmatter.py`

- [ ] **Step 1: main 구현**

`scripts/normalize_session_frontmatter.py` 끝에 추가:

```python
import argparse
import sys

# 폴더 키 → 실제 디렉토리 경로 매핑 (상대 경로, project root 기준)
FOLDER_PATHS = {
    "docs/session_archive": "docs/session_archive",
    "handover_doc": "handover_doc",
    "qmd_drive/recaps": "qmd_drive/recaps",
}

WIKI_ROOT = "docs/wiki"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰기 없이 동작 확인")
    ap.add_argument("--apply", action="store_true", help="실제 적용")
    ap.add_argument(
        "--only",
        choices=list(FOLDER_PATHS.keys()) + ["wiki"],
        help="특정 폴더만 처리",
    )
    ap.add_argument("--project-root", default=".", help="프로젝트 루트 (기본: .)")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("[error] --dry-run 또는 --apply 중 하나 필수", file=sys.stderr)
        return 2

    root = Path(args.project_root).resolve()

    # 처리 대상 결정
    if args.only == "wiki":
        return _run_wiki_validate(root)
    if args.only:
        folder_keys = [args.only]
    else:
        folder_keys = list(FOLDER_PATHS.keys())

    total_counts = {"added": 0, "updated": 0, "kept": 0, "dry-run": 0}
    for key in folder_keys:
        folder = root / FOLDER_PATHS[key]
        if not folder.exists():
            print(f"[warn] 폴더 없음: {folder}", file=sys.stderr)
            continue
        print(f"\n[{key}] scanning {folder} ...")
        for md in sorted(folder.rglob("*.md")):
            action = process_file(md, key, args.dry_run)
            rel = md.relative_to(root)
            print(f"  [{action:<8}] {rel}")
            total_counts[action] = total_counts.get(action, 0) + 1

    # wiki 검증 (--only 지정 안 했을 때만)
    if args.only is None:
        _run_wiki_validate(root)

    print(f"\n[summary] {total_counts}")
    return 0


def _run_wiki_validate(root: Path) -> int:
    wiki_dir = root / WIKI_ROOT
    if not wiki_dir.exists():
        print(f"[warn] wiki 폴더 없음: {wiki_dir}", file=sys.stderr)
        return 0
    print(f"\n[wiki validate] scanning {wiki_dir} ...")
    all_warnings = []
    for md in sorted(wiki_dir.rglob("*.md")):
        if md.name in {"log.md"}:
            continue
        warnings = validate_wiki_file(md)
        all_warnings.extend(warnings)
    if all_warnings:
        for w in all_warnings:
            print(f"  [warn] {w}", file=sys.stderr)
    else:
        print("  (이상 없음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: CLI smoke test — help**

Run: `python scripts/normalize_session_frontmatter.py --help`
Expected: 도움말 출력, 에러 없음.

- [ ] **Step 3: CLI smoke test — 인자 누락**

Run: `python scripts/normalize_session_frontmatter.py`
Expected: stderr 에 `--dry-run 또는 --apply 중 하나 필수`, exit 2.

- [ ] **Step 4: 전체 테스트 재확인**

Run: `python -m pytest tests/test_normalize_session_frontmatter.py -v`
Expected: 35 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/normalize_session_frontmatter.py
git commit -m "feat: CLI main — --dry-run/--apply/--only 지원"
```

---

### Task 12: 실파일 dry-run 검토 + apply

**Files:**
- Auto-modified: `docs/session_archive/*.md` · `handover_doc/*.md` · `qmd_drive/recaps/*.md`

- [ ] **Step 1: dry-run 실행 및 출력 캡처**

Run:
```bash
python scripts/normalize_session_frontmatter.py --dry-run > /tmp/normalize_dryrun.log 2>&1
cat /tmp/normalize_dryrun.log | tail -30
```
Expected: 각 파일별 `[dry-run]` 또는 `[kept]` 표시. `[added]`/`[updated]` 는 dry-run 중 나오면 안 됨.

- [ ] **Step 2: --only 별로 dry-run 재확인**

```bash
python scripts/normalize_session_frontmatter.py --dry-run --only handover_doc | head -20
python scripts/normalize_session_frontmatter.py --dry-run --only docs/session_archive | head -20
python scripts/normalize_session_frontmatter.py --dry-run --only qmd_drive/recaps | head -20
```
Expected: 각 폴더별로 대상 파일 리스트 정상 출력.

- [ ] **Step 3: wiki 검증 출력 확인**

```bash
python scripts/normalize_session_frontmatter.py --dry-run --only wiki
```
Expected: "(이상 없음)" 또는 특정 파일의 누락 필드 warning. 이상 발견 시 **수동 수정** 후 재실행.

- [ ] **Step 4: apply 실행**

```bash
python scripts/normalize_session_frontmatter.py --apply
```
Expected: `[summary]` 에 added/updated count > 0.

- [ ] **Step 5: git diff 검토**

```bash
cd e:/DnT/DnT_WesangGoon && git diff --stat
cd e:/DnT/DnT_WesangGoon && git diff docs/session_archive/ | head -60
cd e:/DnT/DnT_WesangGoon && git diff handover_doc/ | head -60
cd e:/DnT/DnT_WesangGoon && git diff qmd_drive/recaps/ | head -60
```
Expected: 각 파일 상단에 frontmatter 블록 추가됨. 기존 본문은 변경 없음.

- [ ] **Step 6: idempotency 검증 — 2회차 실행**

```bash
python scripts/normalize_session_frontmatter.py --apply
cd e:/DnT/DnT_WesangGoon && git diff --stat
```
Expected: 2회차 실행 후 **추가 변경 없음** (summary 의 added/updated 는 0).

- [ ] **Step 7: Commit — 자동 주입 결과**

```bash
cd e:/DnT/DnT_WesangGoon && git add docs/session_archive/ handover_doc/ qmd_drive/recaps/
cd e:/DnT/DnT_WesangGoon && git commit -m "$(cat <<'EOF'
chore(frontmatter): 세션 산출물 3 폴더 frontmatter 자동 주입

normalize_session_frontmatter.py --apply 결과.
date · type · cssclass · tags · session 필드 보충.
기존 frontmatter 값 보존 (스칼라 skip · 배열 union).
EOF
)"
```

---

### Task 13: docs/session_artifacts.md 생성

**Files:**
- Create: `docs/session_artifacts.md`

- [ ] **Step 1: 파일 작성**

`docs/session_artifacts.md`:

````markdown
---
title: 위상군 — 세션 산출물
date: 2026-04-22
status: Active
cssclass: twk-timeline
tags: [index, session, artifacts]
---

# 세션 산출물 (Session Artifacts)

> [!abstract]+ 범위
> **L2 raw** + **핸드오버** + **QMD recap** + **L3 wiki** 의 통합 타임라인.
> 4개 폴더의 최근 작성/수정 문서를 한 눈에.

## 최근 작성 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  date as "작성일",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT date DESC
LIMIT 10
```

## 최근 수정 10

```dataview
TABLE WITHOUT ID
  file.link as "문서",
  type as "유형",
  dateformat(file.mtime, "yyyy-MM-dd HH:mm") as "수정시각",
  session as "세션"
FROM "docs/wiki" OR "docs/session_archive" OR "handover_doc" OR "qmd_drive/recaps"
WHERE file.name != "index" AND file.name != "log" AND file.name != "session_artifacts"
SORT file.mtime DESC
LIMIT 10
```

## 폴더별 네비게이션

- [[wiki/index|L3 Wiki Index]] — 큐레이션된 지식
- `docs/session_archive/` — L2 raw (기계 추출)
- `handover_doc/` — 세션 핸드오버
- `qmd_drive/recaps/` — QMD recap
````

- [ ] **Step 2: Commit**

```bash
cd e:/DnT/DnT_WesangGoon && git add docs/session_artifacts.md
cd e:/DnT/DnT_WesangGoon && git commit -m "feat(twk): session_artifacts.md — 4폴더 통합 타임라인 인덱스"
```

---

### Task 14: wiki.config.json + twk.css 업데이트

**Files:**
- Modify: `wiki.config.json:87-95` — `obsidian.cssclasses` 에 4 키 추가
- Modify: `.obsidian/snippets/twk.css` — 4 신규 class 최소 스타일

- [ ] **Step 1: wiki.config.json 수정**

`wiki.config.json` 의 `obsidian.cssclasses` 객체에 4 키 추가. 기존:

```json
    "cssclasses": {
      "decision": "twk-decision",
      "concept": "twk-concept",
      "principle": "twk-principle",
      "postmortem": "twk-postmortem",
      "idea": "twk-idea",
      "entity": "twk-entity",
      "daily": "twk-daily"
    }
```

변경 후:

```json
    "cssclasses": {
      "decision": "twk-decision",
      "concept": "twk-concept",
      "principle": "twk-principle",
      "postmortem": "twk-postmortem",
      "idea": "twk-idea",
      "entity": "twk-entity",
      "daily": "twk-daily",
      "raw": "twk-raw",
      "handover": "twk-handover",
      "recap": "twk-recap",
      "timeline": "twk-timeline"
    }
```

- [ ] **Step 2: twk.css 현재 내용 확인**

Run: `cat .obsidian/snippets/twk.css | tail -40`
Expected: 기존 6 cssclass 스타일이 있음. 기존 accent palette 패턴 확인.

- [ ] **Step 3: twk.css 에 4 신규 class 스타일 append**

기존 palette 톤(sky/emerald/blue/amber/violet/red/slate)과 구분되는 색을 선택. 아래 스니펫을 파일 **맨 아래** append:

```css
/* === 세션 산출물 cssclass (S41 추가) === */

/* raw: 기계 추출 L2, 중립 회색 */
.twk-raw {
  --twk-accent: #64748b;  /* slate-500 */
}

/* handover: 세션 핸드오버, 따뜻한 톤 */
.twk-handover {
  --twk-accent: #f97316;  /* orange-500 */
}

/* recap: QMD recap, 차분한 청록 */
.twk-recap {
  --twk-accent: #14b8a6;  /* teal-500 */
}

/* timeline: 세션 산출물 인덱스 */
.twk-timeline {
  --twk-accent: #8b5cf6;  /* violet-500 */
}

.twk-raw h1,
.twk-handover h1,
.twk-recap h1,
.twk-timeline h1 {
  border-bottom: 2px solid var(--twk-accent);
  padding-bottom: 0.25em;
}
```

- [ ] **Step 4: JSON 유효성 검증**

Run:
```bash
python -c "import json; json.load(open('wiki.config.json'))"
```
Expected: 에러 없음.

- [ ] **Step 5: Commit**

```bash
cd e:/DnT/DnT_WesangGoon && git add wiki.config.json .obsidian/snippets/twk.css
cd e:/DnT/DnT_WesangGoon && git commit -m "style(twk): S41 — raw/handover/recap/timeline cssclass 등록"
```

---

### Task 15: docs/wiki/index.md 에 embed 섹션 추가

**Files:**
- Modify: `docs/wiki/index.md:24-26` — `## 최근 변경` 섹션 **앞**에 신규 섹션 삽입

- [ ] **Step 1: 파일 현재 상태 재확인**

Read `docs/wiki/index.md` 의 24~30 라인. 다음과 같음:
```
---

## 최근 변경

​```dataview
TABLE WITHOUT ID
...
```

- [ ] **Step 2: `---\n\n## 최근 변경` 바로 앞에 새 섹션 삽입**

기존:
```markdown
---

## 최근 변경
```

변경 후:
````markdown
---

## 세션 산출물 (통합)

> [!tip] 4폴더 통합 타임라인
> 아래는 [[../session_artifacts]] 의 embed 입니다. 독립 열람도 가능.

![[../session_artifacts]]

---

## 최근 변경
````

- [ ] **Step 3: Commit**

```bash
cd e:/DnT/DnT_WesangGoon && git add docs/wiki/index.md
cd e:/DnT/DnT_WesangGoon && git commit -m "docs(wiki): S41 — index.md 에 session_artifacts embed 섹션 추가"
```

---

### Task 16: session-lifecycle.md step 5.5 추가

**Files:**
- Modify: `.claude/rules/session-lifecycle.md` — step 5 직후에 step 5.5 추가

- [ ] **Step 1: 현재 파일 구조 확인**

Run: `grep -n "LLM Wiki L2 추출\|^5\." .claude/rules/session-lifecycle.md`
Expected: step 5 의 줄 번호와 구조 확인.

- [ ] **Step 2: step 5 의 `extract_session_raw.py` 호출 블록 **직후**, step 6 앞에 step 5.5 추가**

삽입할 내용:

```markdown
5.5. **세션 산출물 frontmatter 정규화 (S41~):**
   ```bash
   python scripts/normalize_session_frontmatter.py --apply
   ```
   - L2 raw · handover · recap 의 frontmatter 누락 필드 자동 보충 (`date` · `type` · `cssclass` · `tags` · `session`)
   - idempotent — 이미 처리된 파일은 skip
   - `docs/wiki/**` 는 **검증만** (필수 필드 `date`·`status` 체크)
   - 출력은 Dataview 기반 [[../../docs/session_artifacts]] 인덱스로 즉시 반영
```

- [ ] **Step 3: Commit**

```bash
cd e:/DnT/DnT_WesangGoon && git add .claude/rules/session-lifecycle.md
cd e:/DnT/DnT_WesangGoon && git commit -m "docs(lifecycle): S41 — step 5.5 frontmatter 정규화 편입"
```

---

### Task 17: End-to-end Obsidian 렌더링 검증

**Files:**
- None (manual verification)

- [ ] **Step 1: Obsidian 에서 `docs/session_artifacts.md` 열기**

기대:
- "최근 작성 10" 표 — 10 행 표시, date DESC 정렬
- "최근 수정 10" 표 — 10 행 표시, file.mtime DESC 정렬
- 각 행의 `type` 컬럼에 `raw` · `handover` · `recap` · (wiki 페이지는 빈 값) 표시
- `session` 컬럼에 `S1` · `S40` 등 표시

실패 케이스:
- 표가 비었다 → frontmatter 주입 미완료 or Dataview 플러그인 미활성
- `type` 이 모두 빈 값 → Task 12 apply 누락

- [ ] **Step 2: `docs/wiki/index.md` 열기**

기대:
- 상단에 `## 세션 산출물 (통합)` 섹션 표시
- 그 아래 `![[../session_artifacts]]` 가 embed 렌더링 — Step 1 의 표 내용이 인덱스 안에 그대로 보임
- 기존 `## 최근 변경` 섹션은 하단에 유지

- [ ] **Step 3: cssclass 스타일 확인**

handover_doc 중 한 파일을 Obsidian 에서 열어 `h1` 하단 border 가 orange 톤(`--twk-accent: #f97316`)으로 표시되는지 확인.
session_archive 파일은 slate 톤, recap 파일은 teal 톤.

- [ ] **Step 4: self-reference 필터 검증**

session_artifacts.md 자신이 "최근 작성 10" 에 포함되어 있지 **않음** 을 확인 (WHERE `file.name != "session_artifacts"` 필터 작동).

- [ ] **Step 5: 검증 결과 메모**

- 모두 OK → `handover_doc/2026-04-22_session41.md` 에 S41 결과로 기록
- 이상 발견 → 해당 Task 로 돌아가 수정 후 재확인

---

## Self-Review 체크리스트 (plan 작성자 자가 검증)

**Spec coverage 대조:**
- §4 Frontmatter Normalizer → Task 2~11 ✓
- §5 session_artifacts.md → Task 13 ✓
- §6 wiki index embed → Task 15 ✓
- §7 session-lifecycle step 5.5 → Task 16 ✓
- §8 Testing → Task 2~10 (unit) + Task 12 (integration) + Task 17 (Obsidian) ✓
- §9.1 변경 파일 → 모두 커버 (wiki.config.json · twk.css 는 Task 14) ✓
- D1~D7 결정 → 모두 구현 반영 ✓

**Placeholder scan:** 없음. 모든 코드/명령 구체화됨.

**Type consistency:** `parse_frontmatter` · `serialize_frontmatter` · `merge_frontmatter` · `build_template` · `process_file` · `validate_wiki_file` · `extract_date_from_filename` · `extract_session_from_filename` · `mtime_date` 시그니처 일관.
