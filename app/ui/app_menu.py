"""The application menu bar: every command in VoxLabs, grouped like a desktop editor.

Commands that belong to a page navigate there first and then run the page's own
method, so the menu, the command palette and the page buttons all do the same thing.
Shortcuts that only apply inside a page (the audio editor's Ctrl+X, Space, …) are
shown as hints; the page itself handles them, so text boxes keep their own
Ctrl+C / Ctrl+V / Ctrl+Z.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

from app.ui import icons

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow

NAV_SHORTCUTS = {"home": "Ctrl+1", "studio": "Ctrl+2", "clone": "Ctrl+3", "generate": "Ctrl+4", "script": "Ctrl+5",
                 "editor": "Ctrl+6", "voices": "Ctrl+7", "projects": "Ctrl+8", "models": "Ctrl+9",
                 "settings": "Ctrl+,"}


def _add(menu: QMenu, text: str, handler: Callable[[], object], *, shortcut: str | None = None,
         hint: str | None = None, icon: str | None = None) -> QAction:
    """A menu command. `shortcut` is registered window-wide; `hint` is only displayed."""
    action = QAction(f"{text}\t{hint}" if hint else text, menu)
    action.triggered.connect(lambda _checked=False: handler())
    if shortcut:
        action.setShortcut(QKeySequence(shortcut))
    if icon:
        action.setProperty("icon_name", icon)
        action.setIcon(icons.icon(icon))
        action.setIconVisibleInMenu(True)
    menu.addAction(action)
    return action


def _submenu(menu: QMenu, title: str, icon: str) -> QMenu:
    sub = menu.addMenu(icons.icon(icon), title)
    sub.menuAction().setProperty("icon_name", icon)
    return sub


def refresh_menu_icons(bar: QMenuBar) -> None:
    """Re-render menu icons after a theme change."""
    def walk(actions):
        for action in actions:
            name = action.property("icon_name")
            if name:
                action.setIcon(icons.icon(name))
            if action.menu() is not None:
                walk(action.menu().actions())

    walk(bar.actions())


def build_menu_bar(window: "MainWindow") -> QMenuBar:
    bar = QMenuBar()
    cmd = window.command
    edit = window.edit_command

    # ------------------------------------------------------------ File
    file = bar.addMenu("&File")
    _add(file, "New Project…", lambda: cmd("projects", "new"), shortcut="Ctrl+Shift+N", icon="plus")
    _add(file, "Open Project…", lambda: window.go("projects"), icon="projects")
    _add(file, "Close Project", lambda: cmd("projects", "close_project"))
    file.addSeparator()
    _add(file, "Open Audio…", lambda: cmd("editor", "choose_audio"), hint="Ctrl+O", icon="open")
    _add(file, "Import Audio File…", lambda: cmd("editor", "import_file"), hint="Ctrl+I", icon="import")
    _add(file, "Save Edits as New Audio", lambda: cmd("editor", "render_edits"), hint="Ctrl+S", icon="save")
    _add(file, "Export Audio…", lambda: cmd("editor", "export"), hint="Ctrl+E", icon="export")
    file.addSeparator()
    _add(file, "Export Project…", lambda: cmd("projects", "export"))
    _add(file, "Duplicate Project", lambda: cmd("projects", "duplicate"))
    file.addSeparator()
    _add(file, "Open Data Folder", window.open_data_folder)
    _add(file, "Settings", lambda: window.go("settings"), shortcut="Ctrl+,", icon="settings")
    file.addSeparator()
    _add(file, "Exit", window.close, shortcut="Ctrl+Q")

    # ------------------------------------------------------------ Edit
    menu = bar.addMenu("&Edit")
    _add(menu, "Undo", lambda: edit("undo"), hint="Ctrl+Z", icon="undo")
    _add(menu, "Redo", lambda: edit("redo"), hint="Ctrl+Shift+Z", icon="redo")
    menu.addSeparator()
    _add(menu, "Cut", lambda: edit("cut"), hint="Ctrl+X", icon="cut")
    _add(menu, "Copy", lambda: edit("copy"), hint="Ctrl+C", icon="copy")
    _add(menu, "Paste", lambda: edit("paste"), hint="Ctrl+V", icon="paste")
    _add(menu, "Delete", lambda: edit("delete"), hint="Del", icon="delete")
    _add(menu, "Duplicate Selection", lambda: edit("duplicate"), hint="Ctrl+D", icon="duplicate")
    menu.addSeparator()
    _add(menu, "Select All", lambda: edit("select_all"), hint="Ctrl+A")

    # ------------------------------------------------------------ View
    view = bar.addMenu("&View")
    _add(view, "Command Palette…", window.show_palette, shortcut="Ctrl+Shift+P", icon="search")
    view.addSeparator()
    for key, label, icon_name in window.nav_items:
        _add(view, label, lambda k=key: window.go(k), shortcut=NAV_SHORTCUTS.get(key), icon=icon_name)
    view.addSeparator()
    _add(view, "Toggle Sidebar", window.toggle_sidebar, shortcut="Ctrl+B", icon="sidebar")
    _add(view, "Full Screen", window.toggle_full_screen, shortcut="F11")
    theme_menu = view.addMenu("Theme")
    group = QActionGroup(theme_menu)
    window.theme_actions = {}
    for mode, label in (("system", "Match System"), ("dark", "Dark"), ("light", "Light")):
        action = _add(theme_menu, label, lambda m=mode: window.set_theme(m))
        action.setCheckable(True)
        group.addAction(action)
        window.theme_actions[mode] = action
    view.addSeparator()
    _add(view, "Background Jobs…", window.show_jobs, shortcut="Ctrl+J", icon="jobs")

    # ------------------------------------------------------------ Voice
    voice = bar.addMenu("V&oice")
    _add(voice, "Clone a Voice…", lambda: window.go("clone"), icon="clone")
    _add(voice, "Add Sample Files…", lambda: cmd("clone", "add_files"), icon="import")
    _add(voice, "Record a Sample", lambda: cmd("clone", "toggle_record"), icon="record")
    _add(voice, "Remove Selected Sample", lambda: cmd("clone", "remove_selected"))
    _add(voice, "Create Cloned Voice (with consent)", lambda: cmd("clone", "clone"))
    voice.addSeparator()
    _add(voice, "New Preset Voice…", lambda: cmd("voices", "new_preset"), icon="plus")
    _add(voice, "Preview Voice", lambda: cmd("voices", "preview"), icon="play")
    _add(voice, "Rename Voice…", lambda: cmd("voices", "rename"))
    _add(voice, "Edit Voice…", lambda: cmd("voices", "edit"))
    _add(voice, "Add Sample to Voice…", lambda: cmd("voices", "add_sample"))
    _add(voice, "Export Voice Metadata…", lambda: cmd("voices", "export_metadata"), icon="export")
    voice.addSeparator()
    _add(voice, "Revoke Consent…", lambda: cmd("voices", "revoke"))
    _add(voice, "Delete Voice…", lambda: cmd("voices", "delete"), icon="delete")

    # ------------------------------------------------------------ Audio
    audio = bar.addMenu("&Audio")
    _add(audio, "Generate Speech", lambda: cmd("generate", "generate"), icon="generate")
    _add(audio, "Regenerate Selected Sentence", lambda: cmd("generate", "regenerate_sentence"))
    _add(audio, "Export Generated Speech…", lambda: cmd("generate", "export"))
    audio.addSeparator()
    _add(audio, "Play / Pause", lambda: cmd("editor", "toggle_play"), hint="Space", icon="play")
    _add(audio, "Play Selection", lambda: cmd("editor", "play_selection"))
    _add(audio, "Play from Cursor", lambda: cmd("editor", "play_from_cursor"))
    audio.addSeparator()
    _add(audio, "Trim to Selection", lambda: cmd("editor", "crop"), hint="Ctrl+T", icon="trim")
    _add(audio, "Split at Cursor", lambda: cmd("editor", "split"), icon="split")
    _add(audio, "Move Selection to Cursor", lambda: cmd("editor", "move_selection"), icon="move")
    _add(audio, "Join Another Audio…", lambda: cmd("editor", "join"), icon="join")
    _add(audio, "Insert Silence…", lambda: cmd("editor", "insert_silence"), icon="silence")
    audio.addSeparator()
    _add(audio, "Fade In", lambda: cmd("editor", "fade_in"), icon="fade_in")
    _add(audio, "Fade Out", lambda: cmd("editor", "fade_out"), icon="fade_out")
    _add(audio, "Volume…", lambda: cmd("editor", "volume"), icon="volume")
    _add(audio, "Normalize", lambda: cmd("editor", "normalize"), icon="normalize")
    enhance = _submenu(audio, "Enhance", "enhance")
    _add(enhance, "Apply Selected Preset", lambda: cmd("editor", "enhance"))
    _add(enhance, "Denoise", lambda: cmd("editor", "enhance", {"denoise": {"strength": 0.6}}))
    _add(enhance, "Compress", lambda: cmd("editor", "enhance", {"compress": {}}))
    _add(enhance, "De-ess", lambda: cmd("editor", "enhance", {"deess": {}}))
    _add(enhance, "Loudness −16 LUFS", lambda: cmd("editor", "enhance", {"loudness": {"target_lufs": -16}}))
    audio.addSeparator()
    _add(audio, "Zoom In", lambda: cmd("editor", "zoom_in"), icon="zoom_in")
    _add(audio, "Zoom Out", lambda: cmd("editor", "zoom_out"), icon="zoom_out")
    _add(audio, "Zoom to Fit", lambda: cmd("editor", "zoom_fit"), icon="fit")

    # ------------------------------------------------------------ Script
    script = bar.addMenu("&Script")
    _add(script, "New Script…", lambda: cmd("script", "new_script"), icon="plus")
    _add(script, "Save Script", lambda: cmd("script", "save"), icon="save")
    _add(script, "Delete Script…", lambda: cmd("script", "delete_script"), icon="delete")
    script.addSeparator()
    _add(script, "Generate Take for Section", lambda: cmd("script", "generate_section"), icon="generate")
    _add(script, "Generate Missing Sections", lambda: cmd("script", "generate_all", False))
    _add(script, "Regenerate All Sections", lambda: cmd("script", "generate_all", True))
    _add(script, "Render Final Audio", lambda: cmd("script", "render_script"), icon="save")
    _add(script, "Open Final Audio in Editor", lambda: cmd("script", "open_final"), icon="editor")
    script.addSeparator()
    _add(script, "Auto-assign Voices to Speakers", lambda: cmd("script", "auto_map"), icon="voices")
    _add(script, "Apply Speaker Mapping", lambda: cmd("script", "save_mapping"))
    _add(script, "Move Section Up", lambda: cmd("script", "move_section", -1))
    _add(script, "Move Section Down", lambda: cmd("script", "move_section", 1))
    _add(script, "Save Script Settings", lambda: cmd("script", "save_settings"))

    # ------------------------------------------------------------ Tools
    tools = bar.addMenu("&Tools")
    models = _submenu(tools, "Models", "models")
    _add(models, "Manage Models", lambda: window.go("models"))
    models.addSeparator()
    for label, method in (("Install Selected Model", "install"), ("Load", "load"), ("Unload", "unload"),
                          ("Reload", "reload"), ("Remove Files", "remove"), ("Health Check", "health"),
                          ("Set as Default", "set_default"), ("Rescan Models Folder", "rescan")):
        _add(models, label, lambda m=method: cmd("models", m))
    projects = _submenu(tools, "Projects", "projects")
    for label, method in (("New Project…", "new"), ("Open Selected Project", "open"), ("Rename…", "rename"),
                          ("Duplicate", "duplicate"), ("Export…", "export"), ("Delete…", "delete"),
                          ("Close Project", "close_project")):
        _add(projects, label, lambda m=method: cmd("projects", m))
    tools.addSeparator()
    api_action = _add(tools, "Run REST API and MCP Server", lambda: window.toggle_api(), icon="api")
    api_action.setCheckable(True)
    window.api_action = api_action
    _add(tools, "Background Jobs…", window.show_jobs, icon="jobs")
    _add(tools, "View Logs", lambda: window.go("settings"))
    tools.addSeparator()
    _add(tools, "Settings", lambda: window.go("settings"), icon="settings")

    # ------------------------------------------------------------ Help
    help_menu = bar.addMenu("&Help")
    _add(help_menu, "Show All Commands", window.show_palette, shortcut="F1", icon="search")
    _add(help_menu, "Keyboard Shortcuts", window.show_shortcuts)
    _add(help_menu, "Documentation", window.open_docs, icon="help")
    help_menu.addSeparator()
    _add(help_menu, "About VoxLabs", window.show_about)
    return bar
