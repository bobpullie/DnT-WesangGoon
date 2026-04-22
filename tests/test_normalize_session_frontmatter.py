import pytest
from scripts.normalize_session_frontmatter import parse_frontmatter, serialize_frontmatter


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
