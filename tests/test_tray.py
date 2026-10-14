"""Tests for the VoxLabs System Tray Icon and Taskbar integration."""

import os
import pytest
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QSystemTrayIcon

from app.services.live_voice_service import live_voice_service
from app.services.system_service import VERSION, system_service
from app.ui.widgets.progress import JobBridge
from app.ui.widgets.tray_icon import VoxTrayIcon

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def window(qtbot):
    from app.ui.main_window import MainWindow

    win = MainWindow()
    qtbot.addWidget(win)
    yield win
    QThreadPool.globalInstance().waitForDone(10_000)
    qtbot.wait(50)
    JobBridge.detach()


def test_tray_icon_menu_and_actions(window, qtbot):
    tray = window.tray_icon
    assert isinstance(tray, VoxTrayIcon)
    assert tray.menu is not None

    # Version header
    assert VERSION in tray.title_action.text()
    assert not tray.title_action.isEnabled()

    # Window controls
    assert tray.show_action.text() == "Show VoxLabs"
    assert tray.hide_action.text() == "Hide to Tray"

    # API status
    assert "HTTP API" in tray.api_status_action.text()
    assert "REST API & MCP" in tray.api_toggle_action.text()

    # Live voice status
    assert "Live Voice" in tray.voice_status_action.text()
    assert "Live Streaming" in tray.voice_toggle_action.text()

    # Status update reflecting live voice state
    live_voice_service.start_stream(test_tone=True)
    tray.update_status()
    assert "Streaming" in tray.voice_status_action.text()
    assert "Stop Live Streaming" in tray.voice_toggle_action.text()

    live_voice_service.stop_stream()
    tray.update_status()
    assert "Idle" in tray.voice_status_action.text()
    assert "Start Live Streaming" in tray.voice_toggle_action.text()


def test_tray_icon_activation_toggle(window, qtbot):
    tray = window.tray_icon

    # Simulate trigger activation to hide window
    window.show()
    tray._on_activated(QSystemTrayIcon.ActivationReason.Trigger)
    assert not window.isVisible()

    # Simulate double click to restore window
    tray._on_activated(QSystemTrayIcon.ActivationReason.DoubleClick)
    assert window.isVisible()
