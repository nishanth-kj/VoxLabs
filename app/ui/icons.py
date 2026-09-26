"""Line icons (24×24, stroke = currentColor) rendered in the active theme's colors.

    icon("home")                              # theme icon color, dimmed when disabled
    icon("home", checked=theme.current().accent)  # a different color for checked buttons
"""

import tempfile
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from app.ui import theme

ICONS: dict[str, str] = {
    # navigation
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h5v-6h4v6h5V10"/>',
    "studio": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18"/><path d="M8 13v4M12 12v6M16 14v2"/>',
    "clone": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3M9 21h6"/>',
    "generate": '<path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/>'
                '<path d="M19 15l.8 2.2 2.2.8-2.2.8L19 21l-.8-2.2-2.2-.8 2.2-.8z"/>',
    "script": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>'
              '<path d="M8 13h8M8 17h5"/>',
    "editor": '<path d="M2 12h1M6 8v8M10 4v16M14 7v10M18 10v4M22 12h-1"/>',
    "voices": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/>'
              '<path d="M18.5 14.5a6.5 6.5 0 0 1 3 5.5"/>',
    "projects": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "models": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>'
              '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "settings": '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/>'
                '<circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
    "sidebar": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    # window
    "minimize": '<path d="M6 12h12"/>',
    "maximize": '<rect x="6" y="6" width="12" height="12" rx="1"/>',
    "restore": '<rect x="5" y="8" width="11" height="11" rx="1"/><path d="M8 8V6a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-2"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    # file and edit
    "open": '<path d="M3 17V6a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v2"/><path d="M3 19l3-8h16l-3 8z"/>',
    "import": '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M4 20h16"/>',
    "export": '<path d="M12 16V4"/><path d="M7 9l5-5 5 5"/><path d="M4 20h16"/>',
    "save": '<path d="M5 3h11l4 4v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 1-2z"/><path d="M8 3v5h7V3"/>'
            '<rect x="7" y="13" width="10" height="7" rx="1"/>',
    "undo": '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    "redo": '<path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/>',
    "cut": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.1 8.1L20 20M8.1 15.9L20 4"/>',
    "copy": '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
    "paste": '<rect x="5" y="4" width="14" height="17" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/>',
    "delete": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/><path d="M10 11v5M14 11v5"/>',
    "duplicate": '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M4 16V5a1 1 0 0 1 1-1h11"/>'
                 '<path d="M14.5 11.5v6M11.5 14.5h6"/>',
    "trim": '<path d="M6 2v14a2 2 0 0 0 2 2h14"/><path d="M18 22V8a2 2 0 0 0-2-2H2"/>',
    "move": '<path d="M4 12h16"/><path d="M16 8l4 4-4 4"/><path d="M8 8l-4 4 4 4"/>',
    "split": '<path d="M12 3v18"/><path d="M8 7l-4 5 4 5"/><path d="M16 7l4 5-4 5"/>',
    "join": '<path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7"/>'
            '<path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7"/>',
    "silence": '<path d="M2 12h5M17 12h5"/><path d="M10 7v10M14 7v10"/>',
    "fade_in": '<path d="M3 19L21 5v14z"/>',
    "fade_out": '<path d="M3 5l18 14H3z"/>',
    "volume": '<path d="M11 5L6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
    "normalize": '<path d="M4 20V10M10 20V4M16 20V8M21 20H3"/>',
    "enhance": '<path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8l1.4 1.4M17.8 6.2l1.4-1.4M12.2 6.2l-1.4-1.4"/>'
               '<path d="M3 21l9-9"/>',
    # transport and view
    "play": '<path d="M7 4v16l13-8z" fill="currentColor"/>',
    "pause": '<rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor"/>'
             '<rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/>',
    "record": '<circle cx="12" cy="12" r="7" fill="currentColor"/>',
    "zoom_in": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4M8 11h6M11 8v6"/>',
    "zoom_out": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4M8 11h6"/>',
    "fit": '<path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "jobs": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "api": '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/>'
           '<path d="M7 7.5h.01M7 16.5h.01"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 0 1 4.9.8c0 1.7-2.4 2.2-2.4 3.7"/><path d="M12 17h.01"/>',
    "chevron_left": '<path d="M15 18l-6-6 6-6"/>',
    "chevron_up": '<path d="M6 15l6-6 6 6"/>',
    "chevron_down": '<path d="M6 9l6 6 6-6"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5" stroke-width="3"/>',
    "chevron_right": '<path d="M9 18l6-6-6-6"/>',
}

LOGO = ('<rect x="1" y="1" width="22" height="22" rx="6" fill="{accent}" stroke="none"/>'
        '<path d="M7 10v4M10 7v10M13 9v6M16 11v2" stroke="#ffffff" stroke-width="2.2"/>')

_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
_SCALE = 2  # render at 2× so icons stay sharp on high-DPI screens


def svg(name: str, color: str) -> str:
    body = LOGO.format(accent=theme.current().accent) if name == "logo" else ICONS[name].replace("currentColor", color)
    return _SVG.format(color=color, body=body)


def pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    image = QImage(size * _SCALE, size * _SCALE, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    QSvgRenderer(QByteArray(svg(name, color).encode())).render(painter, QRectF(0, 0, image.width(), image.height()))
    painter.end()
    result = QPixmap.fromImage(image)
    result.setDevicePixelRatio(_SCALE)
    return result


def icon(name: str, color: str | None = None, *, checked: str | None = None, size: int = 18) -> QIcon:
    """A QIcon in the active theme: normal, disabled (dimmed) and optionally checked colors."""
    colors = theme.current()
    normal = color or colors.icon
    result = QIcon()
    result.addPixmap(pixmap(name, normal, size), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(pixmap(name, colors.text if color is None else normal, size), QIcon.Mode.Active, QIcon.State.Off)
    result.addPixmap(pixmap(name, colors.text_disabled, size), QIcon.Mode.Disabled, QIcon.State.Off)
    on = checked or normal
    result.addPixmap(pixmap(name, on, size), QIcon.Mode.Normal, QIcon.State.On)
    result.addPixmap(pixmap(name, on, size), QIcon.Mode.Active, QIcon.State.On)
    return result


def icon_file(name: str, color: str) -> str:
    """The icon as an SVG file (for stylesheet `image: url(...)`), written once per color."""
    folder = Path(tempfile.gettempdir()) / "voxlabs-icons"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}-{color.lstrip('#')}.svg"
    if not path.exists():
        path.write_text(svg(name, color), encoding="utf-8")
    return path.as_posix()


ICON_SIZE = QSize(18, 18)
