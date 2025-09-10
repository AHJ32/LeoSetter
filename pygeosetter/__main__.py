#!/usr/bin/env python3
"""
PyGeoSetter - A GeoSetter-like application for Linux
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pygeosetter.app import PyGeoSetter
from pygeosetter.utils.logger import setup_logging

def main():
    # Setup logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PyGeoSetter")
    app.setOrganizationName("PyGeoSetter")
    app.setApplicationVersion("1.0.0")
    
    # Show splash screen
    splash_pix = QPixmap(":/splash.png")
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    
    # Create and show main window
    window = PyGeoSetter()
    window.show()
    
    # Close splash screen
    splash.finish(window)
    
    # Start application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
