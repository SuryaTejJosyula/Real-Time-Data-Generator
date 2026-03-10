"""
Application entry point.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFontDatabase, QFont

# When running as a PyInstaller bundle, data files live under sys._MEIPASS;
# when running from source they live next to main.py.
if getattr(sys, "frozen", False):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Make sure internal packages resolve
sys.path.insert(0, os.path.dirname(__file__))

from config import APP_NAME
from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    qss_path = os.path.join(_BASE_DIR, "assets", "styles", "dark_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> None:
    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Microsoft")

    # Apply global dark stylesheet
    load_stylesheet(app)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
