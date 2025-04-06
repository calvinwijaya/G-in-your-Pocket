import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QLineEdit, QDateEdit, QFileDialog
)
from PyQt6.QtCore import QDate, pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from ui_map import MapWidget
import threading
from threading import Thread
import ee
from datetime import datetime

class NDVIPlotTab(QWidget):
    def __init__(self):
        super().__init__()
        
        self.s2_collection = None  # Initialize Sentinel-2 collection
        self.landsat_collection = None  # Initialize Landsat collection
        self.selected_image = None
        self.ndviplot = None
        self.image = None  # To store the processed NDVI image
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()  # Main layout
        content_layout = QHBoxLayout()  # Arrange form and map side by side
        form_layout = QVBoxLayout()  # Form layout on the left
        map_graph_layout = QVBoxLayout()  # Stack map and graph vertically

        # --- Form UI (Left Panel) ---
        self.project_label = QLabel("Google Earth Engine Project Name:")
        self.project_input = QLineEdit()
        form_layout.addWidget(self.project_label)
        form_layout.addWidget(self.project_input)

        self.auth_btn = QPushButton("Authenticate and Initialize GEE")
        self.auth_btn.clicked.connect(self.authenticate_gee)
        form_layout.addWidget(self.auth_btn)

        self.geojson_label = QLabel("Selected GeoJSON: None")
        self.load_geojson_btn = QPushButton("Load GeoJSON")
        self.load_geojson_btn.clicked.connect(self.load_geojson)
        form_layout.addWidget(self.geojson_label)
        form_layout.addWidget(self.load_geojson_btn)

        self.date_layout = QHBoxLayout()
        self.start_date_input = QDateEdit(QDate.fromString("2024-01-01", "yyyy-MM-dd"))
        self.start_date_input.setCalendarPopup(True)
        self.end_date_input = QDateEdit(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.date_layout.addWidget(QLabel("Start Date:"))
        self.date_layout.addWidget(self.start_date_input)
        self.date_layout.addWidget(QLabel("End Date:"))
        self.date_layout.addWidget(self.end_date_input)
        form_layout.addLayout(self.date_layout)

        self.image_label = QLabel("Select Image:")
        self.image_dropdown = QComboBox()
        self.image_dropdown.addItems(["Sentinel-2", "Landsat 9 Surface Reflectance", "Landsat 9 TOA Reflectance", "Landsat 8 Surface Reflectance", "Landsat 8 TOA Reflectance", "Landsat 7 Surface Reflectance", "Landsat 7 TOA Reflectance"])
        form_layout.addWidget(self.image_label)
        form_layout.addWidget(self.image_dropdown)

        self.generate_btn = QPushButton("Start NDVI Plot")
        self.generate_btn.clicked.connect(self.calculate_ndvi)
        form_layout.addWidget(self.generate_btn)

        # Add the save button
        self.save_path_btn = QPushButton("Select Save Path")
        self.save_path_btn.clicked.connect(self.select_save_path)

        self.save_plot_btn = QPushButton("Save NDVI Plot")
        self.save_plot_btn.clicked.connect(self.save_ndvi_plot)

        # Add buttons to the layout
        form_layout.addWidget(self.save_path_btn)
        form_layout.addWidget(self.save_plot_btn)

        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        form_layout.addWidget(self.log_window)

        # --- Map and Graph (Right Panel) ---
        self.map_widget = MapWidget(self)
        map_graph_layout.addWidget(self.map_widget)  # Add Map Widget

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        map_graph_layout.addWidget(self.canvas)  # Add NDVI Graph below Map
        self.canvas.setFixedHeight(250)

        # Wrap map & graph in a QWidget for proper layout management
        canvas_container = QWidget()
        canvas_container.setLayout(map_graph_layout)
        canvas_container.setMinimumWidth(600)

        # --- Arrange Layouts ---
        content_layout.addLayout(form_layout, 1)  # Form takes 1 part
        content_layout.addWidget(canvas_container, 3)  # Map & Graph take 2 parts

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)  # Apply main layout
    
    def authenticate_gee(self):
        self.project = self.project_input.text().strip()
        if not self.project:
            self.log("Error: Please enter a project name before authentication!")
            return
        try:
            ee.Authenticate()  # This will prompt the user to authenticate if needed
            ee.Initialize(project=self.project)
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
    
    def update_cloud_prob(self, value):
        self.max_cloud_prob = value
        self.cloud_prob_label.setText(f"Max Cloud Probability: {value}")

    @staticmethod
    def add_ndvi(selected_image, image):
        """Calculate NDVI and add it as a new band."""
        # Sentinel-2 Bands
        if selected_image == "Sentinel-2":
            ndvi_sentinel2 = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi_sentinel2)
        else:
            if selected_image == "Landsat 9 Surface Reflectance" or selected_image == "Landsat 8 Surface Reflectance":
                ndvi_landsat = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
            elif selected_image == "Landsat 9 TOA Reflectance" or selected_image == "Landsat 8 TOA Reflectance":
                ndvi_landsat = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
            elif selected_image == "Landsat 7 Surface Reflectance":
                ndvi_landsat = image.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
            else:
                ndvi_landsat = image.normalizedDifference(['B4', 'B3']).rename('NDVI')
            return image.addBands(ndvi_landsat)

    def calculate_ndvi(self):
        if not self.geometry:
            self.log("⚠️ Please load a GeoJSON first!")
            return

        selected_image = self.image_dropdown.currentText()
        start_date = self.start_date_input.date().toString("yyyy-MM-dd")
        end_date = self.end_date_input.date().toString("yyyy-MM-dd")

        if selected_image == "Sentinel-2":
            self.log("🔄 Processing Sentinel-2 data...")
            self.s2_collection = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterDate(start_date, end_date)
                .filterBounds(self.geometry)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                .sort('CLOUDY_PIXEL_PERCENTAGE')
                .limit(50)
            )
            self.s2_collection = self.s2_collection.map(lambda img: NDVIPlotTab.add_ndvi(selected_image, img))
            
            self.ndvi = self.s2_collection.select('NDVI')
            self.log("✅ Sentinel-2 NDVI processed successfully.")

        else: 
            self.log("🔄 Processing Landsat data...")
            if selected_image == "Landsat 9 Surface Reflectance":
                l8_collection = "LANDSAT/LC09/C02/T1_L2"
            elif selected_image == "Landsat 9 TOA Reflectance":
                l8_collection = "LANDSAT/LC09/C02/T1_TOA"
            elif selected_image == "Landsat 8 Surface Reflectance":
                l8_collection = "LANDSAT/LC08/C02/T1_L2"
            elif selected_image == "Landsat 8 TOA Reflectance":
                l8_collection = "LANDSAT/LC08/C02/T1_TOA"
            elif selected_image == "Landsat 7 Surface Reflectance":
                l8_collection = "LANDSAT/LE07/C02/T1_L2"
            else:
                l8_collection = "LANDSAT/LE07/C02/T1_TOA"

            self.landsat_collection = (
                ee.ImageCollection(l8_collection)
                .filterDate(start_date, end_date)
                .filterBounds(self.geometry)
                .sort('CLOUD_COVER')
                .limit(50)
            )
            self.landsat_collection = self.landsat_collection.map(lambda img: NDVIPlotTab.add_ndvi(selected_image, img))

            self.ndvi = self.landsat_collection.select('NDVI')
            self.log("✅ Landsat NDVI processed successfully.")

        # Now that NDVI is properly calculated, proceed to plotting
        self.plot_ndvi_timeseries(self.ndvi, self.geometry)

    def plot_ndvi_timeseries(self, image_collection, region):
        """Generate and display NDVI time series plot in the PyQt UI."""

        def extract_ndvi(img):
            """Extract mean NDVI over the region and set the date property."""
            mean_ndvi = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=30,
                bestEffort=True
            ).get('NDVI')
            return img.set('date', img.date().format('YYYY-MM-dd')).set('mean_NDVI', mean_ndvi)

        def fetch_ndvi():
            try:
                ndvi_series = image_collection.map(extract_ndvi)
                ndvi_list = ndvi_series.aggregate_array('mean_NDVI').getInfo()
                date_list = ndvi_series.aggregate_array('date').getInfo()

                if not ndvi_list or not date_list:
                    self.log("⚠️ No valid NDVI data available. Possible issue with image collection.")
                    return
                
                # Debugging output
                self.update_ndvi_plot(ndvi_list, date_list)
                self.log(f"🟢 Fetched Dates: {date_list}")
                self.log(f"🟢 NDVI Value: {ndvi_list}")

            except Exception as e:
                self.log(f"❌ Error fetching NDVI data: {e}")

        # Run NDVI extraction in a separate thread
        Thread(target=fetch_ndvi).start()

    def update_ndvi_plot(self, ndvi_list, date_list):
        """Update the NDVI time series plot in the PyQt UI."""
        self.ax.clear()  # Clear old data to avoid double plotting

        # Convert date strings to datetime objects BEFORE sorting
        date_objects = [datetime.strptime(date, "%Y-%m-%d") for date in date_list]

        # Sort based on datetime objects
        sorted_dates, sorted_ndvi = zip(*sorted(zip(date_objects, ndvi_list)))

        # Store sorted data
        self.date_list = sorted_dates
        self.ndvi_list = sorted_ndvi

        # Convert sorted datetime objects to numerical format for plotting
        date_nums = mdates.date2num(self.date_list)
        self.ax.plot(date_nums, self.ndvi_list, marker='o', linestyle='-', color='green', label="NDVI")

        # Formatting
        self.ax.set_xlabel("Date", fontsize=8)
        self.ax.set_ylabel("NDVI", fontsize=10)
        self.ax.set_title("NDVI Time Series", fontsize=12)

        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10))
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

        self.ax.tick_params(axis='x', rotation=45, labelsize=8)
        self.ax.set_ylim(-1, 1)

        self.ax.legend()
        self.ax.grid()

        self.canvas.draw()

        self.log("✅ NDVI time series updated successfully!")

    def select_save_path(self):
        """Opens a file dialog to select a save path for the NDVI plot."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Save Path", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)")
        if file_path:
            self.save_path = file_path
            self.log(f"✅ Save path selected: {self.save_path}")

    def save_ndvi_plot(self):
        """Creates a separate NDVI plot with proper size and saves it."""
        if not self.save_path:
            self.log("⚠️ Please select a save path first!")
            return
        if not hasattr(self, 'date_list') or not hasattr(self, 'ndvi_list'):
            self.log("⚠️ No NDVI data available. Please generate the NDVI plot first!")
            return

        # Create a new figure with a larger size
        fig, ax = plt.subplots(figsize=(10, 5))  

        # Plot the data
        ax.plot(self.date_list, self.ndvi_list, marker='o', linestyle='-', color='green', label="NDVI")

        # Format X-axis properly
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("NDVI", fontsize=14)
        ax.set_title("NDVI Time Series", fontsize=16)

        # Set X-axis date format
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

        # Rotate labels for better readability
        ax.tick_params(axis='x', rotation=45, labelsize=10)

        # Set Y-axis range
        ax.set_ylim(-1, 1)

        # Enable grid and legend
        ax.legend()
        ax.grid()

        # Save the figure
        fig.savefig(self.save_path, dpi=300, bbox_inches="tight")
        plt.close(fig)  # Close the figure to free memory

        self.log(f"✅ NDVI plot saved to: {self.save_path}")
    
    def log(self, message):
        self.log_window.append(message)