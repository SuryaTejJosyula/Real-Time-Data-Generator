"""
MainWindow — QStackedWidget orchestrating all pages.

Static page indices:
  0 → IndustryPage
  1 → UseCasesPage
  2 → DashboardPage
  3+ → StreamingPage instances (one per active stream, added dynamically)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QStackedWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QCloseEvent, QPixmap
import os, sys

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False

from config import APP_NAME, APP_VERSION, DEFAULT_EVENTS_PER_SECOND
from ui.industry_page import IndustryPage, INDUSTRIES
from ui.use_cases_page import UseCasesPage
from ui.streaming_page import StreamingPage
from ui.sidebar import SidePane
from ui.dashboard_page import DashboardPage

# Static page index constants
PAGE_INDUSTRY   = 0
PAGE_USE_CASES  = 1
PAGE_DASHBOARD  = 2
# Stream pages are added dynamically at indices 3+


class _DraggableHeader(QWidget):
    """Header bar that lets the user drag the frameless window."""

    def __init__(self, window: QMainWindow):
        super().__init__(window)
        self._window = window
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self._window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._window.isMaximized():
                self._window.showNormal()
            else:
                self._window.showMaximized()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._conn_str = ""
        self._hub_name = ""
        # stream_id → {page, stack_idx, use_case, industry_key, industry_label,
        #               accent, status, total, eps}
        self._streams: dict[int, dict] = {}
        self._next_stream_id = 0
        self._setup_window()
        self._build_ui()
        self._connect_signals()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 860)
        self.setObjectName("main_window")

    # ── UI layout ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Global header bar (frameless, draggable) ──
        header = _DraggableHeader(self)
        header.setObjectName("header_bar")
        header.setFixedHeight(46)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 10, 0)
        header_layout.setSpacing(0)

        # ── Left: SVG icon + app name ──
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(26, 26)
        icon_lbl.setStyleSheet("background: transparent;")
        # Resolve icon path (works both in dev and PyInstaller bundle)
        _base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        _icon_path = os.path.join(_base, "assets", "icons", "real_time_intelligence_icon.svg")
        if not os.path.exists(_icon_path):
            # fallback one directory up (dev layout: ui/ is a subdirectory of root)
            _icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets", "icons", "real_time_intelligence_icon.svg"
            )
        _pix = QPixmap(_icon_path)
        if not _pix.isNull():
            icon_lbl.setPixmap(_pix.scaled(
                26, 26,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        elif _QTA:
            icon_lbl.setPixmap(qta.icon("fa5s.database", color="#0078d4").pixmap(20, 20))
        header_layout.addWidget(icon_lbl)
        header_layout.addSpacing(9)

        app_name_lbl = QLabel(APP_NAME)
        app_name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        app_name_lbl.setStyleSheet("color: #888888; background: transparent; letter-spacing: 0.3px;")
        header_layout.addWidget(app_name_lbl)

        header_layout.addStretch(1)

        # ── Right: window control buttons ──
        _controls = [
            ("−", "#ffbd2e", self.showMinimized),
            ("+", "#28c840", self._toggle_maximize),
            ("×", "#ff5f57", self.close),
        ]
        for _label, _color, _slot in _controls:
            _btn = QPushButton()
            _btn.setFixedSize(16, 16)
            _btn.setStyleSheet(
                f"QPushButton {{ background-color: {_color}; color: transparent; "
                f"border: none; border-radius: 8px; font-size: 8pt; font-weight: 700; }}"
                f"QPushButton:hover {{ color: rgba(0,0,0,0.7); }}"
            )
            _btn.setText(_label)
            _btn.clicked.connect(_slot)
            header_layout.addWidget(_btn)
            header_layout.addSpacing(6)
        header_layout.addSpacing(4)

        main_layout.addWidget(header)

        # ── Body: sidebar (hidden until first stream) + content stack ──
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = SidePane()
        self._sidebar.setVisible(False)
        body_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._industry_page  = IndustryPage()
        self._use_cases_page = UseCasesPage()
        self._dashboard_page = DashboardPage()

        for page in [self._industry_page, self._use_cases_page, self._dashboard_page]:
            self._stack.addWidget(page)  # indices 0, 1, 2

        body_layout.addWidget(self._stack, 1)
        main_layout.addWidget(body, 1)

        self._stack.setCurrentIndex(PAGE_INDUSTRY)

    # ── Signal connections ────────────────────────────────────────────────────

    def _connect_signals(self):
        self._industry_page.industry_selected.connect(self._on_industry_selected)
        self._use_cases_page.use_case_selected.connect(self._on_use_case_selected)
        self._use_cases_page.back_requested.connect(self._on_use_cases_back)
        # Sidebar
        self._sidebar.home_clicked.connect(self._on_sidebar_home)
        self._sidebar.dashboard_clicked.connect(self._on_sidebar_dashboard)
        self._sidebar.stream_clicked.connect(self._on_sidebar_stream)
        # Dashboard
        self._dashboard_page.stream_view_clicked.connect(self._on_sidebar_stream)
        self._dashboard_page.stream_close_clicked.connect(self._remove_stream)

    # ── Navigation slots ──────────────────────────────────────────────────────

    @pyqtSlot(str)
    def _on_industry_selected(self, industry_key: str):
        self._use_cases_page.load_industry(industry_key)
        self._stack.setCurrentIndex(PAGE_USE_CASES)

    @pyqtSlot(object, str)
    def _on_use_case_selected(self, use_case, industry_key: str):
        stream_id = self._next_stream_id
        self._next_stream_id += 1

        meta           = next((i for i in INDUSTRIES if i["key"] == industry_key), None)
        industry_label = meta["label"] if meta else industry_key
        accent         = meta["color"] if meta else "#6db8f0"

        page = StreamingPage()
        # Each stream manages its own connection independently;
        # only wire hub_name_changed so the dashboard card stays in sync.
        page.hub_name_changed.connect(
            lambda hn, sid=stream_id: self._on_stream_hub_changed(sid, hn)
        )
        page.back_requested.connect(self._on_sidebar_dashboard)
        page.stats_forwarded.connect(
            lambda total, eps, sid=stream_id: self._on_stream_stats(sid, total, eps)
        )
        page.status_forwarded.connect(
            lambda status, sid=stream_id: self._on_stream_status(sid, status)
        )
        page.eps_changed.connect(
            lambda eps, sid=stream_id: self._on_stream_eps_changed(sid, eps)
        )
        page.set_connection(self._conn_str, self._hub_name)
        page.set_back_button_visible(False)

        stack_idx = self._stack.addWidget(page)

        self._streams[stream_id] = {
            "page":           page,
            "stack_idx":      stack_idx,
            "use_case":       use_case,
            "industry_key":   industry_key,
            "industry_label": industry_label,
            "accent":         accent,
            "status":         "idle",
            "total":          0,
            "eps":            0.0,
            "hub_name":       self._hub_name,
            "target_eps":     DEFAULT_EVENTS_PER_SECOND,
        }

        self._sidebar.add_stream(stream_id, use_case.title, industry_label)
        self._dashboard_page.add_stream(
            stream_id, use_case.title, industry_label, accent,
            self._hub_name, DEFAULT_EVENTS_PER_SECOND
        )

        self._sidebar.setVisible(True)
        page.start_stream(use_case, industry_key, self._conn_str, self._hub_name)
        self._stack.setCurrentIndex(stack_idx)
        self._sidebar.highlight_stream(stream_id)

    def _on_use_cases_back(self):
        if self._streams:
            self._stack.setCurrentIndex(PAGE_DASHBOARD)
            self._sidebar.highlight_nav("dashboard")
        else:
            self._stack.setCurrentIndex(PAGE_INDUSTRY)

    # ── Stream pool management ────────────────────────────────────────────────

    def _on_stream_hub_changed(self, stream_id: int, hub_name: str):
        info = self._streams.get(stream_id)
        if info:
            info["hub_name"] = hub_name
            self._dashboard_page.update_hub_name(stream_id, hub_name)

    def _on_stream_eps_changed(self, stream_id: int, eps: int):
        info = self._streams.get(stream_id)
        if info:
            info["target_eps"] = eps
            self._dashboard_page.update_target_eps(stream_id, eps)

    def _on_stream_stats(self, stream_id: int, total: int, eps: float):
        info = self._streams.get(stream_id)
        if info:
            info["total"] = total
            info["eps"]   = eps
            self._dashboard_page.update_stream(stream_id, info["status"], total, eps)

    def _on_stream_status(self, stream_id: int, status: str):
        info = self._streams.get(stream_id)
        if info:
            info["status"] = status
            self._sidebar.update_stream_status(stream_id, status)
            self._dashboard_page.update_stream(stream_id, status, info["total"], info["eps"])

    def _remove_stream(self, stream_id: int):
        info = self._streams.pop(stream_id, None)
        if not info:
            return
        page: StreamingPage = info["page"]
        page._stop_worker()
        self._stack.removeWidget(page)
        page.deleteLater()
        self._sidebar.remove_stream(stream_id)
        self._dashboard_page.remove_stream(stream_id)
        self._stack.setCurrentIndex(PAGE_DASHBOARD)
        self._sidebar.highlight_nav("dashboard")

    # ── Sidebar navigation ────────────────────────────────────────────────────

    def _on_sidebar_home(self):
        self._stack.setCurrentIndex(PAGE_INDUSTRY)

    def _on_sidebar_dashboard(self):
        self._stack.setCurrentIndex(PAGE_DASHBOARD)
        self._sidebar.highlight_nav("dashboard")

    def _on_sidebar_stream(self, stream_id: int):
        info = self._streams.get(stream_id)
        if info:
            self._stack.setCurrentIndex(info["stack_idx"])
            self._sidebar.highlight_stream(stream_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _toggle_maximize(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ── Close event ───────────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent):
        for info in self._streams.values():
            info["page"]._stop_worker()
        event.accept()
