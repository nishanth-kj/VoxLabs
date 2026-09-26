"""Application look: a dark and a light theme (colors, QPalette and one stylesheet).

    apply_theme(app, "dark" | "light" | "system")
    current().accent  # colors of the active theme, e.g. for icons
"""

from dataclasses import dataclass
from string import Template

import shiboken6
from PySide6.QtCore import QEvent, QModelIndex, QObject, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QKeyEvent, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QHeaderView,
    QLineEdit,
    QListView,
    QMenu,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTreeWidget,
    QWidget,
)

THEMES = ("system", "dark", "light")
UI_FONTS = ("Segoe UI Variable Text", "Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Cantarell")
POPUP_MAX_ROWS = 8
POPUP_ROW_HEIGHT = 32
SEARCH_HEIGHT = 30
SEARCH_GAP = 4


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
    warning: str
    info: str
    statusbar: str
    statusbar_text: str
    icon: str


DARK = ThemeColors(
    name="dark", window="#1b1c20", surface="#23252b", surface_alt="#2b2e35", sidebar="#16171b",
    titlebar="#16171b", border="#30333b", border_strong="#40444e", text="#e7e9ee", text_muted="#9197a3",
    text_disabled="#5c616c", hover="#2f323a", pressed="#383c45", accent="#7c6cff", accent_hover="#8f82ff",
    accent_text="#ffffff", selection="#3a3470", danger="#e5484d", warning="#e5b53d", info="#58a6ff",
    statusbar="#5b4ee0", statusbar_text="#ffffff",
    icon="#b4b9c4",
)

LIGHT = ThemeColors(
    name="light", window="#f5f6f8", surface="#ffffff", surface_alt="#f1f2f5", sidebar="#eceef2",
    titlebar="#e6e8ec", border="#dcdfe5", border_strong="#c7cbd3", text="#1d2026", text_muted="#5f6673",
    text_disabled="#a3a9b4", hover="#e4e6eb", pressed="#d8dbe2", accent="#6352f0", accent_hover="#7465f4",
    accent_text="#ffffff", selection="#dcd8ff", danger="#d93036", warning="#a86400", info="#0969da",
    statusbar="#6352f0", statusbar_text="#ffffff",
    icon="#4b5260",
)

_current: ThemeColors = DARK
_mode = "system"

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
QLineEdit, QSpinBox, QDoubleSpinBox { min-height: 22px; }
QComboBox { min-height: 32px; padding: 4px 30px 4px 10px; border-radius: 10px; combobox-popup: 0; }
QSpinBox, QDoubleSpinBox { padding-right: 24px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right; width: 16px;
    border: none; border-top-right-radius: 10px; border-bottom-right-radius: 10px; background: transparent; }
QComboBox::down-arrow { image: url($chevron_down); width: 12px; height: 12px; }
QComboBox::down-arrow:disabled { image: none; }
/* The inner editor inherits QLineEdit padding, which clips the bottom of an editable combo. */
QComboBox QLineEdit { background: transparent; border: none; padding: 0 2px; min-height: 0; margin: 0; }
QSpinBox::up-button, QDoubleSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right;
    width: 22px; border: none; border-top-right-radius: 7px; background: transparent; }
QSpinBox::down-button, QDoubleSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right;
    width: 22px; border: none; border-bottom-right-radius: 7px; background: transparent; }
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: $hover; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url($chevron_up); width: 10px; height: 10px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url($chevron_down); width: 10px; height: 10px; }

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
/* Select popup. `combobox-popup: 0` above opens it below the select, or above when there is no room.
   Its window is transparent (polish_combo_popup), so only this rounded list shows; _PopupRowDelegate
   paints the rows and #ComboSearch is the search box at the top of every list. */
#ComboPopup { background: transparent; border: none; }
#ComboSearch { background: $surface_alt; border: 1px solid $border; border-radius: 6px; padding: 0 8px;
    min-height: 0; color: $text; }
