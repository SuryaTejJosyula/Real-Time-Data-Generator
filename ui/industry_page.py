"""
Industry selection page — 9 bouncy icon-buttons in a grid.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False

from ui.components.bounce_button import BounceButton


# ── Industry registry ─────────────────────────────────────────────────────────

INDUSTRIES = [
    {
        "key":   "retail",
        "label": "Retail",
        "icon":  "fa5s.shopping-cart",
        "color": "#f9c784",
    },
    {
        "key":   "healthcare",
        "label": "Healthcare",
        "icon":  "fa5s.heartbeat",
        "color": "#f4a0a0",
    },
    {
        "key":   "finance",
        "label": "Finance & Banking",
        "icon":  "fa5s.chart-line",
        "color": "#8de8b0",
    },
    {
        "key":   "manufacturing",
        "label": "Manufacturing",
        "icon":  "fa5s.industry",
        "color": "#8ec8f5",
    },
    {
        "key":   "transportation",
        "label": "Transportation",
        "icon":  "fa5s.truck",
        "color": "#c4a0e8",
    },
    {
        "key":   "energy",
        "label": "Energy & Utilities",
        "icon":  "fa5s.bolt",
        "color": "#ffd080",
    },
    {
        "key":   "telecom",
        "label": "Telecommunications",
        "icon":  "fa5s.broadcast-tower",
        "color": "#7de8d4",
    },
    {
        "key":   "smart_city",
        "label": "Smart City / IoT",
        "icon":  "fa5s.city",
        "color": "#80dcf0",
    },
    {
        "key":   "information_technology",
        "label": "Information Technology",
        "icon":  "fa5s.server",
        "color": "#b0a0f8",
    },
]


# ── Page ─────────────────────────────────────────────────────────────────────

class IndustryPage(QWidget):
    industry_selected = pyqtSignal(str)      # industry "key"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Page body ──
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(40, 24, 40, 24)
        body_layout.setSpacing(20)

        # ── Page header ──
        title = QLabel("Select Industry")
        title.setObjectName("lbl_title")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        body_layout.addWidget(title)

        sub = QLabel("Choose an industry to explore real-time data use cases")
        sub.setObjectName("lbl_muted")
        body_layout.addWidget(sub)

        # ── 2×4 grid of industry buttons ──
        grid = QGridLayout()
        grid.setSpacing(16)

        for idx, industry in enumerate(INDUSTRIES):
            btn = self._make_industry_button(industry)
            row, col = divmod(idx, 4)
            grid.addWidget(btn, row, col)

        body_layout.addLayout(grid)
        body_layout.addStretch()

        root.addWidget(body, stretch=1)

    def _make_industry_button(self, industry: dict) -> BounceButton:
        btn = BounceButton(parent=self)
        btn.setObjectName("industry_btn")
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(130)

        color = industry["color"]
        key   = industry["key"]
        label = industry["label"]

        if _QTA:
            icon = qta.icon(industry["icon"], color=color)
            btn.setIcon(icon)
            from PyQt6.QtCore import QSize
            btn.setIconSize(QSize(36, 36))

        btn.setText(f"\n{label}")
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        # Subtle per-industry accent on hover — only the icon color changes,
        # border stays low-key grey so there's no bright highlight box
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #161616;
                color: #cccccc;
                border: 1px solid #282828;
                border-radius: 16px;
                padding: 20px 10px;
                font-size: 11pt;
                font-weight: 700;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #1e1e1e;
                border-color: #383838;
                color: {color};
            }}
            QPushButton:pressed {{
                background-color: #252525;
                border-color: #444444;
            }}
            """
        )

        btn.clicked.connect(lambda _checked, k=key: self.industry_selected.emit(k))
        return btn


