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

class UnsupervisedTab(QWidget):
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
        self.image_dropdown.addItems(["Sentinel-2", "Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Unsupervised Method Selection
        self.unsupervised_label = QLabel("Select Unsupervised Classification Algorithm:")
        self.unsupervised_dropdown = QComboBox()
        self.unsupervised_dropdown.addItems(["K-Means", "Cascade K-Means", "X-Means"])
        layout.addWidget(self.unsupervised_label)
        layout.addWidget(self.unsupervised_dropdown)

        # Number of Clusters
        self.clusters_label = QLabel("Number of Clusters:")
        self.clusters_dropdown = QComboBox()
        self.clusters_dropdown.addItems(["2", "3", "4", "5", "6", "7", "8", "9", "10"])
        layout.addWidget(self.clusters_label)
        layout.addWidget(self.clusters_dropdown)

        # Start Unsupervised Classification Button
        self.generate_btn = QPushButton("Start Unsupervised Classification")
        self.generate_btn.clicked.connect(self.generate_unsupervised)
        layout.addWidget(self.generate_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export Unsupervised Classified Image")
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

    def generate_unsupervised(self):
        """Applies the selected Unsupervised Algorithm."""
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        selected_algorithm = self.unsupervised_dropdown.currentText()
        cluster_count = int(self.clusters_dropdown.currentText())

        # Map dropdown text to EE clusterer
        algorithm_map = {
            "K-Means": ee.Clusterer.wekaKMeans(cluster_count),
            "Cascade K-Means": ee.Clusterer.wekaCascadeKMeans(cluster_count, 11),
            "X-Means": ee.Clusterer.wekaXMeans(cluster_count, 11)
        }

        if selected_algorithm not in algorithm_map:
            self.log(f"⚠️ Error: Selected algorithm '{selected_algorithm}' is not recognized.")
            return

        # Train the selected clusterer
        self.log(f"🔄 Running {selected_algorithm} with {cluster_count} clusters...")
        training = self.selected_image.sample(region=self.selected_image.geometry(), numPixels=5000, scale=30)
        clusterer = algorithm_map[selected_algorithm].train(training)
        self.classified = self.selected_image.cluster(clusterer)
        self.classified = self.classified.randomVisualizer()
        self.generate_unsupervised_map(self.classified)
        self.log(f"✅ {selected_algorithm} Classification completed.")

    def generate_unsupervised_map(self, image):
        """Generate an interactive Folium map using the image's centroid as the center."""
        # Get the image centroid
        centroid = image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, image, {}, "Unsupervised Classification")

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
        """Export Unsupervised Classified Image."""
        if not self.classified:
            self.log("⚠️ Error: No classified image to export!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.classified, description="Unsupervised_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="Unsupervised_Export", maxPixels=1e13
        )
        task.start()
        self.log("✅ Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)