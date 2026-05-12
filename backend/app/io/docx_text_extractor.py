from __future__ import annotations

import subprocess
from pathlib import Path


def extract_docx_text(docx_path: Path) -> str:
    p = docx_path.resolve()
    if not p.is_file():
        return ""
    try:
        from docx import Document
    except Exception as e:
        raise RuntimeError("python-docx is required to read .docx files") from e

    doc = Document(str(p))
    lines: list[str] = []
    for para in doc.paragraphs:
        t = (para.text or "").strip()
        if t:
            lines.append(t)
    return "\n".join(lines).strip()


def extract_word_text(path: Path) -> str:
    p = path.resolve()
    if not p.is_file():
        return ""
    suf = p.suffix.lower()
    if suf == ".docx":
        return extract_docx_text(p)
    if suf == ".doc":
        try:
            proc = subprocess.run(["antiword", str(p)], capture_output=True, text=True)
        except Exception as e:
            raise RuntimeError("antiword is required to read .doc files") from e
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or "").strip() or "failed to read .doc file")
        return (proc.stdout or "").strip()
    return ""

