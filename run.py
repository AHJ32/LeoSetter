#!/usr/bin/env python3
import sys
import os
import logging

# ── Frozen-app path fix (PyInstaller onefile) ──────────────────────────────────
# When running as a bundled EXE, sys._MEIPASS points to the temp directory where
# PyInstaller extracts everything. We add it to sys.path and change the working
# directory so that relative resource paths resolve correctly.
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS
    os.chdir(_base)
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
        ctk.set_default_color_theme("blue")    # "blue" | "green" | "dark-blue"

        from leosetter.app import App
        app = App()
        app.mainloop()
    except Exception:
        logging.exception("Failed to start LeoSetter:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
