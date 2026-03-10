"""
Streaming page — live output console, stats bar, and stream controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False

from ui.components.conn_bar import ConnBar
from ui.components.log_display import LogDisplay
from core.stream_worker import StreamWorker
from config import DEFAULT_EVENTS_PER_SECOND, EPS_OPTIONS


# LED state → objectName mapping
_LED_STATES = {
    "streaming": "led_streaming",
    "paused":    "led_paused",
    "stopped":   "led_idle",
    "error":     "led_error",
    "idle":      "led_idle",
}


class StreamingPage(QWidget):
    back_requested   = pyqtSignal()
    connected        = pyqtSignal(str, str)  # forwarded from ConnBar
    # Forwarded to MainWindow so dashboard / sidebar stay in sync
    stats_forwarded  = pyqtSignal(int, float)  # total, eps
    status_forwarded = pyqtSignal(str)         # status string
    eps_changed      = pyqtSignal(int)         # user changed the target EPS
    hub_name_changed = pyqtSignal(str)         # connection changed to a new hub

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread:  QThread       | None = None
        self._worker:  StreamWorker  | None = None
        self._use_case                      = None
        self._industry_key                  = ""
        self._conn_str = ""
        self._hub_name = ""
        self._status   = "idle"
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_connection(self, conn_str: str, hub_name: str) -> None:
        """Pre-populate ConnBar and store values for use in start_stream."""
        self._conn_str = conn_str
        self._hub_name = hub_name
        self._conn_bar.set_connection(conn_str, hub_name)

    def start_stream(
        self,
        use_case,
        industry_key: str,
        connection_string: str,
        eventhub_name: str,
    ) -> None:
        """Stop any running stream, then start a new one."""
        self._stop_worker()

        self._use_case      = use_case
        self._industry_key  = industry_key
        self._conn_str      = connection_string
        self._hub_name      = eventhub_name

        # Keep ConnBar in sync with the passed-in connection info
        if connection_string and eventhub_name:
            self._conn_bar.set_connection(connection_string, eventhub_name)

        # Update header
        self._uc_label.setText(use_case.title)
        from ui.industry_page import INDUSTRIES
        meta = next((i for i in INDUSTRIES if i["key"] == industry_key), None)
        if meta:
            self._industry_badge.setText(f"  {meta['label']}  ")
            self._industry_badge.setStyleSheet(
                "background-color: #2a2a2a; color: #ffffff; "
                "border-radius: 10px; padding: 2px 10px; font-weight: 700;"
            )

        self._log.clear_log()
        self._reset_stats()
        if not connection_string or not eventhub_name:
            self._set_status("idle")
            self._warn_lbl.setVisible(True)
            self._log.append_log(
                "⚠  Configure the Eventstream connection above, then click  ▶ Start.",
                "WARN",
            )
            self._update_controls()
            return

        self._warn_lbl.setVisible(False)
        self._set_status("streaming")

        # Instantiate generator
        import importlib
        mod_map = {
            "retail":                  "core.generators.retail",
            "healthcare":              "core.generators.healthcare",
            "finance":                 "core.generators.finance",
            "manufacturing":           "core.generators.manufacturing",
            "transportation":          "core.generators.transportation",
            "energy":                  "core.generators.energy",
            "telecom":                 "core.generators.telecom",
            "smart_city":              "core.generators.smart_city",
            "information_technology":  "core.generators.information_technology",
        }
        mod = importlib.import_module(mod_map[industry_key])
        generator = next(
            (uc.generator_class() for uc in mod.USE_CASES if uc == use_case), None
        )
        if generator is None:
            self._log.append_log("Could not find generator for this use case.", "ERROR")
            return

        eps = self._eps_selected
        self._worker = StreamWorker(connection_string, eventhub_name, generator, eps)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.event_sent.connect(self._on_event_sent)
        self._worker.stats_updated.connect(self._on_stats)
        self._worker.status_changed.connect(self._on_status_changed)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()
        self._update_controls()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ─── Top bar ────────────────────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setObjectName("page_header")
        top_bar.setFixedHeight(70)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 0, 24, 0)
        top_layout.setSpacing(14)

        self._back_btn = QPushButton("  ← Back")
        self._back_btn.setObjectName("btn_back")
        self._back_btn.setFixedWidth(100)
        self._back_btn.clicked.connect(self._on_back)
        top_layout.addWidget(self._back_btn)

        self._industry_badge = QLabel("")
        self._industry_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        top_layout.addWidget(self._industry_badge)

        self._uc_label = QLabel("—")
        self._uc_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        top_layout.addWidget(self._uc_label)

        top_layout.addStretch()

        # LED status indicator
        self._led = QLabel()
        self._led.setObjectName("led_idle")
        self._led.setFixedSize(14, 14)
        top_layout.addWidget(self._led)

        self._status_label = QLabel("Idle")
        self._status_label.setObjectName("lbl_muted")
        top_layout.addWidget(self._status_label)

        root.addWidget(top_bar)

        # ─── Eventstream connection bar ──────────────────────────────────────
        self._conn_bar = ConnBar()
        self._conn_bar.connected.connect(self._on_conn_bar_connected)
        root.addWidget(self._conn_bar)

        # ─── Connection warning (hidden until needed) ─────────────────────────
        self._warn_lbl = QLabel(
            "⚠   Connect to Eventstream above, then click  ▶ Start."
        )
        self._warn_lbl.setStyleSheet(
            "background-color: #3a1500; color: #ff9933; "
            "padding: 8px 24px; font-size: 9pt; font-weight: 600;"
        )
        self._warn_lbl.setVisible(False)
        root.addWidget(self._warn_lbl)

        # ─── Stats bar ──────────────────────────────────────────────────────
        stats_bar = QWidget()
        stats_bar.setObjectName("header_bar")
        stats_bar.setFixedHeight(80)
        stats_layout = QHBoxLayout(stats_bar)
        stats_layout.setContentsMargins(30, 10, 30, 10)
        stats_layout.setSpacing(40)

        self._total_badge, total_box = self._make_stat("0", "TOTAL SENT")
        self._eps_badge,   eps_box   = self._make_stat("0.0", "EVENTS / SEC")
        stats_layout.addLayout(total_box)
        stats_layout.addLayout(eps_box)
        stats_layout.addStretch()

        # EPS rate pill buttons
        eps_box2 = QVBoxLayout()
        eps_box2.setSpacing(4)
        rate_lbl = QLabel("Stream Rate")
        rate_lbl.setObjectName("stat_label")
        eps_box2.addWidget(rate_lbl)

        self._eps_selected = DEFAULT_EVENTS_PER_SECOND
        self._eps_btn_group = QButtonGroup(self)
        self._eps_btn_group.setExclusive(True)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        for eps_val in EPS_OPTIONS:
            btn = QPushButton(f"{eps_val}")
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setChecked(eps_val == DEFAULT_EVENTS_PER_SECOND)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e; color: #888888;
                    border: 1px solid #333333; border-radius: 6px;
                    font-size: 9pt; font-weight: 600;
                    padding: 0 10px; min-width: 38px;
                }
                QPushButton:checked {
                    background-color: #6db8f0; color: #0a1a2e;
                    border-color: #6db8f0;
                }
                QPushButton:hover:!checked { background-color: #2a2a2a; color: #cccccc; }
            """)
            self._eps_btn_group.addButton(btn, eps_val)
            btn_row.addWidget(btn)
        self._eps_btn_group.idClicked.connect(self._on_eps_selected)
        eps_unit = QLabel("eps")
        eps_unit.setObjectName("lbl_muted")
        btn_row.addWidget(eps_unit)
        eps_box2.addLayout(btn_row)
        stats_layout.addLayout(eps_box2)

        # Anomaly injection toggle
        self._anomaly_btn = QPushButton("⚡ Inject Anomaly")
        self._anomaly_btn.setCheckable(True)
        self._anomaly_btn.setFixedHeight(28)
        self._anomaly_btn.setStyleSheet("""
            QPushButton { background-color: #1e1e1e; color: #888888;
                border: 1px solid #333333; border-radius: 6px;
                font-size: 9pt; font-weight: 600; padding: 0 12px; }
            QPushButton:checked { background-color: #bf3030; color: #ffffff;
                border-color: #ff4040; }
            QPushButton:hover:!checked { background-color: #2a2a2a; color: #cccccc; }
        """)
        self._anomaly_btn.toggled.connect(self._on_anomaly_toggled)
        stats_layout.addSpacing(20)
        stats_layout.addWidget(self._anomaly_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        root.addWidget(stats_bar)

        # ─── Log output ─────────────────────────────────────────────────────
        log_container = QWidget()
        log_container.setObjectName("page_container")
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(24, 16, 24, 16)

        log_hdr = QLabel("Live Event Feed")
        log_hdr.setObjectName("lbl_section")
        log_hdr.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        log_layout.addWidget(log_hdr)

        self._log = LogDisplay()
        self._log.setMinimumHeight(300)
        log_layout.addWidget(self._log)

        root.addWidget(log_container, 1)

        # ─── Control bar ────────────────────────────────────────────────────
        ctrl_bar = QWidget()
        ctrl_bar.setObjectName("header_bar")
        ctrl_bar.setFixedHeight(70)
        ctrl_layout = QHBoxLayout(ctrl_bar)
        ctrl_layout.setContentsMargins(24, 0, 24, 0)
        ctrl_layout.setSpacing(14)

        ctrl_layout.addStretch()

        self._btn_start = QPushButton("Start")
        self._btn_start.setObjectName("btn_success")
        self._btn_start.setFixedHeight(42)
        self._btn_start.setFixedWidth(120)
        if _QTA:
            self._btn_start.setIcon(qta.icon("fa5s.play", color="#ffffff"))
        self._btn_start.clicked.connect(self._on_start_click)

        self._btn_pause = QPushButton("Pause")
        self._btn_pause.setObjectName("btn_warning")
        self._btn_pause.setFixedHeight(42)
        self._btn_pause.setFixedWidth(120)
        if _QTA:
            self._btn_pause.setIcon(qta.icon("fa5s.pause", color="#ffffff"))
        self._btn_pause.clicked.connect(self._on_pause_click)

        self._btn_stop = QPushButton("Stop")
        self._btn_stop.setObjectName("btn_danger")
        self._btn_stop.setFixedHeight(42)
        self._btn_stop.setFixedWidth(120)
        if _QTA:
            self._btn_stop.setIcon(qta.icon("fa5s.stop", color="#ffffff"))
        self._btn_stop.clicked.connect(self._on_stop_click)

        self._btn_clear = QPushButton("Clear Log")
        self._btn_clear.setFixedHeight(42)
        if _QTA:
            self._btn_clear.setIcon(qta.icon("fa5s.trash-alt", color="#a0a0c0"))
        self._btn_clear.clicked.connect(self._log.clear_log)

        for btn in [self._btn_start, self._btn_pause, self._btn_stop, self._btn_clear]:
            ctrl_layout.addWidget(btn)

        root.addWidget(ctrl_bar)

        self._update_controls()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_stat(self, default: str, label_text: str):
        """Returns (badge QLabel, QVBoxLayout)."""
        box = QVBoxLayout()
        box.setSpacing(2)
        badge = QLabel(default)
        badge.setObjectName("stat_badge")
        badge.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(label_text)
        lbl.setObjectName("stat_label")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box.addWidget(badge)
        box.addWidget(lbl)
        return badge, box

    def _set_status(self, state: str):
        self._status = state
        self._led.setObjectName(_LED_STATES.get(state, "led_idle"))
        # Re-apply stylesheet to pick up the new objectName
        self._led.setStyleSheet(self._led.styleSheet())
        self._led.style().unpolish(self._led)
        self._led.style().polish(self._led)
        self._status_label.setText(state.capitalize())

    def _reset_stats(self):
        self._total_badge.setText("0")
        self._eps_badge.setText("0.0")

    def _update_controls(self):
        is_streaming = self._status == "streaming"
        is_paused    = self._status == "paused"
        is_idle      = self._status in ("idle", "stopped", "error")

        self._btn_start.setEnabled(is_idle or is_paused)
        self._btn_pause.setEnabled(is_streaming)
        self._btn_stop.setEnabled(is_streaming or is_paused)

        # Rename start button to "Resume" when paused
        self._btn_start.setText("Resume" if is_paused else "Start")

    def _stop_worker(self):
        if self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)
        self._worker = None
        self._thread = None

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(str, str)
    def _on_conn_bar_connected(self, conn_str: str, hub_name: str):
        """Called when the ConnBar on this page establishes a connection."""
        self._conn_str = conn_str
        self._hub_name = hub_name
        self._warn_lbl.setVisible(False)
        self.connected.emit(conn_str, hub_name)
        self.hub_name_changed.emit(hub_name)

    @pyqtSlot(str)
    def _on_event_sent(self, json_str: str):
        import json
        try:
            evt = json.loads(json_str)
            self._log.append_json(evt)
        except Exception:
            self._log.append_log(json_str, "DATA")

    @pyqtSlot(int, float)
    def _on_stats(self, total: int, eps: float):
        self._total_badge.setText(f"{total:,}")
        self._eps_badge.setText(f"{eps:.1f}")
        self.stats_forwarded.emit(total, eps)

    @pyqtSlot(str)
    def _on_status_changed(self, state: str):
        self._set_status(state)
        self._update_controls()
        self.status_forwarded.emit(state)

    @pyqtSlot(str, str)
    def _on_log_message(self, message: str, level: str):
        self._log.append_log(message, level)

    @pyqtSlot(str)
    def _on_error(self, message: str):
        self._log.append_log(f"FATAL: {message}", "ERROR")

    def _on_start_click(self):
        if self._status == "paused" and self._worker:
            self._warn_lbl.setVisible(False)
            self._worker.resume()
        elif self._use_case:
            if not self._conn_str or not self._hub_name:
                self._warn_lbl.setVisible(True)
                return
            self._warn_lbl.setVisible(False)
            self.start_stream(
                self._use_case,
                self._industry_key,
                self._conn_str,
                self._hub_name,
            )

    def _on_pause_click(self):
        if self._worker:
            self._worker.pause()

    def _on_stop_click(self):
        if self._worker:
            self._worker.stop()

    def _on_eps_selected(self, eps_val: int):
        self._eps_selected = eps_val
        if self._worker:
            self._worker.set_eps(eps_val)
        self.eps_changed.emit(eps_val)

    def _on_anomaly_toggled(self, checked: bool):
        if self._worker:
            self._worker.set_anomaly_mode(checked)

    def _on_back(self):
        self._stop_worker()
        self._set_status("idle")
        self._update_controls()
        self.back_requested.emit()

    def set_back_button_visible(self, visible: bool) -> None:
        """Called by MainWindow to hide the Back button when sidebar is present."""
        self._back_btn.setVisible(visible)

    def closeEvent(self, event):
        self._stop_worker()
        event.accept()
