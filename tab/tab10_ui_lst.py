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
import json
from branca.element import Template, MacroElement

class LSTTab(QWidget):
    def __init__(self, landsat_image=None):
        super().__init__()
        self.landsat_image = landsat_image
        self.selected_image = None
        self.lst = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image selection (Landsat)
        self.image_label = QLabel("Select Landsat 7/8/9 Surface Reflectance:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Landsat 8/9 Surface Reflectance", "Landsat 7 Surface Reflectance"])
        self.image_dropdown.currentTextChanged.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_dropdown)

        # Start LST Calculation Button
        self.generate_btn = QPushButton("Start LST Calculation")
        self.generate_btn.clicked.connect(self.generate_lst)
        layout.addWidget(self.generate_btn)

        # Preview LST Map Button
        self.preview_btn = QPushButton("Preview LST Map")
        self.preview_btn.clicked.connect(self.generate_lst_map)
        layout.addWidget(self.preview_btn)

        # Export Image Button
        self.export_btn = QPushButton("Export LST Image")
        self.export_btn.clicked.connect(self.export_image)
        layout.addWidget(self.export_btn)

        # Log window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        self.setLayout(layout)
        self.select_image()

    def select_image(self):
        selected = self.image_dropdown.currentText()
        if selected == "Landsat 8/9 Surface Reflectance" and isinstance(self.landsat_image, ee.Image):
            self.selected_image = self.landsat_image
            self.log("✅ Landsat 8/9 image selected.")
        elif selected == "Landsat 7 Surface Reflectance" and isinstance(self.landsat_image, ee.Image):
            self.selected_image = self.landsat_image
            self.log("✅ Landsat 7 image selected.")
        else:
            self.selected_image = None
            self.log("⚠️ Error: No valid image available. Process an image first!")

    def generate_lst(self):
        """Applies the selected LST Algorithm."""
        if not self.selected_image:
            self.log("⚠️ Error: No processed image selected!")
            return

        band_names = self.landsat_image.bandNames().getInfo()

        if "ST_B10" in band_names:
            lst_band_name = "ST_B10"
        elif "ST_B6" in band_names:
            lst_band_name = "ST_B6"
        else:
            self.log("⚠️ Error: No valid surface temperature band (ST_B10 or ST_B6) found.")
            return

        # Calculate LST
        self.log("🔄 Running LST Calculation...")

        self.LST_image = self.landsat_image.select(lst_band_name).subtract(273.15)
        
        self.log("✅ LST Calculation completed.")

        roi = self.landsat_image.geometry()

        meanLST = self.LST_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=30
        )
        self.log(f"Mean LST: {meanLST.getInfo()} °C")

        stats = self.LST_image.reduceRegion(
            reducer=ee.Reducer.minMax(),
            geometry=roi,
            scale=30,
            bestEffort=True
        ).getInfo()

        min_key = f"{lst_band_name}_min"
        max_key = f"{lst_band_name}_max"
        self.log(f"LST Min: {stats[min_key]:.2f} °C, LST Max: {stats[max_key]:.2f} °C")

    def generate_lst_map(self, image):
        """Generate an interactive Folium map using the LST image's centroid."""
        if not self.LST_image:
            self.log("⚠️ Error: LST Image is not available!")
            return

        # Get the image centroid
        centroid = self.LST_image.geometry().centroid().coordinates().getInfo()
        lon, lat = centroid

        vis_param = {
            "min": 15,
            "max": 50,
            "palette": [
                '040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
                '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
                '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
                'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
                'ff0000', 'de0101', 'c21301', 'a71001', '911003'
            ]
        }

        # Create Folium map centered on image centroid
        m = folium.Map(location=[lat, lon], zoom_start=12)

        # Add the image layer
        add_ee_layer(m, self.LST_image, vis_param, "LST Image")

        # Add layer control
        m.add_child(folium.LayerControl())

        # 🔥 Add legend as a MacroElement
        legend_html = """
        {% macro html(this, kwargs) %}
        <div style="
            position: fixed;
            bottom: 50px;
            left: 50px;
            width: 200px;
            height: auto;
            z-index: 9999;
            background-color: white;
            border: 2px solid grey;
            padding: 10px;
            font-size: 12px;
        ">
        <b>LST Legend (°C)</b><br>
        <i>Low</i>
        <div style="height: 15px; background: linear-gradient(to right,
            #040274, #040281, #0502a3, #0502b8, #0502ce, #0502e6,
            #0602ff, #235cb1, #307ef3, #269db1, #30c8e2, #32d3ef,
            #3be285, #3ff38f, #86e26f, #3ae237, #b5e22e, #d6e21f,
            #fff705, #ffd611, #ffb613, #ff8b13, #ff6e08, #ff500d,
            #ff0000, #de0101, #c21301, #a71001, #911003
        ); margin: 5px 0;"></div>
        <i>High</i>
        </div>
        {% endmacro %}
        """
        legend = MacroElement()
        legend._template = Template(legend_html)
        m.get_root().add_child(legend)

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
        """Export LST Image."""
        if not self.LST_image:
            self.log("⚠️ Error: No LST image to export!")
            return

        task = ee.batch.Export.image.toDrive(
            image=self.LST_image, description="LST_Export", folder="GEE_Exports",
            scale=10, crs="EPSG:4326", fileNamePrefix="LST_Export", maxPixels=1e13
        )
        task.start()
        self.log("✅ Export task started. Check Google Drive.")

    def log(self, message):
        """Logs messages to the log window."""
        self.log_window.append(message)