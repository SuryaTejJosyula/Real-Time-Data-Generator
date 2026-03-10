"""
Dashboard page — live analytics cards for all active streams.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False


_STATUS_COLORS = {
    "streaming": "#7de87d",
    "paused":    "#ffd080",
    "stopped":   "#555555",
    "error":     "#f4a0a0",
    "idle":      "#555555",
}

_COLS = 3   # cards per row


class _StreamCard(QFrame):
    """Analytics tile for one active stream."""

    view_clicked  = pyqtSignal(int)
    close_clicked = pyqtSignal(int)

    def __init__(
        self,
        stream_id: int,
        uc_title: str,
        industry_label: str,
        accent: str,
        hub_name: str = "",
        target_eps: int = 10,
        parent=None,
    ):
        super().__init__(parent)
        self.stream_id = stream_id
        self._accent = accent
        self.setObjectName("dash_card")
        self.setMinimumHeight(195)
        self.setMinimumWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("""
            QFrame#dash_card {
                background-color: #161616;
                border: 1px solid #252525;
                border-radius: 14px;
            }
        """)
        self._build(uc_title, industry_label, hub_name, target_eps)

    def _build(self, uc_title: str, industry_label: str, hub_name: str, target_eps: int):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 14, 14)
        root.setSpacing(6)

        # ── Header row: industry badge + hub name + close button ──
        hdr = QHBoxLayout()

        ind_badge = QLabel(f"  {industry_label}  ")
        ind_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        ind_badge.setStyleSheet(
            "background-color: #2a2a2a; color: #ffffff; "
            "border-radius: 8px; padding: 2px 6px;"
        )
        ind_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        hdr.addWidget(ind_badge)

        # Hub badge — always created so it can be updated later
        self._hub_badge = QLabel()
        self._hub_badge.setFont(QFont("Segoe UI", 7))
        self._hub_badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self._set_hub_badge_text(hub_name)
        hdr.addWidget(self._hub_badge)

        hdr.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip("Remove stream")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #444444;
                border: none; font-size: 15pt; font-weight: 700;
            }
            QPushButton:hover { color: #888888; }
        """)
        close_btn.clicked.connect(lambda: self.close_clicked.emit(self.stream_id))
        hdr.addWidget(close_btn)

        root.addLayout(hdr)

        # ── Use case title ──
        title_lbl = QLabel(uc_title)
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {self._accent};")
        title_lbl.setWordWrap(True)
        root.addWidget(title_lbl)

        # ── Stats row ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        self._total_lbl, total_col = self._stat_col("0",           "EVENTS SENT")
        self._eps_lbl,   eps_col   = self._stat_col("0.0",         "ACTUAL /s")
        self._tgt_lbl,   tgt_col   = self._stat_col(str(target_eps), "TARGET /s")

        stats_row.addLayout(total_col)
        stats_row.addLayout(eps_col)
        stats_row.addLayout(tgt_col)
        stats_row.addStretch()
        root.addLayout(stats_row)

        root.addStretch()

        # ── Footer: LED status + view button ──
        footer = QHBoxLayout()
        footer.setSpacing(6)

        self._led = QLabel()
        self._led.setFixedSize(10, 10)
        self._led.setStyleSheet("background-color: #555555; border-radius: 5px;")
        footer.addWidget(self._led)

        self._status_lbl = QLabel("Idle")
        self._status_lbl.setFont(QFont("Segoe UI", 8))
        self._status_lbl.setStyleSheet("color: #666666;")
        footer.addWidget(self._status_lbl)

        footer.addStretch()

        view_btn = QPushButton("View Logs →")
        view_btn.setFixedHeight(28)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6db8f0;
                border: 1px solid #253545;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 8pt;
                font-weight: 700;
            }
            QPushButton:hover { background-color: #1a2a3a; }
        """)
        view_btn.clicked.connect(lambda: self.view_clicked.emit(self.stream_id))
        footer.addWidget(view_btn)

        root.addLayout(footer)

    @staticmethod
    def _stat_col(default: str, label: str):
        col = QVBoxLayout()
        col.setSpacing(0)
        val_lbl = QLabel(default)
        val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val_lbl.setStyleSheet("color: #e0e0e0;")
        sub_lbl = QLabel(label)
        sub_lbl.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        sub_lbl.setStyleSheet("color: #555555; letter-spacing: 1px;")
        col.addWidget(val_lbl)
        col.addWidget(sub_lbl)
        return val_lbl, col

    def _set_hub_badge_text(self, hub_name: str):
        if hub_name:
            self._hub_badge.setText(f"  🔗 {hub_name}  ")
            self._hub_badge.setStyleSheet(
                "background-color: #1a1a2a; color: #7de8d4; "
                "border-radius: 8px; padding: 2px 6px;"
            )
        else:
            self._hub_badge.setText("  ○ Not connected  ")
            self._hub_badge.setStyleSheet(
                "background-color: #1a1a1a; color: #444444; "
                "border-radius: 8px; padding: 2px 6px;"
            )

    def update_hub_name(self, hub_name: str):
        self._set_hub_badge_text(hub_name)

    def update_target_eps(self, eps: int):
        self._tgt_lbl.setText(str(eps))

    def update_stats(self, status: str, total: int, eps: float):
        self._total_lbl.setText(f"{total:,}")
        self._eps_lbl.setText(f"{eps:.1f}")
        color = _STATUS_COLORS.get(status, "#555555")
        self._led.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        self._status_lbl.setText(status.capitalize())


class DashboardPage(QWidget):
    """
    Scrollable grid of stream analytics cards.

    Signals
    -------
    stream_view_clicked(id)  — user wants to view a stream's logs
    stream_close_clicked(id) — user dismissed a stream card
    """

    stream_view_clicked  = pyqtSignal(int)
    stream_close_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cards: dict[int, _StreamCard] = {}
        self._build_ui()

    # ── Public API ────────────────────────────────────────────────────────────

    def add_stream(
        self,
        stream_id: int,
        uc_title: str,
        industry_label: str,
        accent: str,
        hub_name: str = "",
        target_eps: int = 10,
    ):
        self._empty_lbl.setVisible(False)
        card = _StreamCard(stream_id, uc_title, industry_label, accent, hub_name, target_eps)
        card.view_clicked.connect(self.stream_view_clicked)
        card.close_clicked.connect(self.stream_close_clicked)
        self._cards[stream_id] = card
        self._relayout()
        self._update_count()

    def remove_stream(self, stream_id: int):
        card = self._cards.pop(stream_id, None)
        if card:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._relayout()
        self._update_count()
        if not self._cards:
            self._empty_lbl.setVisible(True)

    def update_stream(self, stream_id: int, status: str, total: int, eps: float):
        card = self._cards.get(stream_id)
        if card:
            card.update_stats(status, total, eps)

    def update_hub_name(self, stream_id: int, hub_name: str):
        card = self._cards.get(stream_id)
        if card:
            card.update_hub_name(hub_name)

    def update_target_eps(self, stream_id: int, eps: int):
        card = self._cards.get(stream_id)
        if card:
            card.update_target_eps(eps)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        hdr_bar = QWidget()
        hdr_bar.setObjectName("page_header")
        hdr_bar.setFixedHeight(70)
        hdr_layout = QHBoxLayout(hdr_bar)
        hdr_layout.setContentsMargins(28, 0, 28, 0)

        if _QTA:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon("fa5s.tachometer-alt", color="#8ec8f5").pixmap(22, 22))
            icon_lbl.setStyleSheet("background: transparent;")
            hdr_layout.addWidget(icon_lbl)
            hdr_layout.addSpacing(10)

        title_lbl = QLabel("Dashboard")
        title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #ffffff;")
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addStretch()

        self._count_lbl = QLabel("0 active streams")
        self._count_lbl.setObjectName("lbl_muted")
        hdr_layout.addWidget(self._count_lbl)

        root.addWidget(hdr_bar)

        # Scrollable card grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._grid_layout = QGridLayout(content)
        self._grid_layout.setContentsMargins(28, 24, 28, 24)
        self._grid_layout.setSpacing(18)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Empty state
        self._empty_lbl = QLabel("No active streams.\nClick  Home  to select an industry and start streaming.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setFont(QFont("Segoe UI", 12))
        self._empty_lbl.setStyleSheet("color: #3a3a3a; padding: 80px;")
        self._grid_layout.addWidget(self._empty_lbl, 0, 0, 1, _COLS)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _relayout(self):
        """Re-place all cards in the 3-column grid after add/remove."""
        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
        for idx, card in enumerate(self._cards.values()):
            row, col = divmod(idx, _COLS)
            self._grid_layout.addWidget(card, row, col)

    def _update_count(self):
        n = len(self._cards)
        self._count_lbl.setText(f"{n} active stream{'s' if n != 1 else ''}")
