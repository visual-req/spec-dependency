#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  echo "usage: sh executable/package.sh <target>"
  echo "targets:"
  echo "  macos-onefile"
  echo "  windows-portable"
  exit 2
fi

ensure_frontend_dist() {
  if [ -f "$ROOT_DIR/frontend/dist/index.html" ]; then
    return 0
  fi
  if command -v npm >/dev/null 2>&1; then
    (cd "$ROOT_DIR/frontend" && npm install --no-audit --no-fund && npm run build)
  fi
  if [ ! -f "$ROOT_DIR/frontend/dist/index.html" ]; then
    echo "frontend/dist not found. Build frontend first."
    exit 1
  fi
}

ensure_backend_venv() {
  if [ -x "$ROOT_DIR/backend/.venv/bin/python" ]; then
    return 0
  fi
  python3 -m venv "$ROOT_DIR/backend/.venv"
}

macos_onefile() {
  ensure_frontend_dist
  ensure_backend_venv
  "$ROOT_DIR/backend/.venv/bin/python" -m pip install -U pip >/dev/null 2>&1 || true
  "$ROOT_DIR/backend/.venv/bin/python" -m pip install -r "$ROOT_DIR/backend/requirements.txt" pyinstaller

  rm -rf "$ROOT_DIR/backend/.pyinstaller_build" "$ROOT_DIR/backend/.pyinstaller_spec"
  rm -f "$SCRIPT_DIR/spec_dep"
  PYINSTALLER_CONFIG_DIR="$ROOT_DIR/backend/.pyinstaller_cache" \
    "$ROOT_DIR/backend/.venv/bin/python" -m PyInstaller \
      --noconfirm \
      --onefile \
      --name spec_dep \
      --distpath "$SCRIPT_DIR" \
      --workpath "$ROOT_DIR/backend/.pyinstaller_build" \
      --specpath "$ROOT_DIR/backend/.pyinstaller_spec" \
      --paths "$ROOT_DIR/backend" \
      --add-data "$ROOT_DIR/frontend/dist:frontend/dist" \
      "$ROOT_DIR/backend/app/cli/main.py"

  echo "built: $SCRIPT_DIR/spec_dep"
}

windows_portable() {
  UNAME_S="$(uname -s 2>/dev/null || echo "")"
  case "$UNAME_S" in
    MINGW*|MSYS*|CYGWIN* ) ;;
    * )
      echo "windows-portable must be built on Windows (Git Bash/MSYS2)."
      echo "current uname: ${UNAME_S:-unknown}"
      echo "reason: pip will download platform-specific wheels (e.g. lxml) for the current OS, which cannot run on Windows."
      exit 1
      ;;
  esac

  ensure_frontend_dist

  PY="${PYTHON:-}"
  if [ -z "$PY" ]; then
    if command -v python >/dev/null 2>&1; then
      PY="python"
    else
      PY="python3"
    fi
  fi

  BUILD_VENV="$ROOT_DIR/backend/.zipapp_venv"
  if [ ! -x "$BUILD_VENV/bin/python" ]; then
    "$PY" -m venv "$BUILD_VENV"
  fi
  BUILD_PY="$BUILD_VENV/bin/python"

  "$BUILD_PY" -m pip install -U pip >/dev/null 2>&1 || true

  BUILD_DIR="$ROOT_DIR/backend/.zipapp_build"
  rm -rf "$BUILD_DIR"
  mkdir -p "$BUILD_DIR"

  "$BUILD_PY" -m pip install --no-cache-dir -r "$ROOT_DIR/backend/requirements.txt" -t "$BUILD_DIR"

  rm -rf "$BUILD_DIR/app"
  mkdir -p "$BUILD_DIR/app"
  cp -R "$ROOT_DIR/backend/app/"* "$BUILD_DIR/app/"

  rm -f "$SCRIPT_DIR/spec_dep.pyz"
  "$BUILD_PY" -m zipapp "$BUILD_DIR" -m "app.cli.main:main" -o "$SCRIPT_DIR/spec_dep.pyz"

  rm -rf "$SCRIPT_DIR/frontend"
  mkdir -p "$SCRIPT_DIR/frontend"
  cp -R "$ROOT_DIR/frontend/dist" "$SCRIPT_DIR/frontend/dist"

  EMBED_VER="${PY_EMBED_VERSION:-3.11.9}"
  EMBED_ARCH="${PY_EMBED_ARCH:-amd64}"
  EMBED_URL="https://www.python.org/ftp/python/${EMBED_VER}/python-${EMBED_VER}-embed-${EMBED_ARCH}.zip"
  EMBED_ZIP="$ROOT_DIR/backend/.python-embed-${EMBED_VER}-${EMBED_ARCH}.zip"

  if [ ! -f "$EMBED_ZIP" ]; then
    "$BUILD_PY" - <<PY
import urllib.request
import zipfile
import os
url = "${EMBED_URL}"
out = "${EMBED_ZIP}"
urllib.request.urlretrieve(url, out)
if not zipfile.is_zipfile(out):
    try:
        with open(out, "rb") as f:
            head = f.read(160)
    except Exception:
        head = b""
    try:
        os.remove(out)
    except Exception:
        pass
    raise SystemExit(f"downloaded file is not a zip: {url}\\nhead={head!r}")
print(out)
PY
  fi

  rm -rf "$SCRIPT_DIR/python"
  mkdir -p "$SCRIPT_DIR/python"

  "$BUILD_PY" - <<PY
import zipfile
from pathlib import Path
z = Path(r"${EMBED_ZIP}")
out = Path(r"${SCRIPT_DIR}") / "python"
with zipfile.ZipFile(z, "r") as f:
    f.extractall(out)
print(str(out))
PY

  echo "built: $SCRIPT_DIR/spec_dep.pyz"
  echo "built: $SCRIPT_DIR/python/python.exe"
  echo "built: $SCRIPT_DIR/frontend/dist"
}

case "$TARGET" in
  macos-onefile) macos_onefile ;;
  windows-portable) windows_portable ;;
  *) echo "unknown target: $TARGET" && exit 2 ;;
esac
