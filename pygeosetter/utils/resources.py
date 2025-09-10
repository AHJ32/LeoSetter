"""
Resource management for PyGeoSetter
"""
import os
import sys
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QDir, QFile, QFileInfo

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_icon(name):
    """Get an icon from the resources/icons directory"""
    icon_path = resource_path(os.path.join("resources", "icons", f"{name}.png"))
    if QFile.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()

def get_pixmap(name):
    """Get a pixmap from the resources/images directory"""
    pixmap_path = resource_path(os.path.join("resources", "images", f"{name}.png"))
    if QFile.exists(pixmap_path):
        return QPixmap(pixmap_path)
    return QPixmap()

def ensure_directory_exists(directory):
    """Ensure that a directory exists, creating it if necessary"""
    if not QDir(directory).exists():
        QDir().mkpath(directory)
    return directory

def get_app_data_dir():
    """Get the application data directory"""
    app_data_dir = os.path.join(os.path.expanduser('~'), '.pygeosetter')
    return ensure_directory_exists(app_data_dir)

def get_config_dir():
    """Get the configuration directory"""
    config_dir = os.path.join(get_app_data_dir(), 'config')
    return ensure_directory_exists(config_dir)

def get_cache_dir():
    """Get the cache directory"""
    cache_dir = os.path.join(get_app_data_dir(), 'cache')
    return ensure_directory_exists(cache_dir)

def get_templates_dir():
    """Get the templates directory"""
    templates_dir = os.path.join(get_app_data_dir(), 'templates')
    return ensure_directory_exists(templates_dir)

def get_plugin_dir():
    """Get the plugins directory"""
    plugin_dir = os.path.join(get_app_data_dir(), 'plugins')
    return ensure_directory_exists(plugin_dir)
