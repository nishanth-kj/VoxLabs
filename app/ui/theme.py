"""Application look: a dark and a light theme (colors, QPalette and one stylesheet).

    apply_theme(app, "dark" | "light" | "system")
    current().accent  # colors of the active theme, e.g. for icons
"""

from dataclasses import dataclass
from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QHeaderView, QTableWidget, QTreeWidget, QWidget

THEMES = ("system", "dark", "light")
UI_FONTS = ("Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Cantarell")


@dataclass(frozen=True)
class ThemeColors:
    name: str
    window: str  # page background
    surface: str  # cards, lists, tables
    surface_alt: str  # inputs, buttons
    sidebar: str
    titlebar: str
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_disabled: str
    hover: str
    pressed: str
    accent: str
    accent_hover: str
    accent_text: str
    selection: str
    danger: str
    statusbar: str
    statusbar_text: str
    icon: str


DARK = ThemeColors(
    name="dark", window="#1b1c20", surface="#23252b", surface_alt="#2b2e35", sidebar="#16171b",
    titlebar="#16171b", border="#30333b", border_strong="#40444e", text="#e7e9ee", text_muted="#9197a3",
    text_disabled="#5c616c", hover="#2f323a", pressed="#383c45", accent="#7c6cff", accent_hover="#8f82ff",
    accent_text="#ffffff", selection="#3a3470", danger="#e5484d", statusbar="#5b4ee0", statusbar_text="#ffffff",
    icon="#b4b9c4",
)

LIGHT = ThemeColors(
    name="light", window="#f5f6f8", surface="#ffffff", surface_alt="#f1f2f5", sidebar="#eceef2",
    titlebar="#e6e8ec", border="#dcdfe5", border_strong="#c7cbd3", text="#1d2026", text_muted="#5f6673",
    text_disabled="#a3a9b4", hover="#e4e6eb", pressed="#d8dbe2", accent="#6352f0", accent_hover="#7465f4",
    accent_text="#ffffff", selection="#dcd8ff", danger="#d93036", statusbar="#6352f0", statusbar_text="#ffffff",
    icon="#4b5260",
)

_current: ThemeColors = DARK

