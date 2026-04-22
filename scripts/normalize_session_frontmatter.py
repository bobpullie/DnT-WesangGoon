"""세션 산출물 frontmatter 자동 정규화.

3 폴더(docs/session_archive · handover_doc · qmd_drive/recaps)의 .md 파일에
누락된 frontmatter 필드(date · type · cssclass · tags · session)를 idempotent
하게 주입한다. docs/wiki/** 는 검증만.

위상군 로컬 전용 (TCL #93). 세션 종료 lifecycle step 5.5 에서 호출.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

FLOW_STYLE_KEYS = {"tags", "aliases"}

ARRAY_KEYS = {"tags", "aliases"}

# 파일명 맨 앞에서만 매칭 (중간 숫자 오인 방지)
DATE_PATTERNS = [
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})"),   # 2026-04-21
    re.compile(r"^(\d{4})(\d{2})(\d{2})"),     # 20260420
]

SESSION_PATTERN = re.compile(r"[_-]s(?:ession)?(\d+)", re.IGNORECASE)

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


def mtime_date(path: Path) -> str:
    """파일 mtime 의 날짜 부분을 YYYY-MM-DD 로 반환."""
    ts = path.stat().st_mtime
    return datetime.date.fromtimestamp(ts).strftime("%Y-%m-%d")


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


def extract_session_from_filename(name: str) -> str | None:
    """파일명에서 'session{N}' 또는 's{N}' 패턴으로 session 번호 추출.

    성공 시 'S{N}', 실패 시 None.
    """
    m = SESSION_PATTERN.search(name)
    if m:
        return f"S{m.group(1)}"
    return None


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


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """markdown 문자열을 (frontmatter dict, body) 로 분리.

    frontmatter 가 없으면 ({}, content) 반환.
    """
    if not content:
        return {}, ""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    meta = yaml.load(m.group(1), Loader=yaml.BaseLoader) or {}
    body = content[m.end():]
    return meta, body


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
            # yaml.safe_dump 으로 escape 처리 후 trailing newline 제거.
            # BaseLoader 로 parse 되므로 모든 scalar 는 str — PyYAML 이 date-like
            # 문자열에 자동으로 추가하는 quote 를 제거하여 round-trip 시 원본과
            # 동일한 표현 유지.
            dumped = yaml.safe_dump({key: value}, allow_unicode=True, default_flow_style=False)
            line = dumped.rstrip()
            # "key: 'value'" → "key: value" (ISO date 등 안전한 문자열만)
            prefix = f"{key}: "
            if line.startswith(prefix):
                rest = line[len(prefix):]
                if len(rest) >= 2 and rest[0] == "'" and rest[-1] == "'":
                    unquoted = rest[1:-1]
                    # escape 된 single quote 없고, 콜론/해시/YAML 특수문자 없을 때만
                    if "''" not in unquoted and not any(c in unquoted for c in ":#\n"):
                        line = f"{prefix}{unquoted}"
            lines.append(line)
    fm = "---\n" + "\n".join(lines) + "\n---\n"
    if body and not body.startswith("\n"):
        fm += "\n"
    return fm + body
