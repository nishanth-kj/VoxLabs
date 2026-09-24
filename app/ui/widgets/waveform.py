"""Waveform view with cursor, drag selection and zoom (Ctrl+wheel) / scroll (wheel)."""

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from app.utils import audio as au

WAVE_COLOR = QColor(86, 156, 255)  # readable on light and dark palettes


class WaveformWidget(QWidget):
    cursor_moved = Signal(float)
    selection_changed = Signal(float, float)
    view_changed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self._y = np.zeros(0, dtype=np.float32)
        self._sr = 1
        self._peaks = None
        self.duration = 0.0
        self.view_start = 0.0
        self.view_end = 0.0
        self.cursor = 0.0
        self.playhead: float | None = None
        self.selection: tuple[float, float] | None = None
        self._drag_from: float | None = None

    # ------------------------------------------------------------ data

    def set_audio(self, y: np.ndarray, sr: int, keep_view: bool = False) -> None:
        self._y, self._sr = au.to_mono(y), sr
        self.duration = au.duration(self._y, sr)
        if not keep_view or self.view_end <= self.view_start or self.view_end > self.duration:
            self.view_start, self.view_end = 0.0, self.duration
        self.cursor = min(self.cursor, self.duration)
        if self.selection and self.selection[1] > self.duration:
            self.selection = None
        self._peaks = None
        self.update()
        self.view_changed.emit(self.view_start, self.view_end)

    def clear(self) -> None:
        self.set_audio(np.zeros(0, dtype=np.float32), 1)

    # ------------------------------------------------------------ geometry

    def x_to_time(self, x: float) -> float:
        span = max(self.view_end - self.view_start, 1e-9)
        return float(np.clip(self.view_start + x / max(self.width(), 1) * span, 0, self.duration))

    def time_to_x(self, t: float) -> float:
        span = max(self.view_end - self.view_start, 1e-9)
        return (t - self.view_start) / span * self.width()

    def set_view(self, start: float, end: float) -> None:
        span = max(0.01, end - start)
        start = max(0.0, min(start, max(0.0, self.duration - span)))
        self.view_start, self.view_end = start, min(self.duration, start + span)
        self._peaks = None
        self.update()
        self.view_changed.emit(self.view_start, self.view_end)

    def zoom(self, factor: float, around: float | None = None) -> None:
        around = self.cursor if around is None else around
        span = (self.view_end - self.view_start) * factor
        span = min(max(span, 0.01), max(self.duration, 0.01))
        ratio = (around - self.view_start) / max(self.view_end - self.view_start, 1e-9)
        self.set_view(around - ratio * span, around - ratio * span + span)

    # ------------------------------------------------------------ painting

    def _compute_peaks(self):
        if self._y.size == 0:
            return np.zeros((0, 2))
        a = int(self.view_start * self._sr)
        b = max(a + 1, int(self.view_end * self._sr))
        return au.waveform_peaks(self._y[a:b], max(1, self.width()))

    def paintEvent(self, _event):
        painter = QPainter(self)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.base())
        h, mid = self.height(), self.height() / 2
        if self.selection:
            x1, x2 = self.time_to_x(self.selection[0]), self.time_to_x(self.selection[1])
            painter.fillRect(QRectF(x1, 0, x2 - x1, h), QColor(66, 133, 244, 60))
        painter.setPen(QPen(palette.mid().color(), 1))
        painter.drawLine(0, int(mid), self.width(), int(mid))
        if self._peaks is None:
            self._peaks = self._compute_peaks()
        painter.setPen(QPen(WAVE_COLOR, 1))
        for x, (lo, hi) in enumerate(self._peaks):
            painter.drawLine(QPointF(x, mid - hi * mid * 0.95), QPointF(x, mid - lo * mid * 0.95))
        painter.setPen(QPen(QColor(230, 81, 0), 1.5))
        cx = self.time_to_x(self.cursor)
        painter.drawLine(QPointF(cx, 0), QPointF(cx, h))
        if self.playhead is not None:
            painter.setPen(QPen(QColor(46, 160, 67), 1.5))
            px = self.time_to_x(self.playhead)
            painter.drawLine(QPointF(px, 0), QPointF(px, h))
        if self._y.size == 0:
            painter.setPen(palette.placeholderText().color())
            painter.drawText(self.rect(), Qt.AlignCenter, "Open or import audio to edit")

    def resizeEvent(self, event):
        self._peaks = None
        super().resizeEvent(event)

    # ------------------------------------------------------------ interaction

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.duration:
            t = self.x_to_time(event.position().x())
            if event.modifiers() & Qt.ShiftModifier and self.selection:
                self.selection = (min(self.selection[0], t), max(self.selection[1], t))
                self.selection_changed.emit(*self.selection)
            else:
                self._drag_from = t
                self.selection = None
                self.cursor = t
                self.cursor_moved.emit(t)
                self.selection_changed.emit(t, t)
            self.update()

    def mouseMoveEvent(self, event):
        if self._drag_from is not None:
            t = self.x_to_time(event.position().x())
            a, b = sorted((self._drag_from, t))
            if b - a > 0.005:
                self.selection = (a, b)
                self.selection_changed.emit(a, b)
                self.update()

    def mouseReleaseEvent(self, _event):
        self._drag_from = None

    def wheelEvent(self, event):
        if not self.duration:
            return
        steps = event.angleDelta().y() / 120
        if event.modifiers() & Qt.ControlModifier:
            self.zoom(0.8**steps, self.x_to_time(event.position().x()))
        else:
            span = self.view_end - self.view_start
            self.set_view(self.view_start - steps * span * 0.1, self.view_end - steps * span * 0.1)

    def set_playhead(self, seconds: float | None):
        self.playhead = seconds
        self.update()

    def select(self, start: float, end: float):
        self.selection = (start, end) if end > start else None
        self.update()
        self.selection_changed.emit(start, end)

    def peak_level_db(self) -> float:
        if self.selection:
            a, b = (int(t * self._sr) for t in self.selection)
            return au.peak_db(self._y[a:b])
        return au.peak_db(self._y)
