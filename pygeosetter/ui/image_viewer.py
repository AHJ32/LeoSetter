"""
Image viewer widget for PyGeoSetter
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel, 
                            QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QMouseEvent
import exifread
from PIL import Image, ImageQt

class ImageViewer(QGraphicsView):
    """Image viewer with zoom and pan functionality"""
    
    # Signals
    mouse_moved = pyqtSignal(int, int, float, float)  # x, y, lat, lon
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Image properties
        self._pixmap = None
        self._image_item = None
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        
        # Set up the view
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setBackgroundBrush(self.palette().color(self.backgroundRole()))
        self.setFrameShape(QGraphicsView.NoFrame)
        
        # Initialize EXIF data
        self.exif_data = {}
        self.gps_latitude = None
        self.gps_longitude = None
        self.gps_altitude = None
        
        # Mouse tracking
        self.setMouseTracking(True)
        self._pan = False
        self._pan_start = QPoint()
        
    def has_image(self):
        """Check if the viewer has an image loaded"""
        return not self._empty
    
    def load_image(self, file_path):
        """Load an image from file"""
        try:
            # Load image with PIL first to handle orientation
            pil_image = Image.open(file_path)
            
            # Read EXIF data
            with open(file_path, 'rb') as f:
                self.exif_data = exifread.process_file(f, details=False)
                self._extract_gps_info()
            
            # Convert to QPixmap
            qimage = ImageQt.ImageQt(pil_image)
            self._pixmap = QPixmap.fromImage(qimage)
            
            # Set the scene
            self._photo.setPixmap(self._pixmap)
            self._empty = False
            self.fitInView()
            
            return True
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            return False
    
    def _extract_gps_info(self):
        """Extract GPS information from EXIF data"""
        if 'GPS GPSLatitude' in self.exif_data and 'GPS GPSLatitudeRef' in self.exif_data:
            lat = self._convert_to_degrees(self.exif_data['GPS GPSLatitude'].values)
            if self.exif_data['GPS GPSLatitudeRef'].values != 'N':
                lat = -lat
            self.gps_latitude = lat
            
        if 'GPS GPSLongitude' in self.exif_data and 'GPS GPSLongitudeRef' in self.exif_data:
            lon = self._convert_to_degrees(self.exif_data['GPS GPSLongitude'].values)
            if self.exif_data['GPS GPSLongitudeRef'].values != 'E':
                lon = -lon
            self.gps_longitude = lon
            
        if 'GPS GPSAltitude' in self.exif_data:
            try:
                self.gps_altitude = float(self.exif_data['GPS GPSAltitude'].values[0])
            except (ValueError, IndexError):
                self.gps_altitude = None
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to decimal degrees"""
        d, m, s = value
        d = float(d.num) / float(d.den)
        m = float(m.num) / float(m.den)
        s = float(s.num) / float(s.den)
        return d + (m / 60.0) + (s / 3600.0)
    
    def get_exif_data(self):
        """Get the EXIF data"""
        return self.exif_data
    
    def get_gps_latitude(self):
        """Get the GPS latitude"""
        return self.gps_latitude
    
    def get_gps_longitude(self):
        """Get the GPS longitude"""
        return self.gps_longitude
    
    def get_gps_altitude(self):
        """Get the GPS altitude"""
        return self.gps_altitude
    
    def fitInView(self, scale=True):
        """Scale the view to fit the image"""
        if not self._pixmap:
            return
            
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.has_image():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                view_rect = self.viewport().rect()
                scene_rect = self.transform().mapRect(rect)
                factor = min(view_rect.width() / scene_rect.width(),
                            view_rect.height() / scene_rect.height())
                self.scale(factor, factor)
            self._zoom = 0
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if self.has_image():
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self._pan = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            # Emit mouse position with GPS coordinates if available
            pos = self.mapToScene(event.pos())
            lat = self.gps_latitude if self.gps_latitude else 0
            lon = self.gps_longitude if self.gps_longitude else 0
            self.mouse_moved.emit(int(pos.x()), int(pos.y()), lat, lon)
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning"""
        if self._pan and self._pan_start is not None:
            delta = self.mapToScene(self._pan_start) - self.mapToScene(event.pos())
            self._pan_start = event.pos()
            self.setSceneRect(self.sceneRect().translated(delta.x(), delta.y()))
        
        # Emit mouse position with GPS coordinates if available
        pos = self.mapToScene(event.pos())
        lat = self.gps_latitude if self.gps_latitude else 0
        lon = self.gps_longitude if self.gps_longitude else 0
        self.mouse_moved.emit(int(pos.x()), int(pos.y()), lat, lon)
        
        super().mouseMoveEvent(event)
    
    def zoom_in(self):
        """Zoom in the view"""
        if self.has_image():
            factor = 1.25
            self._zoom += 1
            self.scale(factor, factor)
    
    def zoom_out(self):
        """Zoom out the view"""
        if self.has_image():
            factor = 1.0 / 1.25
            self._zoom -= 1
            if self._zoom <= 0:
                self.fitInView()
            else:
                self.scale(factor, factor)
    
    def actual_size(self):
        """Reset zoom to actual size"""
        self._zoom = 0
        self.resetTransform()
