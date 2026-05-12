from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config.config import load_config
from app.core.dependency_scanner import DependencyScanner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="py-spec-dep")
    sub = parser.add_subparsers(dest="cmd")

    scan = sub.add_parser("scan", help="scan requirement files for external dependencies")
    scan.add_argument("-req", required=True, dest="req_path", help="requirement file (.doc/.docx) or directory")
    scan.add_argument("--deps", required=False, dest="deps_path", help="external systems json (optional)")
    scan.add_argument("--out", required=False, dest="out_dir", help="output directory (optional)")

    web = sub.add_parser("web", help="start a local web UI")
    web.add_argument("--host", required=False, dest="host")
    web.add_argument("--port", required=False, dest="port", type=int)

    args = parser.parse_args(argv)
    if args.cmd == "scan":
        req_path = Path(args.req_path)
        deps_path = Path(args.deps_path) if args.deps_path else None
        out_dir = Path(args.out_dir) if args.out_dir else None
        outputs = DependencyScanner().scan(req_path, deps_path, out_dir)
        for p in outputs:
            print(str(p))
        return 0

    if args.cmd == "web":
        cfg = load_config()
        host = args.host or cfg.server_host or "127.0.0.1"
        port = args.port or cfg.server_port or 8766
        url = f"http://{host}:{port}/"
        print(url)
        try:
            import uvicorn
        except Exception as e:
            raise RuntimeError("uvicorn is required to run the web server") from e
        from app.web.api import create_app

        uvicorn.run(create_app(), host=host, port=port, log_level="info")
        return 0

    print("请使用: py-spec-dep scan -req <需求文件或目录> [--deps <外部系统JSON>]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
