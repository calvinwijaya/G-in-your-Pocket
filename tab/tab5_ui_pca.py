import tempfile
import os
import ee
import folium
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit
)
from function.generate_map import add_ee_layer
from tab.tab5_pca import get_principal_components
import threading

class PCATab(QWidget):
    def __init__(self, sentinel2_image=None, landsat_image=None):
        super().__init__()
        self.sentinel2_image = sentinel2_image
        self.landsat_image = landsat_image
        self.selected_image = None
        self.pca_map = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Sentinel-2 or Landsat)
        self.image_label = QLabel("Select Processed Image:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Sentinel-2", "Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Calculate PCA Button
        self.generate_btn = QPushButton("Calculate Principal Components")
        self.generate_btn.clicked.connect(self.calculate_pca)
        layout.addWidget(self.generate_btn)

        # Preview PCA Map Button
        self.preview_btn = QPushButton("Generate PCA Map")
        self.preview_btn.clicked.connect(self.generate_pca_map)
        layout.addWidget(self.preview_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export PCA Image")
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

    def calculate_pca(self):
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        # ✅ Calculate Principal Components
        self.log("🔄 Calculating Principal Components...")
        region = self.selected_image.geometry()
        # if "Landsat" in self.image_dropdown.currentText():
        #     scale = 30
        # else:
        #     scale = 10
        scale = 30
        self.pca_map = get_principal_components(self.selected_image, region, scale)
        self.log("✅ Principal Components calculated.")

    def generate_pca_map(self):
        """Generate an interactive Folium map using the image's centroid as the center."""
        if not self.pca_map:
            self.log("⚠️ Error: PCA has not been calculated yet!")
            return

        info = self.pca_map.getInfo()
        self.log(f"PCA Image info: {info}")

        # Calculate scale
        # if "Landsat" in self.image_dropdown.currentText():
        #     scale = 30
        # else:
        #     scale = 10
        scale = 30

        # Compute min and max dynamically based on the image data
        try:
            stats = self.pca_map.reduceRegion(
                # reducer=ee.Reducer.minMax(),
                reducer=ee.Reducer.percentile([2, 98]),
                geometry=self.pca_map.geometry(),
                scale=scale,
                bestEffort=True
            ).getInfo()
        except Exception as e:
            self.log(f"⚠️ Could not calculate visualization stats: {str(e)}")
            return


        bands = ['pc1', 'pc2', 'pc3']

        # Get min and max values for selected bands
        # min_values = [stats.get(band + "_min", 0) for band in bands]
        # max_values = [stats.get(band + "_max", 1) for band in bands]

        # Get percentile min/max values for each band
        # min_values = [stats.get(band + "_p2", 0) for band in bands]  # 2nd percentile
        # max_values = [stats.get(band + "_p98", 1) for band in bands]  # 98th percentile
        min_values = -2
        max_values = 2

        # Set visualization parameters
        # vis_params = {'min': min(min_values), 'max': max(max_values), 'bands': bands}
        vis_params = {
            'min': min_values,
            'max': max_values,
            'bands': bands,
        }

        # Get the image centroid (center of the image)
        centroid = self.selected_image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=13)

        # Add the image layer
        add_ee_layer(m, self.pca_map, vis_params, "PCA False Color")

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
            image=self.pca_map, description="PCA_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="PCA_Export", maxPixels=1e13
        )
        task.start()
        self.log("Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)