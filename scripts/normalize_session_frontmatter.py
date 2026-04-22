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

FLOW_STYLE_KEYS = {"tags", "aliases"}


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
