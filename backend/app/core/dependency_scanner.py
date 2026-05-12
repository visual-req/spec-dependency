from __future__ import annotations

import json
import time
from pathlib import Path

from ..config.config import load_config
from ..io.docx_text_extractor import extract_word_text
from ..io.excel_exporter import write_module_dependency_excel
from ..llm.llm_client import llm_extract_module_deps
from .dependency_catalog import DependencyCatalog
from .module_splitter import split_text_into_modules


class DependencyScanner:
    def scan(self, req_path: Path, deps_path: Path | None, out_dir: Path | None) -> list[Path]:
        rp = req_path.resolve()
        if not rp.exists():
            raise ValueError(f"req path not found: {req_path}")

        cfg = load_config()
        od = self._resolve_out_dir(out_dir)
        od.mkdir(parents=True, exist_ok=True)
        scan_id_base = time.strftime("%Y%m%d%H%M%S", time.localtime())
        scan_id = scan_id_base
        scan_dir = (od / scan_id).resolve()
        if scan_dir.exists():
            i = 1
            while True:
                cand = (od / f"{scan_id_base}_{i}").resolve()
                if not cand.exists():
                    scan_id = f"{scan_id_base}_{i}"
                    scan_dir = cand
                    break
                i += 1
        scan_dir.mkdir(parents=True, exist_ok=True)

        resolved_deps = self._resolve_deps_path(deps_path)
        catalog = DependencyCatalog.load(resolved_deps)

        outputs: list[Path] = []
        req_files = [rp] if rp.is_file() else list(sorted(self._iter_req_files(rp), key=lambda p: p.name.lower()))
        if not req_files:
            raise ValueError(f"no requirement files found under: {req_path}")

        for f in req_files:
            text = self._read_text(f)
            modules = split_text_into_modules(text)
            module_rows: list[dict] = []
            for sec in modules:
                mod = sec.get("module") or "global"
                body = sec.get("text") or ""
                deps = catalog.match_systems(body)
                module_rows.append({"module": mod, "dependencies": deps})

            result = {
                "scan_id": scan_id,
                "requirement_file": str(f.resolve()),
                "dependencies_file": str(resolved_deps.resolve()),
                "modules": module_rows,
            }
            llm = llm_extract_module_deps(cfg, text, resolved_deps)
            if llm is not None:
                result["modules"] = _dedupe_modules(llm.get("modules") or result["modules"])
                result["llm"] = {"provider": "deepseek", "model": cfg.deepseek_model, "used": True}
            else:
                result["modules"] = _dedupe_modules(result["modules"])
                result["llm"] = {"provider": "deepseek", "model": cfg.deepseek_model, "used": False}

            base = f.stem or "output"
            json_path = (scan_dir / f"{base}.module_deps.json").resolve()
            xlsx_path = (scan_dir / f"{base}.module_deps.xlsx").resolve()
            json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            write_module_dependency_excel(xlsx_path, result)
            outputs.append(json_path)
            outputs.append(xlsx_path)

        return outputs

    def _resolve_out_dir(self, out_dir: Path | None) -> Path:
        if out_dir is not None:
            return out_dir.resolve()
        cfg = load_config()
        if cfg.work_dir is not None:
            return (cfg.work_dir / "output").resolve()
        return (Path.cwd() / "work" / "output").resolve()

    def _resolve_deps_path(self, deps_path: Path | None) -> Path:
        if deps_path is not None:
            return deps_path.resolve()
        cfg = load_config()
        if cfg.work_dir is not None:
            dep_dir = (cfg.work_dir / "input" / "dependencies").resolve()
        else:
            dep_dir = (Path.cwd() / "work" / "input" / "dependencies").resolve()
        idx = (dep_dir / "index.json").resolve()
        if idx.is_file():
            return idx
        candidates = []
        if dep_dir.is_dir():
            for p in dep_dir.iterdir():
                if p.is_file() and p.name.lower().endswith(".json"):
                    candidates.append(p)
        candidates.sort(key=lambda p: p.name.lower())
        if candidates:
            return candidates[0].resolve()
        raise ValueError(f"dependencies json not found under: {dep_dir}")

    def _iter_req_files(self, root: Path):
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            n = p.name.lower()
            if n.endswith(".doc") or n.endswith(".docx"):
                yield p

    def _read_text(self, p: Path) -> str:
        n = p.name.lower()
        if n.endswith(".doc") or n.endswith(".docx"):
            return extract_word_text(p)
        return p.read_text(encoding="utf-8")


def _dedupe_modules(modules) -> list:
    ms = modules if isinstance(modules, list) else []
    out = []
    for m in ms:
        if not isinstance(m, dict):
            continue
        name = m.get("module") or "global"
        deps = m.get("dependencies")
        deps_list = deps if isinstance(deps, list) else []
        sys_map: dict[str, dict] = {}
        sys_order: list[str] = []
        for d in deps_list:
            if not isinstance(d, dict):
                continue
            sid = d.get("id")
            sname = d.get("name")
            key = (str(sid).strip() if sid is not None else "") or (str(sname).strip() if sname is not None else "")
            if not key:
                continue
            if key not in sys_map:
                sys_map[key] = dict(d)
                sys_map[key]["apis"] = []
                sys_order.append(key)
            cur = sys_map[key]
            cur["confidence"] = _better_conf(cur.get("confidence"), d.get("confidence"))
            for k in ["id", "name", "type", "reason", "evidence"]:
                if not cur.get(k) and d.get(k):
                    cur[k] = d.get(k)
            apis = d.get("apis")
            api_list = apis if isinstance(apis, list) else []
            api_map = {_api_key(a): a for a in (cur.get("apis") or []) if isinstance(a, dict) and _api_key(a)}
            for a in api_list:
                if not isinstance(a, dict):
                    continue
                ak = _api_key(a)
                if not ak:
                    continue
                if ak not in api_map:
                    api_map[ak] = a
                else:
                    api_map[ak] = _better_api(api_map[ak], a)
            cur["apis"] = list(api_map.values())
        out.append({"module": name, "dependencies": [sys_map[k] for k in sys_order]})
    return out


def _api_key(a: dict) -> str:
    aid = a.get("id")
    name = a.get("name")
    method = a.get("method")
    path = a.get("path")
    first = (str(aid).strip() if aid is not None else "") or (str(name).strip() if name is not None else "")
    return "|".join([first, str(method or ""), str(path or "")]).strip("|")


def _better_conf(a, b):
    try:
        na = float(a)
    except Exception:
        na = None
    try:
        nb = float(b)
    except Exception:
        nb = None
    if nb is not None and (na is None or nb > na):
        return b
    return a


def _better_api(old: dict, new: dict) -> dict:
    if not isinstance(old, dict):
        return dict(new)
    if not isinstance(new, dict):
        return dict(old)
    out = dict(old)
    out["confidence"] = _better_conf(out.get("confidence"), new.get("confidence"))
    for k in ["id", "name", "method", "path", "reason", "evidence"]:
        if not out.get(k) and new.get(k):
            out[k] = new.get(k)
    return out
