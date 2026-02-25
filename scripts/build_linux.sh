#!/usr/bin/env bash
set -euo pipefail

# Build LeoSetter MVP executable for Linux using PyInstaller
# Usage: ./scripts/build_linux.sh [--onefile]

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

NAME="leosetter"
ENTRY="run.py"
ADDDATA=(
  "leosetter/templates/templates.json:leosetter/templates"
)

# Optionally bundle exiftool if present. This makes the app more self-contained.
# Requirements: perl must exist on the target system (usually true on Linux).
BUNDLE_FLAG="${BUNDLE_EXIFTOOL:-}"
if [[ -z "$BUNDLE_FLAG" && -x "/usr/bin/exiftool" ]]; then
  # Auto-enable if system exiftool exists
  BUNDLE_FLAG=1
fi

if [[ "${BUNDLE_FLAG}" == "1" ]]; then
  mkdir -p leosetter/tools
  if [[ -x "/usr/bin/exiftool" ]]; then
    cp -f /usr/bin/exiftool leosetter/tools/exiftool
    chmod +x leosetter/tools/exiftool
    echo "[i] Bundling /usr/bin/exiftool into the build"
  elif [[ -x "leosetter/tools/exiftool" ]]; then
    echo "[i] Found existing leosetter/tools/exiftool; bundling it"
  else
    echo "[!] BUNDLE_EXIFTOOL=1 requested, but exiftool not found. Skipping bundle."
    BUNDLE_FLAG=""
  fi
fi

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

# If bundling exiftool, add it as a binary to tools/
if [[ "${BUNDLE_FLAG}" == "1" && -f "leosetter/tools/exiftool" ]]; then
  FLAGS+=(--add-binary "leosetter/tools/exiftool:tools")
fi

# Clean previous build artifacts (keep spec file if it exists)
rm -rf build/ dist/ || true

# Use spec file if it exists, otherwise build from scratch
if [[ -f "leosetter.spec" ]]; then
  echo "[i] Using existing leosetter.spec file"
  "$PYI" leosetter.spec
else
  echo "[i] No leosetter.spec found, building from scratch"
  "$PYI" "${FLAGS[@]}" "$ENTRY"
fi

echo "[✓] Build complete. Artifacts in: dist/$NAME/ (or dist/$NAME if --onefile)."

# Helpful run hint
if [[ -f "dist/$NAME/$NAME" ]]; then
  echo "Run: ./dist/$NAME/$NAME"
elif [[ -f "dist/$NAME" ]]; then
  echo "Run: ./dist/$NAME"
fi
