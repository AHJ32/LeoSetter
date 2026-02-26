#!/usr/bin/env python3
"""
LeoSetter entry point.

When running as a frozen PyInstaller app, sys._MEIPASS is the temp directory
where all bundled files are extracted.  We add it to sys.path so that the
`leosetter` package can be imported.  All file-path resolution is done via
the _resource_path() helper in app.py — we do NOT chdir() here because that
would break the system file-open dialog's "current directory".
"""
import sys
import os
import logging

# ── Frozen-app path fix (PyInstaller onefile) ──────────────────────────────────
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS          # type: ignore[attr-defined]
    sys.path.insert(0, _base)
else:
    # Development: ensure project root is on path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

import customtkinter as ctk


def main():
    try:
        ctk.set_appearance_mode("System")      # "System" | "Dark" | "Light"
        ctk.set_default_color_theme("blue")    # placeholder; overridden in app.py

        from leosetter.app import App
        app = App()
        app.mainloop()
    except Exception:
        logging.exception("Failed to start LeoSetter:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
