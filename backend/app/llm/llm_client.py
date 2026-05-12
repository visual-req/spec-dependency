from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from ..config.config import AppConfig


def llm_extract_module_deps(cfg: AppConfig, requirement_text: str, deps_json_path: Path) -> dict | None:
    if cfg.deepseek_api_key is None or not cfg.deepseek_api_key.strip():
        return None
    base_url = (cfg.deepseek_base_url or "https://api.deepseek.com/v1").rstrip("/")
    model = cfg.deepseek_model or "deepseek-chat"
    deps_text = deps_json_path.read_text(encoding="utf-8")

    system = "\n".join(
        [
            "你是资深软件需求分析架构师。你的任务是根据需求文本，识别当前系统会调用哪些【外部依赖系统】以及具体的【外部 API 能力】。",
            "注意：",
            "1. 严格区分“系统内部模块”和“外部依赖系统”。例如：一个电商系统自身会有“订单管理模块”或“库存字段”，这属于内部实现，绝不能识别为依赖外部的“订单系统”或“仓储系统”！只有当需求明确提到“调用外部xxx”、“同步给xxx中台”、“对接第三方xxx”时，才算外部依赖。",
            "2. 旅游/海外出行系统中的“机酒订单”、“门票库存”是内部业务概念，绝不能生搬硬套匹配到物流系统、WMS仓储系统或通用订单中台，除非明确说明对接。",
            "3. 只能从给定的外部系统清单中选择系统与 API，不要臆造新的系统或 API。",
            "4. 输出必须是严格的 JSON，根节点包含 modules 数组。",
            "5. modules 元素格式：{module: string, dependencies: [{id, name, type, confidence, reason, evidence, apis:[{id, name, method, path, confidence, evidence}]}]}。",
            "6. confidence 取 0~1 的小数。要求非常严格，只有置信度大于 0.8 才输出。",
            "7. reason 必须给出你判断这是外部依赖而不是内部模块的理由。",
            "8. evidence 必须给出需求原文的短片段作为证据。",
        ]
    )
    user = "\n".join(
        [
            "外部系统清单(JSON):",
            deps_text,
            "",
            "需求文本:",
            requirement_text,
        ]
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    url = base_url + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg.deepseek_api_key.strip(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            _ = e.read()
        except Exception:
            pass
        return None
    except Exception:
        return None

    try:
        obj = json.loads(raw)
    except Exception:
        return None
    content = _extract_content(obj)
    if content is None:
        return None
    parsed = _parse_json_from_text(content)
    if parsed is None:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("modules"), list):
        return None
    return parsed


def llm_adjust_scan_result(cfg: AppConfig, scan_result: dict, instruction: str, deps_json_path: Path) -> dict | None:
    if cfg.deepseek_api_key is None or not cfg.deepseek_api_key.strip():
        return None
    ins = (instruction or "").strip()
    if not ins:
        return None
    base_url = (cfg.deepseek_base_url or "https://api.deepseek.com/v1").rstrip("/")
    model = cfg.deepseek_model or "deepseek-chat"
    deps_text = deps_json_path.read_text(encoding="utf-8")

    system = "\n".join(
        [
            "你是资深软件需求分析架构师。你的任务是根据用户的指令，对“依赖识别扫描结果 JSON”进行二次编辑。",
            "严格要求：",
            "1. 只能输出严格的 JSON（不要 Markdown，不要解释）。",
            "2. 必须保持 JSON 的结构/字段不变（根对象必须包含 scan_id、output_dir、dependencies_file、files、outputs 字段；files 必须是数组；每个 files[i] 必须包含 file、modules、llm）。",
            "3. 允许在 dependencies / apis 的数组内容中进行增加、删除、修改，但不能改变字段名，不能改变类型。",
            "4. 不要臆造新的外部系统或 API，除非用户明确要求；优先从给定外部系统清单中选择。",
            "5. 保留 scan_id 不变。",
        ]
    )
    user = "\n".join(
        [
            "外部系统清单(JSON):",
            deps_text,
            "",
            "原始扫描结果(JSON):",
            json.dumps(scan_result, ensure_ascii=False),
            "",
            "用户指令:",
            ins,
        ]
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    url = base_url + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg.deepseek_api_key.strip(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            _ = e.read()
        except Exception:
            pass
        return None
    except Exception:
        return None

    try:
        obj = json.loads(raw)
    except Exception:
        return None
    content = _extract_content(obj)
    if content is None:
        return None
    parsed = _parse_json_from_text(content)
    if not isinstance(parsed, dict):
        return None
    if not isinstance(parsed.get("files"), list):
        return None
    if parsed.get("scan_id") is None:
        return None
    return parsed


def llm_extract_dependency_catalog_from_excel(cfg: AppConfig, excel_json: dict, known_systems: list[dict] | None = None) -> dict | None:
    if cfg.deepseek_api_key is None or not cfg.deepseek_api_key.strip():
        return None
    base_url = (cfg.deepseek_base_url or "https://api.deepseek.com/v1").rstrip("/")
    model = cfg.deepseek_model or "deepseek-chat"

    system = "\n".join(
        [
            "你是资深软件架构师。你的任务是把“Excel 表格里的外部依赖清单”结构化成系统/接口的层级 JSON，用于更新外部依赖库。",
            "严格要求：",
            "1. 只能输出严格 JSON（不要 Markdown，不要解释）。",
            "2. 根对象必须包含 systems 数组。",
            "3. systems 元素格式：{id?, name, type?, description?, aliases?, keywords?, deleted?, apis:[...]}",
            "4. apis 元素格式：{id?, name, method?, path?, keywords?, deleted?, request_params?, response_params?}",
            "5. deleted 为 true 表示“标记删除”（不要从数组移除）。",
            "6. request_params/response_params 若能识别，输出数组：[{name, type?, required?, desc?}]；识别不到就输出空数组或不输出该字段。",
            "7. 尽量复用 known_systems 中已有系统的 id（按 name/aliases/关键词相近匹配），避免产生重复系统。",
            "8. 如果 Excel 明显包含多套系统（例如按 sheet 分开或按分组列），就输出多个 systems；否则输出 1 个 systems。",
        ]
    )

    user = "\n".join(
        [
            "known_systems(用于匹配已有 system_id，可能不完整):",
            json.dumps(known_systems or [], ensure_ascii=False),
            "",
            "excel_json(按 sheets/rows 提供，可能已截断):",
            json.dumps(excel_json or {}, ensure_ascii=False),
        ]
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    url = base_url + "/chat/completions"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + cfg.deepseek_api_key.strip(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            _ = e.read()
        except Exception:
            pass
        return None
    except Exception:
        return None

    try:
        obj = json.loads(raw)
    except Exception:
        return None
    content = _extract_content(obj)
    if content is None:
        return None
    parsed = _parse_json_from_text(content)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("systems"), list):
        return None
    return parsed


def _extract_content(obj: dict) -> str | None:
    choices = obj.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    msg = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(msg, dict):
        return None
    c = msg.get("content")
    if not isinstance(c, str):
        return None
    return c


def _parse_json_from_text(text: str) -> dict | list | None:
    t = text.strip()
    if not t:
        return None
    try:
        return json.loads(t)
    except Exception:
        pass
    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        frag = t[start : end + 1]
        try:
            return json.loads(frag)
        except Exception:
            return None
    return None
