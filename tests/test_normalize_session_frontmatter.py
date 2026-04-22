import os
import time
from pathlib import Path

import pytest
from scripts.normalize_session_frontmatter import (
    extract_date_from_filename,
    extract_session_from_filename,
    mtime_date,
    parse_frontmatter,
    serialize_frontmatter,
)


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


def test_parse_serialize_roundtrip():
    original_meta = {"date": "2026-04-22", "type": "recap", "tags": ["a", "b"], "session": "S41"}
    serialized = serialize_frontmatter(original_meta, "# body\n")
    parsed_meta, parsed_body = parse_frontmatter(serialized)
    assert parsed_meta == original_meta
    assert parsed_body == "# body\n"


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


def test_extract_session_word_format():
    assert extract_session_from_filename("20260420_session1_raw.md") == "S1"


def test_extract_session_multi_digit():
    assert extract_session_from_filename("2026-04-21_session40.md") == "S40"


def test_extract_session_not_present():
    assert extract_session_from_filename("2026-04-22_note.md") is None


def test_extract_session_sN_shortform():
    """sN 형식도 허용 (혹시 미래에 사용될 경우)."""
    assert extract_session_from_filename("20260421_s3_raw.md") == "S3"


def test_mtime_date_format(tmp_path: Path):
    """file.mtime 을 YYYY-MM-DD 로 변환."""
    p = tmp_path / "test.md"
    p.write_text("x", encoding="utf-8")
    # 특정 시각으로 mtime 고정: 2026-04-01 00:00:00
    fixed = time.mktime(time.strptime("2026-04-01", "%Y-%m-%d"))
    os.utime(p, (fixed, fixed))
    assert mtime_date(p) == "2026-04-01"
