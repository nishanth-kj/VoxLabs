"""System Tray and Taskbar integration for VoxLabs.

Provides quick access to application status, HTTP REST API and MCP server toggles,
Live Voice Changer streaming controls, and fast page navigation from the Windows/OS
notification area.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.services.live_voice_service import live_voice_service
from app.services.system_service import VERSION, system_service
from app.ui import icons, theme
from app.utils.logger import logger


class VoxTrayIcon(QSystemTrayIcon):
    """System tray icon with live status, HTTP/MCP controls, and voice changer toggles."""

    def __init__(self, main_window):
        super().__init__(icons.app_icon(), main_window)
        self.main_window = main_window
        self.setToolTip(f"VoxLabs {VERSION} — Voice Studio")

        # Context Menu
        self.menu = QMenu()
        self.menu.setObjectName("TrayMenu")

        # 1. Header / Version
        self.title_action = QAction(f"VoxLabs {VERSION}", self.menu)
        self.title_action.setEnabled(False)
        self.menu.addAction(self.title_action)
        self.menu.addSeparator()

        # 2. Window Visibility
        self.show_action = self.menu.addAction("Show VoxLabs")
        self.show_action.triggered.connect(self.show_window)
        self.hide_action = self.menu.addAction("Hide to Tray")
        self.hide_action.triggered.connect(self.hide_window)
        self.menu.addSeparator()

        # 3. HTTP REST API & MCP Server Status
        self.api_status_action = QAction("HTTP API: Checking…", self.menu)
        self.api_status_action.setEnabled(False)
        self.menu.addAction(self.api_status_action)

        self.api_toggle_action = self.menu.addAction("Start REST API & MCP")
        self.api_toggle_action.triggered.connect(self._toggle_api)

        self.mcp_info_action = QAction("MCP Server: stdio & HTTP enabled", self.menu)
        self.mcp_info_action.setEnabled(False)
        self.menu.addAction(self.mcp_info_action)
        self.menu.addSeparator()

        # 4. Live Voice Changer Controls
        self.voice_status_action = QAction("Live Voice: Idle", self.menu)
        self.voice_status_action.setEnabled(False)
        self.menu.addAction(self.voice_status_action)

        self.voice_toggle_action = self.menu.addAction("Start Live Streaming")
        self.voice_toggle_action.triggered.connect(self._toggle_live_voice)
        self.menu.addSeparator()

        # 5. Quick Page Navigation
        nav_menu = self.menu.addMenu("Open Page")
        pages = [
            ("Live Voice Changer", "live_voice"),
            ("Studio", "studio"),
            ("Generate Speech", "generate"),
            ("Video Dubbing", "dubbing"),
            ("Voice Clones", "voices"),
            ("Audio Editor", "editor"),
            ("Model Manager", "models"),
            ("Settings", "settings"),
        ]
        for label, page_key in pages:
            action = nav_menu.addAction(label)
            action.triggered.connect(lambda checked=False, k=page_key: self._open_page(k))
        self.menu.addSeparator()

        # 6. Exit
        self.quit_action = self.menu.addAction("Quit VoxLabs")
        self.quit_action.triggered.connect(self._quit_application)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)

        # Wire live signals
        live_voice_service.state_changed.connect(self.update_status)
        self.update_status()

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.show()

    def update_status(self, *_args) -> None:
        """Update context menu action labels and states to match current background services."""
        try:
            # API & MCP
            api_running = system_service.api_running()
            if api_running:
                settings = system_service.get_settings()
                host = settings.get("api_host", "127.0.0.1")
                port = settings.get("api_port", 8942)
                self.api_status_action.setText(f"HTTP API: http://{host}:{port}")
                self.api_toggle_action.setText("Stop REST API & MCP")
                self.mcp_info_action.setText(f"MCP Server: Active (port {port} & stdio)")
            else:
                self.api_status_action.setText("HTTP API: Stopped")
                self.api_toggle_action.setText("Start REST API & MCP")
                self.mcp_info_action.setText("MCP Server: stdio ready")

            # Live Voice Changer
            streaming = live_voice_service.is_streaming()
            if streaming:
                preset = live_voice_service.preset_key.replace("_", " ").title()
                pitch = live_voice_service.pitch_semitones
                self.voice_status_action.setText(f"Live Voice: Streaming ({preset}, {pitch:+.1f} st)")
                self.voice_toggle_action.setText("Stop Live Streaming")
                self.setToolTip(f"VoxLabs — Live Streaming Active ({preset})")
            else:
                self.voice_status_action.setText("Live Voice: Idle")
                self.voice_toggle_action.setText("Start Live Streaming")
                self.setToolTip(f"VoxLabs {VERSION} — Voice Studio")
        except Exception as exc:
            logger.debug(f"Tray status update error: {exc}")

    def show_window(self) -> None:
        """Bring main window to front."""
        self.main_window.show()
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def hide_window(self) -> None:
        """Hide main window to tray."""
        self.main_window.hide()

    def _toggle_api(self) -> None:
        self.main_window.toggle_api()
        self.update_status()

    def _toggle_live_voice(self) -> None:
        live_voice_service.toggle_stream()
        self.update_status()

    def _open_page(self, key: str) -> None:
        self.show_window()
        self.main_window.go(key)

    def _quit_application(self) -> None:
        live_voice_service.stop_stream()
        self.hide()
        QApplication.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.main_window.isVisible() and not self.main_window.isMinimized():
                self.main_window.hide()
            else:
                self.show_window()
