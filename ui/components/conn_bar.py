"""
Reusable Eventstream connection bar widget.

Emits `connected(conn_str, hub_name)` on successful test.
Can be pre-populated and locked from outside via `set_connection()`.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from PyQt6.QtCore import pyqtSignal, QThread, QObject, pyqtSlot

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False


class _ConnTestWorker(QObject):
    success = pyqtSignal(str, str)
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
            self.success.emit(self._conn_str, self._hub_name)
        else:
            self.failure.emit(msg)


class ConnBar(QWidget):
    """Compact connection bar: plug icon · connection string inputs · Connect btn · LED."""

    connected    = pyqtSignal(str, str)   # conn_str, hub_name — successful test
    disconnected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._conn_str = ""
        self._hub_name = ""
        self._thread: QThread | None = None
        self._worker: _ConnTestWorker | None = None
        self.setObjectName("conn_bar")
        self._build()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_connection(self) -> tuple[str, str]:
        return self._conn_str, self._hub_name

    def is_connected(self) -> bool:
        return bool(self._conn_str and self._hub_name)

    def set_connection(self, conn_str: str, hub_name: str):
        """Pre-populate with known-good values, or reset when both are empty."""
        self._conn_str = conn_str
        self._hub_name = hub_name
        self._conn_edit.setText(conn_str)
        self._hub_edit.setText(hub_name)
        if conn_str and hub_name:
            self._set_led(True, f"Connected  ·  {hub_name}")
            self._connect_btn.setText("Connected ✓")
            self._connect_btn.setEnabled(True)
        else:
            self._set_led(None, "Not connected")
            self._connect_btn.setText("Connect")
            self._connect_btn.setEnabled(True)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        if _QTA:
            plug = QLabel()
            plug.setPixmap(qta.icon("fa5s.plug", color="#555555").pixmap(14, 14))
            plug.setStyleSheet("background: transparent;")
            layout.addWidget(plug)

        lbl = QLabel("Eventstream:")
        lbl.setStyleSheet("color: #666666; font-size: 9pt; font-weight: 600; background: transparent;")
        layout.addWidget(lbl)

        self._conn_edit = QLineEdit()
        self._conn_edit.setPlaceholderText("Connection string  (Endpoint=sb://…)")
        self._conn_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._conn_edit.setMinimumWidth(320)
        self._conn_edit.setFixedHeight(34)
        layout.addWidget(self._conn_edit, stretch=3)

        self._hub_edit = QLineEdit()
        self._hub_edit.setPlaceholderText("Event Hub name")
        self._hub_edit.setFixedHeight(34)
        self._hub_edit.setMinimumWidth(140)
        layout.addWidget(self._hub_edit, stretch=1)

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setFixedHeight(34)
        self._connect_btn.setMinimumWidth(100)
        self._connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 3px 14px; font-size: 9pt; font-weight: 700;
            }
            QPushButton:hover    { background-color: #1086d8; }
            QPushButton:pressed  { background-color: #005a9e; }
            QPushButton:disabled { background-color: #1a3a55; color: #4a6a80; }
        """)
        self._connect_btn.clicked.connect(self._test_connection)
        layout.addWidget(self._connect_btn)

        # LED
        self._led = QLabel()
        self._led.setObjectName("led_disconnected")
        self._led.setFixedSize(12, 12)
        self._led.setToolTip("Not connected")
        layout.addWidget(self._led)

        self._status_lbl = QLabel("Not connected")
        self._status_lbl.setStyleSheet("color: #555555; font-size: 8.5pt; background: transparent;")
        layout.addWidget(self._status_lbl)

        layout.addStretch()

    # ── Connection test ───────────────────────────────────────────────────────

    def _test_connection(self):
        conn_str = self._conn_edit.text().strip()
        hub_name = self._hub_edit.text().strip()
        if not conn_str or not hub_name:
            self._set_led(False, "Enter connection string and entity name")
            return

        self._connect_btn.setEnabled(False)
        self._connect_btn.setText("Testing…")
        self._set_led(None, "Testing…")

        self._thread = QThread(self)
        self._worker = _ConnTestWorker(conn_str, hub_name)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(self._on_success)
        self._worker.failure.connect(self._on_failure)
        self._worker.success.connect(self._thread.quit)
        self._worker.failure.connect(self._thread.quit)
        self._thread.start()

    @pyqtSlot(str, str)
    def _on_success(self, conn_str: str, hub_name: str):
        self._conn_str = conn_str
        self._hub_name = hub_name
        self._set_led(True, f"Connected  ·  {hub_name}")
        self._connect_btn.setEnabled(True)
        self._connect_btn.setText("Connected ✓")
        self.connected.emit(conn_str, hub_name)

    @pyqtSlot(str)
    def _on_failure(self, msg: str):
        self._conn_str = ""
        self._hub_name = ""
        self._set_led(False, msg[:70])
        self._connect_btn.setEnabled(True)
        self._connect_btn.setText("Retry")
        self.disconnected.emit()

    def _set_led(self, state, text: str):
        if state is True:
            self._led.setObjectName("led_connected")
            self._status_lbl.setStyleSheet("color: #22bb22; font-size: 8.5pt; background: transparent;")
        elif state is False:
            self._led.setObjectName("led_disconnected")
            self._status_lbl.setStyleSheet("color: #bb2222; font-size: 8.5pt; background: transparent;")
        else:
            self._led.setObjectName("led_idle")
            self._status_lbl.setStyleSheet("color: #888888; font-size: 8.5pt; background: transparent;")
        self._status_lbl.setText(text)
        self._led.style().unpolish(self._led)
        self._led.style().polish(self._led)



