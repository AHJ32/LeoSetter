# Building Executables (Linux and Windows)

This guide explains how to build standalone executables for LeoSetter using PyInstaller.

The entry point is `run.py` which launches `leosetter/app.py`.

## Requirements

- Python 3.10+
- A virtual environment (recommended)
- Dependencies installed from `requirements.txt`
- PyInstaller (installed by the build scripts)
- exiftool
  - Linux: `sudo apt install -y exiftool`
  - Windows: Download from https://exiftool.org/ (optional if bundling exiftool)

## Bundled exiftool (optional)

`leosetter/exif_backend.py` auto-detects a bundled exiftool at runtime when packaged.

Search order:
1. PyInstaller `_MEIPASS`-based `tools/exiftool.exe` (Windows) or `tools/exiftool` (Linux)
2. `leosetter/tools/exiftool(.exe)` next to the module (for dev)
3. System `exiftool` on PATH

To bundle exiftool, place it at:
- Windows: `tools/exiftool.exe` and add `--add-binary "tools\\exiftool.exe;tools"` to your PyInstaller flags
- Linux: `tools/exiftool` and add `--add-binary "tools/exiftool:tools"`

Note: The provided scripts do not bundle exiftool by default; they rely on the system install.

## Quick Start (Linux)

```
# From repository root
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh            # folder build
./scripts/build_linux.sh --onefile  # single-file build
```

Artifacts will be created under `dist/leosetter/` (folder build) or `dist/leosetter` (onefile).

Run it:
```
./dist/leosetter/leosetter   # folder build
# or
./dist/leosetter                 # onefile build
```

## Quick Start (Windows)

```
REM From repository root
scripts\build_windows.bat              REM folder build
scripts\build_windows.bat --onefile    REM single-file build
```

Artifacts will be in `dist\leosetter\` (folder build) or `dist\leosetter.exe` (onefile).

## Adding icons (optional)

- Windows: `--icon path\to\app.ico`
- Linux: `--icon path/to/app.png`

## Adding resources

If you add static resources, include them via `--add-data` flags. Examples already present:
- `leosetter/templates/templates.json:leosetter/templates`

Windows uses `src;dest` while Linux uses `src:dest`.

## Troubleshooting

- PyQtWebEngine sandboxing on Linux: if running in restricted environments, you may need to set
  `QTWEBENGINE_DISABLE_SANDBOX=1` before launching.
- Missing OpenGL context: the app sets `Qt.AA_ShareOpenGLContexts` before creating the app.
- If the map widget is blank, ensure network access is available (Leaflet tiles are loaded from OSM).
- If metadata fails to write, ensure `exiftool` is installed and accessible.
