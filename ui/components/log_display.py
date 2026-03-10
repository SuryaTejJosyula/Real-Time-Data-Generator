"""
LogDisplay — a QTextEdit that appends color-coded JSON/event log lines,
auto-scrolls to the bottom, and caps the rolling buffer at LOG_MAX_LINES.
"""

import html
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor

from config import LOG_MAX_LINES

# Colour palette keyed by log level
_LEVEL_COLORS = {
    "INFO":    "#60cfff",
    "SUCCESS": "#40e090",
    "WARNING": "#ffcc44",
    "ERROR":   "#ff6060",
    "DATA":    "#c0e0ff",
    "SYSTEM":  "#a080ff",
    "PAUSED":  "#ffcc44",
    "STOPPED": "#ff8040",
}

_TS_COLOR   = "#505070"
_JSON_KEY   = "#80b4ff"
_JSON_VAL   = "#a0e0a0"
_JSON_STR   = "#f0a060"


class LogDisplay(QTextEdit):
    """
    Self-contained scrolling log widget intended for real-time event output.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("log_panel")
        self._line_count = 0

        # Batch pending lines to reduce re-paint overhead under high throughput
        self._pending: list[str] = []
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(80)   # flush every 80 ms
        self._flush_timer.timeout.connect(self._flush)
        self._flush_timer.start()

    # ── Public API ────────────────────────────────────────────────────────────

    def append_log(self, message: str, level: str = "INFO") -> None:
        """Queue a plain-text log entry (will be flushed on next timer tick)."""
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = _LEVEL_COLORS.get(level.upper(), "#e0e0f0")
        ts_span  = f'<span style="color:{_TS_COLOR};">[{ts}]</span>'
        lvl_span = f'<span style="color:{color};font-weight:700;">{html.escape(level.upper()[:7])}</span>'
        msg_span = f'<span style="color:{color};">{html.escape(message)}</span>'
        self._pending.append(f'{ts_span} {lvl_span} {msg_span}')

    def append_json(self, event_dict: dict, level: str = "DATA") -> None:
        """Queue a JSON-coloured event entry."""
        import json
        raw = json.dumps(event_dict, default=str)
        self.append_log(raw, level)

    def clear_log(self) -> None:
        self._pending.clear()
        self.clear()
        self._line_count = 0

    # ── Internal ──────────────────────────────────────────────────────────────

    def _flush(self) -> None:
        if not self._pending:
            return

        lines = self._pending[:]
        self._pending.clear()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

        for line in lines:
            self.append(line)
            self._line_count += 1

        # Rolling cap — remove oldest lines
        excess = self._line_count - LOG_MAX_LINES
        if excess > 0:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(excess):
                cursor.movePosition(QTextCursor.MoveOperation.Down,
                                    QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            self._line_count = LOG_MAX_LINES

        # Auto-scroll
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
