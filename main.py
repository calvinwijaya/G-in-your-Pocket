import sys
from PyQt6.QtWidgets import QApplication
from splash import FadeSplashScreen
from ui_main import MainWindow
from PyQt6.QtCore import QTimer

main_window = None

def start_main_window():
    global main_window
    main_window = MainWindow()
    main_window.show()
    splash.finish(main_window)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())

    splash = FadeSplashScreen("assets/logo.png", duration=2500)
    splash.start()

    QTimer.singleShot(splash.duration, start_main_window)

    sys.exit(app.exec())