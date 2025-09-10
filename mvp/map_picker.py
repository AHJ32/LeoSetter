from PyQt5.QtCore import QObject, pyqtSignal, QUrl, pyqtSlot
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Map Picker</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body, #map { height: 100%; margin: 0; padding: 0; }
    .searchbar { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000; background: white; padding: 6px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
    .searchbar input { width: 300px; padding: 6px; }
    .searchbar button { padding: 6px 10px; margin-left: 4px; }
  </style>
</head>
<body>
  <div class="searchbar">
    <input id="q" type="text" placeholder="Search country or place (Nominatim)">
    <button onclick="searchPlace()">Search</button>
  </div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
  <script>
    let marker = null;
    function initChannel() {
      new QWebChannel(qt.webChannelTransport, function(channel) {
        window.bridge = channel.objects.bridge;
      });
    }

    function initMap() {
      const map = L.map('map').setView([20, 0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
      }).addTo(map);

      function setPoint(latlng) {
        if (marker) { marker.remove(); }
        marker = L.marker(latlng).addTo(map);
        if (window.bridge) {
          window.bridge.onPicked(latlng.lat, latlng.lng);
        }
      }

      map.on('click', function(e) { setPoint(e.latlng); });
      window.setPoint = setPoint;
      window._map = map;
    }

    async function searchPlace() {
      const q = document.getElementById('q').value;
      if (!q) return;
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`;
        const resp = await fetch(url, { headers: { 'Accept': 'application/json' } });
        const data = await resp.json();
        if (data && data.length) {
          const { lat, lon } = data[0];
          const latNum = parseFloat(lat), lonNum = parseFloat(lon);
          window._map.setView([latNum, lonNum], 6);
          window.setPoint({lat: latNum, lng: lonNum});
        }
      } catch (e) { console.error(e); }
    }

    document.addEventListener('DOMContentLoaded', function() {
      initChannel();
      initMap();
    });
  </script>
</body>
</html>
"""

class Bridge(QObject):
    picked = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def onPicked(self, lat: float, lon: float):  # type: ignore
        self.picked.emit(lat, lon)

class MapPickerDialog(QDialog):
    def __init__(self, parent=None, start_lat: float = 0.0, start_lon: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle("Pick Location on Map")
        self.resize(900, 600)
        self.lat = None
        self.lon = None

        layout = QVBoxLayout(self)
        self.web = QWebEngineView(self)
        layout.addWidget(self.web, 1)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Use Location")
        self.btn_cancel = QPushButton("Cancel")
        btns.addStretch(1)
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        # WebChannel bridge
        self.bridge = Bridge()
        self.bridge.picked.connect(self.on_picked)
        self.channel = QWebChannel(self.web.page())
        self.channel.registerObject('bridge', self.bridge)
        self.web.page().setWebChannel(self.channel)

        # Load HTML
        self.web.setHtml(HTML, baseUrl=QUrl("https://local/"))

        # Optional: center on provided coords
        if start_lat or start_lon:
            js = f"if (window._map) {{ _map.setView([{start_lat}, {start_lon}], 8); setPoint({{lat:{start_lat}, lng:{start_lon}}}); }}"
            self.web.page().runJavaScript(js)

    def on_picked(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    @staticmethod
    def get_location(parent=None, start_lat: float = 0.0, start_lon: float = 0.0):
        dlg = MapPickerDialog(parent, start_lat, start_lon)
        ok = dlg.exec_() == QDialog.Accepted and dlg.lat is not None and dlg.lon is not None
        return (dlg.lat, dlg.lon, ok)
