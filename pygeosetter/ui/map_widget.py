"""
Map widget for PyGeoSetter
"""
import os
import folium
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSizePolicy, QMessageBox)
from PyQt5.QtCore import QUrl, Qt, QSize, QEvent, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon

class MapWidget(QWidget):
    """Interactive map widget for selecting and displaying locations"""
    
    # Signals
    location_changed = pyqtSignal(float, float)  # lat, lon
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize map properties
        self.default_lat = 0.0
        self.default_lon = 0.0
        self.default_zoom = 2
        
        # Current marker position
        self.current_marker = None
        self.current_lat = None
        self.current_lon = None
        
        # Initialize UI
        self.init_ui()
        
        # Create the map
        self.create_map()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view for the map
        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.web_view.setMinimumSize(400, 300)
        
        # Connect signals
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        # Add web view to layout
        layout.addWidget(self.web_view)
    
    def create_map(self):
        """Create a new map with default settings"""
        # Create a new map
        self.map = folium.Map(
            location=[self.default_lat, self.default_lon],
            zoom_start=self.default_zoom,
            tiles='OpenStreetMap',
            control_scale=True
        )
        
        # Add click event to the map
        self.map.get_root().html.add_child(
            folium.Element("""
            <script>
                // Function to handle map clicks
                function onMapClick(e) {
                    // Emit the click event with coordinates
                    let lat = e.latlng.lat;
                    let lng = e.latlng.lng;
                    console.log("Map clicked at: " + lat + ", " + lng);
                    
                    // Send the coordinates to the Python side
                    if (window.pywebview !== undefined) {
                        window.pywebview.api.set_location(lat, lng);
                    } else {
                        console.log("pywebview not available");
                    }
                }
                
                // Add click event listener to the map
                map.on('click', onMapClick);
            </script>
            """)
        )
        
        # Save the map to an HTML file
        self.map_file = os.path.join(os.path.dirname(__file__), '..', 'resources', 'map.html')
        self.map.save(self.map_file)
        
        # Load the map in the web view
        self.web_view.setUrl(QUrl.fromLocalFile(self.map_file))
    
    def on_load_finished(self, ok):
        """Handle map load completion"""
        if ok:
            # Enable JavaScript
            self.web_view.page().runJavaScript("""
                // Enable map interaction
                map.dragging.enable();
                map.touchZoom.enable();
                map.doubleClickZoom.enable();
                map.scrollWheelZoom.enable();
                map.boxZoom.enable();
                map.keyboard.enable();
                
                // Add a marker at the current position if available
                if (window.pywebview !== undefined && window.pywebview.api.current_lat && window.pywebview.api.current_lon) {
                    var lat = window.pywebview.api.current_lat;
                    var lng = window.pywebview.api.current_lon;
                    
                    if (window.current_marker) {
                        window.current_marker.setLatLng([lat, lng]);
                    } else {
                        window.current_marker = L.marker([lat, lng], {
                            draggable: true
                        }).addTo(map);
                        
                        // Center the map on the marker
                        map.setView([lat, lng], 15);
                        
                        // Add drag end event
                        window.current_marker.on('dragend', function(event) {
                            var marker = event.target;
                            var position = marker.getLatLng();
                            
                            // Update the marker position
                            window.pywebview.api.set_location(position.lat, position.lng);
                        });
                    }
                }
            """)
    
    def set_location(self, lat, lon):
        """Set the current location on the map"""
        self.current_lat = lat
        self.current_lon = lon
        
        # Update the marker position
        self.web_view.page().runJavaScript(f"""
            if (!window.current_marker) {{
                window.current_marker = L.marker([{lat}, {lon}], {{
                    draggable: true
                }}).addTo(map);
                
                // Center the map on the marker
                map.setView([{lat}, {lon}], 15);
                
                // Add drag end event
                window.current_marker.on('dragend', function(event) {{
                    var marker = event.target;
                    var position = marker.getLatLng();
                    
                    // Update the marker position
                    window.pywebview.api.set_location(position.lat, position.lng);
                }});
            }} else {{
                window.current_marker.setLatLng([{lat}, {lon}]);
                map.setView([{lat}, {lon}], 15);
            }}
        """)
        
        # Emit the location changed signal
        self.location_changed.emit(lat, lon)
    
    def get_location(self):
        """Get the current location from the map"""
        return self.current_lat, self.current_lon
    
    def clear_marker(self):
        """Remove the current marker from the map"""
        self.web_view.page().runJavaScript("""
            if (window.current_marker) {
                map.removeLayer(window.current_marker);
                window.current_marker = null;
            }
        """)
        
        self.current_lat = None
        self.current_lon = None
    
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        
        # Update the map size when the widget is resized
        self.web_view.page().runJavaScript("""
            map.invalidateSize();
        """)
