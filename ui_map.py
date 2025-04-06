from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import pyqtSlot, QObject

class MapWidget(QWidget):
    def __init__(self, pyqt_channel_object):
        super().__init__()

        # Create WebEngineView
        self.web_view = QWebEngineView()
        self.web_view.setHtml(self.get_map_html())
        self.web_view.setMinimumWidth(400)
        self.web_view.setMinimumHeight(1000)

        # Setup Web Channel
        self.channel = QWebChannel()
        self.channel.registerObject("pyqtChannel", pyqt_channel_object)
        self.web_view.page().setWebChannel(self.channel)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        self.setLayout(layout)

    def get_map_html(self):
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Leaflet Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet-draw/dist/leaflet.draw.css" />
            <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet-draw/dist/leaflet.draw.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="map" style="width: 100%; height: 600px;"></div>
            <script>
                var baseLayers = {
                    "OpenStreetMap": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors'
                    }),
                    "Esri World Imagery": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                        attribution: 'Tiles © Esri'
                    }),
                    "CartoDB Positron": L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                        attribution: '&copy; CartoDB'
                    })
                };

                var map = L.map('map', {
                    center: [-7.782760, 110.374335],
                    zoom: 12,
                    layers: [baseLayers["OpenStreetMap"]]
                });

                L.control.layers(baseLayers).addTo(map);

                var drawnItems = new L.FeatureGroup();
                map.addLayer(drawnItems);

                var drawControl = new L.Control.Draw({
                    edit: {
                        featureGroup: drawnItems
                    },
                    draw: {
                        polygon: true,
                        marker: false,
                        circle: false,
                        circlemarker: false,
                        rectangle: true,
                        polyline: false
                    }
                });
                map.addControl(drawControl);

                function sendGeoJSONToPyQt(geojson) {
                    if (window.pyqtChannel && typeof window.pyqtChannel.receiveGeoJSON === "function") {
                        window.pyqtChannel.receiveGeoJSON(geojson);
                    } else {
                        console.log("PyQt channel not ready yet!");
                    }
                }

                map.on('draw:created', function (e) {
                    var layer = e.layer;
                    drawnItems.addLayer(layer);
                    var geojson = JSON.stringify(layer.toGeoJSON());
                    console.log("Sending GeoJSON to PyQt:", geojson);
                    sendGeoJSONToPyQt(geojson);
                });

                new QWebChannel(qt.webChannelTransport, function (channel) {
                    window.pyqtChannel = channel.objects.pyqtChannel;
                    console.log("PyQt Web Channel connected!");
                });
            </script>
        </body>
        </html>
        '''