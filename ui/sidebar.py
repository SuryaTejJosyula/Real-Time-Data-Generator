"""
Left navigation sidebar — appears once the first stream is launched.
Provides Home, Dashboard, and per-stream navigation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False


_LED_COLORS = {
    "streaming": "#7de87d",
    "paused":    "#ffd080",
    "stopped":   "#555555",
    "error":     "#f4a0a0",
    "idle":      "#555555",
}


class _StreamItem(QWidget):
    """Compact clickable row for one stream in the sidebar list."""

    clicked = pyqtSignal()

    def __init__(self, stream_id: int, uc_title: str, industry_label: str):
        super().__init__()
        self.stream_id = stream_id
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self._led = QLabel()
        self._led.setFixedSize(8, 8)
        self._led.setStyleSheet("background-color: #555555; border-radius: 4px;")
        layout.addWidget(self._led)

        info_col = QVBoxLayout()
        info_col.setSpacing(1)

        self._title_lbl = QLabel(uc_title)
        self._title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self._title_lbl.setStyleSheet("color: #cccccc; background: transparent;")
        self._title_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self._ind_lbl = QLabel(industry_label)
        self._ind_lbl.setFont(QFont("Segoe UI", 7))
        self._ind_lbl.setStyleSheet("color: #555555; background: transparent;")

        info_col.addWidget(self._title_lbl)
        info_col.addWidget(self._ind_lbl)
        layout.addLayout(info_col, 1)

        self._refresh_style()

    def _refresh_style(self):
        bg = "#1e1e1e" if self._active else "transparent"
        self.setStyleSheet(
            f"QWidget {{ background-color: {bg}; border-radius: 8px; }}"
            "QWidget:hover { background-color: #1c1c1c; }"
        )

    def set_status(self, status: str):
        color = _LED_COLORS.get(status, "#555555")
        self._led.setStyleSheet(f"background-color: {color}; border-radius: 4px;")

    def highlight(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class SidePane(QWidget):
    """
    Fixed-width left navigation pane.

    Signals
    -------
    home_clicked       — user clicked Home
    dashboard_clicked  — user clicked Dashboard
    stream_clicked(id) — user clicked a stream item
    """

    home_clicked      = pyqtSignal()
    dashboard_clicked = pyqtSignal()
    stream_clicked    = pyqtSignal(int)  # stream_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._items: dict[int, _StreamItem] = {}
        self._active_stream: int | None = None
        self._active_nav: str = ""
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_stream(self, stream_id: int, uc_title: str, industry_label: str):
        item = _StreamItem(stream_id, uc_title, industry_label)
        item.clicked.connect(lambda sid=stream_id: self.stream_clicked.emit(sid))
        self._items[stream_id] = item
        # Insert before the trailing stretch
        stretch_idx = self._stream_layout.count() - 1
        self._stream_layout.insertWidget(stretch_idx, item)

    def remove_stream(self, stream_id: int):
        item = self._items.pop(stream_id, None)
        if item:
            self._stream_layout.removeWidget(item)
            item.deleteLater()
        if self._active_stream == stream_id:
            self._active_stream = None

    def update_stream_status(self, stream_id: int, status: str):
        item = self._items.get(stream_id)
        if item:
            item.set_status(status)

    def highlight_stream(self, stream_id: int):
        """Mark a stream row as active; un-highlight nav buttons."""
        self._active_nav = ""
        self._active_stream = stream_id
        for sid, item in self._items.items():
            item.highlight(sid == stream_id)
        self._set_nav_active(self._home_btn, False)
        self._set_nav_active(self._dash_btn, False)

    def highlight_nav(self, which: str):
        """Mark 'home' or 'dashboard' nav button as active; un-highlight streams."""
        self._active_nav = which
        self._active_stream = None
        for item in self._items.values():
            item.highlight(False)
        self._set_nav_active(self._home_btn, which == "home")
        self._set_nav_active(self._dash_btn, which == "dashboard")

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 14, 8, 14)
        layout.setSpacing(4)

        # Nav buttons
        self._home_btn = self._make_nav_btn("  Home", "fa5s.home")
        self._home_btn.clicked.connect(self._on_home)
        layout.addWidget(self._home_btn)

        self._dash_btn = self._make_nav_btn("  Dashboard", "fa5s.tachometer-alt")
        self._dash_btn.clicked.connect(self._on_dashboard)
        layout.addWidget(self._dash_btn)

        layout.addSpacing(6)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #1e1e1e; max-height: 1px; border: none;")
        layout.addWidget(div)

        layout.addSpacing(6)

        # Section label
        section_lbl = QLabel("ACTIVE STREAMS")
        section_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        section_lbl.setStyleSheet(
            "color: #444444; background: transparent; "
            "padding-left: 8px; letter-spacing: 1px;"
        )
        layout.addWidget(section_lbl)

        layout.addSpacing(4)

        # Scrollable stream list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        self._stream_container = QWidget()
        self._stream_container.setStyleSheet("background: transparent;")
        self._stream_layout = QVBoxLayout(self._stream_container)
        self._stream_layout.setContentsMargins(0, 0, 0, 0)
        self._stream_layout.setSpacing(2)
        self._stream_layout.addStretch()

        scroll.setWidget(self._stream_container)
        layout.addWidget(scroll, 1)

    def _make_nav_btn(self, text: str, icon_name: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(40)
        btn.setProperty("nav_active", False)
        if _QTA:
            btn.setIcon(qta.icon(icon_name, color="#777777"))
        btn.setStyleSheet(self._nav_btn_style(False))
        return btn

    @staticmethod
    def _nav_btn_style(active: bool) -> str:
        bg      = "#1e1e1e" if active else "transparent"
        color   = "#ffffff" if active else "#aaaaaa"
        h_color = "#ffffff"
        return (
            f"QPushButton {{ background-color: {bg}; color: {color}; "
            f"border: none; border-radius: 8px; text-align: left; "
            f"padding: 0 12px; font-size: 10pt; }}"
            f"QPushButton:hover {{ background-color: #1e1e1e; color: {h_color}; }}"
        )

    def _set_nav_active(self, btn: QPushButton, active: bool):
        btn.setStyleSheet(self._nav_btn_style(active))

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_home(self):
        self.highlight_nav("home")
        self.home_clicked.emit()

    def _on_dashboard(self):
        self.highlight_nav("dashboard")
        self.dashboard_clicked.emit()
