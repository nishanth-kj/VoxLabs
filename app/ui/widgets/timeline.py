"""Time ruler that follows a waveform view, optionally showing labelled clips (script sections)."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.utils.time import format_duration

_CLIP_COLORS = [QColor(66, 133, 244), QColor(52, 168, 83), QColor(251, 188, 5), QColor(234, 67, 53),
                QColor(155, 81, 224), QColor(0, 172, 193)]


class TimelineWidget(QWidget):
    seek_requested = Signal(float)
    clip_clicked = Signal(object)

    def __init__(self, parent=None, show_clips: bool = False):
        super().__init__(parent)
        self.view_start = 0.0
        self.view_end = 1.0
        self.cursor_time = 0.0
        self.clips: list[dict] = []  # {"start", "end", "label", "key", "group"}
        self.setFixedHeight(56 if show_clips else 26)

    def set_view(self, start: float, end: float):
        self.view_start, self.view_end = start, max(end, start + 1e-3)
        self.update()

    def set_cursor(self, seconds: float):
        self.cursor_time = seconds
        self.update()

    def set_clips(self, clips: list[dict]):
        self.clips = clips
        if clips:
            self.set_view(0.0, max(c["end"] for c in clips))
        self.update()

    def _x(self, t: float) -> float:
        return (t - self.view_start) / (self.view_end - self.view_start) * self.width()

    def _t(self, x: float) -> float:
        return self.view_start + x / max(self.width(), 1) * (self.view_end - self.view_start)

    def paintEvent(self, _event):
        painter = QPainter(self)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.window())
        span = self.view_end - self.view_start
        step = next((s for s in (0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600)
                     if span / s <= max(self.width() / 80, 1)), 1200)
        painter.setPen(QPen(palette.text().color(), 1))
        t = (int(self.view_start / step)) * step
        while t <= self.view_end:
            x = self._x(t)
            painter.drawLine(int(x), 0, int(x), 6)
            painter.drawText(int(x) + 3, 16, format_duration(t))
            t += step
        top = 24
        for index, clip in enumerate(self.clips):
            x1, x2 = self._x(clip["start"]), self._x(clip["end"])
            rect = QRectF(x1, top, max(2.0, x2 - x1 - 1), self.height() - top - 2)
            color = _CLIP_COLORS[clip.get("group", index) % len(_CLIP_COLORS)]
            painter.fillRect(rect, color.lighter(150) if not clip.get("missing") else QColor(200, 200, 200))
            painter.setPen(color.darker(150))
            painter.drawRect(rect)
            painter.drawText(rect.adjusted(3, 0, -2, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, clip.get("label", ""))
        painter.setPen(QPen(QColor(230, 81, 0), 1.5))
        cx = self._x(self.cursor_time)
        painter.drawLine(int(cx), 0, int(cx), self.height())

    def mousePressEvent(self, event):
        t = self._t(event.position().x())
        for clip in self.clips:
            if clip["start"] <= t <= clip["end"] and event.position().y() > 24:
                self.clip_clicked.emit(clip)
                break
        self.seek_requested.emit(max(0.0, t))
