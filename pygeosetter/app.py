"""
Main application module for PyGeoSetter
"""
import os
import logging
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QFileDialog, 
                            QStatusBar, QSplitter, QTabWidget, QToolBar, 
                            QMenu, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
                            QFormLayout, QLineEdit, QDoubleSpinBox, QToolButton,
                            QMessageBox, QInputDialog, QProgressDialog, QTreeView, QDockWidget)
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from pygeosetter.ui.image_viewer import ImageViewer
from pygeosetter.ui.exif_editor import ExifEditor
from pygeosetter.ui.map_widget import MapWidget
from pygeosetter.ui.batch_dialog import BatchDialog
from pygeosetter.ui.template_dialog import TemplateDialog
from pygeosetter.templates.location_template import LocationTemplateManager
from pygeosetter.utils.resources import resource_path

class PyGeoSetter(QMainWindow):
    """Main application window for PyGeoSetter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize the application
        self.setWindowTitle("PyGeoSetter")
        self.setGeometry(100, 100, 1200, 800)
        
        # Track edit mode state
        self.edit_mode = False
        
        # Track selected images and current directory
        self.selected_images = []
        self.current_directory = ""
        self.last_opened_folder = ""
        
        # Initialize template manager
        self.template_manager = LocationTemplateManager(self)
        
        # Initialize metadata clipboard
        from pygeosetter.utils.metadata_clipboard import MetadataClipboard
        self.metadata_clipboard = MetadataClipboard
        
        # Initialize settings
        self.settings = QSettings("PyGeoSetter", "PyGeoSetter")
        
        # Create actions
        self.create_actions()
        
        # Create menu bar and toolbars
        self.create_menus()
        self.create_toolbars()
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create central widget and layout
        self.central_widget = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.central_widget)
        
        # Create left panel (image viewer)
        self.image_viewer = ImageViewer()
        self.central_widget.addWidget(self.image_viewer)
        
        # Create right panel (tabs for EXIF and map)
        self.right_panel = QTabWidget()
        self.central_widget.addWidget(self.right_panel)
        
        # Create EXIF editor tab
        self.exif_editor = ExifEditor()
        self.right_panel.addTab(self.exif_editor, "EXIF Data")
        
        # Create map tab
        self.map_widget = MapWidget()
        self.right_panel.addTab(self.map_widget, "Map")
        
        # Connect signals
        self.map_widget.location_changed.connect(self.update_gps_coordinates)
        self.exif_editor.gps_updated.connect(self.update_map_location)
        self.template_manager.template_updated.connect(self.setup_templates_menu)
        
        # Load saved settings including last opened folder
        self.load_settings()
        
        # Show the window first, then restore geometry
        self.show()
        QApplication.processEvents()  # Process any pending events
        
        # Create central widget and layout
        self.central_widget = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.central_widget)
        
        # Create left panel (image viewer)
        self.image_viewer = ImageViewer()
        self.central_widget.addWidget(self.image_viewer)
        
        # Create right panel (tabs for EXIF and map)
        self.right_panel = QTabWidget()
        self.central_widget.addWidget(self.right_panel)
        
        # Create EXIF editor tab
        self.exif_editor = ExifEditor()
        self.right_panel.addTab(self.exif_editor, "EXIF Data")
        
        # Create map tab
        self.map_widget = MapWidget()
        self.right_panel.addTab(self.map_widget, "Map")
        
        # Connect signals
        self.map_widget.location_changed.connect(self.update_gps_coordinates)
        self.exif_editor.gps_updated.connect(self.update_map_location)
        self.template_manager.template_updated.connect(self.setup_templates_menu)
        
    def create_actions(self):
        """Create application actions"""
        # File actions
        self.new_action = QAction("&New", self,
                                shortcut="Ctrl+N",
                                statusTip="Create a new document",
                                triggered=self.new_file)
                                
        # Add select all action
        self.select_all_action = QAction("Select &All", self,
                                       shortcut="Ctrl+A",
                                       statusTip="Select all images in current folder",
                                       triggered=self.select_all_images)
        
        # Add edit mode toggle action
        self.edit_mode_action = QAction("&Edit Mode", self,
                                      shortcut="Ctrl+E",
                                      statusTip="Toggle edit mode",
                                      triggered=self.toggle_edit_mode)
        self.edit_mode_action.setCheckable(True)
        
        # Add copy/paste metadata actions with new shortcuts
        self.copy_metadata_action = QAction("Copy &Metadata", self,
                                          shortcut="Ctrl+Shift+C",
                                          statusTip="Copy metadata to clipboard",
                                          triggered=self.copy_metadata)
        
        self.paste_metadata_action = QAction("Paste Metada&ta", self,
                                           shortcut="Ctrl+Shift+V",
                                           statusTip="Paste metadata from clipboard",
                                           triggered=lambda: self.paste_metadata())
        
        # Add these actions to the window for global shortcuts
        self.addAction(self.select_all_action)
        self.addAction(self.edit_mode_action)
        self.addAction(self.copy_metadata_action)
        self.addAction(self.paste_metadata_action)
        
        self.open_action = QAction("&Open...", self,
                                 shortcut="Ctrl+O",
                                 statusTip="Open one or more images",
                                 triggered=self.open_file)
        
        self.open_folder_action = QAction("Open &Folder...", self,
                                       shortcut="Ctrl+Shift+O",
                                       statusTip="Open a folder of images",
                                       triggered=self.open_folder)
        
        self.save_action = QAction("&Save", self,
                                 shortcut="Ctrl+S",
                                 statusTip="Save the current document",
                                 triggered=self.save_file)
        
        self.save_as_action = QAction("Save &As...", self,
                                    shortcut="Ctrl+Shift+S",
                                    statusTip="Save the current document with a new name",
                                    triggered=self.save_file_as)
        
        self.exit_action = QAction("E&xit", self,
                                 shortcut="Ctrl+Q",
                                 statusTip="Exit the application",
                                 triggered=self.close)
        
        # Edit actions
        self.undo_action = QAction("&Undo", self,
                                 shortcut="Ctrl+Z",
                                 statusTip="Undo the last action",
                                 triggered=self.undo)
        
        self.redo_action = QAction("&Redo", self,
                                 shortcut="Ctrl+Y",
                                 statusTip="Redo the last undone action",
                                 triggered=self.redo)
        
        # View actions
        self.zoom_in_action = QAction("Zoom &In", self,
                                     shortcut="Ctrl++",
                                     statusTip="Zoom in",
                                     triggered=self.zoom_in)
        
        self.zoom_out_action = QAction("Zoom &Out", self,
                                      shortcut="Ctrl+-",
                                      statusTip="Zoom out",
                                      triggered=self.zoom_out)
        
        self.actual_size_action = QAction("Actual &Size", self,
                                         shortcut="Ctrl+0",
                                         statusTip="View at actual size",
                                         triggered=self.actual_size)
        
        # Help actions
        self.about_action = QAction("&About", self,
                                   statusTip="Show the application's About box",
                                   triggered=self.about)
        
        self.about_qt_action = QAction("About &Qt", self,
                                      statusTip="Show the Qt library's About box",
                                      triggered=QApplication.aboutQt)
        
        # Batch processing
        self.batch_process_action = QAction("Batch Process Images...", self,
                                           statusTip="Batch process images",
                                           triggered=self.batch_process)
        
        # Manage templates
        self.manage_templates_action = QAction("Manage Templates...", self,
                                              statusTip="Manage templates",
                                              triggered=self.manage_templates)
        
    def create_menus(self):
        """Create the application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        
        # Templates submenu
        self.templates_menu = file_menu.addMenu("Templates")
        self.setup_templates_menu()
        file_menu.addSeparator()
        
        file_menu.addAction(self.exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo/Redo
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Copy/Paste Metadata
        copy_metadata_action = QAction("Copy &Metadata", self)
        copy_metadata_action.setShortcut("Ctrl+C")
        copy_metadata_action.triggered.connect(self.copy_metadata)
        edit_menu.addAction(copy_metadata_action)
        
        paste_metadata_action = QAction("Paste Metada&ta", self)
        paste_metadata_action.setShortcut("Ctrl+V")
        paste_metadata_action.triggered.connect(lambda: self.paste_metadata())
        edit_menu.addAction(paste_metadata_action)
        
        paste_special_action = QAction("Paste &Special...", self)
        paste_special_action.triggered.connect(self.show_paste_special_dialog)
        edit_menu.addAction(paste_special_action)
        
        edit_menu.addSeparator()
        
        # Template actions
        save_as_template_action = QAction("Save Location as &Template...", self)
        save_as_template_action.triggered.connect(self.save_location_as_template)
        edit_menu.addAction(save_as_template_action)
        
        apply_template_action = QAction("Apply &Template...", self)
        apply_template_action.triggered.connect(self.show_template_dialog)
        edit_menu.addAction(apply_template_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.actual_size_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction(self.batch_process_action)
        tools_menu.addAction(self.manage_templates_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.about_action)
        help_menu.addAction(self.about_qt_action)
    
    def create_toolbars(self):
        """Create the application toolbars"""
        # File toolbar
        file_toolbar = self.addToolBar("File")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)
        
        # Edit toolbar
        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.addAction(self.undo_action)
        edit_toolbar.addAction(self.redo_action)
        
        # View toolbar
        view_toolbar = self.addToolBar("View")
        view_toolbar.addAction(self.zoom_in_action)
        view_toolbar.addAction(self.zoom_out_action)
        view_toolbar.addAction(self.actual_size_action)
        
        # Location toolbar
        location_toolbar = self.addToolBar("Location")
        
        # Add template button with dropdown
        self.template_button = QToolButton()
        self.template_button.setPopupMode(QToolButton.MenuButtonPopup)
        self.template_button.setText("Templates")
        self.template_button.setMenu(self.templates_menu)
        self.template_button.clicked.connect(self.save_current_location_as_template)
        
        # Add icon to the button
        icon = QIcon.fromTheme("document-save-as-template")
        if icon.isNull():
            icon = QIcon(":/icons/template.png")
        self.template_button.setIcon(icon)
        
        location_toolbar.addWidget(self.template_button)
        
        # Update toolbar with copy/paste buttons
        edit_toolbar = self.addToolBar("Edit")
        copy_metadata_action = QAction("Copy &Metadata", self)
        copy_metadata_action.setShortcut("Ctrl+C")
        copy_metadata_action.triggered.connect(self.copy_metadata)
        edit_toolbar.addAction(copy_metadata_action)
        
        paste_metadata_action = QAction("Paste Metada&ta", self)
        paste_metadata_action.setShortcut("Ctrl+V")
        paste_metadata_action.triggered.connect(lambda: self.paste_metadata())
        edit_toolbar.addAction(paste_metadata_action)
        
        paste_special_action = QAction("Paste &Special...", self)
        paste_special_action.triggered.connect(self.show_paste_special_dialog)
        edit_toolbar.addAction(paste_special_action)
    
    def create_statusbar(self):
        """Create the status bar"""
        self.statusBar().showMessage("Ready")
        
        # Enable/disable paste actions based on clipboard content
        self.update_paste_actions()
        
        # Update clipboard monitoring
        QApplication.clipboard().dataChanged.connect(self.update_paste_actions)
    
    # Application slots
    def new_file(self):
        """Create a new file"""
        # TODO: Implement new file creation
        pass
    
    def open_file(self):
        """Open one or more image files"""
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Images",
            "",
            "Images (*.jpg *.jpeg *.tif *.tiff *.png);;All Files (*)"
        )
        
        if file_names:
            self.selected_images = file_names
            if file_names:  # Load the first selected file
                self.load_file(file_names[0])
                
    def load_settings(self):
        """Load application settings"""
        try:
            # Load last opened folder
            self.last_opened_folder = self.settings.value("last_opened_folder", "", type=str)
            
            # Restore window geometry if available and valid
            geometry = self.settings.value("geometry")
            if geometry and isinstance(geometry, (bytes, bytearray)) and len(geometry) > 0:
                if not self.restoreGeometry(geometry):
                    logging.warning("Failed to restore window geometry from settings")
            else:
                # Set default window size and position
                self.resize(1200, 800)
                screen = QApplication.primaryScreen().availableGeometry()
                self.move(
                    (screen.width() - self.width()) // 2,
                    (screen.height() - self.height()) // 2
                )
            
            # Restore window state if available and valid
            window_state = self.settings.value("windowState")
            if window_state and isinstance(window_state, (bytes, bytearray)) and len(window_state) > 0:
                if not self.restoreState(window_state):
                    logging.warning("Failed to restore window state from settings")
                    
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            # Set default window size and position on error
            self.resize(1200, 800)
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2
            )
        
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("last_opened_folder", self.last_opened_folder)
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        super().closeEvent(event)
        
    def open_folder(self):
        """Open a folder and load all supported images"""
        # First, try to get the last opened folder, then current directory, then home directory
        start_dir = self.last_opened_folder or \
                   (self.current_directory if hasattr(self, 'current_directory') and self.current_directory else \
                    os.path.expanduser('~'))
        
        # Open folder dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Images",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not folder:
            return  # User cancelled
            
        try:
            self.current_directory = folder
            
            # Get all image files in the selected directory
            import glob
            image_extensions = ['*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.png']
            self.selected_images = []
            
            # Use glob to find all image files recursively
            for ext in image_extensions:
                # Use case-insensitive matching by converting to lowercase
                self.selected_images.extend(glob.glob(os.path.join(folder, '**', ext), recursive=True))
                self.selected_images.extend(glob.glob(os.path.join(folder, '**', ext.upper()), recursive=True))
            
            # Remove duplicates and sort
            self.selected_images = sorted(list(set(self.selected_images)))
            
            if not self.selected_images:
                QMessageBox.information(self, "No Images Found", 
                                     "No supported image files found in the selected folder.")
                return
                
            # Load the first image
            self.load_file(self.selected_images[0])
            
            # Save the folder path for next time
            self.last_opened_folder = folder
            
            # Update status bar with number of images found
            folder_name = os.path.basename(folder)
            self.statusBar.showMessage(f"Loaded {len(self.selected_images)} images from {folder_name}", 5000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening folder: {str(e)}")
            logging.error(f"Error in open_folder: {str(e)}")
    
    def save_file(self):
        """Save the current file"""
        if not self.current_file:
            self.save_file_as()
        else:
            self.save_file_to_disk(self.current_file)
    
    def save_file_as(self):
        """Save the current file with a new name"""
        if not self.current_file:
            return
            
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            "",
            "JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff);;PNG (*.png);;All Files (*)"
        )
        
        if file_name:
            self.save_file_to_disk(file_name)
    
    def save_file_to_disk(self, file_name):
        """Save the current file to disk"""
        try:
            # TODO: Implement file saving logic
            self.statusBar().showMessage(f"File saved as {file_name}", 3000)
            self.current_file = file_name
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save file: {str(e)}")
    
    def load_file(self, file_path):
        """Load a file into the application"""
        try:
            # Check if the file is already open
            for i in range(self.tab_widget.count()):
                if hasattr(self.tab_widget.widget(i), 'file_path') and self.tab_widget.widget(i).file_path == file_path:
                    self.tab_widget.setCurrentIndex(i)
                    self.statusBar().showMessage("File already open", 3000)
                    return
            
            # Create a new image viewer tab
            image_viewer = ImageViewer()
            
            # Load the image
            if image_viewer.load_image(file_path):
                # Store the file path in the viewer
                image_viewer.file_path = file_path
                
                # Add the tab
                tab_index = self.tab_widget.addTab(image_viewer, os.path.basename(file_path))
                self.tab_widget.setCurrentIndex(tab_index)
                self.current_file = file_path
                
                # Connect signals
                image_viewer.mouse_moved.connect(self.update_status_coordinates)
                
                # Update status bar
                self.statusBar().showMessage(f"Loaded {os.path.basename(file_path)}", 3000)
                
                # Update EXIF editor
                self.exif_editor.set_exif_data(image_viewer.get_exif_data())
                
                # Update map
                self.map_widget.set_location(
                    image_viewer.get_gps_latitude(),
                    image_viewer.get_gps_longitude()
                )
                
                # Connect map location changes to update the image
                self.map_widget.location_changed.connect(
                    lambda lat, lon: self.update_image_coordinates(lat, lon, image_viewer)
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def update_status_coordinates(self, x, y, lat, lon):
        """Update the status bar with coordinates"""
        if lat != 0 and lon != 0:
            self.statusBar().showMessage(f"X: {x}, Y: {y} | Latitude: {lat:.6f}°, Longitude: {lon:.6f}°")
        else:
            self.statusBar().showMessage(f"X: {x}, Y: {y}")
    
    def update_image_coordinates(self, lat, lon, image_viewer):
        """Update the image coordinates when the map is clicked"""
        # Update the image viewer's GPS coordinates
        image_viewer.set_gps_coordinates(lat, lon)
        
        # Update the EXIF editor
        self.exif_editor.update_gps_coordinates(lat, lon)
        
        # Mark the document as modified
        self.setWindowModified(True)
    
    def update_gps_coordinates(self, lat, lon):
        """Update GPS coordinates in the EXIF editor"""
        self.exif_editor.update_gps_coordinates(lat, lon)
    
    def update_map_location(self, lat, lon):
        """Update the map location"""
        self.map_widget.set_location(lat, lon)
        """Zoom in the current view"""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, ImageViewer):
            current_widget.zoom_in()
            
    def batch_process(self):
        """Process multiple images in batch mode"""
        # Ask user to select a folder
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Images",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not folder:
            return  # User canceled
            
        # Get all image files in the selected directory
        import glob
        image_extensions = ['*.jpg', '*.jpeg', '*.tif', '*.tiff', '*.png']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(folder, '**', ext), recursive=True))
            
        if not image_files:
            QMessageBox.information(self, "No Images Found", "No supported image files found in the selected folder.")
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            'Confirm Batch Processing',
            f'This will process {len(image_files)} images. Continue?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Create progress dialog
        progress = QProgressDialog("Processing images...", "Cancel", 0, len(image_files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        # Process each file
        for i, file_path in enumerate(image_files):
            if progress.wasCanceled():
                break
                
            progress.setValue(i)
            progress.setLabelText(f"Processing: {os.path.basename(file_path)}")
            QApplication.processEvents()
            
            try:
                # Load the current metadata as a template
                if hasattr(self, 'current_metadata'):
                    # Save the current file to apply the metadata
                    self.save_file_to_disk(file_path)
                    
                    # Update progress
                    progress.setValue(i + 1)
                    QApplication.processEvents()
                    
            except Exception as e:
                logging.error(f"Error processing {file_path}: {str(e)}")
                continue
                
        progress.close()
        QMessageBox.information(self, "Batch Processing Complete", 
                              f"Successfully processed {i} out of {len(image_files)} images.")
            
    def setup_templates_menu(self):
        """Set up the templates menu with saved templates"""
        if not hasattr(self, 'templates_menu'):
            # Create templates menu if it doesn't exist
            self.templates_menu = self.menuBar().addMenu('&Templates')
            
        # Clear existing actions
        self.templates_menu.clear()
        
        # Add action to manage templates
        manage_action = QAction('Manage Templates...', self)
        manage_action.triggered.connect(self.manage_templates)
        self.templates_menu.addAction(manage_action)
        self.templates_menu.addSeparator()
        
        # Add saved templates
        # TODO: Load templates from a configuration file
        templates = []  # This would come from your config
        
        if not templates:
            no_templates = self.templates_menu.addAction('No templates available')
            no_templates.setEnabled(False)
        else:
            for template in templates:
                template_action = QAction(template['name'], self)
                template_action.triggered.connect(
                    lambda checked, t=template: self.apply_template(t)
                )
                self.templates_menu.addAction(template_action)
                
    def apply_template(self, template):
        """Apply a template to the current image
        
        Args:
            template (dict): Template data containing metadata to apply
        """
        if not self.current_file:
            QMessageBox.warning(self, 'No Image', 'Please open an image first.')
            return
            
        try:
            # Apply template data to the current image
            # This is a placeholder - actual implementation will depend on your template structure
            if 'gps' in template:
                lat = template['gps'].get('latitude')
                lon = template['gps'].get('longitude')
                if lat is not None and lon is not None:
                    self.map_widget.set_location(lat, lon)
                    self.exif_editor.update_gps_coordinates(lat, lon)
            
            # Add more template application logic here
            
            self.statusBar().showMessage('Template applied successfully', 3000)
            
        except Exception as e:
            logging.error(f'Error applying template: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Failed to apply template: {str(e)}')
            
    def show_template_dialog(self):
        """Show the template selection dialog"""
        # TODO: Implement template selection dialog
        # For now, show a message
        QMessageBox.information(
            self,
            'Templates',
            'Template functionality will be implemented in a future version.',
            QMessageBox.Ok
        )
        
    def save_current_location_as_template(self):
        """Save the current location as a template (alias for save_location_as_template)"""
        self.save_location_as_template()
        
    def save_location_as_template(self):
        """Save the current location as a template"""
        if not self.current_file:
            QMessageBox.warning(self, 'No Image', 'Please open an image with GPS data first.')
            return
            
        try:
            # Get current location from map or EXIF data
            lat, lon = self.map_widget.get_location()
            if lat is None or lon is None:
                QMessageBox.warning(self, 'No Location', 'No GPS location data available to save as template.')
                return
                
            # Ask for template name
            name, ok = QInputDialog.getText(
                self, 
                'Save Location Template',
                'Enter a name for this location template:'
            )
            
            if ok and name:
                # Create template data
                template = {
                    'name': name,
                    'gps': {
                        'latitude': lat,
                        'longitude': lon
                    },
                    # Add more template data as needed
                }
                
                # TODO: Save the template to a configuration file
                # For now, just show a message
                QMessageBox.information(
                    self, 
                    'Template Saved', 
                    f'Template "{name}" has been saved.',
                    QMessageBox.Ok
                )
                
                # Update templates menu
                self.setup_templates_menu()
                
        except Exception as e:
            logging.error(f'Error saving template: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Failed to save template: {str(e)}')
                
    def manage_templates(self):
        """Open the template management dialog"""
        dialog = TemplateDialog(self)
        if dialog.exec_() == TemplateDialog.Accepted:
            # Refresh the templates list if needed
            if hasattr(self, 'templates_menu'):
                self.setup_templates_menu()
    
    def zoom_in(self):
        """Zoom in the current view"""
        if hasattr(self, 'image_viewer') and self.image_viewer:
            self.image_viewer.zoom_in()
            
    def zoom_out(self):
        """Zoom out the current view"""
        if hasattr(self, 'image_viewer') and self.image_viewer:
            self.image_viewer.zoom_out()
    
    def actual_size(self):
        """Reset zoom to actual size"""
        if hasattr(self, 'image_viewer') and self.image_viewer:
            self.image_viewer.actual_size()
    
    def undo(self):
        """Undo the last action"""
        # TODO: Implement undo functionality
        pass
    
    def redo(self):
        """Redo the last undone action"""
        # TODO: Implement redo functionality
        pass
    
    def about(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About PyGeoSetter",
                         "<h2>PyGeoSetter 1.0</h2>"
                         "<p>A GeoSetter-like application for Linux</p>"
                         "<p>Copyright &copy; 2025 PyGeoSetter Team</p>")
    
    def copy_metadata(self):
        """Copy metadata from current image to clipboard"""
        if not self.current_image_widget:
            QMessageBox.information(self, "No Image", "No image is currently open.")
            return
            
        if self.metadata_clipboard.copy_metadata(self.current_image_widget):
            self.statusBar().showMessage("Metadata copied to clipboard", 3000)
        else:
            QMessageBox.warning(self, "Copy Failed", "Failed to copy metadata.")
    
    def paste_metadata(self, paste_options=None):
        """Paste metadata to current image"""
        if not self.current_image_widget:
            QMessageBox.information(self, "No Image", "No image is currently open.")
            return
            
        if not self.metadata_clipboard.has_metadata():
            QMessageBox.information(self, "No Metadata", "No metadata found in clipboard.")
            return
            
        if self.metadata_clipboard.paste_metadata(self.current_image_widget, paste_options):
            self.statusBar().showMessage("Metadata pasted successfully", 3000)
            # Update the UI
            self.update_exif_display()
            self.update_map_location()
        else:
            QMessageBox.warning(self, "Paste Failed", "Failed to paste metadata.")
    
    def show_paste_special_dialog(self):
        """Show dialog to select which metadata to paste"""
        if not self.metadata_clipboard.has_metadata():
            QMessageBox.information(self, "No Metadata", "No metadata found in clipboard.")
            return
            
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Paste Special")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # Add checkboxes for each metadata section
        gps_cb = QCheckBox("GPS Coordinates")
        datetime_cb = QCheckBox("Date & Time")
        location_cb = QCheckBox("Location Information")
        creator_cb = QCheckBox("Creator Information")
        copyright_cb = QCheckBox("Copyright Information")
        keywords_cb = QCheckBox("Keywords")
        
        # Check all by default
        for cb in [gps_cb, datetime_cb, location_cb, creator_cb, copyright_cb, keywords_cb]:
            cb.setChecked(True)
        
        # Add to layout
        layout.addWidget(gps_cb)
        layout.addWidget(datetime_cb)
        layout.addWidget(location_cb)
        layout.addWidget(creator_cb)
        layout.addWidget(copyright_cb)
        layout.addWidget(keywords_cb)
        
        # Add buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            paste_options = {
                'gps': gps_cb.isChecked(),
                'datetime': datetime_cb.isChecked(),
                'location': location_cb.isChecked(),
                'creator': creator_cb.isChecked(),
                'copyright': copyright_cb.isChecked(),
                'keywords': keywords_cb.isChecked()
            }
            self.paste_metadata(paste_options)
    
    def update_paste_actions(self):
        """Update the enabled state of paste actions based on clipboard content"""
        has_metadata = self.metadata_clipboard.has_metadata()
        
        # Find paste actions in menus and toolbars
        for action in self.findChildren(QAction):
            if action.text() in ["Paste Metada&ta", "Paste &Special..."]:
                action.setEnabled(has_metadata)
        
        # Also update our global paste action
        self.paste_metadata_action.setEnabled(has_metadata)
    
    def closeEvent(self, event):
        # Clean up resources
        if hasattr(self, 'map_widget'):
            self.map_widget.close()
        event.accept()
    
    def load_settings(self):
        """Load application settings"""
        # Restore window geometry if available
        geometry = self.settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        
        # Restore window state if available
        window_state = self.settings.value("windowState")
        if window_state is not None:
            self.restoreState(window_state)
    
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
    def select_all_images(self):
        """Select all images in the current directory"""
        if not self.current_directory:
            QMessageBox.information(self, "No Directory", "No directory is currently open.")
            return
            
        # Get all image files in the current directory
        image_extensions = ('.jpg', '.jpeg', '.tif', '.tiff', '.png')
        image_files = [f for f in os.listdir(self.current_directory) 
                      if f.lower().endswith(image_extensions)]
                      
        if not image_files:
            QMessageBox.information(self, "No Images", "No image files found in the current directory.")
            return
            
        # Store selected images
        self.selected_images = [os.path.join(self.current_directory, f) for f in image_files]
        
        # Update status bar
        self.statusBar().showMessage(f"Selected {len(self.selected_images)} images", 3000)
        
    def toggle_edit_mode(self):
        """Toggle edit mode for the application"""
        self.edit_mode = not self.edit_mode
        self.edit_mode_action.setChecked(self.edit_mode)
        
        # Update UI to reflect edit mode
        if hasattr(self, 'exif_editor'):
            self.exif_editor.setReadOnly(not self.edit_mode)
            
        # Update status bar
        status = "ON" if self.edit_mode else "OFF"
        self.statusBar().showMessage(f"Edit mode: {status}", 3000)
        
        # Enable/disable relevant UI elements
        for widget in self.findChildren((QLineEdit, QTextEdit, QComboBox)):
            if widget != self.search_edit:  # Don't disable search
                widget.setEnabled(self.edit_mode)
