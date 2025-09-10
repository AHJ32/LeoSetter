"""
Batch processing dialog for PyGeoSetter
"""
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QPushButton, QFileDialog, QLabel, QProgressBar,
                            QMessageBox, QCheckBox, QGroupBox, QFormLayout,
                            QSpinBox, QDoubleSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import exifread
import piexif
from PIL import Image
from pygeosetter.utils.metadata_clipboard import MetadataClipboard

class BatchProcessor(QThread):
    """Worker thread for batch processing images"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, file_paths, settings, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.settings = settings
        self.is_running = True
    
    def run(self):
        """Process the batch of images"""
        total = len(self.file_paths)
        for i, file_path in enumerate(self.file_paths):
            if not self.is_running:
                break
                
            try:
                self.status.emit(f"Processing {os.path.basename(file_path)}...")
                self._process_image(file_path)
                self.progress.emit(int((i + 1) / total * 100))
            except Exception as e:
                self.error.emit(f"Error processing {file_path}: {str(e)}")
        
        self.finished_signal.emit()
    
    def _process_image(self, file_path):
        """Process a single image with the given settings"""
        # Create output filename
        if self.settings['output_dir']:
            output_dir = self.settings['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(file_path))
        else:
            base, ext = os.path.splitext(file_path)
            output_path = f"{base}_geotagged{ext}"
        
        # Read the image
        img = Image.open(file_path)
        
        # Initialize EXIF data
        exif_dict = {}
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict['0th'] = {}
            exif_dict['Exif'] = {}
            exif_dict['GPS'] = {}
        
        # Apply settings
        if self.settings['update_gps']:
            self._update_gps_data(exif_dict)
        
        if self.settings['update_datetime']:
            self._update_datetime(exif_dict)
        
        # Save the image with updated EXIF
        if img.mode in ('RGBA', 'LA'):
            img = img.convert('RGB')
        
        exif_bytes = piexif.dump(exif_dict)
        img.save(output_path, "JPEG", exif=exif_bytes, quality=95)
    
    def _update_gps_data(self, exif_dict):
        """Update GPS data in EXIF"""
        if 'GPS' not in exif_dict:
            exif_dict['GPS'] = {}
        
        gps = exif_dict['GPS']
        
        # Set latitude
        if 'latitude' in self.settings and self.settings['latitude'] is not None:
            lat = abs(self.settings['latitude'])
            lat_ref = 'S' if self.settings['latitude'] < 0 else 'N'
            
            # Convert to degrees, minutes, seconds
            d = int(lat)
            m = int((lat - d) * 60)
            s = int(((lat - d - m/60) * 3600) * 100) / 100
            
            gps[piexif.GPSIFD.GPSLatitude] = [(d, 1), (m, 1), (int(s*100), 100)]
            gps[piexif.GPSIFD.GPSLatitudeRef] = lat_ref
        
        # Set longitude
        if 'longitude' in self.settings and self.settings['longitude'] is not None:
            lon = abs(self.settings['longitude'])
            lon_ref = 'W' if self.settings['longitude'] < 0 else 'E'
            
            # Convert to degrees, minutes, seconds
            d = int(lon)
            m = int((lon - d) * 60)
            s = int(((lon - d - m/60) * 3600) * 100) / 100
            
            gps[piexif.GPSIFD.GPSLongitude] = [(d, 1), (m, 1), (int(s*100), 100)]
            gps[piexif.GPSIFD.GPSLongitudeRef] = lon_ref
        
        # Set altitude
        if 'altitude' in self.settings and self.settings['altitude'] is not None:
            gps[piexif.GPSIFD.GPSAltitude] = (int(self.settings['altitude'] * 100), 100)
            gps[piexif.GPSIFD.GPSAltitudeRef] = 0 if self.settings['altitude'] >= 0 else 1
    
    def _update_datetime(self, exif_dict):
        """Update date/time in EXIF"""
        if 'datetime' in self.settings and self.settings['datetime']:
            dt = self.settings['datetime'].toString("yyyy:MM:dd hh:mm:ss")
            exif_dict['0th'][piexif.ImageIFD.DateTime] = dt
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dt
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = dt
    
    def stop(self):
        """Stop the batch processing"""
        self.is_running = False


class BatchDialog(QDialog):
    """Dialog for batch processing images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Batch Process Images")
        
        # Initialize metadata clipboard
        self.metadata_clipboard = MetadataClipboard()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Batch Process Images")
        self.setMinimumSize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Files")
        self.add_btn.clicked.connect(self.add_files)
        
        self.add_dir_btn = QPushButton("Add Folder")
        self.add_dir_btn.clicked.connect(self.add_folder)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected)
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.file_list.clear)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.add_dir_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        
        # Options group
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        
        # GPS options
        gps_group = QGroupBox("GPS Data")
        gps_layout = QFormLayout()
        
        self.update_gps_cb = QCheckBox("Update GPS data")
        self.update_gps_cb.setChecked(True)
        
        self.lat_edit = QDoubleSpinBox()
        self.lat_edit.setRange(-90, 90)
        self.lat_edit.setDecimals(6)
        self.lat_edit.setSuffix("°")
        
        self.lon_edit = QDoubleSpinBox()
        self.lon_edit.setRange(-180, 180)
        self.lon_edit.setDecimals(6)
        self.lon_edit.setSuffix("°")
        
        self.alt_edit = QDoubleSpinBox()
        self.alt_edit.setRange(-1000, 10000)
        self.alt_edit.setSuffix(" m")
        
        gps_layout.addRow(self.update_gps_cb)
        gps_layout.addRow("Latitude:", self.lat_edit)
        gps_layout.addRow("Longitude:", self.lon_edit)
        gps_layout.addRow("Altitude:", self.alt_edit)
        
        # Use current map position if available
        if hasattr(self.parent, 'map_widget'):
            lat, lon = self.parent.map_widget.get_location()
            if lat is not None and lon is not None:
                self.lat_edit.setValue(lat)
                self.lon_edit.setValue(lon)
        
        gps_group.setLayout(gps_layout)
        
        # Date/Time options
        dt_group = QGroupBox("Date/Time")
        dt_layout = QVBoxLayout()
        
        self.update_dt_cb = QCheckBox("Update date/time")
        self.update_dt_cb.setChecked(False)
        
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setDateTime(self.dt_edit.dateTime().currentDateTime())
        
        dt_layout.addWidget(self.update_dt_cb)
        dt_layout.addWidget(self.dt_edit)
        dt_group.setLayout(dt_layout)
        
        # Output options
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Leave empty to save in same folder")
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.select_output_dir)
        
        output_layout.addWidget(QLabel("Output directory:"))
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.browse_btn)
        output_group.setLayout(output_layout)
        
        # Add all option groups to the layout
        options_layout.addWidget(gps_group)
        options_layout.addWidget(dt_group)
        options_layout.addWidget(output_group)
        options_group.setLayout(options_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        
        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add action buttons
        self.copy_btn = QPushButton("Copy Metadata")
        self.copy_btn.clicked.connect(self.copy_metadata)
        self.copy_btn.setEnabled(False)
        
        self.paste_btn = QPushButton("Paste to All")
        self.paste_btn.clicked.connect(self.paste_metadata_to_all)
        self.paste_btn.setEnabled(False)
        
        # Add process button
        self.process_btn = button_box.addButton("Process", QDialogButtonBox.ActionRole)
        self.process_btn.clicked.connect(self.process_images)
        self.process_btn.setEnabled(False)
        
        # Add buttons to layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.paste_btn)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        # Update main layout to use the button layout
        layout.addWidget(QLabel("Files to process:"))
        layout.addWidget(self.file_list)
        layout.addLayout(btn_layout)
        layout.addWidget(options_group)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
    
    def add_files(self):
        """Add files to the batch"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", 
            "Images (*.jpg *.jpeg *.tif *.tiff);;All Files (*)"
        )
        
        if files:
            self.file_list.addItems(files)
            self.update_ui_state()
    
    def add_folder(self):
        """Add a folder of images to the batch"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        
        if folder:
            import os
            from glob import glob
            
            # Get all image files in the folder
            extensions = ('*.jpg', '*.jpeg', '*.tif', '*.tiff')
            files = []
            for ext in extensions:
                files.extend(glob(os.path.join(folder, ext)))
                files.extend(glob(os.path.join(folder, ext.upper())))
            
            if files:
                self.file_list.addItems(files)
                self.update_ui_state()
    
    def remove_selected(self):
        """Remove selected files from the batch"""
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        self.update_ui_state()
    
    def select_output_dir(self):
        """Select output directory for processed files"""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_edit.setText(directory)
    
    def clear_list(self):
        """Clear all files from the batch"""
        self.file_list.clear()
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update the UI state based on the current selection"""
        has_items = self.file_list.count() > 0
        has_selection = len(self.file_list.selectedItems()) > 0
        
        self.process_btn.setEnabled(has_items)
        self.copy_btn.setEnabled(has_selection)
        self.paste_btn.setEnabled(has_items and self.metadata_clipboard.has_metadata())
    
    def copy_metadata(self):
        """Copy metadata from the first selected image"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        self.clear_btn.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)
        self.update_gps_cb.setEnabled(enabled)
        self.lat_edit.setEnabled(enabled)
        self.lon_edit.setEnabled(enabled)
        self.alt_edit.setEnabled(enabled)
        self.update_dt_cb.setEnabled(enabled)
        self.dt_edit.setEnabled(enabled)
        self.output_dir_edit.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, 'Processing in Progress',
                'Processing is still in progress. Are you sure you want to cancel?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
