from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from tab.tab1_ui_sentinel2 import Sentinel2Tab
from tab.tab2_ui_landsat import LandsatTab
from tab.tab3_ui_falsecolor import FalseColorTab
from tab.tab4_ui_specindices import SpectralIndicesTab
from tab.tab5_ui_pca import PCATab
from tab.tab6_ui_pansharp import PansharpTab
from tab.tab7_ui_unsupervised import UnsupervisedTab
from tab.tab8_ui_supervised import SupervisedTab
from tab.tab9_ui_ndviplot import NDVIPlotTab
from tab.tab10_ui_lst import LSTTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("assets/logo.png"))
        self.setWindowTitle("G-in-your-Pocket")
        self.setGeometry(100, 70, 900, 600)
        self.setMinimumSize(800, 500)

        # Tab Widget
        self.tabs = QTabWidget()

        # Add Tabs
        self.sentinel2_tab = Sentinel2Tab()
        self.landsat_tab = LandsatTab()
        self.false_color_tab = FalseColorTab()
        self.spec_indices_tab = SpectralIndicesTab()
        self.NDVIPlotTab = NDVIPlotTab()
        self.pca_tab = PCATab()
        self.pansharp_tab = PansharpTab()
        self.unsupervised_tab = UnsupervisedTab()
        self.supervised_tab = SupervisedTab()
        self.lst_tab = LSTTab()

        self.tabs.addTab(self.sentinel2_tab, "Sentinel 2 Cloud Mask")
        self.tabs.addTab(self.landsat_tab, "Landsat Import")
        self.tabs.addTab(self.false_color_tab, "False Color Composite")
        self.tabs.addTab(self.spec_indices_tab, "Spectral Indices")
        self.tabs.addTab(self.NDVIPlotTab, "NDVI Plot")
        self.tabs.addTab(self.pca_tab, "Principal Component Analysis")
        self.tabs.addTab(self.pansharp_tab, "Pansharpening")
        self.tabs.addTab(self.unsupervised_tab, "Unsupervised Classification")
        self.tabs.addTab(self.supervised_tab, "Supervised Classification")
        self.tabs.addTab(self.lst_tab, "Land Surface Temperature")

        # Connect signals
        self.sentinel2_tab.processed_signal.connect(self.update_sentinel2_image)
        self.landsat_tab.processed_signal.connect(self.update_landsat_image)

        # Main Layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        watermark = QLabel("© Department of Geodetic Engineering FT UGM")
        watermark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        watermark.setStyleSheet("font-size: 10px; color: black;")

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        layout.addWidget(watermark)

    def update_sentinel2_image(self, image):
        self.false_color_tab.sentinel2_image = image
        self.spec_indices_tab.sentinel2_image = image
        self.pca_tab.sentinel2_image = image
        self.unsupervised_tab.sentinel2_image = image
        self.supervised_tab.sentinel2_image = image
        self.false_color_tab.select_image()
        self.spec_indices_tab.select_image()
        self.pca_tab.select_image()
        self.unsupervised_tab.select_image()
        self.supervised_tab.select_image()

    def update_landsat_image(self, image):
        self.false_color_tab.landsat_image = image
        self.spec_indices_tab.landsat_image = image
        self.pca_tab.landsat_image = image
        self.pansharp_tab.landsat_image = image
        self.unsupervised_tab.landsat_image = image
        self.supervised_tab.landsat_image = image
        self.lst_tab.landsat_image = image
        self.spec_indices_tab.select_image()
        self.false_color_tab.select_image()
        self.pca_tab.select_image()
        self.pansharp_tab.select_image()
        self.unsupervised_tab.select_image()
        self.supervised_tab.select_image()
        self.lst_tab.select_image()
