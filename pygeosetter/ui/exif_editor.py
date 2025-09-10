"""
EXIF editor widget for PyGeoSetter
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                            QHeaderView, QLabel, QLineEdit, QComboBox, QPushButton,
                            QHBoxLayout, QDateTimeEdit, QDoubleSpinBox, QCheckBox,
                            QTabWidget, QFormLayout, QGroupBox, QSpinBox, QSplitter,
                            QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QDateTime, pyqtSignal
import exifread

class ExifEditor(QWidget):
    """Widget for viewing and editing EXIF data"""
    
    # Signal emitted when GPS coordinates are updated
    gps_updated = pyqtSignal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize UI
        self.init_ui()
        
        # EXIF data storage
        self.exif_data = {}
        
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.create_general_tab()
        self.create_gps_tab()
        self.create_camera_tab()
        self.create_advanced_tab()
        
        # Add tabs to the tab widget
        layout.addWidget(self.tab_widget)
        
        # Save button
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)
    
    def create_general_tab(self):
        """Create the General tab with basic EXIF information"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # File information group
        file_group = QGroupBox("File Information")
        file_layout = QFormLayout()
        
        self.filename_edit = QLineEdit()
        self.filename_edit.setReadOnly(True)
        file_layout.addRow("Filename:", self.filename_edit)
        
        self.filesize_edit = QLineEdit()
        self.filesize_edit.setReadOnly(True)
        file_layout.addRow("File size:", self.filesize_edit)
        
        self.filedate_edit = QDateTimeEdit()
        self.filedate_edit.setCalendarPopup(True)
        file_layout.addRow("File date:", self.filedate_edit)
        
        file_group.setLayout(file_layout)
        
        # Image information group
        image_group = QGroupBox("Image Information")
        image_layout = QFormLayout()
        
        self.width_edit = QLineEdit()
        self.width_edit.setReadOnly(True)
        image_layout.addRow("Width:", self.width_edit)
        
        self.height_edit = QLineEdit()
        self.height_edit.setReadOnly(True)
        image_layout.addRow("Height:", self.height_edit)
        
        self.depth_edit = QLineEdit()
        self.depth_edit.setReadOnly(True)
        image_layout.addRow("Color depth:", self.depth_edit)
        
        self.resolution_edit = QLineEdit()
        self.resolution_edit.setReadOnly(True)
        image_layout.addRow("Resolution:", self.resolution_edit)
        
        image_group.setLayout(image_layout)
        
        # Add groups to tab layout
        layout.addWidget(file_group)
        layout.addWidget(image_group)
        
        # Add a spacer to push content to the top
        from PyQt5.QtWidgets import QSpacerItem, QSizePolicy
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)
        
        # Add tab to tab widget
        self.tab_widget.addTab(tab, "General")
    
    def create_gps_tab(self):
        """Create the GPS tab with location information"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)  # Main layout for the tab
        
        # GPS coordinates group
        coords_group = QGroupBox("GPS Coordinates")
        coords_layout = QFormLayout()
        
        # Latitude
        lat_layout = QHBoxLayout()
        self.lat_degrees = QDoubleSpinBox()
        self.lat_degrees.setRange(-90, 90)
        self.lat_degrees.setDecimals(6)
        self.lat_direction = QComboBox()
        self.lat_direction.addItems(["N", "S"])
        lat_layout.addWidget(self.lat_degrees)
        lat_layout.addWidget(self.lat_direction)
        coords_layout.addRow("Latitude:", lat_layout)
        
        # Longitude
        lon_layout = QHBoxLayout()
        self.lon_degrees = QDoubleSpinBox()
        self.lon_degrees.setRange(-180, 180)
        self.lon_degrees.setDecimals(6)
        self.lon_direction = QComboBox()
        self.lon_direction.addItems(["E", "W"])
        lon_layout.addWidget(self.lon_degrees)
        lon_layout.addWidget(self.lon_direction)
        coords_layout.addRow("Longitude:", lon_layout)
        
        # Altitude
        self.altitude_edit = QDoubleSpinBox()
        self.altitude_edit.setRange(-1000, 10000)
        self.altitude_edit.setSuffix(" m")
        coords_layout.addRow("Altitude:", self.altitude_edit)
        
        # Map link button
        self.map_button = QPushButton("Show on Map")
        self.map_button.clicked.connect(self.show_on_map)
        coords_layout.addRow(self.map_button)
        
        coords_group.setLayout(coords_layout)
        
        # GPS details group
        details_group = QGroupBox("GPS Details")
        details_layout = QFormLayout()
        
        self.gps_date_edit = QDateTimeEdit()
        self.gps_date_edit.setCalendarPopup(True)
        details_layout.addRow("GPS Date/Time:", self.gps_date_edit)
        
        self.gps_status_edit = QLineEdit()
        details_layout.addRow("GPS Status:", self.gps_status_edit)
        
        self.gps_measure_mode_edit = QLineEdit()
        details_layout.addRow("Measure Mode:", self.gps_measure_mode_edit)
        
        self.gps_dop_edit = QDoubleSpinBox()
        self.gps_dop_edit.setDecimals(2)
        details_layout.addRow("Dilution of Precision:", self.gps_dop_edit)
        
        details_group.setLayout(details_layout)
        
        # Add groups to main layout
        main_layout.addWidget(coords_group)
        main_layout.addWidget(details_group)
        
        # Add a spacer to push content to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)
        
        # Add tab to tab widget
        self.tab_widget.addTab(tab, "GPS")
    
    def create_camera_tab(self):
        """Create the Camera tab with camera settings"""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)  # Main layout for the tab
        
        # Camera information group
        camera_group = QGroupBox("Camera Information")
        camera_layout = QFormLayout()
        
        self.make_edit = QLineEdit()
        camera_layout.addRow("Make:", self.make_edit)
        
        self.model_edit = QLineEdit()
        camera_layout.addRow("Model:", self.model_edit)
        
        self.serial_edit = QLineEdit()
        camera_layout.addRow("Serial Number:", self.serial_edit)
        
        self.software_edit = QLineEdit()
        camera_layout.addRow("Software:", self.software_edit)
        
        camera_group.setLayout(camera_layout)
        
        # Exposure settings group
        exposure_group = QGroupBox("Exposure Settings")
        exposure_layout = QFormLayout()
        
        self.aperture_edit = QDoubleSpinBox()
        self.aperture_edit.setRange(0.7, 32)
        self.aperture_edit.setDecimals(1)
        exposure_layout.addRow("Aperture (f/):", self.aperture_edit)
        
        self.shutter_speed_edit = QLineEdit()
        exposure_layout.addRow("Shutter Speed:", self.shutter_speed_edit)
        
        self.iso_edit = QSpinBox()
        self.iso_edit.setRange(1, 1000000)
        exposure_layout.addRow("ISO:", self.iso_edit)
        
        self.exposure_bias_edit = QDoubleSpinBox()
        self.exposure_bias_edit.setRange(-5, 5)
        self.exposure_bias_edit.setSingleStep(0.3)
        exposure_layout.addRow("Exposure Bias (EV):", self.exposure_bias_edit)
        
        exposure_group.setLayout(exposure_layout)
        
        # Add groups to main layout
        main_layout.addWidget(camera_group)
        main_layout.addWidget(exposure_group)
        
        # Add a spacer to push content to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)
        
        # Add tab to tab widget
        self.tab_widget.addTab(tab, "Camera")
    
    def create_advanced_tab(self):
        """Create the Advanced tab with raw EXIF data"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Raw EXIF data tree
        self.exif_tree = QTreeWidget()
        self.exif_tree.setHeaderLabels(["Tag", "Value"])
        self.exif_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        layout.addWidget(self.exif_tree)
        
        # Add tab to tab widget
        self.tab_widget.addTab(tab, "Advanced")
    
    def set_exif_data(self, exif_data):
        """Set the EXIF data to display"""
        if not exif_data:
            return
            
        self.exif_data = exif_data
        self.update_ui()
    
    def update_ui(self):
        """Update the UI with the current EXIF data"""
        if not self.exif_data:
            return
        
        # Update general tab
        if 'Image Make' in self.exif_data:
            self.make_edit.setText(str(self.exif_data['Image Make']))
        if 'Image Model' in self.exif_data:
            self.model_edit.setText(str(self.exif_data['Image Model']))
        
        # Update GPS tab
        if 'GPS GPSLatitude' in self.exif_data and 'GPS GPSLatitudeRef' in self.exif_data:
            lat = self._convert_to_degrees(self.exif_data['GPS GPSLatitude'].values)
            if self.exif_data['GPS GPSLatitudeRef'].values == 'S':
                self.lat_direction.setCurrentText("S")
                lat = -lat
            else:
                self.lat_direction.setCurrentText("N")
            self.lat_degrees.setValue(lat)
        
        if 'GPS GPSLongitude' in self.exif_data and 'GPS GPSLongitudeRef' in self.exif_data:
            lon = self._convert_to_degrees(self.exif_data['GPS GPSLongitude'].values)
            if self.exif_data['GPS GPSLongitudeRef'].values == 'W':
                self.lon_direction.setCurrentText("W")
                lon = -lon
            else:
                self.lon_direction.setCurrentText("E")
            self.lon_degrees.setValue(lon)
        
        if 'GPS GPSAltitude' in self.exif_data:
            try:
                alt = float(self.exif_data['GPS GPSAltitude'].values[0])
                self.altitude_edit.setValue(alt)
            except (ValueError, IndexError):
                pass
        
        # Update advanced tab
        self.exif_tree.clear()
        for tag, value in self.exif_data.items():
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail'):
                item = QTreeWidgetItem([tag, str(value)])
                self.exif_tree.addTopLevelItem(item)
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to decimal degrees"""
        d, m, s = value
        d = float(d.num) / float(d.den)
        m = float(m.num) / float(m.den)
        s = float(s.num) / float(s.den)
        return d + (m / 60.0) + (s / 3600.0)
    
    def show_on_map(self):
        """Show the current location on a map"""
        lat = self.lat_degrees.value()
        lon = self.lon_degrees.value()
        
        if lat != 0.0 or lon != 0.0:
            url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15"
            import webbrowser
            webbrowser.open(url)
    
    def save_changes(self):
        """Save changes to the EXIF data"""
        # TODO: Implement saving changes to EXIF data
        pass
