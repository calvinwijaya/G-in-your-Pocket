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

class FalseColorTab(QWidget):
    def __init__(self, sentinel2_image=None, landsat_image=None):
        super().__init__()
        self.sentinel2_image = sentinel2_image
        self.landsat_image = landsat_image
        self.selected_image = None
        self.fcc_map = {}  # Initialize fcc_map to avoid KeyError
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Sentinel-2 or Landsat)
        self.image_label = QLabel("Select Processed Image:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Sentinel-2", "Landsat"])
        self.image_dropdown.currentTextChanged.connect(self.update_fcc_options)
        self.image_dropdown.currentTextChanged.connect(self.select_image)  # ✅ Fix: Ensure image is selected

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # False Color Composite Selection
        self.fcc_label = QLabel("Select False Color Composite:")
        self.fcc_dropdown = QComboBox()
        layout.addWidget(self.fcc_label)
        layout.addWidget(self.fcc_dropdown)

        # Generate FCC Button
        self.generate_btn = QPushButton("Generate False Color Composite")
        self.generate_btn.clicked.connect(self.generate_false_color)
        layout.addWidget(self.generate_btn)

        # Log window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        self.setLayout(layout)
        self.update_fcc_options()
        self.select_image()  # ✅ Fix: Ensure an image is selected when UI initializes

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

    def update_fcc_options(self):
        """Updates the FCC options based on selected image type."""
        selected_image_type = self.image_dropdown.currentText()
        self.fcc_dropdown.clear()  # Clear previous options

        if selected_image_type == "Sentinel-2":
            self.fcc_map = {
                "Agriculture": ["B11", "B8", "B2"],
                "Geology": ["B12", "B11", "B2"],
                "Bathymetric": ["B4", "B3", "B1"],
                "False Color Infrared": ["B8", "B4", "B3"],
                "False Color Urban": ["B12", "B11", "B4"],
                "Healthy Vegetation": ["B8", "B11", "B2"],
                "Land/Water": ["B8", "B11", "B4"],
                "Natural Colors with Atmospheric Removal": ["B12", "B8", "B3"],
                "Shortwave Infrared": ["B12", "B8", "B4"],
                "Vegetation Analysis": ["B11", "B8", "B4"]
            }
        else:
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
            elif is_l8_9_sr:
                self.log("🛰️ Detected: Landsat 8/9 Surface Reflectance")
            elif is_l7_toa:
                self.log("🛰️ Detected: Landsat 7 TOA")
            else:
                self.log("🛰️ Detected: Landsat 8/9 TOAe")

            if is_l7_sr:
                # Landsat 7 Surface Reflectance
                self.fcc_map = {
                    "False Color (Urban)": ["SR_B5", "SR_B4", "SR_B3"],
                    "Color Infrared (Vegetation)": ["SR_B4", "SR_B3", "SR_B2"],
                    "Agriculture": ["SR_B5", "SR_B4", "SR_B1"],
                    "Atmospheric Penetration": ["SR_B7", "SR_B5", "SR_B3"],
                    "Healthy Vegetation": ["SR_B4", "SR_B5", "SR_B2"],
                    "Land/Water": ["SR_B4", "SR_B5", "SR_B3"],
                    "Natural With Atmospheric Removal": ["SR_B7", "SR_B4", "SR_B2"],
                    "Shortwave Infrared": ["SR_B7", "SR_B5", "SR_B4"],
                    "Vegetation Analysis": ["SR_B5", "SR_B4", "SR_B3"]
                }
            elif is_l8_9_sr:
                # Landsat 8/9 Surface Reflectance
                self.fcc_map = {
                    "False Color (Urban)": ["SR_B7", "SR_B6", "SR_B4"],
                    "Color Infrared (Vegetation)": ["SR_B5", "SR_B4", "SR_B3"],
                    "Agriculture": ["SR_B6", "SR_B5", "SR_B2"],
                    "Atmospheric Penetration": ["SR_B7", "SR_B6", "SR_B5"],
                    "Healthy Vegetation": ["SR_B5", "SR_B6", "SR_B2"],
                    "Land/Water": ["SR_B5", "SR_B6", "SR_B4"],
                    "Natural With Atmospheric Removal": ["SR_B7", "SR_B5", "SR_B3"],
                    "Shortwave Infrared": ["SR_B7", "SR_B5", "SR_B4"],
                    "Vegetation Analysis": ["SR_B6", "SR_B5", "SR_B4"]
                }
            elif is_l7_toa:
                # Landsat 7 TOA or Radiance
                self.fcc_map = {
                    "False Color (Urban)": ["B5", "B4", "B3"],
                    "Color Infrared (Vegetation)": ["B4", "B3", "B2"],
                    "Agriculture": ["B5", "B4", "B1"],
                    "Atmospheric Penetration": ["B7", "B5", "B3"],
                    "Healthy Vegetation": ["B4", "B5", "B2"],
                    "Land/Water": ["B4", "B5", "B3"],
                    "Natural With Atmospheric Removal": ["B7", "B4", "B2"],
                    "Shortwave Infrared": ["B7", "B5", "B4"],
                    "Vegetation Analysis": ["B5", "B4", "B3"]
                }
            else:
                # Landsat 8/9 TOA or Radiance
                self.fcc_map = {
                    "False Color (Urban)": ["B7", "B6", "B4"],
                    "Color Infrared (Vegetation)": ["B5", "B4", "B3"],
                    "Agriculture": ["B6", "B5", "B2"],
                    "Atmospheric Penetration": ["B7", "B6", "B5"],
                    "Healthy Vegetation": ["B5", "B6", "B2"],
                    "Land/Water": ["B5", "B6", "B4"],
                    "Natural With Atmospheric Removal": ["B7", "B5", "B3"],
                    "Shortwave Infrared": ["B7", "B5", "B4"],
                    "Vegetation Analysis": ["B6", "B5", "B4"]
                }

        self.fcc_dropdown.addItems(self.fcc_map.keys())

    def generate_false_color(self):
        """Applies the selected False Color Composite visualization."""
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return
        
        selected_fcc = self.fcc_dropdown.currentText()
        bands = self.fcc_map.get(selected_fcc, ['B4', 'B3', 'B2'])

        if self.selected_image == "Sentinel-2":
            scale = 10
        else:
            scale = 30
        
        stats = self.selected_image.reduceRegion(
            # reducer=ee.Reducer.minMax(),
            reducer=ee.Reducer.percentile([2, 98]),
            geometry=self.selected_image.geometry(),
            scale=scale,
            bestEffort=True
        ).getInfo()

        # Get min and max values for selected bands
        # min_values = [stats.get(band + "_min", 0) for band in bands]
        # max_values = [stats.get(band + "_max", 1) for band in bands]

        # Get percentile min/max values for each band
        min_values = [stats.get(band + "_p2", 0) for band in bands]  # 2nd percentile
        max_values = [stats.get(band + "_p98", 1) for band in bands]  # 98th percentile

        # Set visualization parameters
        vis_params = {'min': min(min_values), 'max': max(max_values), 'bands': bands}

        # Generate the map
        self.log(f"🌍 Generating False Color Composite: {selected_fcc}")
        self.generate_false_color_map(self.selected_image, selected_fcc, vis_params)

    def generate_false_color_map(self, image, fcc_name, vis_params):
        """Generate an interactive Folium map using the image's centroid as the center."""
        # Get the image centroid (center of the image)
        centroid = image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid  # Extract coordinates

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, image, vis_params, fcc_name)

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

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)