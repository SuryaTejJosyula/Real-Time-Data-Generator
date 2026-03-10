"""
Eventstream Picker Page — discover Fabric Eventstreams and auto-connect.

Flow:
  Page becomes visible → load_workspaces() called from MainWindow
    → workspaces load in background thread
  User picks a workspace → eventstreams load in background thread
  User picks an eventstream → Custom Endpoint connection string fetched
    → Success: emit connection_ready(conn_str, entity_name)
    → No endpoint / API error: show message, offer manual fallback
  "Connect Manually" button: emit skip_requested() at any time
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False


# ── Background workers ────────────────────────────────────────────────────────

class _WorkspaceLoader(QObject):
    done    = pyqtSignal(list)   # list of workspace dicts
    failure = pyqtSignal(str)

    @pyqtSlot()
    def run(self):
        try:
            from core.fabric_api import list_workspaces
            from core.auth import auth_manager
            token = auth_manager.access_token
            if not token:
                self.failure.emit("Not authenticated.  Please sign in again.")
                return
            self.done.emit(list_workspaces(token))
        except Exception as exc:
            self.failure.emit(str(exc))


class _EventstreamLoader(QObject):
    done    = pyqtSignal(list)
    failure = pyqtSignal(str)

    def __init__(self, workspace_id: str):
        super().__init__()
        self._ws_id = workspace_id

    @pyqtSlot()
    def run(self):
        try:
            from core.fabric_api import list_eventstreams
            from core.auth import auth_manager
            token = auth_manager.access_token
            self.done.emit(list_eventstreams(token, self._ws_id))
        except Exception as exc:
            self.failure.emit(str(exc))


class _EndpointLoader(QObject):
    done    = pyqtSignal(str, str)   # conn_str, entity_name
    failure = pyqtSignal(str)

    def __init__(self, workspace_id: str, eventstream_id: str):
        super().__init__()
        self._ws_id = workspace_id
        self._es_id = eventstream_id

    @pyqtSlot()
    def run(self):
        try:
            from core.fabric_api import get_custom_endpoint
            from core.auth import auth_manager
            token = auth_manager.access_token
            conn_str, entity = get_custom_endpoint(token, self._ws_id, self._es_id)
            self.done.emit(conn_str, entity)
        except Exception as exc:
            self.failure.emit(str(exc))


# ── Page ──────────────────────────────────────────────────────────────────────

class EventstreamPickerPage(QWidget):
    """
    Full-page Eventstream picker.

    Signals:
        connection_ready(conn_str, entity_name) — auto-discovered endpoint
        skip_requested()                        — user chose manual entry
    """

    connection_ready = pyqtSignal(str, str)
    skip_requested   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker = None
        self._conn_str = ""
        self._entity   = ""
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def load_workspaces(self) -> None:
        """Start loading workspaces in the background. Call this after login."""
        self._reset_connection()
        self._ws_combo.blockSignals(True)
        self._ws_combo.clear()
        self._ws_combo.addItem("Loading workspaces…")
        self._ws_combo.setEnabled(False)
        self._ws_combo.blockSignals(False)

        self._es_combo.blockSignals(True)
        self._es_combo.clear()
        self._es_combo.addItem("Select a workspace first")
        self._es_combo.setEnabled(False)
        self._es_combo.blockSignals(False)

        self._set_status("loading", "Connecting to Microsoft Fabric…")
        self._connect_btn.setEnabled(False)
        self._launch(self._attach_workspace_loader)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Card panel ──────────────────────────────────────────────────────
        panel = QFrame()
        panel.setObjectName("es_picker_card")
        panel.setFixedWidth(640)
        panel.setStyleSheet("""
            QFrame#es_picker_card {
                background-color: #181820;
                border: 1px solid #2a2a3e;
                border-radius: 18px;
            }
        """)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(52, 44, 52, 40)
        pl.setSpacing(0)

        # ── Icon + title row ──────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(14)

        if _QTA:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(
                qta.icon("fa5s.stream", color="#0078d4").pixmap(28, 28)
            )
            icon_lbl.setStyleSheet("background: transparent;")
            title_row.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        title_lbl = QLabel("Connect to Eventstream")
        title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #f0f0f0; background: transparent;")
        title_row.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch()
        pl.addLayout(title_row)

        pl.addSpacing(10)

        subtitle = QLabel(
            "Select a Fabric workspace and Eventstream. The app will automatically "
            "read the Custom Endpoint connection string so you can start streaming "
            "without any manual copy-paste.\n"
            "If no Custom Endpoint source is configured, use Connect Manually."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            "color: #777788; font-size: 9.5pt; background: transparent; "
            "line-height: 1.5;"
        )
        pl.addWidget(subtitle)

        pl.addSpacing(30)

        # ── Workspace selector ────────────────────────────────────────────
        ws_lbl = QLabel("Workspace")
        ws_lbl.setStyleSheet(
            "color: #aaaacc; font-size: 9pt; font-weight: 700; background: transparent;"
        )
        pl.addWidget(ws_lbl)
        pl.addSpacing(6)

        self._ws_combo = QComboBox()
        self._ws_combo.setFixedHeight(40)
        self._ws_combo.setStyleSheet(self._combo_css())
        self._ws_combo.addItem("Loading workspaces…")
        self._ws_combo.setEnabled(False)
        self._ws_combo.currentIndexChanged.connect(self._on_workspace_changed)
        pl.addWidget(self._ws_combo)

        pl.addSpacing(20)

        # ── Eventstream selector ──────────────────────────────────────────
        es_lbl = QLabel("Eventstream")
        es_lbl.setStyleSheet(
            "color: #aaaacc; font-size: 9pt; font-weight: 700; background: transparent;"
        )
        pl.addWidget(es_lbl)
        pl.addSpacing(6)

        self._es_combo = QComboBox()
        self._es_combo.setFixedHeight(40)
        self._es_combo.setStyleSheet(self._combo_css())
        self._es_combo.addItem("Select a workspace first")
        self._es_combo.setEnabled(False)
        self._es_combo.currentIndexChanged.connect(self._on_eventstream_changed)
        pl.addWidget(self._es_combo)

        pl.addSpacing(22)

        # ── Status row ────────────────────────────────────────────────────
        status_row = QHBoxLayout()
        status_row.setSpacing(10)
        status_row.setContentsMargins(0, 0, 0, 0)

        self._status_led = QLabel()
        self._status_led.setObjectName("led_idle")
        self._status_led.setFixedSize(10, 10)
        status_row.addWidget(self._status_led, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._status_lbl = QLabel("Waiting…")
        self._status_lbl.setStyleSheet(
            "color: #666677; font-size: 9pt; background: transparent;"
        )
        status_row.addWidget(self._status_lbl, 1)
        pl.addLayout(status_row)

        pl.addSpacing(30)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._skip_btn = QPushButton("Connect Manually")
        self._skip_btn.setFixedHeight(42)
        self._skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #888899;
                border: 1px solid #333344; border-radius: 8px;
                padding: 6px 20px; font-size: 9.5pt;
            }
            QPushButton:hover { border-color: #555566; color: #aaaacc; }
        """)
        self._skip_btn.clicked.connect(lambda: self.skip_requested.emit())
        btn_row.addWidget(self._skip_btn)

        btn_row.addStretch()

        self._connect_btn = QPushButton("Connect  →")
        self._connect_btn.setObjectName("btn_primary")
        self._connect_btn.setFixedHeight(42)
        self._connect_btn.setFixedWidth(160)
        self._connect_btn.setEnabled(False)
        self._connect_btn.clicked.connect(self._on_connect_clicked)
        btn_row.addWidget(self._connect_btn)

        pl.addLayout(btn_row)

        root.addWidget(panel)

    # ── Combo stylesheet ──────────────────────────────────────────────────────

    @staticmethod
    def _combo_css() -> str:
        return """
            QComboBox {
                background-color: #0d0d18; color: #ddddee;
                border: 1px solid #2e2e4e; border-radius: 8px;
                padding: 6px 12px; font-size: 9.5pt;
            }
            QComboBox:disabled {
                color: #444455; border-color: #1a1a2e;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 28px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0; height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666677;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #12121e; color: #ddddee;
                border: 1px solid #2e2e4e;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                outline: none;
                padding: 4px 0;
            }
            QComboBox QAbstractItemView::item {
                padding: 6px 12px;
                min-height: 28px;
            }
        """

    # ── State helpers ─────────────────────────────────────────────────────────

    def _reset_connection(self):
        self._conn_str = ""
        self._entity   = ""
        self._connect_btn.setEnabled(False)

    def _set_status(self, state: str, text: str):
        _led_map = {
            "loading": "led_idle",
            "ok":      "led_connected",
            "error":   "led_disconnected",
            "warn":    "led_paused",
            "idle":    "led_idle",
        }
        _color_map = {
            "ok":    "#33cc55",
            "error": "#cc3333",
            "warn":  "#dd9900",
        }
        self._status_led.setObjectName(_led_map.get(state, "led_idle"))
        self._status_led.style().unpolish(self._status_led)
        self._status_led.style().polish(self._status_led)
        color = _color_map.get(state, "#666677")
        self._status_lbl.setStyleSheet(
            f"color: {color}; font-size: 9pt; background: transparent;"
        )
        self._status_lbl.setText(text)

    # ── Worker management ─────────────────────────────────────────────────────

    def _launch(self, attach_fn):
        """Stop current thread, create a new one, attach worker via attach_fn."""
        self._stop_thread()
        self._thread = QThread(self)
        attach_fn(self._thread)
        self._thread.start()

    def _stop_thread(self):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        self._thread = None
        self._worker = None

    def _attach_workspace_loader(self, thread: QThread):
        worker = _WorkspaceLoader()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(self._on_workspaces_loaded)
        worker.failure.connect(self._on_general_failure)
        worker.done.connect(thread.quit)
        worker.failure.connect(thread.quit)
        self._worker = worker

    def _attach_eventstream_loader(self, ws_id: str, thread: QThread):
        worker = _EventstreamLoader(ws_id)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(self._on_eventstreams_loaded)
        worker.failure.connect(self._on_general_failure)
        worker.done.connect(thread.quit)
        worker.failure.connect(thread.quit)
        self._worker = worker

    def _attach_endpoint_loader(
        self, ws_id: str, es_id: str, thread: QThread
    ):
        worker = _EndpointLoader(ws_id, es_id)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.done.connect(self._on_endpoint_found)
        worker.failure.connect(self._on_endpoint_failure)
        worker.done.connect(thread.quit)
        worker.failure.connect(thread.quit)
        self._worker = worker

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(list)
    def _on_workspaces_loaded(self, workspaces: list):
        self._ws_combo.blockSignals(True)
        self._ws_combo.clear()
        if workspaces:
            self._ws_combo.addItem("— Select workspace —", None)
            for ws in workspaces:
                label = ws.get("displayName", ws["id"])
                # Mark Fabric-capacity workspaces with an indicator
                if ws.get("capacityId"):
                    label = "⚡ " + label
                self._ws_combo.addItem(label, ws["id"])
            self._ws_combo.setEnabled(True)
            self._set_status(
                "idle",
                f"{len(workspaces)} workspace(s) loaded  —  select one to see its Eventstreams",
            )
        else:
            self._ws_combo.addItem("No workspaces found")
            self._ws_combo.setEnabled(False)
            self._set_status(
                "warn",
                "No workspaces found.  Make sure you have access to a Fabric-enabled workspace.",
            )
        self._ws_combo.blockSignals(False)

    @pyqtSlot(str)
    def _on_general_failure(self, msg: str):
        self._set_status("error", f"Error: {msg[:120]}")
        self._ws_combo.setEnabled(True)

    @pyqtSlot(int)
    def _on_workspace_changed(self, index: int):
        ws_id = self._ws_combo.itemData(index)
        self._reset_connection()

        self._es_combo.blockSignals(True)
        self._es_combo.clear()
        self._es_combo.setEnabled(False)
        self._es_combo.blockSignals(False)

        if not ws_id:
            self._set_status("idle", "Select a workspace to list its Eventstreams")
            return

        self._es_combo.blockSignals(True)
        self._es_combo.addItem("Loading Eventstreams…")
        self._es_combo.blockSignals(False)

        self._set_status("loading", "Loading Eventstreams in this workspace…")
        self._launch(lambda t: self._attach_eventstream_loader(ws_id, t))

    @pyqtSlot(list)
    def _on_eventstreams_loaded(self, eventstreams: list):
        self._es_combo.blockSignals(True)
        self._es_combo.clear()
        if eventstreams:
            self._es_combo.addItem("— Select Eventstream —", None)
            for es in eventstreams:
                self._es_combo.addItem(es.get("displayName", es["id"]), es["id"])
            self._es_combo.setEnabled(True)
            self._set_status(
                "idle",
                f"{len(eventstreams)} Eventstream(s) found  —  select one to auto-connect",
            )
        else:
            self._es_combo.addItem("No Eventstreams in this workspace")
            self._es_combo.setEnabled(False)
            self._set_status(
                "warn",
                "No Eventstreams found in this workspace.  "
                "Try a different workspace or connect manually.",
            )
        self._es_combo.blockSignals(False)

    @pyqtSlot(int)
    def _on_eventstream_changed(self, index: int):
        es_id = self._es_combo.itemData(index)
        self._reset_connection()

        if not es_id:
            self._set_status("idle", "Select an Eventstream to auto-configure the connection")
            return

        ws_id = self._ws_combo.currentData()
        if not ws_id:
            self._set_status("error", "No workspace selected")
            return

        es_name = self._es_combo.currentText()
        self._set_status("loading", f"Fetching Custom Endpoint details for '{es_name}'…")
        self._launch(lambda t: self._attach_endpoint_loader(ws_id, es_id, t))

    @pyqtSlot(str, str)
    def _on_endpoint_found(self, conn_str: str, entity: str):
        self._conn_str = conn_str
        self._entity   = entity
        es_name = self._es_combo.currentText()
        entity_display = f" · {entity}" if entity else ""
        self._set_status("ok", f"Ready  ·  {es_name}{entity_display}")
        self._connect_btn.setEnabled(True)

    @pyqtSlot(str)
    def _on_endpoint_failure(self, msg: str):
        self._set_status("warn", msg)
        self._connect_btn.setEnabled(False)

    def _on_connect_clicked(self):
        if self._conn_str:
            self.connection_ready.emit(self._conn_str, self._entity)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._stop_thread()
        event.accept()