STYLESHEET = Template("""
* { outline: none; }
QMainWindow, QDialog { background: $window; }
QWidget { color: $text; font-size: 13px; }
QToolTip { background: $surface; color: $text; border: 1px solid $border_strong; border-radius: 6px; padding: 5px 8px; }

/* ---------- title bar, menus ---------- */
#TitleBar { background: $titlebar; border-bottom: 1px solid $border; }
#TitleBar QLabel#AppName { font-weight: 600; color: $text; padding-right: 4px; }
#TitleBar QMenuBar { background: transparent; border: none; }
QMenuBar { background: $titlebar; padding: 2px 4px; }
QMenuBar::item { background: transparent; padding: 5px 10px; border-radius: 6px; color: $text; }
QMenuBar::item:selected { background: $hover; }
QMenuBar::item:pressed { background: $pressed; }
QMenu { background: $surface; border: 1px solid $border_strong; border-radius: 8px; padding: 5px; }
QMenu::item { padding: 6px 28px 6px 12px; border-radius: 5px; }
QMenu::item:selected { background: $accent; color: $accent_text; }
QMenu::item:disabled { color: $text_disabled; }
QMenu::separator { height: 1px; background: $border; margin: 5px 8px; }
QMenu::indicator { width: 14px; height: 14px; left: 6px; }
QMenu::indicator:checked { image: url($check_text); }
QMenu::indicator:checked:selected { image: url($check_white); }
#CommandCenter { background: $surface_alt; border: 1px solid $border; border-radius: 7px; padding: 4px 12px;
                 color: $text_muted; text-align: center; min-width: 320px; }
#CommandCenter:hover { background: $hover; color: $text; border-color: $border_strong; }
#WindowButton { background: transparent; border: none; border-radius: 0; min-width: 46px; max-width: 46px;
                min-height: 36px; padding: 0; }
#WindowButton:hover { background: $hover; }
#CloseButton { background: transparent; border: none; border-radius: 0; min-width: 46px; max-width: 46px;
               min-height: 36px; padding: 0; }
#CloseButton:hover { background: #e81123; }

/* ---------- navigation ---------- */
#NavBar { background: $sidebar; border-right: 1px solid $border; }
#NavBar QLabel#NavSection { color: $text_muted; font-size: 11px; font-weight: 600; letter-spacing: 1px;
                            padding: 14px 14px 4px 14px; }
#NavBar QPushButton { background: transparent; border: none; border-radius: 7px; padding: 8px 12px;
                      text-align: left; color: $text_muted; font-size: 13px; }
#NavBar QPushButton:hover { background: $hover; color: $text; }
#NavBar QPushButton:checked { background: $selection; color: $text; font-weight: 600; }
#NavBar QPushButton#NavToggle { color: $text_muted; }

/* ---------- pages ---------- */
#PageHeader { background: transparent; }
#PageTitle { font-size: 22px; font-weight: 700; }
#PageSubtitle { color: $text_muted; font-size: 13px; }
#Hint { color: $text_muted; }
#Banner { background: $selection; border: 1px solid $accent; border-radius: 8px; padding: 10px 12px; }
QGroupBox { background: $surface; border: 1px solid $border; border-radius: 10px; margin-top: 0px;
            padding: 36px 14px 14px 14px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: border; subcontrol-position: top left; left: 15px; top: 12px;
                   padding: 0px; color: $text; background: transparent; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget#qt_scrollarea_viewport, QScrollArea > QWidget > QWidget { background: transparent; }
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: $accent; }

/* ---------- buttons ---------- */
QPushButton { background: $surface_alt; border: 1px solid $border; border-radius: 7px; padding: 6px 14px;
              min-height: 18px; }
QPushButton:hover { background: $hover; border-color: $border_strong; }
QPushButton:pressed { background: $pressed; }
QPushButton:checked { background: $selection; border-color: $accent; }
QPushButton:disabled { color: $text_disabled; background: $surface; border-color: $border; }
QPushButton#Primary { background: $accent; color: $accent_text; border: 1px solid $accent; font-weight: 600; }
QPushButton#Primary:hover { background: $accent_hover; border-color: $accent_hover; }
QPushButton#Primary:disabled { background: $surface_alt; color: $text_disabled; border-color: $border; }
QPushButton#Danger { color: $danger; }
QPushButton#Tile { background: $surface; border: 1px solid $border; border-radius: 10px; padding: 12px 14px;
                   text-align: left; font-size: 13px; font-weight: 500; }
QPushButton#Tile:hover { border-color: $accent; background: $hover; }
QToolBar { background: $surface; border: 1px solid $border; border-radius: 9px; padding: 3px; spacing: 2px; }
QToolBar::separator { background: $border; width: 1px; margin: 5px 4px; }
QToolButton { background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 5px; }
QToolButton:hover { background: $hover; }
QToolButton:pressed, QToolButton:checked { background: $pressed; }
QToolButton:disabled { color: $text_disabled; }

/* ---------- inputs ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: $surface_alt; border: 1px solid $border; border-radius: 7px; padding: 5px 8px;
    selection-background-color: $accent; selection-color: $accent_text; }
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: $border_strong; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: $accent; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: $text_disabled; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { min-height: 22px; }
QSpinBox, QDoubleSpinBox { padding-right: 24px; }
QComboBox { padding-right: 28px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right; width: 26px; border: none; }
QComboBox::down-arrow { image: url($chevron_down); width: 12px; height: 12px; }
QComboBox::down-arrow:disabled { image: none; }
QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right;
    width: 22px; border: none; border-top-right-radius: 7px; background: transparent; }
QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right;
    width: 22px; border: none; border-bottom-right-radius: 7px; background: transparent; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: $hover; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url($chevron_up); width: 10px; height: 10px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url($chevron_down); width: 10px; height: 10px; }
QComboBox QAbstractItemView { background: $surface; border: 1px solid $border_strong; border-radius: 6px;
                              selection-background-color: $accent; selection-color: $accent_text; padding: 4px; }
QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
QCheckBox::indicator { border: 1px solid $border_strong; border-radius: 4px; background: $surface_alt; }
QCheckBox::indicator:hover { border-color: $accent; }
QCheckBox::indicator:checked { background: $accent; border-color: $accent; image: url($check_white); }
QCheckBox::indicator:disabled { background: $surface; border-color: $border; }
QRadioButton::indicator { border: 1px solid $border_strong; border-radius: 9px; background: $surface_alt; }
QRadioButton::indicator:checked { border: 5px solid $accent; background: $accent_text; }
QSlider::groove:horizontal { height: 4px; background: $border_strong; border-radius: 2px; }
QSlider::sub-page:horizontal { background: $accent; border-radius: 2px; }
QSlider::handle:horizontal { background: $accent_text; border: 2px solid $accent; width: 12px; height: 12px;
                             margin: -6px 0; border-radius: 8px; }
QProgressBar { background: $surface_alt; border: none; border-radius: 3px; max-height: 6px; text-align: center;
               color: transparent; }
QProgressBar::chunk { background: $accent; border-radius: 3px; }

/* ---------- lists and tables ---------- */
QListWidget, QTreeWidget, QTableWidget, QTableView, QTreeView, QListView {
    background: $surface; border: 1px solid $border; border-radius: 8px; padding: 2px;
    alternate-background-color: $surface_alt; gridline-color: $border; }
QListWidget::item, QTreeWidget::item { padding: 5px 6px; border-radius: 5px; }
QTableWidget::item { padding: 4px 8px; border: none; }
QListWidget::item:hover, QTreeWidget::item:hover, QTableWidget::item:hover { background: $hover; }
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {
    background: $selection; color: $text; }
QGroupBox QListWidget, QGroupBox QTreeWidget, QGroupBox QTableWidget { background: transparent; border: none; }
QHeaderView { background: transparent; }
QHeaderView::section { background: $surface; color: $text_muted; border: none; border-bottom: 1px solid $border;
                       padding: 6px 8px; font-weight: 600; }
QTableCornerButton::section { background: $surface; border: none; }
QTabWidget::pane { border: 1px solid $border; border-radius: 8px; top: -1px; background: $surface; }
QTabBar::tab { background: transparent; color: $text_muted; padding: 7px 14px; border: none;
               border-bottom: 2px solid transparent; }
QTabBar::tab:selected { color: $text; border-bottom-color: $accent; }
QTabBar::tab:hover { color: $text; }

/* ---------- scroll bars ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $border_strong; border-radius: 3px; min-height: 28px; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $border_strong; border-radius: 3px; min-width: 28px; }
QScrollBar::handle:hover { background: $text_muted; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---------- status bar ---------- */
QStatusBar { background: $statusbar; color: $statusbar_text; border: none; min-height: 24px; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: $statusbar_text; padding: 0 8px; font-size: 12px; }
QStatusBar QPushButton { background: transparent; color: $statusbar_text; border: none; border-radius: 0;
                         padding: 2px 10px; font-size: 12px; min-height: 0; }
QStatusBar QPushButton:hover { background: rgba(255, 255, 255, 0.16); }
QStatusBar QProgressBar { background: rgba(255, 255, 255, 0.25); max-width: 120px; }
QStatusBar QProgressBar::chunk { background: $statusbar_text; }

/* ---------- command palette ---------- */
#CommandPalette { background: $surface; border: 1px solid $border_strong; border-radius: 10px; }
#CommandPalette QLineEdit { font-size: 14px; padding: 8px 10px; }
#CommandPalette QListWidget { border: none; background: transparent; }
#CommandPalette QListWidget::item { padding: 7px 10px; }
#CommandPalette QListWidget::item:selected { background: $accent; color: $accent_text; }
""")


