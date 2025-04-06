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

class PansharpTab(QWidget):
    def __init__(self, landsat_image=None):
        super().__init__()
        self.landsat_image = landsat_image
        self.selected_image = None
        self.pansharp_map = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Landsat)
        self.image_label = QLabel("Select Landsat 8/9 TOA Reflectance:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Start Pansharpening Button
        self.generate_btn = QPushButton("Start Pansharpening")
        self.generate_btn.clicked.connect(self.pansharpening)
        layout.addWidget(self.generate_btn)

        # Preview Pansharpened Map Button
        self.preview_btn = QPushButton("Generate Pansharpened Map")
        self.preview_btn.clicked.connect(self.generate_pansharpened_map)
        layout.addWidget(self.preview_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export Pansharpened Image")
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
        if selected == "Landsat" and isinstance(self.landsat_image, ee.Image):
            self.selected_image = self.landsat_image
            self.log("✅ Landsat image selected.")
        else:
            self.selected_image = None
            self.log("⚠️ Error: No valid image available. Process an image first!")

    def pansharpening(self):
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        # Start Pansharpening
        self.log("🔄 Start Pansharpening...")

        # Convert RGB to HSV
        hsv = self.selected_image.select(['B4', 'B3', 'B2']).rgbToHsv()
    
        # Replace Value (V) band with Panchromatic (B8) and convert back to RGB
        self.pansharpened_map = ee.Image.cat([
            hsv.select('hue'),          # Keep Hue
            hsv.select('saturation'),   # Keep Saturation
            self.selected_image.select('B8')          # Replace Value with Panchromatic
        ]).hsvToRgb()

        self.log("✅ Pansharpening complete.")

    def generate_pansharpened_map(self):
        """Generate an interactive Folium map using the image's centroid as the center."""
        if not self.pansharpened_map:
            self.log("⚠️ Error: Pansharpened Image not yet generated!")
            return

        # Compute min and max dynamically based on the image data
        stats = self.pansharpened_map.reduceRegion(
            # reducer=ee.Reducer.minMax(),
            reducer=ee.Reducer.percentile([2, 98]),
            scale=30,
            bestEffort=True
        ).getInfo()

        bands = ["red", "green", "blue"]

        # Get min and max values for selected bands
        # min_values = [stats.get(band + "_min", 0) for band in bands]
        # max_values = [stats.get(band + "_max", 1) for band in bands]

        # Get percentile min/max values for each band
        min_values = [stats.get(band + "_p2", 0) for band in bands]  # 2nd percentile
        max_values = [stats.get(band + "_p98", 1) for band in bands]  # 98th percentile

        # Set visualization parameters
        vis_params = {'min': min(min_values), 'max': max(max_values), 'bands': bands}

        # Get the image centroid (center of the image)
        centroid = self.selected_image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, self.pansharpened_map, vis_params, "Pansharpened Image")

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
        """"Export PCA image."""
        task = ee.batch.Export.image.toDrive(
            image=self.pansharpened_map, description="PCA_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="PCA_Export", maxPixels=1e13
        )
        task.start()
        self.log("Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)