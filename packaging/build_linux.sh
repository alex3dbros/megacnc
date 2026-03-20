#!/usr/bin/env bash
# Build Mega CNC as a Linux onedir bundle (PyInstaller).
# Run on Linux (or WSL):  bash packaging/build_linux.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MEGACNC_ROOT="$ROOT"
cd "$ROOT"

echo "Project root: $ROOT"

if [[ ! -f manage.py ]]; then
  echo "manage.py not found" >&2
  exit 1
fi

if [[ ! -d .venv-build ]]; then
  python3 -m venv .venv-build
fi
PY="$ROOT/.venv-build/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt -r packaging/requirements-build.txt

rm -rf build dist/MegaCNC
"$PY" -m PyInstaller --noconfirm packaging/MegaCNC.spec

echo ""
echo "Done. Run:  ./dist/MegaCNC/MegaCNC"
echo "Distribute the entire dist/MegaCNC/ directory."
