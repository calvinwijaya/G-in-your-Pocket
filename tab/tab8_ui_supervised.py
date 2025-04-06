import tempfile
import os
import ee
import folium
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit
)
from function.generate_map import add_ee_layer
import threading
from geemap import ml

class SupervisedTab(QWidget):
    def __init__(self, sentinel2_image=None, landsat_image=None):
        super().__init__()
        self.sentinel2_image = sentinel2_image
        self.landsat_image = landsat_image
        self.selected_image = None
        self.classified = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Sentinel-2 or Landsat)
        self.image_label = QLabel("Select Processed Image:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Supervised Method Selection
        self.supervised_label = QLabel("Select Supervised Classification Algorithm:")
        self.supervised_dropdown = QComboBox()
        self.supervised_dropdown.addItems(["Random Forest", "Extra Trees"])
        layout.addWidget(self.supervised_label)
        layout.addWidget(self.supervised_dropdown)

        # Start Supervised Classification Button
        self.generate_btn = QPushButton("Start Supervised Classification")
        self.generate_btn.clicked.connect(self.generate_supervised)
        layout.addWidget(self.generate_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export Supervised Classified Image")
        self.export_btn.clicked.connect(self.export_image)
        layout.addWidget(self.export_btn)

        # Log window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        self.setLayout(layout)
        self.select_image()

    def select_image(self):
        """Selects the processed image based on dropdown selection."""
        selected = self.image_dropdown.currentText()
        if selected == "Sentinel-2" and isinstance(self.sentinel2_image, ee.Image):
            self.selected_image = self.sentinel2_image
            self.log("✅ Sentinel-2 image selected.")
        elif selected == "Landsat" and isinstance(self.landsat_image, ee.Image):
            self.selected_image = self.landsat_image
            self.log("✅ Landsat image selected.")
        else:
            self.selected_image = None
            self.log("⚠️ Error: No valid image available. Process an image first!")

    def generate_supervised(self):
        """Applies the selected Supervised Algorithm."""
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        selected_algorithm = self.supervised_dropdown.currentText()
        band_names = self.selected_image.bandNames().getInfo()
        self.log(f"📛 Bands in image: {band_names}")

        # Detect image type from band names
        is_sr = any(b.startswith("SR_") for b in band_names)
        has = lambda b: b in band_names

        # Get satellite metadata
        satellite_id = self.selected_image.get("SPACECRAFT_ID").getInfo()
        product_id = self.selected_image.get("LANDSAT_PRODUCT_ID").getInfo()
        self.log(f"🛰️ Satellite ID: {satellite_id}")
        self.log(f"🗂️ Product ID: {product_id}")

        image_type = None
        feature_names = []

        # Surface Reflectance
        if is_sr:
            if satellite_id == "LANDSAT_7":
                image_type = "L7SR"
                feature_names = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"]
            elif satellite_id == "LANDSAT_8":
                image_type = "L8SR"
                feature_names = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
            elif satellite_id == "LANDSAT_9":
                image_type = "L9SR"
                feature_names = ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"]
        # TOA Reflectance
        else:
            if satellite_id == "LANDSAT_7":
                image_type = "L7TOA"
                feature_names = ["B1", "B2", "B3", "B4", "B5", "B7", "B8"]
            elif satellite_id == "LANDSAT_8":
                image_type = "L8TOA"
                feature_names = ["B2", "B3", "B4", "B5", "B6", "B7", "B10", "B11"]
            elif satellite_id == "LANDSAT_9":
                image_type = "L9TOA"
                feature_names = ["B2", "B3", "B4", "B5", "B6", "B7", "B10", "B11"]

        if image_type:
            self.log(f"🛰️ Detected: {image_type.replace('SR', ' Surface Reflectance').replace('TOA', ' TOA')}")

            algo_key = "random_forest" if selected_algorithm == "Random Forest" else "extratrees"
            asset_id = f"projects/ee-penelitianclv/assets/models/{image_type}_{algo_key}"

            self.log(f"🔄 Running Supervised Classification with {selected_algorithm}...")
            model = ee.FeatureCollection(asset_id)
            classifier = ml.fc_to_classifier(model)

            self.classified = self.selected_image.select(feature_names).classify(classifier)
            self.generate_supervised_map(self.classified)
            self.log(f"✅ {selected_algorithm} Classification completed.")
        else:
            self.log("❌ Unrecognized image type: cannot determine feature bands or satellite.")

    def generate_supervised_map(self, image):
        """Generate an interactive Folium map using the image's centroid as the center."""
        # Get the image centroid
        centroid = image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, image, {"min": 0, "max": 2, "palette": ['red', 'green', 'blue']}, "Supervised Classification")

        # Add layer control
        m.add_child(folium.LayerControl())

        # Save and open the map
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
            temp_path = temp_file.name
        m.save(temp_path)
        webbrowser.open(temp_path)

        def delete_temp_file():
            """Delete the temporary file after closing the browser."""
            import time
            time.sleep(2)
            if os.path.exists(temp_path):
                os.remove(temp_path)

        threading.Thread(target=delete_temp_file, daemon=True).start()

    def export_image(self):
        """Export Supervised Classified Image."""
        if not self.classified:
            self.log("⚠️ Error: No classified image to export!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.classified, description="Supervised_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="Supervised_Export", maxPixels=1e13
        )
        task.start()
        self.log("✅ Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)