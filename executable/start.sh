#!/usr/bin/env sh
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

PY="../backend/.venv/bin/python"
if [ -x "$PY" ]; then
  PYTHON="$PY"
else
  PYTHON="python3"
fi

ensure_deps() {
  if "$PYTHON" -c "import uvicorn, fastapi, multipart, docx, openpyxl" >/dev/null 2>&1; then
    return 0
  fi
  if [ ! -x "../backend/.venv/bin/python" ]; then
    python3 -m venv "../backend/.venv"
    PYTHON="../backend/.venv/bin/python"
  else
    PYTHON="../backend/.venv/bin/python"
  fi
  "$PYTHON" -m pip install -U pip >/dev/null 2>&1 || true
  "$PYTHON" -m pip install -r "../backend/requirements.txt"
}

ensure_deps

if [ "$#" -eq 0 ]; then
  exec env PYTHONPATH="../backend" "$PYTHON" -m app.cli.main web
fi

exec env PYTHONPATH="../backend" "$PYTHON" -m app.cli.main "$@"