#ComboSearch:focus { border-color: $accent; }
QComboBox QListView, #ComboPopup QListView {
    background: $surface;
    alternate-background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 10px;
    padding: 4px;
    margin: 0;
    outline: 0;
}
QComboBox QListView::item, #ComboPopup QListView::item {
    height: 32px;
    padding: 0;
    margin: 0;
    border: none;
    background: transparent;
    color: $text;
}
QComboBox QListView::item:hover, #ComboPopup QListView::item:hover { background: transparent; }
QComboBox QListView::item:selected, #ComboPopup QListView::item:selected { background: transparent; color: $text; }
#ComboPopup QScrollBar:vertical { background: transparent; width: 8px; margin: 10px 3px 10px 0; }
/* With a search box, the scrollbar starts under it (the box sits above the rows in the same list). */
#ComboPopup QListView[search="true"] QScrollBar:vertical { margin-top: $search_bar_top; }
#ComboPopup QScrollBar::handle:vertical { background: $border_strong; border-radius: 3px; min-height: 24px; }
#ComboPopup QScrollBar::add-line:vertical, #ComboPopup QScrollBar::sub-line:vertical { height: 0; width: 0; border: none; background: none; }
#ComboPopup QScrollBar::add-page:vertical, #ComboPopup QScrollBar::sub-page:vertical { background: none; }
QHeaderView { background: transparent; }
/* Speaker mapping: one row divider, no box around the voice select. */
#SpeakerMap { background: transparent; border: none; border-radius: 0; padding: 0; }
#SpeakerMap::item { border: none; border-bottom: 1px solid $border; padding: 0 12px; background: transparent; }
#SpeakerMap QHeaderView::section { background: transparent; border: none; border-bottom: 1px solid $border;
    padding: 8px 12px; font-weight: 600; }
#SpeakerVoice, #SpeakerVoice QComboBox { background: transparent; border: none; border-radius: 6px; min-height: 28px; }
#SpeakerVoice QComboBox:hover { background: $hover; }
#SpeakerVoice QComboBox:focus, #SpeakerVoice QComboBox:on { background: $selection; border: none; }
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
QScrollBar::add-line, QScrollBar::sub-line,
QComboBox QScrollBar::add-line, QComboBox QScrollBar::sub-line { width: 0; height: 0; border: none; background: none; }
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

/* ---------- logs panel (bottom, VS Code "Output" style) ---------- */
#LogPanel { background: $surface; border-top: 1px solid $border; }
#LogPanel #PanelTitle { color: $text_muted; font-size: 11px; font-weight: 600; letter-spacing: 1px; }
#LogPanel QPlainTextEdit { background: $surface; border: none; border-radius: 0; padding: 4px 10px;
                           selection-background-color: $selection; selection-color: $text; }
#LogPanel QComboBox, #LogPanel QLineEdit { min-height: 0; padding: 2px 8px; font-size: 12px; }
#LogPanel QToolButton { background: transparent; border: none; border-radius: 4px; padding: 3px; }
#LogPanel QToolButton:hover { background: $hover; }

