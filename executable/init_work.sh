#!/usr/bin/env sh
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

WORK_DIR="work"

mkdir -p "$WORK_DIR/input"
mkdir -p "$WORK_DIR/input/req"
mkdir -p "$WORK_DIR/input/dependencies"
mkdir -p "$WORK_DIR/output"
mkdir -p "$WORK_DIR/logs"
mkdir -p "$WORK_DIR/uploads"

echo "Work directories are ready:"
echo "  $PWD/$WORK_DIR/input"
echo "  $PWD/$WORK_DIR/input/req"
echo "  $PWD/$WORK_DIR/input/dependencies"
echo "  $PWD/$WORK_DIR/output"
echo "  $PWD/$WORK_DIR/logs"
echo "  $PWD/$WORK_DIR/uploads"
