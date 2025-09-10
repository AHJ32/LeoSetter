#!/usr/bin/env python3
"""
Simple script to run PyGeoSetter with minimal configuration
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication

# Set up basic logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(
        None,
        "Unexpected Error",
        f"An unexpected error occurred:\n\n{str(exc_value)}\n\nCheck the logs for more details."
    )

# Set the exception handler
sys.excepthook = handle_exception

def main():
    try:
        # Set required attributes before creating the application
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        
        # Create application
        app = QApplication(sys.argv)
        app.setApplicationName("PyGeoSetter")
        app.setOrganizationName("PyGeoSetter")
        
        # Import after setting up the application
        from pygeosetter.app import PyGeoSetter
        
        # Create and show main window
        logger.info("Creating main window...")
        window = PyGeoSetter()
        window.show()
        logger.info("Application started successfully")
        
        # Start application
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.exception("Fatal error in main:")
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Failed to start application:\n\n{str(e)}\n\nCheck the logs for more details."
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