/* ---------- command palette ---------- */
#CommandPalette { background: $surface; border: 1px solid $border_strong; border-radius: 10px; }
#CommandPalette QLineEdit { font-size: 14px; padding: 8px 10px; }
#CommandPalette QListWidget { border: none; background: transparent; }
#CommandPalette QListWidget::item { padding: 7px 10px; }
#CommandPalette QListWidget::item:selected { background: $accent; color: $accent_text; }
""")


def current() -> ThemeColors:
    return _current


def mode() -> str:
    """The chosen setting: "system", "dark" or "light"."""
    return _mode


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


def _transparent_popup(window: QWidget) -> None:
    """Let a popup window show only its rounded content: no square background, no square system shadow.

    Must run before the window is first shown. Turning transparency on later leaves black corners on
    Windows, because the native window already exists without an alpha channel.
    """
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    window.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
    window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)


class _PopupRowDelegate(QStyledItemDelegate):
    """Rows of an open select: a rounded highlight inset from the edges (the stylesheet can only draw square bars)."""

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        colors = current()
        enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
        selected = enabled and bool(option.state & QStyle.StateFlag.State_Selected)
        hover = enabled and bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected or hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors.accent if selected else colors.hover))
            painter.drawRoundedRect(QRectF(option.rect).adjusted(2, 1, -2, -1), 6.0, 6.0)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        if not enabled:
            painter.setPen(QColor(colors.text_disabled))
        elif selected:
            painter.setPen(QColor(colors.accent_text))
        else:
            painter.setPen(QColor(colors.text))
        painter.setFont(option.font)
        painter.drawText(
            option.rect.adjusted(10, 0, -10, 0),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            option.fontMetrics.elidedText(text, Qt.TextElideMode.ElideRight, max(option.rect.width() - 20, 20)),
        )
        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        hint = super().sizeHint(option, index)
        hint.setHeight(POPUP_ROW_HEIGHT)
        return hint


class _PopupSearch(QObject):
    """Search as the first row of an open select: a real text box whose text filters the rows below it.

    Click it to place the cursor or select text, or just start typing while the list is open: the keys
    move into the box. From the box, Up/Down move through the matches, Enter picks the highlighted one
    and Esc closes the list. The box sits in a top viewport margin of the list, which Qt counts when it
    sizes the popup, so the popup still opens at its final size below the select (or above it when
    there is no room).
    """

    NAVIGATION = (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown)

    def __init__(self, combo: QComboBox, view: QListView, container: QWidget):
        super().__init__(combo)
        self.combo, self.view, self.container = combo, view, container
        self.box = QLineEdit(view)
        self.box.setObjectName("ComboSearch")
        self.box.setPlaceholderText("Type to search")
        self.box.setClearButtonEnabled(True)
        self.box.hide()
        self.box.textChanged.connect(self.search)
        self.box.installEventFilter(self)
        view.installEventFilter(self)
        container.installEventFilter(self)
        model = combo.model()
        for signal in (model.rowsInserted, model.rowsRemoved, model.modelReset, model.layoutChanged):
            signal.connect(self.reserve_space)
        self.reserve_space()

    def active(self) -> bool:
        return not self.combo.isEditable()

    def reserve_space(self, *_args) -> None:
        active = self.active()
        self.view.setViewportMargins(0, SEARCH_HEIGHT + SEARCH_GAP if active else 0, 0, 0)
        self.box.setVisible(active)
        self._place_box()
        if self.view.property("search") != active:
            self.view.setProperty("search", active)  # moves the scrollbar under the box (stylesheet)
            bar = self.view.verticalScrollBar()
            bar.style().unpolish(bar)
            bar.style().polish(bar)

    def _place_box(self) -> None:
        area = self.view.contentsRect()
        self.box.setGeometry(area.left() + 2, area.top(), area.width() - 4, SEARCH_HEIGHT)

    def search(self, text: str) -> None:
        """Show only rows containing every word of `text` (any case, any order) and highlight the first
        one that can be chosen."""
        words = text.lower().split()
        needle = " ".join(words)
        model, column = self.combo.model(), self.combo.modelColumn()
        first = None
        for row in range(self.combo.count()):
            label = self.combo.itemText(row).lower()
            match = all(word in label for word in words)
            self.view.setRowHidden(row, not match)
            if match and first is None and model.flags(model.index(row, column)) & Qt.ItemFlag.ItemIsEnabled:
                first = row
        if not needle:
            self.view.setCurrentIndex(model.index(self.combo.currentIndex(), column))
        elif first is None:
            self.view.setCurrentIndex(QModelIndex())  # nothing to choose: Enter does nothing
        else:
            self.view.setCurrentIndex(model.index(first, column))

    def choose(self) -> None:
        """Pick the highlighted row, the way a click on it would."""
        index = self.view.currentIndex()
        if not index.isValid() or not index.flags() & Qt.ItemFlag.ItemIsEnabled:
            return
        row = index.row()
        self.combo.hidePopup()
        self.combo.setCurrentIndex(row)
        self.combo.activated.emit(row)
        self.combo.textActivated.emit(self.combo.itemText(row))

    def reset(self) -> None:
        """Empty search, every row back, for the next open. The highlight is left alone: Qt reads it
        right after hiding the popup to know which row was chosen."""
        self.box.blockSignals(True)
        self.box.clear()
        self.box.blockSignals(False)
        for row in range(self.combo.count()):
            self.view.setRowHidden(row, False)

    def _box_key(self, event: QKeyEvent) -> bool:
        """Keys typed in the box: navigation goes to the list, Enter picks, Esc closes."""
        key = event.key()
        if key in self.NAVIGATION:
            QApplication.sendEvent(self.view, QKeyEvent(event.type(), key, event.modifiers()))
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.choose()
            return True
        if key == Qt.Key.Key_Escape:
            self.combo.hidePopup()
            return True
        return False

    def _list_key(self, event: QKeyEvent) -> bool:
        """Typing while the list has focus: move the keys into the box and keep typing there."""
        modifiers = event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
                                         | Qt.KeyboardModifier.MetaModifier)
        if event.key() == Qt.Key.Key_Backspace:
            self.box.setFocus()
            self.box.backspace()
            return True
        if not modifiers and event.text() and event.text().isprintable():
            self.box.setFocus()
            self.box.insert(event.text())
            return True
        return False

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not shiboken6.isValid(self.combo):
            return False  # app shutdown: Qt hides the popup after the select itself is gone
        kind = event.type()
        if watched is self.container:
            if kind == QEvent.Type.Hide and self.box.text():
                self.reset()
        elif watched is self.view and kind == QEvent.Type.Resize:
            self._place_box()
        elif isinstance(event, QKeyEvent) and self.active() and self.container.isVisible():
            if kind == QEvent.Type.ShortcutOverride and watched is self.box and event.key() in (
                    Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
                event.accept()  # handled on the key press below, not as a window shortcut
                return True
            if kind == QEvent.Type.KeyPress:
                if watched is self.box:
                    return self._box_key(event)
                if watched is self.view:
                    return self._list_key(event)
        return False


def polish_combo_popup(combo: QComboBox) -> None:
    """A select's list as a rounded dropdown with rounded row highlights and a search box first.

    Qt's own popup is kept, so keyboard, wheel and item states behave as usual.
    """
    if combo.property("popup_polished"):
        return
    combo.setProperty("popup_polished", True)
    combo.setMaxVisibleItems(POPUP_MAX_ROWS)
    view = combo.view()
    view.setItemDelegate(_PopupRowDelegate(view))
    view.setFrameShape(QFrame.Shape.NoFrame)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setTextElideMode(Qt.TextElideMode.ElideRight)
    view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    view.setMouseTracking(True)
    container = view.window()  # Qt's popup window around the list, created by view()
    if container is combo.window():
        return
    container.setObjectName("ComboPopup")
    _transparent_popup(container)
    if isinstance(view, QListView):
        view.setUniformItemSizes(True)
        view.setSpacing(0)
        _PopupSearch(combo, view, container)


def polish_menu(menu: QMenu) -> None:
    """Rounded menus (see the QMenu stylesheet) without a square backdrop."""
    if not menu.property("popup_polished"):
        menu.setProperty("popup_polished", True)
        _transparent_popup(menu)


def apply_theme(app: QApplication, mode: str | None) -> ThemeColors:
    """Apply "dark", "light" or "system" to the whole application and return its colors."""
    global _current, _mode
    _mode = mode if mode in THEMES else "system"
    # Tell Qt which scheme the app uses, so native parts (the system title bar, native dialogs) match.
    # Unknown hands the choice back to the OS for "system".
    app.styleHints().setColorScheme({"dark": Qt.ColorScheme.Dark, "light": Qt.ColorScheme.Light}
                                    .get(_mode, Qt.ColorScheme.Unknown))
    _current = resolve(_mode)
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
    sizes = {"search_bar_top": f"{SEARCH_HEIGHT + SEARCH_GAP + 10}px"}
    app.setStyleSheet(STYLESHEET.substitute({**vars(_current), **images, **sizes}))
    return _current


def polish_views(root: QWidget) -> None:
    """Uniform tables (left-aligned headers, columns sized to fit, no grid), select popups and menus under `root`."""
    for combo in root.findChildren(QComboBox):
        polish_combo_popup(combo)
    for menu in root.findChildren(QMenu):
        polish_menu(menu)
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
