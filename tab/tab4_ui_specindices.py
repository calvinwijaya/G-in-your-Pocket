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

class SpectralIndicesTab(QWidget):
    def __init__(self, sentinel2_image=None, landsat_image=None):
        super().__init__()
        self.sentinel2_image = sentinel2_image
        self.landsat_image = landsat_image
        self.selected_image = None
        self.spec_map = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Sentinel-2 or Landsat)
        self.image_label = QLabel("Select Processed Image:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Sentinel-2", "Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.update_spec_options)
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Spectral Indices Selection
        self.spec_label = QLabel("Select Spectral Index:")
        self.spec_dropdown = QComboBox()
        layout.addWidget(self.spec_label)
        layout.addWidget(self.spec_dropdown)

        # Generate Spectral Indices Button
        self.generate_btn = QPushButton("Generate Spectral Index")
        self.generate_btn.clicked.connect(self.generate_spec_indices)
        layout.addWidget(self.generate_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export Spectral Indices Image")
        self.export_btn.clicked.connect(self.export_image)
        layout.addWidget(self.export_btn)

        # Log window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        self.setLayout(layout)
        self.update_spec_options()
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

    def update_spec_options(self):
        """Updates the Spectral Indices options based on selected image type."""
        selected_image_type = self.image_dropdown.currentText()
        self.spec_dropdown.clear()  # Clear previous options

        if selected_image_type == "Sentinel-2":
            self.spec_map = {
                "NDVI": lambda img: img.normalizedDifference(['B8', 'B4']),  # Near-Infrared (B8) & Red (B4)
                "NDWI": lambda img: img.normalizedDifference(['B3', 'B8']),  # Green (B3) & NIR (B8)
                "NDBI": lambda img: img.normalizedDifference(['B11', 'B8']),  # SWIR (B11) & NIR (B8)
                "RVI" : lambda img: img.expression('B8 / B4', {'B8': img.select('B8'), 'B4': img.select('B4')}),  # Red (B4) & NIR (B8)
                "GRVI": lambda img: img.normalizedDifference(['B3', 'B4']),  # Green (B3) & NIR (B8)
                "GNDVI": lambda img: img.normalizedDifference(['B8', 'B3'])  # NIR (B8) & Green (B3)
            }
        else:  # Landsat
            # --- Band detection for Landsat ---
            band_names = self.landsat_image.bandNames().getInfo()
            self.log(f"📛 Bands in Landsat image: {band_names}")

            is_sr = any(b.startswith("SR_") for b in band_names)
            has_st_b10 = "ST_B10" in band_names
            has_b10 = "B10" in band_names
            has_sr_b6 = "SR_B6" in band_names
            has_sr_b1 = "SR_B1" in band_names
            has_st_b6 = "ST_B6" in band_names
            has_b1 = "B1" in band_names
            has_b11 = "B11" in band_names

            is_l8_9_sr = is_sr and has_sr_b6 and has_st_b10
            is_l7_sr = is_sr and has_sr_b1 and has_st_b6 and not has_sr_b6
            is_l8_9_toa = not is_sr and has_b10 and has_b11
            is_l7_toa = not is_sr and not has_b10 and has_b1

            if is_l7_sr:
                self.log("🛰️ Detected: Landsat 7 Surface Reflectance")
                self.spec_map = {
                    "NDVI": lambda img: img.normalizedDifference(['SR_B4', 'SR_B3']),
                    "NDWI": lambda img: img.normalizedDifference(['SR_B2', 'SR_B4']),
                    "NDBI": lambda img: img.normalizedDifference(['SR_B5', 'SR_B4']),
                    "RVI": lambda img: img.expression('SR_B4 / SR_B3', {'SR_B4': img.select('SR_B4'), 'SR_B3': img.select('SR_B3')}),
                    "GRVI": lambda img: img.normalizedDifference(['SR_B2', 'SR_B3']),
                    "GNDVI": lambda img: img.normalizedDifference(['SR_B4', 'SR_B2'])
                }
            elif is_l8_9_sr:
                self.log("🛰️ Detected: Landsat 8/9 Surface Reflectance")
                self.spec_map = {
                    "NDVI": lambda img: img.normalizedDifference(['SR_B5', 'SR_B4']),
                    "NDWI": lambda img: img.normalizedDifference(['SR_B3', 'SR_B5']),
                    "NDBI": lambda img: img.normalizedDifference(['SR_B6', 'SR_B5']),
                    "RVI": lambda img: img.expression('SR_B5 / SR_B4', {'SR_B5': img.select('SR_B5'), 'SR_B4': img.select('SR_B4')}),
                    "GRVI": lambda img: img.normalizedDifference(['SR_B3', 'SR_B4']),
                    "GNDVI": lambda img: img.normalizedDifference(['SR_B5', 'SR_B3'])
                }
            elif is_l7_toa:
                self.log("🛰️ Detected: Landsat 7 TOA")
                self.spec_map = {
                    "NDVI": lambda img: img.normalizedDifference(['B4', 'B3']),
                    "NDWI": lambda img: img.normalizedDifference(['B2', 'B4']),
                    "NDBI": lambda img: img.normalizedDifference(['B5', 'B4']),
                    "RVI": lambda img: img.expression('B4 / B3', {'B4': img.select('B4'), 'B3': img.select('B3')}),
                    "GRVI": lambda img: img.normalizedDifference(['B2', 'B3']),
                    "GNDVI": lambda img: img.normalizedDifference(['B4', 'B2'])
                }
            else:
                self.log("🛰️ Detected: Landsat 8/9 TOA")
                self.spec_map = {
                    "NDVI": lambda img: img.normalizedDifference(['B5', 'B4']),
                    "NDWI": lambda img: img.normalizedDifference(['B3', 'B5']),
                    "NDBI": lambda img: img.normalizedDifference(['B6', 'B5']),
                    "RVI": lambda img: img.expression('B5 / B4', {'B5': img.select('B5'), 'B4': img.select('B4')}),
                    "GRVI": lambda img: img.normalizedDifference(['B3', 'B4']),
                    "GNDVI": lambda img: img.normalizedDifference(['B5', 'B3'])
                }

        self.spec_dropdown.addItems(self.spec_map.keys())

    def generate_spec_indices(self):
        """Applies the selected Spectral Indices visualization."""
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        selected_spec = self.spec_dropdown.currentText()

        if selected_spec not in self.spec_map:
            self.log("⚠️ Error: Invalid spectral index selected!")
            return

        # ✅ Compute the spectral index
        self.spectral_index_image = self.spec_map[selected_spec](self.selected_image)

        # ✅ Compute 2% and 98% percentiles for better contrast stretching
        percentiles = self.spectral_index_image.reduceRegion(
            reducer=ee.Reducer.percentile([2, 98]),  
            geometry=self.selected_image.geometry(),
            scale=30,
            bestEffort=True
        ).getInfo()

        # ✅ Set default min/max in case of missing data
        min_val = percentiles.get('constant_p2', -1)  # Ensure key exists
        max_val = percentiles.get('constant_p98', 1)  # Ensure key exists

        # ✅ Custom palettes for different indices
        palette_map = {
            "NDVI": ['blue', 'white', 'green'],
            "NDWI": ['brown', 'white', 'blue'],
            "NDBI": ['blue', 'white', 'red'],
            "RVI": ['purple', 'white', 'yellow'],
            "GRVI": ['black', 'white', 'green'],
            "GNDVI": ['cyan', 'white', 'darkgreen']
        }
        
        # ✅ Choose appropriate palette
        palette = palette_map.get(selected_spec, ['blue', 'white', 'green'])  # Default palette

        # ✅ Dynamic visualization parameters
        vis_params = {'min': min_val, 'max': max_val, 'palette': palette}

        # ✅ Generate the map with the computed vis_params
        self.log(f"🌍 Generating Spectral Index: {selected_spec} (min={min_val}, max={max_val})")
        self.generate_spec_indices_map(self.spectral_index_image, selected_spec, vis_params)
        self.log(f"✅ {selected_spec} generated.")

    def generate_spec_indices_map(self, image, spec_name, vis_params):
        """Generate an interactive Folium map using the image's centroid as the center."""
        # Get the image centroid (center of the image)
        centroid = image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, image, vis_params, spec_name)

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
        """"Export Spectral Indices image."""
        task = ee.batch.Export.image.toDrive(
            image=self.spectral_index_image, description="SpectralIndices_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="SpectralIndices_Export", maxPixels=1e13
        )
        task.start()
        self.log("Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)