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
