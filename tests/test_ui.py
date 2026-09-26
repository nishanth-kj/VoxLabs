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


def test_open_project_scopes_new_work(window, qtbot):
    from PySide6.QtCore import Qt

    from app.services.project_service import project_service
    from app.services.script_service import script_service
    from app.services.system_service import system_service

    window.show()  # pages refresh live on a project switch only while visible
    script_service.create("Loose script", "Hello.")
    project = project_service.create_project("Course")
    window.state.set_project(project)
    assert window.project_button.text() == "Course" and "Course" in window.windowTitle()
    assert window.pages["generate"].params()["projects_id"] == project["projects_id"]
    qtbot.waitUntil(lambda: system_service.get_setting("current_projects_id") == project["projects_id"],
                    timeout=5000)

    lesson = script_service.create("Lesson", "Hi.", projects_id=project["projects_id"])
    page = window.pages["script"]
    window.go("script")
    qtbot.waitUntil(lambda: page.script_list.count() == 1, timeout=5000)
    assert page.script_list.item(0).data(Qt.ItemDataRole.UserRole) == lesson["scripts_id"]

    window.close_project()
    assert window.project_button.text() == "No project" and window.pages["generate"].params()["projects_id"] is None
    qtbot.waitUntil(lambda: page.script_list.count() == 2, timeout=5000)


def test_open_project_is_reopened_on_start(qtbot):
    from app.services.project_service import project_service
    from app.services.system_service import system_service
    from app.ui.main_window import MainWindow

    project = project_service.create_project("Podcast")
    system_service.update_settings(current_projects_id=project["projects_id"])
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.state.projects_id == project["projects_id"] and win.project_button.text() == "Podcast"

    project_service.delete_project(project["projects_id"])
    win = MainWindow()
    qtbot.addWidget(win)
    assert win.state.project is None and win.project_button.text() == "No project"


def test_log_panel_shows_source_and_filters(window, qtbot):
    from app.utils.logger import log_source, logger

    window.show_logs()
    assert not window.log_panel.isHidden()
    with log_source("api"):
        logger.warning("disk almost full")
    with log_source("ui"):
        logger.info("opened the editor")
    window.log_panel.poll()
    lines = window.log_panel.visible_lines()
    assert any("WARNING" in line and "API" in line and "disk almost full" in line for line in lines)
    assert any("UI" in line and "opened the editor" in line for line in lines)
    assert "warning" in window.logs_button.text()

    window.log_panel.set_filters(source="ui")
    assert all("disk almost full" not in line for line in window.log_panel.visible_lines())
    window.log_panel.set_filters(level="warning")
    assert all("opened the editor" not in line for line in window.log_panel.visible_lines())
    window.log_panel.set_filters(text="disk")
    assert [line for line in window.log_panel.visible_lines() if line] and \
        all("disk" in line for line in window.log_panel.visible_lines())
    window.log_panel.set_filters()  # all sources, all levels, no text
    assert len(window.log_panel.visible_lines()) >= 2
    window.toggle_logs()
    assert window.log_panel.isHidden()


def test_theme_menu_choice_reaches_settings(window, qtbot):
    from app.services.system_service import system_service
    from app.ui import theme

    settings = window.pages["settings"]
    window.go("settings")
    window.set_theme("light")
    assert theme.mode() == "light" and theme.current().name == "light"
    qtbot.waitUntil(lambda: settings.theme.currentData() == "light", timeout=5000)
    assert system_service.get_setting("theme") == "light"
    window.set_theme("system")  # hands the scheme back to the OS
    qtbot.waitUntil(lambda: settings.theme.currentData() == "system", timeout=5000)


def test_select_opens_below_with_search_first(qtbot):
    """Selects open under the box on a transparent window; long ones start with a search row."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QVBoxLayout, QWidget

    from app.ui import theme

    theme.apply_theme(QApplication.instance(), "dark")
    host = QWidget()
    qtbot.addWidget(host)
    combo, short = QComboBox(), QComboBox()
    combo.addItems([f"Voice {i}" for i in range(12)])
    short.addItems(["Match system", "Dark", "Light"])
    layout = QVBoxLayout(host)
    layout.addWidget(combo)
    layout.addWidget(short)
    host.setGeometry(40, 40, 300, 120)
    theme.polish_views(host)
    host.show()

    combo.showPopup()
    popup, view = combo.view().window(), combo.view()
    qtbot.waitUntil(popup.isVisible)
    assert popup.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # no black corners
    assert popup.geometry().top() >= combo.mapToGlobal(combo.rect().bottomLeft()).y()  # below, not over it
    search = view.findChild(QLineEdit, "ComboSearch")
    assert search.isVisible() and search.geometry().bottom() < view.viewport().geometry().top()  # first row

    assert not search.isReadOnly()  # a real input: click to place the cursor, select, type
    qtbot.mouseClick(search, Qt.MouseButton.LeftButton)
    assert search.hasFocus() and popup.isVisible()
    qtbot.keyClicks(search, "1 voice")  # every word, any order
    assert [combo.itemText(r) for r in range(combo.count()) if not view.isRowHidden(r)] == \
        ["Voice 1", "Voice 10", "Voice 11"]
    qtbot.keyClick(search, Qt.Key.Key_Down)  # Up/Down move through the matches from the box
    qtbot.keyClick(search, Qt.Key.Key_Return)
    assert combo.currentText() == "Voice 10" and not popup.isVisible()
    assert not any(view.isRowHidden(r) for r in range(combo.count()))  # the next open shows every row

    combo.showPopup()
    qtbot.waitUntil(popup.isVisible)
    view.setFocus()
    qtbot.keyClicks(view, "11")  # typing on the list moves into the box
    assert search.text() == "11" and search.hasFocus()
    qtbot.keyClick(search, Qt.Key.Key_Escape)
    assert not popup.isVisible() and combo.currentText() == "Voice 10"

    short.showPopup()
    qtbot.waitUntil(short.view().window().isVisible)
    assert short.view().findChild(QLineEdit, "ComboSearch").isVisible()
    short.hidePopup()


def test_every_select_is_the_app_select(window, qtbot):
    """Every select in the window, and the item-picker dialog, gets the rounded list with search first."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit

    from app.ui.widgets.select import choose_item

    combos = window.findChildren(QComboBox)
    assert len(combos) > 20
    assert [c for c in combos if not c.property("popup_polished")] == []
    assert all(c.view().findChild(QLineEdit, "ComboSearch") is not None for c in combos)

    seen = {}

    def accept_dialog():
        dialog = QApplication.activeModalWidget()
        seen["polished"] = bool(dialog.findChild(QComboBox).property("popup_polished"))
        dialog.accept()

    QTimer.singleShot(0, accept_dialog)
    assert choose_item(window, "Export", "Format:", ["wav", "mp3"], 1) == "mp3"
    assert seen["polished"]
