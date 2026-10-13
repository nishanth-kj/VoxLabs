"""MCP: let AI apps use VoxLabs. Server status, every tool, ready-to-paste connection config, and a live log
of every tool call (arguments, result or error, time), from any transport or process."""

import json
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.api.mcp import tool_catalog
from app.constants.status import Status
from app.services.mcp_service import mcp_service
from app.services.system_service import system_service
from app.ui.pages import BasePage
from app.ui.widgets.select import Select
from app.utils.time import local_display

CALL_COLUMNS = ("Time", "Tool", "Transport", "Result", "Duration", "Arguments")
TOOL_COLUMNS = ("Tool", "Access", "Calls", "Description")
REFRESH_MS = 2000


class McpPage(BasePage):
    title = "MCP"
    subtitle = ("Let AI apps such as Claude Desktop and Claude Code use VoxLabs: speech, scripts, audio, files and "
                "models. Voice cloning is never offered to agents. Every call is logged here.")

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.calls: list[dict] = []
        self.connection: dict = {}
        self._last_id = 0

        status = QHBoxLayout()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.http_button = QPushButton("")
        self.http_button.clicked.connect(self.toggle_http)
        status.addWidget(self.status, 1)
        status.addWidget(self.http_button)
        self.root.addLayout(status)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._activity_tab(), "Activity")
        self.tabs.addTab(self._tools_tab(), "Tools")
        self.tabs.addTab(self._connect_tab(), "Connect an AI app")
        self.root.addWidget(self.tabs, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(REFRESH_MS)
        self.timer.timeout.connect(self._poll)
        state.data_changed.connect(lambda what: self._show_status() if what == "settings" and self.isVisible()
                                   else None)

    # ------------------------------------------------------------ tabs

    def _activity_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        filters = QHBoxLayout()
        self.tool_filter = Select()
        self.tool_filter.addItem("All tools", None)
        for tool in tool_catalog():
            self.tool_filter.addItem(tool["name"], tool["name"])
        self.tool_filter.currentIndexChanged.connect(lambda _i: self.reload_calls())
        self.failed_only = QCheckBox("Failures only")
        self.failed_only.toggled.connect(lambda _on: self.reload_calls())
        self.summary = QLabel("")
        self.summary.setObjectName("Hint")
        clear = QPushButton("Clear log")
        clear.clicked.connect(self.clear_log)
        filters.addWidget(self.tool_filter)
        filters.addWidget(self.failed_only)
        filters.addWidget(self.summary, 1)
        filters.addWidget(clear)
        layout.addLayout(filters)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.call_table = QTableWidget(0, len(CALL_COLUMNS))
        self.call_table.setHorizontalHeaderLabels(CALL_COLUMNS)
        self.call_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.call_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.call_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.call_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.call_table.itemSelectionChanged.connect(self._show_details)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a call to see its arguments and its result or error.")
        splitter.addWidget(self.call_table)
        splitter.addWidget(self.details)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter, 1)
        return tab

    def _tools_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        hint = QLabel("What an AI app can do once connected. Tools that change something ask the app's user for "
                      "approval in most AI apps.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.tool_table = QTableWidget(0, len(TOOL_COLUMNS))
        self.tool_table.setHorizontalHeaderLabels(TOOL_COLUMNS)
        self.tool_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tool_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tool_table.setWordWrap(True)
        layout.addWidget(self.tool_table, 1)
        return tab

    def _connect_tab(self) -> QWidget:
        tab = QWidget()
        grid = QGridLayout(tab)
        self.config_boxes: dict[str, QPlainTextEdit] = {}
        sections = (
            ("claude_desktop", "Claude Desktop (and other apps with an mcpServers file)",
             "The app starts VoxLabs itself when it needs it: no window, no port, and the desktop app does not "
             "have to be running."),
            ("claude_code", "Claude Code", "Run this once in a terminal."),
            ("http_config", "Over HTTP (the local API's /mcp endpoint)",
             "Needs the API running (the button above). Beyond this computer it needs the API token."),
            ("claude_code_http", "Claude Code over HTTP", "Run this once in a terminal while the API runs."),
        )
        for row, (key, title, hint_text) in enumerate(sections):
            box = QGroupBox(title)
            column = QVBoxLayout(box)
            hint = QLabel(hint_text)
            hint.setObjectName("Hint")
            hint.setWordWrap(True)
            text = QPlainTextEdit()
            text.setReadOnly(True)
            text.setMaximumHeight(120)
            copy = QPushButton("Copy")
            copy.clicked.connect(lambda _checked=False, k=key: self.copy(k))
            column.addWidget(hint)
            column.addWidget(text)
            column.addWidget(copy, 0, Qt.AlignmentFlag.AlignRight)
            self.config_boxes[key] = text
            grid.addWidget(box, row // 2, row % 2)
        return tab

    # ------------------------------------------------------------ refresh

    def refresh(self):
        self._show_status()
        self._show_tools()
        self.reload_calls()
        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()  # only poll while the page is on screen
        super().hideEvent(event)

    def _show_status(self):
        def done(connection):
            self.connection = connection
            http = connection["http"]
            access = "token required" if http["token_required"] else (
                "this computer only" if http["local_only"] else "no token: reachable from the network")
            self.status.setText(
                (f"HTTP endpoint: running at {http['url']} ({access})" if http["running"]
                 else "HTTP endpoint: off (AI apps can still start VoxLabs over stdio, see Connect an AI app)"))
            self.http_button.setText("Stop HTTP endpoint" if http["running"] else "Start HTTP endpoint")
            for key, box in self.config_boxes.items():
                value = connection[key]
                box.setPlainText(value if isinstance(value, str) else json.dumps(value, indent=2))

        self.run(mcp_service.connection, done, busy=False)

    def _show_tools(self):
        def done(summary):
            tools = tool_catalog()
            self.tool_table.setRowCount(len(tools))
            for row, tool in enumerate(tools):
                access = "Reads" if tool["read_only"] else ("Changes or deletes" if tool["destructive"] else "Changes")
                values = (tool["name"], access, str(summary["per_tool"].get(tool["name"], 0)), tool["description"])
                for col, value in enumerate(values):
                    self.tool_table.setItem(row, col, QTableWidgetItem(value))
            self.tool_table.resizeRowsToContents()

        self.run(mcp_service.summary, done, busy=False)

    def reload_calls(self):
        """The newest calls for the current filter (replaces the table)."""
        tool, failed = self.tool_filter.currentData(), self.failed_only.isChecked()
        self.run(lambda: (mcp_service.list_calls(200, tool, failed), mcp_service.summary()), self._show_calls,
                 busy=False)

    def _poll(self):
        """Add calls logged since the last refresh (from this process or an MCP client's VoxLabs process)."""
        tool, failed, after = self.tool_filter.currentData(), self.failed_only.isChecked(), self._last_id

        def done(data):
            new, summary = data
            if new:
                self._show_calls((new + self.calls)[:200], summary)
            else:
                self._show_summary(summary)

        self.run(lambda: (mcp_service.list_calls(200, tool, failed, after), mcp_service.summary()), done, busy=False)

    def _show_calls(self, data, summary=None):
        if summary is None:
            data, summary = data
        selected = self._selected_id()
        self.calls = data
        self._last_id = max((call["mcp_calls_id"] for call in data), default=self._last_id)
        self._show_summary(summary)
        self.call_table.setRowCount(len(data))
        for row, call in enumerate(data):
            failed = call["status"] == Status.FAILED.code
            values = (_time(call["created_at"]), call["tool"], call["transport"],
                      f"Failed: {call['error']}" if failed else "OK", f"{call['duration_ms']} ms",
                      json.dumps(call["arguments"], ensure_ascii=False)[:300])
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, call["mcp_calls_id"])
                if col == 3 and failed:
                    item.setToolTip(call["error"] or "")
                self.call_table.setItem(row, col, item)
            if call["mcp_calls_id"] == selected:
                self.call_table.selectRow(row)

    def _show_summary(self, summary: dict):
        self.summary.setText(f"{summary['calls']} call{'s' if summary['calls'] != 1 else ''} logged · "
                             f"{summary['failed']} failed")

    def _selected_id(self) -> int | None:
        item = self.call_table.item(self.call_table.currentRow(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _show_details(self):
        call = next((c for c in self.calls if c["mcp_calls_id"] == self._selected_id()), None)
        if call is None:
            self.details.clear()
            return
        lines = [f"{call['tool']} · {call['transport']} · {call['duration_ms']} ms · {_time(call['created_at'])}",
                 "", "Arguments:", json.dumps(call["arguments"], indent=2, ensure_ascii=False)]
        if call["status"] == Status.FAILED.code:
            lines += ["", f"Error: {call['error']}"]
        else:
            lines += ["", "Result:", json.dumps(call["result"], indent=2, ensure_ascii=False)]
        self.details.setPlainText("\n".join(lines))

    # ------------------------------------------------------------ commands

    def toggle_http(self):
        enabled = not (self.connection.get("http") or {}).get("running", False)

        def apply():
            system_service.update_settings(api_enabled=enabled)
            system_service.apply_api_setting()

        self.run(apply, lambda _r: (self.state.notify("settings"), self._show_status()), on_error=self._show_status)

    def clear_log(self):
        self.run(mcp_service.clear_calls, lambda _n: (self.details.clear(), self.reload_calls()))

    def copy(self, key: str):
        QGuiApplication.clipboard().setText(self.config_boxes[key].toPlainText())

    def copy_claude_desktop_config(self):
        self.tabs.setCurrentIndex(2)
        self.copy("claude_desktop")


def _time(value: str | None) -> str:
    if not value:
        return ""
    stamp = datetime.fromisoformat(value)
    return local_display(stamp) + stamp.astimezone().strftime(":%S")
