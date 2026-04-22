import os
import time
from pathlib import Path

import pytest
from scripts.normalize_session_frontmatter import (
    FOLDER_CONFIG,
    build_template,
    extract_date_from_filename,
    extract_session_from_filename,
    merge_frontmatter,
    mtime_date,
    parse_frontmatter,
    process_file,
    serialize_frontmatter,
    validate_wiki_file,
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
