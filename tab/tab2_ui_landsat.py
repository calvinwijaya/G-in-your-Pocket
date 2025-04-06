import json
import ee
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QLineEdit, QDateEdit, QSlider, QTextEdit, QHBoxLayout, QComboBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon
from tab.tab2_landsat import authenticate_and_initialize, process_landsat
from function.generate_map import generate_map
from ui_map import MapWidget

class LandsatTab(QWidget):
    processed_signal = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.project = None
        self.geojson_path = None
        self.geometry = None
        self.landsat_clipped = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QVBoxLayout()

        # Project Name
        self.project_label = QLabel("Google Earth Engine Project Name:")
        self.project_input = QLineEdit()
        form_layout.addWidget(self.project_label)
        form_layout.addWidget(self.project_input)

        # Authenticate Button
        self.auth_btn = QPushButton("Authenticate and Initialize GEE")
        self.auth_btn.clicked.connect(self.authenticate_gee)
        form_layout.addWidget(self.auth_btn)

        # Load GeoJSON
        self.geojson_label = QLabel("Selected GeoJSON: None")
        self.load_geojson_btn = QPushButton("Load GeoJSON")
        self.load_geojson_btn.clicked.connect(self.load_geojson)
        form_layout.addWidget(self.geojson_label)
        form_layout.addWidget(self.load_geojson_btn)

        # Date Selection
        self.date_layout = QHBoxLayout()
        self.start_date = QDate.fromString("2024-01-01", "yyyy-MM-dd")
        self.start_date_input = QDateEdit(self.start_date)
        self.start_date_input.setCalendarPopup(True)
        self.end_date_input = QDateEdit(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.date_layout.addWidget(QLabel("Start Date:"))
        self.date_layout.addWidget(self.start_date_input)
        self.date_layout.addWidget(QLabel("End Date:"))
        self.date_layout.addWidget(self.end_date_input)
        form_layout.addLayout(self.date_layout)

        # Select Landsat
        self.landsat_label = QLabel("Select Landsat Version:")
        self.landsat_dropdown = QComboBox()
        self.landsat_dropdown.addItems(["L9 Surface Reflectance", "L9 TOA Reflectance", "L8 Surface Reflectance", "L8 TOA Reflectance", "L7 Surface Reflectance", "L7 TOA Reflectance"])
        form_layout.addWidget(self.landsat_label)
        form_layout.addWidget(self.landsat_dropdown)

        # Process Button
        self.process_btn = QPushButton("Process Landsat Imagery")
        self.process_btn.clicked.connect(self.process_landsat_data)
        form_layout.addWidget(self.process_btn)

        # Generate Map Button
        map_replay_layout = QHBoxLayout()
        self.map_btn = QPushButton("Generate Map")
        self.map_btn.clicked.connect(self.generate_map)
        map_replay_layout.addWidget(self.map_btn)

        # Replay Button
        self.replay_button = QPushButton()
        self.replay_button.setIcon(QIcon("assets/replay.png"))
        self.replay_button.setFixedSize(32, 32)
        self.replay_button.setStyleSheet("border: none;")
        self.replay_button.clicked.connect(self.reset_parameters)
        map_replay_layout.addWidget(self.replay_button)

        form_layout.addLayout(map_replay_layout)

        # Export Image Button
        self.export_btn = QPushButton("Export Image")
        self.export_btn.clicked.connect(self.export_image)
        form_layout.addWidget(self.export_btn)

        # Log Window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        form_layout.addWidget(self.log_window)

        # Map UI
        self.map_widget = MapWidget(self)

        # Horizontal layout to arrange form and map side by side
        content_layout = QHBoxLayout()
        content_layout.addLayout(form_layout, 1)  # Form takes 1 part
        content_layout.addWidget(self.map_widget, 2)  # Map takes 2 parts

        # Add to main vertical layout
        main_layout.addLayout(content_layout)

        # Apply layout
        self.setLayout(main_layout)

    def authenticate_gee(self):
        self.project = self.project_input.text().strip()
        if not self.project:
            self.log("Error: Please enter a project name before authentication!")
            return
        try:
            authenticate_and_initialize(self.project)
            self.log(f"GEE Authentication Successful! Authenticated with project: {self.project}")
        except Exception as e:
            self.log(f"Authentication failed: {str(e)}")

    def load_geojson(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select GeoJSON File", "", "GeoJSON Files (*.geojson)")
        if file_path:
            self.geojson_path = file_path
            with open(file_path, "r") as f:
                geojson = json.load(f)
            if "features" in geojson and len(geojson["features"]) > 0:
                self.geometry = ee.Geometry(geojson["features"][0]["geometry"])
                self.geojson_label.setText(f"Selected GeoJSON: {file_path}")
                self.log("GeoJSON loaded successfully!")
            else:
                self.log("Invalid GeoJSON file.")

    @pyqtSlot(str)
    def receiveGeoJSON(self, geojson_str):
        geojson = json.loads(geojson_str)
        self.geom = geojson['geometry']
        self.geometry = ee.Geometry(self.geom)
        self.log("Polygon received from map and set as geometry!")
        print("Polygon received from map and set as geometry!")

    def process_landsat_data(self):
        if not self.geometry:
            self.log("Load GeoJSON first!")
            return
        landsat_version = self.landsat_dropdown.currentText()
        self.landsat_clipped = process_landsat(landsat_version, self.geometry, self.start_date_input.date().toString("yyyy-MM-dd"), 
                                            self.end_date_input.date().toString("yyyy-MM-dd"))
        self.processed_signal.emit(self.landsat_clipped)
        if self.landsat_clipped:
            self.log(f"Landsat {landsat_version} Imagery processed successfully.")
        else:
            self.log("No valid Landsat image found for the given parameters.")

    def generate_map(self):
        if not self.landsat_clipped:
            self.log("Process Landsat Imagery first!")
            return
        self.log("Generating map...")
        geojson_geometry = self.geometry.getInfo()
        generate_map(self.landsat_clipped, geojson_geometry, "Landsat")
        self.log("Map generated successfully.")

    def export_image(self):
        """"Export processed Landsat image."""
        if not self.landsat_clipped:
            self.log("Error: Process Landsat data first!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.landsat_clipped, description="Landsat_Export", folder="GEE_Exports",
            scale=10, region=self.geometry, crs="EPSG:4326", fileNamePrefix="Landsat_Export", maxPixels=1e13
        )
        task.start()
        self.log("Export task started. Check Google Drive.")

    def reset_parameters(self):
        """Resets Landsat processing parameters without re-authenticating."""
        self.landsat_clipped = None
        self.geometry = None
        self.log("All inputs have been reset. Please input new parameters.")

    def log(self, message):
        self.log_window.append(message)