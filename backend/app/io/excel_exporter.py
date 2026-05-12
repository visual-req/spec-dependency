from __future__ import annotations

from pathlib import Path


def write_module_dependency_excel(path: Path, data: dict) -> None:
    try:
        from openpyxl import Workbook
    except Exception as e:
        raise RuntimeError("openpyxl is required to write excel files") from e

    wb = Workbook()
    ws = wb.active
    ws.title = "module_deps"

    ws.append(["module", "system_id", "system_name", "system_type", "api_id", "api_name", "method", "path", "confidence", "reason", "evidence"])

    modules = data.get("modules") if isinstance(data, dict) else None
    if not isinstance(modules, list):
        modules = []

    for m in modules:
        if not isinstance(m, dict):
            continue
        module_name = m.get("module") or ""
        deps = m.get("dependencies")
        if not isinstance(deps, list) or not deps:
            ws.append([module_name, "", "", "", "", "", "", "", "", "", ""])
            continue
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            apis = dep.get("apis")
            if not isinstance(apis, list) or not apis:
                ws.append(
                    [
                        module_name,
                        dep.get("id") or "",
                        dep.get("name") or "",
                        dep.get("type") or "",
                        "",
                        "",
                        "",
                        "",
                        dep.get("confidence") or "",
                        dep.get("reason") or "",
                        dep.get("evidence") or "",
                    ]
                )
                continue
            for api in apis:
                if not isinstance(api, dict):
                    continue
                ws.append(
                    [
                        module_name,
                        dep.get("id") or "",
                        dep.get("name") or "",
                        dep.get("type") or "",
                        api.get("id") or "",
                        api.get("name") or "",
                        api.get("method") or "",
                        api.get("path") or "",
                        api.get("confidence") or dep.get("confidence") or "",
                        api.get("reason") or dep.get("reason") or "",
                        api.get("evidence") or dep.get("evidence") or "",
                    ]
                )

    out = path.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out))

