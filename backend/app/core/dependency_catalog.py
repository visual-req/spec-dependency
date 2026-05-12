from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ApiCapability:
    id: str
    name: str
    method: str | None
    path: str | None
    keywords: list[str]


@dataclass
class ExternalSystem:
    id: str
    name: str
    type: str
    aliases: list[str]
    keywords: list[str]
    apis: list[ApiCapability]


class DependencyCatalog:
    def __init__(self, systems: list[ExternalSystem]) -> None:
        self.systems = systems

    @staticmethod
    def load(path: Path) -> "DependencyCatalog":
        p = path.resolve()
        if not p.is_file():
            raise ValueError(f"dependencies json not found: {path}")
        raw = p.read_text(encoding="utf-8")
        obj = json.loads(raw) if raw.strip() else {}
        systems_raw = obj.get("systems") if isinstance(obj, dict) else None
        if not isinstance(systems_raw, list):
            systems_raw = []
        systems: list[ExternalSystem] = []
        for item in systems_raw:
            if not isinstance(item, dict):
                continue
            if item.get("deleted") is True:
                continue
            sid = _as_str(item.get("id")) or ""
            name = _as_str(item.get("name")) or ""
            if not sid or not name:
                continue
            typ = _as_str(item.get("type")) or "external_system"
            aliases = _as_list_str(item.get("aliases"))
            keywords = _as_list_str(item.get("keywords"))
            api_file = _as_str(item.get("api_file")) or _as_str(item.get("apis_file"))
            apis = _parse_apis(item.get("apis"))
            if api_file is not None and api_file.strip():
                apis_from_file = _load_apis_file(p.parent, api_file.strip())
                if apis_from_file:
                    apis = _dedupe_apis(apis + apis_from_file)
            systems.append(
                ExternalSystem(
                    id=sid,
                    name=name,
                    type=typ,
                    aliases=aliases,
                    keywords=keywords,
                    apis=apis,
                )
            )
        return DependencyCatalog(systems=systems)

    def match_systems(self, text: str) -> list[dict]:
        t = text or ""
        out: list[dict] = []
        for sys in self.systems:
            sys_match = _best_hit(t, [sys.name] + sys.aliases, 0.95) or _best_hit(t, sys.keywords, 0.85)
            api_hits: list[dict] = []
            for api in sys.apis:
                api_hit = _best_hit(t, [api.name] + api.keywords + _non_empty([api.path]), 0.85)
                if api_hit is None:
                    continue
                api_hits.append(
                    {
                        "id": api.id,
                        "name": api.name,
                        "method": api.method,
                        "path": api.path,
                        "confidence": api_hit["confidence"],
                        "evidence": api_hit["evidence"],
                    }
                )
            if sys_match is None and not api_hits:
                continue
            best_conf = sys_match["confidence"] if sys_match is not None else max([x["confidence"] for x in api_hits])
            evidence = sys_match["evidence"] if sys_match is not None else api_hits[0]["evidence"]
            out.append(
                {
                    "id": sys.id,
                    "name": sys.name,
                    "type": sys.type,
                    "confidence": best_conf,
                    "evidence": evidence,
                    "apis": api_hits,
                }
            )
        out.sort(key=lambda x: (-(x.get("confidence") or 0.0), x.get("name") or ""))
        return out


def _parse_apis(v) -> list[ApiCapability]:
    if not isinstance(v, list):
        return []
    out: list[ApiCapability] = []
    for item in v:
        if not isinstance(item, dict):
            continue
        if item.get("deleted") is True:
            continue
        aid = _as_str(item.get("id")) or ""
        name = _as_str(item.get("name")) or ""
        if not aid or not name:
            continue
        method = _as_str(item.get("method"))
        path = _as_str(item.get("path"))
        keywords = _as_list_str(item.get("keywords"))
        out.append(ApiCapability(id=aid, name=name, method=method, path=path, keywords=keywords))
    return out


def _load_apis_file(base_dir: Path, api_file: str) -> list[ApiCapability]:
    rel = api_file.strip()
    p = (base_dir / rel).resolve() if not Path(rel).is_absolute() else Path(rel).resolve()
    if not p.is_file():
        return []
    try:
        raw = p.read_text(encoding="utf-8")
        obj = json.loads(raw) if raw.strip() else {}
    except Exception:
        return []
    if isinstance(obj, list):
        return _parse_apis(obj)
    if isinstance(obj, dict):
        if isinstance(obj.get("apis"), list):
            return _parse_apis(obj.get("apis"))
    return []


def _dedupe_apis(apis: list[ApiCapability]) -> list[ApiCapability]:
    seen: set[str] = set()
    out: list[ApiCapability] = []
    for a in apis:
        if not a.id or a.id in seen:
            continue
        seen.add(a.id)
        out.append(a)
    return out


def _as_str(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def _as_list_str(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out: list[str] = []
        for x in v:
            s = _as_str(x)
            if s is not None and s.strip():
                out.append(s.strip())
        return out
    s = _as_str(v)
    return [s.strip()] if s is not None and s.strip() else []


def _non_empty(items: list[str | None]) -> list[str]:
    out: list[str] = []
    for x in items:
        if x is not None and x.strip():
            out.append(x.strip())
    return out


def _best_hit(text: str, needles: list[str], base_conf: float) -> dict | None:
    t = text or ""
    best = None
    for n in needles:
        if not n or not n.strip():
            continue
        idx = _index_of(t, n)
        if idx < 0:
            continue
        hit = {"confidence": float(base_conf), "evidence": _snippet(t, idx)}
        if best is None or hit["confidence"] > best["confidence"]:
            best = hit
    return best


def _index_of(text: str, needle: str) -> int:
    if any(ord(ch) > 127 for ch in needle):
        return text.find(needle)
    return text.lower().find(needle.lower())


def _snippet(text: str, idx: int) -> str:
    if not text:
        return ""
    at = max(0, idx)
    start = max(0, at - 40)
    end = min(len(text), at + 80)
    return text[start:end].replace("\r", " ").replace("\n", " ").strip()