def current() -> ThemeColors:
    return _current


def resolve(mode: str | None) -> ThemeColors:
    """The colors for a setting value; "system" follows the OS light/dark preference."""
    if mode == "light":
        return LIGHT
    if mode == "dark":
        return DARK
    try:
        scheme = QGuiApplication.styleHints().colorScheme()
        return LIGHT if scheme == Qt.ColorScheme.Light else DARK
    except Exception:
        return DARK


def _palette(c: ThemeColors) -> QPalette:
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: c.window, QPalette.ColorRole.WindowText: c.text,
        QPalette.ColorRole.Base: c.surface_alt, QPalette.ColorRole.AlternateBase: c.surface,
        QPalette.ColorRole.Text: c.text, QPalette.ColorRole.Button: c.surface_alt,
        QPalette.ColorRole.ButtonText: c.text, QPalette.ColorRole.ToolTipBase: c.surface,
        QPalette.ColorRole.ToolTipText: c.text, QPalette.ColorRole.Highlight: c.accent,
        QPalette.ColorRole.HighlightedText: c.accent_text, QPalette.ColorRole.PlaceholderText: c.text_muted,
        QPalette.ColorRole.Link: c.accent, QPalette.ColorRole.Mid: c.border, QPalette.ColorRole.Midlight: c.border,
        QPalette.ColorRole.Dark: c.sidebar, QPalette.ColorRole.Light: c.border_strong,
    }
    for role, color in roles.items():
        palette.setColor(role, QColor(color))
    for role in (QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText, QPalette.ColorRole.WindowText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(c.text_disabled))
    return palette


def apply_theme(app: QApplication, mode: str | None) -> ThemeColors:
    """Apply "dark", "light" or "system" to the whole application and return its colors."""
    global _current
    _current = resolve(mode)
    app.setStyle("Fusion")
    families = set(QFontDatabase.families())
    family = next((f for f in UI_FONTS if f in families), None)
    if family:
        font = QFont(family)
        font.setPointSizeF(9.5)
        app.setFont(font)
    app.setPalette(_palette(_current))
    from app.ui import icons

    images = {
        "check_white": icons.icon_file("check", _current.accent_text),
        "check_text": icons.icon_file("check", _current.text),
        "chevron_down": icons.icon_file("chevron_down", _current.text_muted),
        "chevron_up": icons.icon_file("chevron_up", _current.text_muted),
    }
    app.setStyleSheet(STYLESHEET.substitute({**vars(_current), **images}))
    return _current


def polish_views(root: QWidget) -> None:
    """Uniform tables under `root`: left-aligned headers, columns sized to fit their text, no grid."""
    for table in root.findChildren(QTableWidget):
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setHighlightSections(False)
        header.setMinimumSectionSize(64)
        stretch = [c for c in range(header.count()) if header.sectionResizeMode(c) == QHeaderView.ResizeMode.Stretch]
        for column in range(header.count()):
            if column not in stretch:
                header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(not stretch)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(34)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
    for tree in root.findChildren(QTreeWidget):
        tree.header().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
