"""Smoke tests: the main window builds and every page can refresh (offscreen Qt)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")


@pytest.fixture
def window(qtbot):
    from app.ui.main_window import MainWindow

    from PySide6.QtCore import QThreadPool

    from app.ui.widgets.progress import JobBridge

    win = MainWindow()
    qtbot.addWidget(win)
    yield win
    QThreadPool.globalInstance().waitForDone(10_000)
    qtbot.wait(50)  # deliver queued callbacks before the data directory goes away
    JobBridge.detach()


def test_every_page_opens(window, qtbot):
    for key in window.pages:
        window.go(key)
        assert window.stack.currentWidget() is window.pages[key]
    qtbot.wait(200)


def test_editor_undo_redo(window, voice_wav, qtbot):
    from app.services.audio_service import audio_service

    audio = audio_service.import_file(voice_wav)
    editor = window.pages["editor"]
    editor.open_audio(audio["audios_id"])
    qtbot.waitUntil(lambda: editor.audio is not None, timeout=5000)
    editor.waveform.select(1.0, 2.0)
    editor.delete()
    assert editor.waveform.duration == pytest.approx(3.0, abs=0.01)
    editor.undo()
    assert editor.waveform.duration == pytest.approx(4.0, abs=0.01)
    editor.redo()
    assert editor.ops[-1]["op"] == "delete"


def test_clone_button_requires_consent(window):
    page = window.pages["clone"]
    page.samples = [{"path": "x.wav", "analysis": {"ok": True, "errors": [], "issues": []}}]
    page.granted_by.setText("Operator")
    page.speaker.setText("Speaker")
    page._update_buttons()
    assert not page.clone_button.isEnabled()
    page.confirm.setChecked(True)
    assert page.clone_button.isEnabled()


def test_menus_reach_every_page_command(window):
    """Every `cmd("page", "method")` in the menu must exist on that page."""
    import re
    from pathlib import Path

    source = Path("app/ui/app_menu.py").read_text(encoding="utf-8")
    calls = set(re.findall(r'cmd\("(\w+)", "(\w+)"', source))
    calls |= {("models", m) for m in re.findall(r'\("[^"]+", "(\w+)"\)', source.split("models = _submenu")[1].split("projects = _submenu")[0])}
    assert len(calls) > 40
    missing = [f"{page}.{method}" for page, method in calls if not callable(getattr(window.pages[page], method, None))]
    assert missing == []
    titles = [action.text().replace("&", "") for action in window.menu_bar.actions()]
    assert titles == ["File", "Edit", "View", "Voice", "Audio", "Script", "Tools", "Help"]


def test_command_palette_runs_menu_commands(window):
    from app.ui.widgets.command_palette import CommandPalette

    palette = CommandPalette(window.menu_bar, window)
    palette.filter("toggle sidebar")
    assert palette.list.count() == 1
    palette.run_selected()
    assert window.nav.collapsed
    palette.filter("view settings")
    assert palette.list.count() >= 1
    assert any("Ctrl+Shift+P" in shortcut for _label, shortcut in window.shortcut_rows())


def test_theme_switch_and_title_bar(window, qtbot):
    from app.ui import theme

    assert window.frameless and window.title_bar is not None
    window.set_theme("light")
    assert theme.current().name == "light" and window.theme_actions["light"].isChecked()
    window.set_theme("dark")
    assert theme.current().name == "dark"
    window.go("editor")
    assert "Audio Editor" in window.title_bar.command_center.text()
    qtbot.wait(100)


def test_native_title_bar_option(qtbot):
    from app.ui.main_window import MainWindow

    win = MainWindow(native_title_bar=True)
    qtbot.addWidget(win)
    assert win.title_bar is None and win.menuBar() is win.menu_bar
