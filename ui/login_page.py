"""
Login page — Microsoft Entra ID interactive sign-in via MSAL.
"""

import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget

try:
    import qtawesome as qta
    _QTA_AVAILABLE = True
except ImportError:
    _QTA_AVAILABLE = False

import sys

_ASSETS_DIR = os.path.join(
    getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(__file__), "..")),
    "assets",
)
_RTI_SVG = os.path.normpath(os.path.join(_ASSETS_DIR, "icons", "real_time_intelligence_icon.svg"))


class _LoginWorker(QObject):
    """Runs MSAL interactive login off the UI thread."""
    success = pyqtSignal(str)   # display_name
    failure = pyqtSignal(str)   # error message

    @pyqtSlot()
    def run(self):
        from core.auth import auth_manager
        try:
            auth_manager.login_interactive()
            self.success.emit(auth_manager.display_name)
        except Exception as exc:
            self.failure.emit(str(exc))


class LoginPage(QWidget):
    login_successful = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _LoginWorker | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Card ──
        card = QFrame()
        card.setFrameShape(QFrame.Shape.NoFrame)
        card.setObjectName("login_card")
        card.setFixedWidth(400)
        # Use object-name selector so the border only applies to THIS frame,
        # not to any child QFrame instances (avoids nested-box effect)
        card.setStyleSheet("""
            QFrame#login_card {
                background-color: #181818;
                border: 1px solid #2a2a2a;
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(52, 48, 52, 44)
        card_layout.setSpacing(0)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # ── RTI icon ──
        if os.path.exists(_RTI_SVG):
            svg_widget = QSvgWidget(_RTI_SVG)
            svg_widget.setFixedSize(80, 80)
            svg_widget.setStyleSheet("background: transparent; border: none;")
            card_layout.addWidget(svg_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        elif _QTA_AVAILABLE:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon("fa5s.bolt", color="#0078d4").pixmap(72, 72))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("background: transparent; border: none;")
            card_layout.addWidget(icon_lbl)

        card_layout.addSpacing(24)

        # ── Title ──
        title = QLabel("Fabric Real-Time\nData Generator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #f0f0f0; background: transparent; border: none;")
        card_layout.addWidget(title)

        card_layout.addSpacing(36)

        # ── Status label (hidden until needed) ──
        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setFont(QFont("Segoe UI", 9))
        self._status_lbl.setStyleSheet("color: #666666; background: transparent; border: none;")
        self._status_lbl.setVisible(False)
        card_layout.addWidget(self._status_lbl)

        # ── Sign-in button ──
        self._btn_login = QPushButton("Sign in with Microsoft")
        self._btn_login.setObjectName("btn_primary")
        self._btn_login.setFixedHeight(48)
        self._btn_login.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        if _QTA_AVAILABLE:
            self._btn_login.setIcon(qta.icon("fa5b.microsoft", color="#ffffff"))
        self._btn_login.clicked.connect(self._start_login)
        card_layout.addWidget(self._btn_login)

        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Login logic ───────────────────────────────────────────────────────────

    def _start_login(self):
        self._set_busy(True)
        self._show_status("Opening Microsoft login window…", "#666666")

        self._thread = QThread()
        self._worker = _LoginWorker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.success.connect(self._thread.quit)
        self._worker.failure.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @pyqtSlot(str)
    def _on_success(self, display_name: str):
        self._set_busy(False)
        self._show_status(f"Welcome, {display_name}!", "#40d080")
        self.login_successful.emit()

    @pyqtSlot(str)
    def _on_failure(self, message: str):
        self._set_busy(False)
        self._show_status(f"Sign-in failed: {message}", "#e05050")

    def _set_busy(self, busy: bool):
        self._btn_login.setEnabled(not busy)
        self._btn_login.setText("Signing in…" if busy else "Sign in with Microsoft")

    def _show_status(self, message: str, color: str = "#666666"):
        self._status_lbl.setText(message)
        self._status_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        self._status_lbl.setVisible(True)
