"""
Use Cases page — shows the 6 use-case cards for the selected industry.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QSizePolicy, QGridLayout,
    QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
import os, sys

try:
    import qtawesome as qta
    _QTA = True
except ImportError:
    _QTA = False

from ui.industry_page import INDUSTRIES


# ── Icon map: use-case id → Font Awesome 5 icon name ───────────────────────────

_USE_CASE_ICONS: dict[str, str] = {
    # retail
    "retail_pos":          "fa5s.cash-register",
    "retail_inventory":    "fa5s.boxes",
    "retail_footfall":     "fa5s.walking",
    "retail_cart":         "fa5s.shopping-cart",
    "retail_loyalty":      "fa5s.star",
    "retail_price":        "fa5s.tag",
    # healthcare
    "health_vitals":       "fa5s.heartbeat",
    "health_er":           "fa5s.hospital",
    "health_medication":   "fa5s.pills",
    "health_lab":          "fa5s.flask",
    "health_device":       "fa5s.exclamation-triangle",
    "health_appointments": "fa5s.calendar-check",
    # finance
    "fin_trades":  "fa5s.chart-line",
    "fin_cards":   "fa5s.credit-card",
    "fin_fraud":   "fa5s.user-secret",
    "fin_fx":      "fa5s.exchange-alt",
    "fin_loans":   "fa5s.file-invoice-dollar",
    "fin_atm":     "fa5s.money-bill-wave",
    # manufacturing
    "mfg_sensors":     "fa5s.microchip",
    "mfg_defects":     "fa5s.times-circle",
    "mfg_throughput":  "fa5s.tachometer-alt",
    "mfg_energy":      "fa5s.bolt",
    "mfg_maintenance": "fa5s.tools",
    "mfg_materials":   "fa5s.cubes",
    # transportation
    "trans_gps":      "fa5s.map-marker-alt",
    "trans_packages": "fa5s.box",
    "trans_traffic":  "fa5s.car",
    "trans_cargo":    "fa5s.ship",
    "trans_driver":   "fa5s.cog",
    "trans_fuel":     "fa5s.gas-pump",
    # energy
    "energy_meter":     "fa5s.tachometer-alt",
    "energy_grid":      "fa5s.network-wired",
    "energy_renewable": "fa5s.solar-panel",
    "energy_pipeline":  "fa5s.water",
    "energy_outage":    "fa5s.power-off",
    "energy_forecast":  "fa5s.chart-bar",
    # telecom
    "tel_traffic": "fa5s.wifi",
    "tel_cdr":     "fa5s.phone",
    "tel_data":    "fa5s.database",
    "tel_faults":  "fa5s.exclamation-triangle",
    "tel_churn":   "fa5s.user-minus",
    "tel_sms":     "fa5s.comment",
    # smart city
    "sc_traffic":     "fa5s.road",
    "sc_air":         "fa5s.wind",
    "sc_waste":       "fa5s.trash",
    "sc_parking":     "fa5s.parking",
    "sc_transit":     "fa5s.bus",
    "sc_environment": "fa5s.leaf",
    # information technology
    "it_security":    "fa5s.shield-alt",
    "it_audit":       "fa5s.clipboard-list",
    "it_network":     "fa5s.network-wired",
    "it_system":      "fa5s.server",
}


# ── Lazy import registry ──────────────────────────────────────────────────────

def _get_use_cases(industry_key: str):
    """Return the list of UseCase objects for a given industry key."""
    mapping = {
        "retail":         "core.generators.retail",
        "healthcare":     "core.generators.healthcare",
        "finance":        "core.generators.finance",
        "manufacturing":  "core.generators.manufacturing",
        "transportation": "core.generators.transportation",
        "energy":         "core.generators.energy",
        "telecom":        "core.generators.telecom",
        "smart_city":              "core.generators.smart_city",
        "information_technology":  "core.generators.information_technology",
    }
    module_name = mapping.get(industry_key, "")
    if not module_name:
        return []
    import importlib
    mod = importlib.import_module(module_name)
    return mod.USE_CASES


# ── Use-case card widget ──────────────────────────────────────────────────────

class UseCaseCard(QFrame):
    start_clicked = pyqtSignal(object)   # emits the UseCase dataclass

    def __init__(self, use_case, accent_color: str = "#0078d4", parent=None):
        super().__init__(parent)
        self._uc = use_case
        self._accent = accent_color
        self.setObjectName("uc_card")
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Per-card scoped stylesheet mirroring the industry button aesthetic
        self.setStyleSheet(f"""
            QFrame#uc_card {{
                background-color: #161616;
                border: 1px solid #262626;
                border-radius: 16px;
            }}
            QFrame#uc_card:hover {{
                background-color: #1c1c24;
                border: 1px solid {accent_color};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 24, 22, 20)
        layout.setSpacing(0)

        # ── Icon ──────────────────────────────────────────────────────────────
        if _QTA:
            uc_id = getattr(self._uc, "id", "")
            icon_name = _USE_CASE_ICONS.get(uc_id, "fa5s.stream")
            try:
                pix = qta.icon(icon_name, color=self._accent).pixmap(46, 46)
            except Exception:
                pix = qta.icon("fa5s.stream", color=self._accent).pixmap(46, 46)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(pix)
            icon_lbl.setFixedSize(46, 46)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)

        layout.addSpacing(14)

        # ── Title ─────────────────────────────────────────────────────────────
        title_lbl = QLabel(self._uc.title)
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
        layout.addWidget(title_lbl)

        layout.addSpacing(8)

        # ── Description ───────────────────────────────────────────────────────
        desc_lbl = QLabel(self._uc.description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setFont(QFont("Segoe UI", 9))
        desc_lbl.setStyleSheet("color: #cccccc; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(desc_lbl, stretch=1)

        layout.addSpacing(16)

        # ── Divider ───────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #262626; margin: 0;")
        layout.addWidget(sep)

        layout.addSpacing(14)

        # ── Button row ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 0, 0, 0)

        details_btn = QPushButton("Details")
        details_btn.setFixedHeight(34)
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #5a5a6a;
                border: 1px solid #2e2e2e; border-radius: 8px;
                padding: 4px 14px; font-size: 9pt;
            }
            QPushButton:hover { border-color: #484858; color: #9999aa; }
        """)
        if _QTA:
            details_btn.setIcon(qta.icon("fa5s.info-circle", color="#4a4a5a"))
        details_btn.clicked.connect(self._show_details)
        btn_row.addWidget(details_btn)

        start_btn = QPushButton("  Stream")
        start_btn.setFixedHeight(34)
        # Load RTI SVG icon
        _base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        _rti = os.path.join(_base, "assets", "icons", "real_time_intelligence_icon.svg")
        if not os.path.exists(_rti):
            _rti = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets", "icons", "real_time_intelligence_icon.svg",
            )
        _pix = QPixmap(_rti)
        if not _pix.isNull():
            start_btn.setIcon(QIcon(_pix.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            start_btn.setIconSize(QSize(16, 16))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 4px 14px; font-size: 9pt; font-weight: 700;
            }
            QPushButton:hover  { background-color: #1086d8; }
            QPushButton:pressed { background-color: #005a9e; }
        """)
        start_btn.clicked.connect(lambda: self.start_clicked.emit(self._uc))
        btn_row.addWidget(start_btn, stretch=1)

        layout.addLayout(btn_row)

    def _show_details(self):
        dlg = UseCaseDetailDialog(self._uc, self._accent, parent=self)
        dlg.exec()


# ── Detail dialog ─────────────────────────────────────────────────────────────

class UseCaseDetailDialog(QDialog):
    def __init__(self, use_case, accent_color: str = "#0078d4", parent=None):
        super().__init__(parent)
        self._uc     = use_case
        self._accent = accent_color
        self.setWindowTitle(use_case.title)
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)
        self.setStyleSheet("""
            QDialog {
                background-color: #151515;
                border: 1px solid #2a2a2a;
                border-radius: 14px;
            }
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        if _QTA:
            uc_id     = getattr(self._uc, "id", "")
            icon_name = _USE_CASE_ICONS.get(uc_id, "fa5s.bolt")
            try:
                pix = qta.icon(icon_name, color=self._accent).pixmap(36, 36)
            except Exception:
                pix = qta.icon("fa5s.bolt", color=self._accent).pixmap(36, 36)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(pix)
            icon_lbl.setFixedSize(36, 36)
            icon_lbl.setStyleSheet("background: transparent;")
            title_row.addWidget(icon_lbl)
            title_row.addSpacing(10)

        title_lbl = QLabel(self._uc.title)
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {self._accent}; background: transparent;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("""
            QPushButton { background: #222222; color: #888888; border: none; border-radius: 14px; font-size: 11pt; }
            QPushButton:hover { background: #333333; color: #ffffff; }
        """)
        close_btn.clicked.connect(self.accept)
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        # Description
        sec_lbl = QLabel("Description")
        sec_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sec_lbl.setStyleSheet("color: #555555; background: transparent; letter-spacing: 1px;")
        layout.addWidget(sec_lbl)

        desc_lbl = QLabel(self._uc.description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setFont(QFont("Segoe UI", 10))
        desc_lbl.setStyleSheet("color: #cccccc; background: transparent;")
        layout.addWidget(desc_lbl)

        # JSON schema
        schema_sec = QLabel("Sample Event Schema")
        schema_sec.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        schema_sec.setStyleSheet("color: #555555; background: transparent; letter-spacing: 1px;")
        layout.addWidget(schema_sec)

        schema_box = QTextEdit()
        schema_box.setReadOnly(True)
        schema_box.setFont(QFont("Cascadia Code", 9))
        schema_box.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #70e0a0;
                border: 1px solid #202020;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        schema_box.setPlainText(self._uc.schema_preview)
        schema_box.setMaximumHeight(160)
        layout.addWidget(schema_box)

        # Use-case ID (handy reference)
        meta_lbl = QLabel(f"ID:  {getattr(self._uc, 'id', '—')}")
        meta_lbl.setFont(QFont("Cascadia Code", 8))
        meta_lbl.setStyleSheet("color: #3a3a3a; background: transparent;")
        layout.addWidget(meta_lbl)

        layout.addStretch()

        ok_btn = QPushButton("Close")
        ok_btn.setObjectName("btn_primary")
        ok_btn.setFixedHeight(38)
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignRight)

class UseCasesPage(QWidget):
    use_case_selected = pyqtSignal(object, str)  # (UseCase, industry_key)
    back_requested    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._industry_key  = ""
        self._industry_name = ""
        self._accent_color  = "#0078d4"
        self._build_ui()

    def load_industry(self, industry_key: str) -> None:
        """Populate the page for the given industry key."""
        self._industry_key = industry_key

        # Look up metadata
        meta = next((i for i in INDUSTRIES if i["key"] == industry_key), None)
        if meta:
            self._industry_name = meta["label"]
            self._accent_color  = meta["color"]

        self._title_lbl.setText(self._industry_name)
        self._title_lbl.setStyleSheet(f"color: {self._accent_color}; background: transparent;")

        # Update industry icon in header
        if _QTA and meta:
            try:
                pix = qta.icon(meta["icon"], color=meta["color"]).pixmap(28, 28)
                self._industry_icon.setPixmap(pix)
            except Exception:
                pass
        self._industry_icon.setVisible(True)

        # Rebuild cards in 3 columns
        self._clear_cards()
        use_cases = _get_use_cases(industry_key)
        for idx, uc in enumerate(use_cases):
            card = UseCaseCard(uc, self._accent_color)
            card.start_clicked.connect(
                lambda uc_=uc: self.use_case_selected.emit(uc_, self._industry_key)
            )
            row, col = divmod(idx, 3)
            self._grid.addWidget(card, row, col)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar: back + industry icon + title ──
        top_bar = QWidget()
        top_bar.setObjectName("page_header")
        top_bar.setFixedHeight(70)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 0, 24, 0)
        top_layout.setSpacing(14)

        back_btn = QPushButton("  ← Back")
        back_btn.setObjectName("btn_back")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.back_requested.emit())
        top_layout.addWidget(back_btn)

        # Industry icon — filled in by load_industry()
        self._industry_icon = QLabel()
        self._industry_icon.setFixedSize(28, 28)
        self._industry_icon.setStyleSheet("background: transparent;")
        self._industry_icon.setVisible(False)
        top_layout.addWidget(self._industry_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        self._title_lbl = QLabel("")
        self._title_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._title_lbl.setStyleSheet("background: transparent;")
        top_layout.addWidget(self._title_lbl)
        top_layout.addStretch()

        self._subtitle_lbl = QLabel("Select a use case to start streaming")
        self._subtitle_lbl.setObjectName("lbl_muted")
        top_layout.addWidget(self._subtitle_lbl)

        root.addWidget(top_bar)

        # ── Scrollable 3-column card grid ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 28, 32, 28)
        container_layout.setSpacing(0)

        self._grid = QGridLayout()
        self._grid.setSpacing(18)
        self._grid.setColumnStretch(0, 1)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(2, 1)
        container_layout.addLayout(self._grid)
        container_layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    def _clear_cards(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
