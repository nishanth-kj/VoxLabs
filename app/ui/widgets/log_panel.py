"""Logs panel (VS Code "Output" style) at the bottom of the main window.

Each line shows when, how serious and who made the call:

    18:20:18  INFO     API     POST /api/tts (412 ms)
    18:20:19  WARNING  UI      Editor autosave failed: …

Levels are color-coded (debug muted, info blue, warnings amber, errors red); the source
(UI, API, MCP, System) is in the accent color. Filters narrow by source, level and text,
and every filter has an "All" option. The panel keeps the last 2000 records; the full
history is in data/logs/voxlabs.log (the file button opens it).

It polls the in-memory log buffer for records newer than the last one it saw, so it stays
live without touching the logging threads.
"""

from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
)

from app.services.system_service import system_service
from app.ui import icons, theme
from app.utils.logger import LOG_BUFFER_SIZE

LEVEL_RANK = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}
LEVEL_FILTERS = (("All levels", "debug"), ("Info and above", "info"), ("Warnings and errors", "warning"),
                 ("Errors only", "error"))
SOURCE_FILTERS = (("All sources", None), ("Desktop UI", "ui"), ("REST API", "api"), ("MCP", "mcp"),
                  ("System", "system"))
SOURCE_LABELS = {"ui": "UI", "api": "API", "mcp": "MCP", "system": "System"}
MONO_FONTS = ["Cascadia Mono", "Consolas", "SF Mono", "Menlo", "JetBrains Mono", "DejaVu Sans Mono", "Ubuntu Mono",
              "Liberation Mono", "Courier New"]
POLL_MS = 700


def level_color(level: str) -> str:
    colors = theme.current()
    return {"debug": colors.text_muted, "info": colors.info, "warning": colors.warning}.get(level, colors.danger)


class LogPanel(QFrame):
    closed = Signal()
    counts_changed = Signal(int, int)  # warnings, errors since the last clear

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogPanel")
        self.records: list[dict] = []
        self.warnings = self.errors = 0
        self._last_seq = 0

        header = QHBoxLayout()
        header.setContentsMargins(12, 4, 6, 2)
        header.setSpacing(6)
        title = QLabel("LOGS")
        title.setObjectName("PanelTitle")
        self.source = self._combo(SOURCE_FILTERS, "Show logs from one caller, or all")
        self.level = self._combo(LEVEL_FILTERS, "Minimum level to show")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter text")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(220)
        self.search.textChanged.connect(lambda _t: self.render())
        self.clear_button = self._tool("delete", "Clear the panel", self.clear)
        self.file_button = self._tool("open", "Open the full log file (all history)", self.open_log_file)
        self.close_button = self._tool("close", "Close panel", self._close)
        header.addWidget(title)
        header.addStretch(1)
        for widget in (self.source, self.level, self.search, self.clear_button, self.file_button, self.close_button):
            header.addWidget(widget)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.view.setMaximumBlockCount(LOG_BUFFER_SIZE)
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        installed = set(QFontDatabase.families())
        font.setFamilies([f for f in MONO_FONTS if f in installed] + font.families())  # columns line up
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSizeF(9)
        self.view.setFont(font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(header)
        layout.addWidget(self.view, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.poll)
        self._timer.start(POLL_MS)
        self.poll()

    def _combo(self, options, tip: str) -> QComboBox:
        combo = QComboBox()
        for label, value in options:
            combo.addItem(label, value)
        combo.setToolTip(tip)
        combo.currentIndexChanged.connect(lambda _i: self.render())
        return combo

    def _tool(self, icon_name: str, tip: str, handler) -> QToolButton:
        button = QToolButton()
        button.setProperty("icon_name", icon_name)
        button.setIcon(icons.icon(icon_name, size=14))
        button.setToolTip(tip)
        button.clicked.connect(handler)
        return button

    # ------------------------------------------------------------ data

    def poll(self) -> None:
        """Append records logged since the last poll."""
        try:
            new = system_service.logs(LOG_BUFFER_SIZE, after=self._last_seq)
        except Exception:
            return
        if not new:
            return
        self._last_seq = new[-1]["seq"]
        self.records = (self.records + new)[-LOG_BUFFER_SIZE:]
        for record in new:
            self.warnings += record["level"] == "warning"
            self.errors += record["level"] in ("error", "critical")
            if self.shows(record):
                self._append(record)
        self.counts_changed.emit(self.warnings, self.errors)

    def clear(self) -> None:
        self.records.clear()
        self.warnings = self.errors = 0
        self.view.clear()
        self.counts_changed.emit(0, 0)

    def set_filters(self, source: str | None = None, level: str = "debug", text: str = "") -> None:
        """Show one caller (or all, with None), a minimum level and matching text."""
        self.source.setCurrentIndex(max(self.source.findData(source), 0))
        self.level.setCurrentIndex(max(self.level.findData(level), 0))
        self.search.setText(text)

    def shows(self, record: dict) -> bool:
        source = self.source.currentData()
        text = self.search.text().strip().lower()
        return (LEVEL_RANK.get(record["level"], 3) >= LEVEL_RANK[self.level.currentData()]
                and (source is None or record.get("source") == source)
                and (not text or text in record["message"].lower()))

    def visible_lines(self) -> list[str]:
        return self.view.toPlainText().splitlines()

    # ------------------------------------------------------------ rendering

    def render(self) -> None:
        """Redraw every kept record (after a filter or theme change)."""
        self.view.clear()
        for record in self.records:
            if self.shows(record):
                self._append(record)

    def _append(self, record: dict) -> None:
        bar = self.view.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 2
        colors = theme.current()
        level = record["level"]
        serious = LEVEL_RANK.get(level, 3) >= LEVEL_RANK["warning"]

        def fmt(color: str, bold: bool = False) -> QTextCharFormat:
            char = QTextCharFormat()
            char.setForeground(QColor(color))
            if bold:
                char.setFontWeight(QFont.Weight.DemiBold)
            return char

        cursor = QTextCursor(self.view.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.view.document().isEmpty():
            cursor.insertBlock()
        cursor.insertText(f"{record['ts'][11:19]}  ", fmt(colors.text_muted))
        cursor.insertText(f"{level.upper():<8} ", fmt(level_color(level), bold=True))
        source = record.get("source", "system")
        cursor.insertText(f"{SOURCE_LABELS.get(source, source):<7} ", fmt(colors.accent, bold=True))
        cursor.insertText(record["message"], fmt(level_color(level) if serious else colors.text))
        if at_bottom:
            bar.setValue(bar.maximum())

    def refresh_icons(self) -> None:
        for button in (self.clear_button, self.file_button, self.close_button):
            button.setIcon(icons.icon(button.property("icon_name"), size=14))
        self.render()

    # ------------------------------------------------------------ actions

    def open_log_file(self) -> None:
        from app.utils.files import subdir

        folder = subdir("logs")
        path = folder / "voxlabs.log"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path if path.exists() else folder)))

    def _close(self) -> None:
        self.hide()
        self.closed.emit()
