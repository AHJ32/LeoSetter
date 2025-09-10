#!/usr/bin/env bash
set -euo pipefail

# Build GeoSetter MVP executable for Linux using PyInstaller
# Usage: ./scripts/build_mvp_linux.sh [--onefile]

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

VENV="${HERE}/venv"
PY="$VENV/bin/python3"
PIP="$VENV/bin/pip"
PYI="$VENV/bin/pyinstaller"

if [[ ! -x "$PY" ]]; then
  echo "[i] Creating virtualenv at $VENV"
  python3 -m venv "$VENV"
fi

# Upgrade basic tooling and ensure PyInstaller is available
"$PIP" install --upgrade pip setuptools wheel >/dev/null
"$PIP" install pyinstaller >/dev/null

NAME="geosetter-mvp"
ENTRY="run_mvp.py"
ADDDATA=(
  "mvp/templates/templates.json:mvp/templates"
)

# Compose --add-data flags for Linux (src:dest)
ADD_FLAGS=()
for pair in "${ADDDATA[@]}"; do
  ADD_FLAGS+=(--add-data "$pair")
done

FLAGS=(
  --name "$NAME"
  --noconsole
  --clean
  "${ADD_FLAGS[@]}"
)

if [[ "${1:-}" == "--onefile" ]]; then
  FLAGS+=(--onefile)
fi

# Clean previous build artifacts
rm -rf build/ dist/ "$NAME.spec" || true

"$PYI" "${FLAGS[@]}" "$ENTRY"

echo "[✓] Build complete. Artifacts in: dist/$NAME/ (or dist/$NAME if --onefile)."

# Helpful run hint
if [[ -f "dist/$NAME/$NAME" ]]; then
  echo "Run: ./dist/$NAME/$NAME"
elif [[ -f "dist/$NAME" ]]; then
  echo "Run: ./dist/$NAME"
fi
