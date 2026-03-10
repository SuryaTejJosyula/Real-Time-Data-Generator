"""
Config page — user enters the Fabric Eventstream Custom App connection string
and optionally tests the connection before proceeding.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False


class _TestWorker(QObject):
    success = pyqtSignal(str)
    failure = pyqtSignal(str)

    def __init__(self, conn_str: str, hub_name: str):
        super().__init__()
        self._conn_str = conn_str
        self._hub_name = hub_name

    @pyqtSlot()
    def run(self):
        from core.eventhub_client import EventHubClient
        ok, msg = EventHubClient.test_connection(self._conn_str, self._hub_name)
        if ok:
            self.success.emit(msg)
        else:
            self.failure.emit(msg)


class ConfigPage(QWidget):
    connected = pyqtSignal(str, str)   # connection_string, eventhub_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _TestWorker | None = None
        self._build_ui()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def connection_string(self) -> str:
        return self._conn_edit.text().strip()

    @property
    def eventhub_name(self) -> str:
        return self._hub_edit.text().strip()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(0)

        card = QFrame()
        card.setFixedWidth(640)
        card.setStyleSheet(
            "QFrame { background-color: #12121f; border: 1px solid #2a2a50; "
            "border-radius: 18px; }"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(18)

        # ── Header ──
        hdr = QHBoxLayout()
        if _QTA:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon("fa5s.plug", color="#0078d4").pixmap(32, 32))
            hdr.addWidget(icon_lbl)
        title = QLabel("Configure Eventstream Endpoint")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setObjectName("lbl_subtitle")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        sub = QLabel(
            "Enter your Fabric Eventstream <b>Custom App</b> connection string and Event Hub name."
        )
        sub.setObjectName("lbl_muted")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #2a2a50;")
        layout.addWidget(div)

        # ── Connection string ──
        layout.addWidget(self._field_label("Connection String"))
        self._conn_edit = QLineEdit()
        self._conn_edit.setPlaceholderText(
            "Endpoint=sb://...servicebus.windows.net/;SharedAccessKeyName=...;SharedAccessKey=...;EntityPath=..."
        )
        self._conn_edit.setEchoMode(QLineEdit.EchoMode.Password)  # mask key by default
        self._conn_edit.setFixedHeight(42)
        layout.addWidget(self._conn_edit)

        # Toggle visibility
        toggle_row = QHBoxLayout()
        self._toggle_btn = QPushButton("Show")
        self._toggle_btn.setFixedWidth(70)
        self._toggle_btn.setFixedHeight(30)
        self._toggle_btn.clicked.connect(self._toggle_visibility)
        toggle_row.addStretch()
        toggle_row.addWidget(self._toggle_btn)
        layout.addLayout(toggle_row)

        # ── Event Hub / Entity name ──
        layout.addWidget(self._field_label("Event Hub Name  (EntityPath)"))
        self._hub_edit = QLineEdit()
        self._hub_edit.setPlaceholderText("e.g.  es_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        self._hub_edit.setFixedHeight(42)
        layout.addWidget(self._hub_edit)

        # ── Status label ──
        self._status_lbl = QLabel("")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setObjectName("lbl_muted")
        self._status_lbl.setVisible(False)
        layout.addWidget(self._status_lbl)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        self._test_btn = QPushButton("  Test Connection")
        self._test_btn.setFixedHeight(42)
        if _QTA:
            self._test_btn.setIcon(qta.icon("fa5s.vial", color="#60cfff"))
        self._test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(self._test_btn)

        self._continue_btn = QPushButton("  Continue  →")
        self._continue_btn.setObjectName("btn_primary")
        self._continue_btn.setFixedHeight(42)
        self._continue_btn.setEnabled(False)
        self._continue_btn.clicked.connect(self._on_continue)
        btn_row.addWidget(self._continue_btn)
        layout.addLayout(btn_row)

        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("lbl_section")
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        return lbl

    # ── Interactions ──────────────────────────────────────────────────────────

    def _toggle_visibility(self):
        if self._conn_edit.echoMode() == QLineEdit.EchoMode.Password:
            self._conn_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_btn.setText("Hide")
        else:
            self._conn_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_btn.setText("Show")

    def _test_connection(self):
        conn = self.connection_string
        hub  = self.eventhub_name
        if not conn or not hub:
            self._show_status("Please fill in both fields.", "#ffcc44")
            return

        self._set_busy(True)
        self._show_status("Testing connection…", "#a0c0f0")

        self._thread = QThread()
        self._worker = _TestWorker(conn, hub)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_test_success)
        self._worker.failure.connect(self._on_test_failure)
        self._worker.success.connect(self._thread.quit)
        self._worker.failure.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @pyqtSlot(str)
    def _on_test_success(self, msg: str):
        self._set_busy(False)
        self._show_status(f"✓ {msg}", "#40e090")
        self._continue_btn.setEnabled(True)

    @pyqtSlot(str)
    def _on_test_failure(self, msg: str):
        self._set_busy(False)
        self._show_status(f"✗ {msg}", "#ff6060")
        self._continue_btn.setEnabled(False)

    def _on_continue(self):
        self.connected.emit(self.connection_string, self.eventhub_name)

    def _set_busy(self, busy: bool):
        self._test_btn.setEnabled(not busy)
        self._continue_btn.setEnabled(False)

    def _show_status(self, message: str, color: str = "#a0a0c0"):
        self._status_lbl.setText(message)
        self._status_lbl.setStyleSheet(f"color: {color};")
        self._status_lbl.setVisible(True)
