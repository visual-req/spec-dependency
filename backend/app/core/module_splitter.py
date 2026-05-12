from __future__ import annotations

import re


_NUM_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*([、.\-:：\s]+)\s*(.+?)\s*$")
_TAG_HEADING = re.compile(r"^\s*[【\[]\s*([^】\]]{2,40})\s*[】\]]\s*$")
_KW_HEADING = re.compile(r"^\s*(模块|子系统|功能|业务)\s*[:：]\s*(.+?)\s*$")


def split_text_into_modules(text: str) -> list[dict]:
    t = (text or "").strip()
    if not t:
        return [{"module": "global", "text": ""}]

    lines = [x.rstrip() for x in t.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    sections: list[dict] = []
    cur_module = "global"
    cur_lines: list[str] = []

    def flush():
        nonlocal cur_lines, cur_module
        body = "\n".join([x for x in cur_lines if x.strip()]).strip()
        sections.append({"module": cur_module, "text": body})
        cur_lines = []

    for line in lines:
        s = (line or "").strip()
        if not s:
            continue
        module = _try_heading(s)
        if module is not None:
            if cur_lines:
                flush()
            cur_module = module
            continue
        cur_lines.append(s)

    flush()
    merged: dict[str, list[str]] = {}
    for sec in sections:
        m = sec["module"]
        merged.setdefault(m, [])
        if sec["text"]:
            merged[m].append(sec["text"])
    out = []
    for m, parts in merged.items():
        out.append({"module": m, "text": "\n".join(parts).strip()})
    return out


def _try_heading(line: str) -> str | None:
    m1 = _NUM_HEADING.match(line)
    if m1:
        title = (m1.group(3) or "").strip()
        return title if title else None
    m2 = _KW_HEADING.match(line)
    if m2:
        title = (m2.group(2) or "").strip()
        return title if title else None
    m3 = _TAG_HEADING.match(line)
    if m3:
        title = (m3.group(1) or "").strip()
        return title if title else None
    return None

