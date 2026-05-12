from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    work_dir: Path | None = None
    server_host: str | None = None
    server_port: int | None = None
    deepseek_base_url: str | None = None
    deepseek_model: str | None = None
    deepseek_api_key: str | None = None
    config_path: Path | None = None


def load_config() -> AppConfig:
    p = _resolve_config_path()
    data: dict[str, Any] = {}
    if p is not None and p.is_file():
        raw = p.read_text(encoding="utf-8")
        name = p.name.lower()
        if name.endswith(".json"):
            data = json.loads(raw) if raw.strip() else {}
        elif name.endswith(".yaml") or name.endswith(".yml"):
            try:
                import yaml
            except Exception:
                data = {}
            else:
                loaded = yaml.safe_load(raw)
                data = loaded if isinstance(loaded, dict) else {}
        else:
            data = {}

    server = data.get("server") if isinstance(data.get("server"), dict) else {}
    llm = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    cfg = AppConfig()
    cfg.config_path = p.resolve() if p is not None and p.exists() else None

    cfg.server_host = os.getenv("SPEC_DEP_HOST") or _as_str(server.get("host"))
    cfg.server_port = _as_int(os.getenv("SPEC_DEP_PORT") or _as_str(server.get("port")))

    cfg.deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL") or _as_str(llm.get("base_url")) or "https://api.deepseek.com/v1"
    cfg.deepseek_model = os.getenv("DEEPSEEK_MODEL") or _as_str(llm.get("model")) or "deepseek-chat"
    cfg.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY") or _as_str(llm.get("api_key"))
    if cfg.deepseek_api_key is not None and cfg.deepseek_api_key.strip() == "YOUR_DEEPSEEK_API_KEY":
        cfg.deepseek_api_key = None
    if cfg.deepseek_api_key is not None and not cfg.deepseek_api_key.strip():
        cfg.deepseek_api_key = None

    cfg.work_dir = _resolve_work_dir(data, cfg.config_path)
    return cfg


def _resolve_work_dir(data: dict[str, Any], config_path: Path | None) -> Path | None:
    config_dir = config_path.parent if config_path is not None else None
    env_work = os.getenv("SPEC_DEP_WORK_DIR")
    if env_work and env_work.strip():
        p = _expand_home(env_work.strip())
        return (p if p.is_absolute() else (Path.cwd() / p)).resolve()

    raw = _as_str(data.get("work_dir"))
    if not raw or not raw.strip():
        return None
    p = _expand_home(raw.strip())
    if p.is_absolute() or config_dir is None:
        return p.resolve()
    return (config_dir / p).resolve()


def _resolve_config_path() -> Path | None:
    env_config = os.getenv("SPEC_DEP_CONFIG")
    if env_config and env_config.strip():
        p = _expand_home(env_config.strip())
        abs_p = p if p.is_absolute() else (Path.cwd() / p).resolve()
        if abs_p.is_file():
            return abs_p

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        try:
            exe_dir = Path(sys.executable).resolve().parent
        except Exception:
            exe_dir = None
        if exe_dir is not None:
            for candidate in _candidate_configs(exe_dir):
                if candidate.is_file():
                    return candidate

    for candidate in _candidate_configs(Path.cwd()):
        if candidate.is_file():
            return candidate

    exec_dir = Path.cwd() / "executable"
    for candidate in _candidate_configs(exec_dir):
        if candidate.is_file():
            return candidate

    backend_dir = Path(__file__).resolve().parents[3]
    project_root = backend_dir.parent
    exec_dir2 = project_root / "executable"
    for candidate in _candidate_configs(exec_dir2):
        if candidate.is_file():
            return candidate

    return None


def _candidate_configs(dir_path: Path) -> list[Path]:
    return [
        dir_path / "config.yaml",
        dir_path / "config.yml",
        dir_path / "config.example.yaml",
        dir_path / "config.example.yml",
        dir_path / "config.json",
    ]


def _expand_home(raw: str) -> Path:
    s = raw.strip()
    if s == "~":
        return Path.home()
    if s.startswith("~/") or s.startswith("~\\"):
        return Path.home() / s[2:]
    return Path(s)


def _as_str(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def _as_int(s: str | None) -> int | None:
    if s is None:
        return None
    t = s.strip()
    if not t:
        return None
    try:
        return int(t)
    except Exception:
        return None
