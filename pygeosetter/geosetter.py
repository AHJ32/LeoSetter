#!/usr/bin/env python3
import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QWidget, QTabWidget,
                            QLineEdit, QDoubleSpinBox, QFormLayout, QMessageBox,
                            QGroupBox, QCheckBox, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen
import exifread
from PIL import Image, ImageQt, ImageDraw, ImageFont
import piexif
from datetime import datetime

class GeoSetterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyGeoSetter")
        self.setGeometry(100, 100, 1200, 800)
        self.current_file = None
        self.original_image = None
        self.current_image = None
        self.exif_data = {}
        self.templates = {}
        self.load_templates()
        self.init_ui()

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel for image preview
        left_panel = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(600, 400)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        left_panel.addWidget(self.image_label)

        # Right panel for controls
        right_panel = QVBoxLayout()
        
        # File controls
        file_group = QGroupBox("File")
        file_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        file_layout.addWidget(open_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_image)
        file_layout.addWidget(save_btn)
        
        file_group.setLayout(file_layout)
        right_panel.addWidget(file_group)

        # GPS Coordinates
        gps_group = QGroupBox("GPS Coordinates")
        gps_layout = QFormLayout()
        
        self.latitude = QDoubleSpinBox()
        self.latitude.setRange(-90, 90)
        self.latitude.setDecimals(6)
        gps_layout.addRow("Latitude:", self.latitude)
        
        self.longitude = QDoubleSpinBox()
        self.longitude.setRange(-180, 180)
        self.longitude.setDecimals(6)
        gps_layout.addRow("Longitude:", self.longitude)
        
        self.altitude = QDoubleSpinBox()
        self.altitude.setRange(-1000, 10000)
        self.altitude.setSuffix(" m")
        gps_layout.addRow("Altitude:", self.altitude)
        
        gps_group.setLayout(gps_layout)
        right_panel.addWidget(gps_group)

        # Templates
        template_group = QGroupBox("Templates")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("Select a template...")
        self.template_combo.addItems(self.templates.keys())
        template_layout.addWidget(self.template_combo)
        
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_template)
        btn_layout.addWidget(load_btn)
        
        save_as_btn = QPushButton("Save As...")
        save_as_btn.clicked.connect(self.save_as_template)
        btn_layout.addWidget(save_as_btn)
        
        template_layout.addLayout(btn_layout)
        template_group.setLayout(template_layout)
        right_panel.addWidget(template_group)
        
        # Add stretch to push everything to the top
        right_panel.addStretch()
        
        # Add panels to main layout
        layout.addLayout(left_panel, 2)
        layout.addLayout(right_panel, 1)

    def load_templates(self):
        templates_file = os.path.join(os.path.dirname(__file__), 'templates', 'locations.json')
        if os.path.exists(templates_file):
            try:
                with open(templates_file, 'r') as f:
                    self.templates = json.load(f)
            except Exception as e:
                print(f"Error loading templates: {e}")

    def save_templates(self):
        templates_file = os.path.join(os.path.dirname(__file__), 'templates', 'locations.json')
        try:
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=4)
        except Exception as e:
            print(f"Error saving templates: {e}")

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", 
            "Image Files (*.jpg *.jpeg *.tiff *.tif *.png)"
        )
        
        if file_path:
            self.current_file = file_path
            self.load_image(file_path)
            self.load_exif_data(file_path)

    def load_image(self, file_path):
        try:
            self.original_image = Image.open(file_path)
            self.current_image = self.original_image.copy()
            self.display_image()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")

    def display_image(self):
        if self.current_image:
            # Convert PIL Image to QPixmap
            qimage = ImageQt.ImageQt(self.current_image)
            pixmap = QPixmap.fromImage(qimage)
            
            # Scale the pixmap to fit the label while maintaining aspect ratio
            pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(pixmap)

    def load_exif_data(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                self.exif_data = {}
                
                for tag, value in tags.items():
                    if tag not in ('JPEGThumbnail', 'TIFFThumbnail'):
                        self.exif_data[tag] = str(value)
                
                # Extract GPS coordinates if available
                if 'GPS GPSLatitude' in self.exif_data:
                    lat = self.convert_to_degrees(self.exif_data['GPS GPSLatitude'])
                    if 'GPS GPSLatitudeRef' in self.exif_data and self.exif_data['GPS GPSLatitudeRef'] == 'S':
                        lat = -lat
                    self.latitude.setValue(lat)
                
                if 'GPS GPSLongitude' in self.exif_data:
                    lon = self.convert_to_degrees(self.exif_data['GPS GPSLongitude'])
                    if 'GPS GPSLongitudeRef' in self.exif_data and self.exif_data['GPS GPSLongitudeRef'] == 'W':
                        lon = -lon
                    self.longitude.setValue(lon)
                
                if 'GPS GPSAltitude' in self.exif_data:
                    try:
                        alt = float(self.exif_data['GPS GPSAltitude'].split()[0])
                        self.altitude.setValue(alt)
                    except (ValueError, IndexError):
                        pass
                        
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Could not read EXIF data: {str(e)}")

    def convert_to_degrees(self, value):
        # Convert GPS coordinates from DMS to decimal degrees
        try:
            parts = value.replace('[', '').replace(']', '').split(',')
            d = float(parts[0])
            m = float(parts[1])
            s = float(parts[2].split('/')[0]) / float(parts[2].split('/')[1])
            return d + (m / 60.0) + (s / 3600.0)
        except (ValueError, IndexError):
            return 0.0

    def save_image(self):
        if not self.current_file:
            QMessageBox.warning(self, "Error", "No file is currently open.")
            return
        
        try:
            # Create EXIF data
            exif_dict = {}
            
            # Add GPS data
            gps_ifd = {}
            
            # Latitude
            lat = self.latitude.value()
            lat_ref = 'N' if lat >= 0 else 'S'
            lat = abs(lat)
            lat_deg = int(lat)
            lat_min = int((lat - lat_deg) * 60)
            lat_sec = int(((lat - lat_deg - lat_min/60) * 3600) * 100) / 100
            gps_ifd[piexif.GPSIFD.GPSLatitude] = [(lat_deg, 1), (lat_min, 1), (int(lat_sec*100), 100)]
            gps_ifd[piexif.GPSIFD.GPSLatitudeRef] = lat_ref
            
            # Longitude
            lon = self.longitude.value()
            lon_ref = 'E' if lon >= 0 else 'W'
            lon = abs(lon)
            lon_deg = int(lon)
            lon_min = int((lon - lon_deg) * 60)
            lon_sec = int(((lon - lon_deg - lon_min/60) * 3600) * 100) / 100
            gps_ifd[piexif.GPSIFD.GPSLongitude] = [(lon_deg, 1), (lon_min, 1), (int(lon_sec*100), 100)]
            gps_ifd[piexif.GPSIFD.GPSLongitudeRef] = lon_ref
            
            # Altitude
            alt = self.altitude.value()
            gps_ifd[piexif.GPSIFD.GPSAltitude] = (int(alt * 100), 100)
            gps_ifd[piexif.GPSIFD.GPSAltitudeRef] = 0 if alt >= 0 else 1
            
            # Date/Time
            now = datetime.now()
            gps_date = now.strftime("%Y:%m:%d")
            gps_time = now.strftime("%H:%M:%S")
            gps_ifd[piexif.GPSIFD.GPSDateStamp] = gps_date
            gps_ifd[piexif.GPSIFD.GPSTimeStamp] = [(int(part), 1) for part in gps_time.split(':')]
            
            exif_dict["GPS"] = gps_ifd
            
            # Save the image with EXIF data
            exif_bytes = piexif.dump(exif_dict)
            
            # Create output filename
            base, ext = os.path.splitext(self.current_file)
            output_file = f"{base}_geotagged{ext}"
            
            # Save the image
            if self.current_image.mode in ('RGBA', 'LA'):
                self.current_image = self.current_image.convert('RGB')
            
            self.current_image.save(output_file, "JPEG", exif=exif_bytes, quality=95)
            
            QMessageBox.information(self, "Success", f"Image saved as {output_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")

    def load_template(self):
        template_name = self.template_combo.currentText()
        if template_name in self.templates:
            template = self.templates[template_name]
            if 'latitude' in template:
                self.latitude.setValue(template['latitude'])
            if 'longitude' in template:
                self.longitude.setValue(template['longitude'])
            if 'altitude' in template:
                self.altitude.setValue(template['altitude'])

    def save_as_template(self):
        name, ok = QInputDialog.getText(self, 'Save Location', 'Enter a name for this location:')
        if ok and name:
            self.templates[name] = {
                'latitude': self.latitude.value(),
                'longitude': self.longitude.value(),
                'altitude': self.altitude.value()
            }
            self.save_templates()
            # Update the template dropdown
            self.template_combo.clear()
            self.template_combo.addItem("Select a template...")
            self.template_combo.addItems(self.templates.keys())
            self.template_combo.setCurrentText(name)

def main():
    app = QApplication(sys.argv)
    window = GeoSetterApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
