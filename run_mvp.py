#!/usr/bin/env python3
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        app = QApplication(sys.argv)
        app.setApplicationName("PyGeoSetter MVP")
        app.setOrganizationName("PyGeoSetter")

        from mvp.app import MVPWindow
        win = MVPWindow()
        win.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.exception("Failed to start MVP:")
        QMessageBox.critical(None, "Fatal Error", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
