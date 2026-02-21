#!/usr/bin/env python3
import sys
import os
import logging
import customtkinter as ctk

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
        
        from mvp.app import App
        app = App()
        app.mainloop()
    except Exception as e:
        logging.exception("Failed to start MVP:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
