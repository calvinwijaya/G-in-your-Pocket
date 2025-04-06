# splash.py
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

class FadeSplashScreen(QSplashScreen):
    def __init__(self, logo_path: str, duration: int = 2500):
        # Resize the logo nicely
        pixmap = QPixmap(logo_path).scaled(
            400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        super().__init__(pixmap)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setMask(pixmap.mask())
        self.duration = duration
        self.setWindowOpacity(0.0)

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1000)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def start(self):
        self.show()
        self.fade_anim.start()