"""Audio Editor: non-destructive waveform editing.

The source file is never modified. Every edit is an operation in `self.ops`
(replayed by AudioService.apply_edit_ops); undo/redo move operations between
stacks. "Render" writes a new library audio, and the edit list is autosaved
into the project so a session can be resumed.
"""

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import ENHANCE_PRESETS, EXPORT_FORMATS
from app.models.request import AudioExportRequest, AudioProcessRequest
from app.services.audio_service import audio_service
from app.services.project_service import project_service
from app.services.system_service import system_service
from app.ui import icons
from app.ui.pages import BasePage
from app.ui.pages.clone_page import AUDIO_FILTER
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.timeline import TimelineWidget
from app.ui.widgets.waveform import WaveformWidget
from app.utils import audio as au
from app.utils.logger import logger
from app.utils.time import format_duration


class LibraryDialog(QDialog):
    """Pick an audio from the library."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open audio")
        self.resize(560, 420)
        self.list = QListWidget()
        for audio in audio_service.list_audios(projects_id=None, limit=500):
            label = f"{audio['name']}  · {format_duration(audio['duration'])} · {audio['source']}"
            if audio["ai_generated"]:
                label += " · AI"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, audio["audios_id"])
            self.list.addItem(item)
        self.list.itemActivated.connect(lambda _i: self.accept())
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list)
        layout.addWidget(buttons)

    def selected(self) -> int | None:
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None


class EditorPage(BasePage):
    title = "Audio Editor"
    subtitle = "Non-destructive editing: every change is an edit you can undo; the source file is never changed."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.audio: dict | None = None
        self.sr = 1
        self.states: list[np.ndarray] = []  # states[i] = audio after ops[:i]
        self.ops: list[dict] = []
        self.redo_ops: list[dict] = []
        self.clip_path: str | None = None
        self._preview_path: str | None = None
        self._preview_dirty = True
        self._saved_ops: list[dict] = []

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(icons.ICON_SIZE)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._icon_actions: list[tuple[QAction, str]] = []
        self.root.addWidget(self.toolbar)
        self._build_actions()

        splitter = QSplitter(Qt.Orientation.Vertical)
        wave_box = QWidget()
        wv = QVBoxLayout(wave_box)
        wv.setContentsMargins(0, 0, 0, 0)
        self.waveform = WaveformWidget()
        self.timeline = TimelineWidget()
        self.waveform.view_changed.connect(self.timeline.set_view)
        self.waveform.cursor_moved.connect(self._cursor_moved)
        self.waveform.selection_changed.connect(lambda *_: self._update_properties())
        self.timeline.seek_requested.connect(self._seek)
        wv.addWidget(self.waveform, 1)
        wv.addWidget(self.timeline)
        self.player = AudioPlayer(compact=True)
        self.player.position_changed.connect(self._on_play_position)
        transport = QHBoxLayout()
        transport.addWidget(self.player, 1)
        self.loop = QCheckBox("Loop selection")
        play_sel = QPushButton("Play selection")
        play_sel.clicked.connect(self.play_selection)
        play_cursor = QPushButton("Play from cursor")
        play_cursor.clicked.connect(self.play_from_cursor)
        for widget in (play_cursor, play_sel, self.loop):
            transport.addWidget(widget)
        wv.addLayout(transport)
        splitter.addWidget(wave_box)

        bottom = QSplitter(Qt.Orientation.Horizontal)
        props = QGroupBox("Properties")
        pf = QFormLayout(props)
        self.prop_labels = {}
        for key in ("File", "Duration", "Sample rate", "Selection", "Peak level", "Loudness", "Edits", "Label"):
            label = QLabel("—")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.prop_labels[key] = label
            pf.addRow(key, label)
        bottom.addWidget(props)

        effects = QGroupBox("Effects (apply to selection, or whole file when nothing is selected)")
        ef = QFormLayout(effects)
        self.preset = QComboBox()
        self.preset.addItems([p for p in ENHANCE_PRESETS if p != "Raw"])
        apply_preset = QPushButton("Apply enhancement preset")
        apply_preset.setObjectName("Primary")
        apply_preset.clicked.connect(lambda: self.enhance())
        ef.addRow("Preset", self.preset)
        ef.addRow(apply_preset)
        row = QHBoxLayout()
        for label, slot in (("Denoise", lambda: self.enhance({"denoise": {"strength": 0.6}})),
                            ("Compress", lambda: self.enhance({"compress": {}})),
                            ("De-ess", lambda: self.enhance({"deess": {}})),
                            ("Loudness −16 LUFS", lambda: self.enhance({"loudness": {"target_lufs": -16}}))):
            button = QPushButton(label)
            button.clicked.connect(slot)
            row.addWidget(button)
        ef.addRow(row)
        bottom.addWidget(effects)
        bottom.setSizes([420, 560])
        splitter.addWidget(bottom)
        splitter.setSizes([520, 200])
        self.root.addWidget(splitter, 1)

        state.open_audio.connect(self.open_audio)

    # ------------------------------------------------------------ actions

    def _action(self, text, slot, shortcut=None, toolbar=True, icon=None):
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            action.setToolTip(f"{text} ({QKeySequence(shortcut).toString()})")
        if icon:
            action.setIcon(icons.icon(icon))
            self._icon_actions.append((action, icon))
        self.addAction(action)
        if toolbar:
            self.toolbar.addAction(action)
        return action

    def refresh_icons(self):
        for action, name in self._icon_actions:
            action.setIcon(icons.icon(name))

    def _build_actions(self):
        self._action("Open…", self.choose_audio, "Ctrl+O", icon="open")
        self._action("Import…", self.import_file, "Ctrl+I", icon="import")
        self._action("Save edits as new audio", self.render_edits, "Ctrl+S", icon="save")
        self._action("Export…", self.export, "Ctrl+E", icon="export")
        self.toolbar.addSeparator()
        self.undo_action = self._action("Undo", self.undo, "Ctrl+Z", icon="undo")
        self.redo_action = self._action("Redo", self.redo, "Ctrl+Shift+Z", icon="redo")
        self._action("Redo", self.redo, "Ctrl+Y", toolbar=False)
        self.toolbar.addSeparator()
        self._action("Cut", self.cut, "Ctrl+X", icon="cut")
        self._action("Copy", self.copy, "Ctrl+C", icon="copy")
        self._action("Paste", self.paste, "Ctrl+V", icon="paste")
        self._action("Delete", self.delete, "Delete", icon="delete")
        self._action("Duplicate", self.duplicate, "Ctrl+D", icon="duplicate")
        self.toolbar.addSeparator()
        self._action("Trim to selection", self.crop, "Ctrl+T", icon="trim")
        self._action("Move selection to cursor", self.move_selection, icon="move")
        self._action("Split at cursor", self.split, icon="split")
        self._action("Join another audio…", self.join, icon="join")
        self._action("Insert silence…", self.insert_silence, icon="silence")
        self.toolbar.addSeparator()
        self._action("Fade in", self.fade_in, icon="fade_in")
        self._action("Fade out", self.fade_out, icon="fade_out")
        self._action("Volume…", self.volume, icon="volume")
        self._action("Normalize", self.normalize, icon="normalize")
        self.toolbar.addSeparator()
        self._action("Zoom in", self.zoom_in, icon="zoom_in")
        self._action("Zoom out", self.zoom_out, icon="zoom_out")
        self._action("Zoom to fit", self.zoom_fit, icon="fit")
        self._action("Play/Pause", self.toggle_play, "Space", toolbar=False)
        self._action("Select all", self.select_all, "Ctrl+A", toolbar=False)
        self._action("Cursor to start", lambda: self._cursor_moved(0.0, move_waveform=True), "Home", toolbar=False)
        self._action("Cursor to end", lambda: self._cursor_moved(self.waveform.duration, move_waveform=True),
                     "End", toolbar=False)
        self._update_actions()

    # ------------------------------------------------------------ loading

    def choose_audio(self):
        dialog = LibraryDialog(self)
        audios_id = dialog.selected() if dialog.exec() else None
        if audios_id:
            self.open_audio(audios_id)

    def import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import audio", "", AUDIO_FILTER)
        if path:
            self.run(lambda: audio_service.import_file(path),
                     lambda audio: (self.state.notify("audio"), self.open_audio(audio["audios_id"])))

    def open_audio(self, audios_id: int):
        self.autosave()

        def load():
            audio = audio_service.get(audios_id)
            y, sr = au.load(audio["path"])
            ops = project_service.load_edit_ops(audio["projects_id"], audios_id)
            states = [y]
            if ops:
                try:
                    for op in ops:
                        states.append(audio_service.apply_edit_ops(states[-1], sr, [op]))
                except Exception:
                    ops, states = [], [y]
            return audio, sr, ops, states

        self.run(load, self._loaded)

    def _loaded(self, data):
        self.audio, self.sr, self.ops, self.states = data
        self._saved_ops = list(self.ops)
        self.redo_ops = []
        self._refresh_view(keep_view=False)

    # ------------------------------------------------------------ state

    @property
    def current(self) -> np.ndarray:
        return self.states[-1] if self.states else np.zeros(0, dtype=np.float32)

    def _refresh_view(self, keep_view=True):
        self.waveform.set_audio(self.current, self.sr, keep_view=keep_view)
        self._preview_dirty = True
        self.player.load(None)
        self._update_properties()
        self._update_actions()

    def _update_actions(self):
        self.undo_action.setEnabled(bool(self.ops))
        self.redo_action.setEnabled(bool(self.redo_ops))

    def _update_properties(self):
        labels = self.prop_labels
        if not self.audio:
            for label in labels.values():
                label.setText("—")
            return
        labels["File"].setText(self.audio["name"])
        labels["Duration"].setText(f"{format_duration(self.waveform.duration)} "
                                   f"(source {format_duration(self.audio['duration'])})")
        labels["Sample rate"].setText(f"{self.sr} Hz · mono working copy")
        sel = self.waveform.selection
        labels["Selection"].setText(f"{sel[0]:.2f}s – {sel[1]:.2f}s ({sel[1] - sel[0]:.2f}s)" if sel
                                    else f"cursor {self.waveform.cursor_time:.2f}s")
        labels["Peak level"].setText(f"{self.waveform.peak_level_db():.1f} dBFS")
        loudness = self.audio.get("loudness")
        labels["Loudness"].setText(f"{loudness:.1f} LUFS (source)" if loudness is not None else "—")
        labels["Edits"].setText(f"{len(self.ops)} operation(s) · source file untouched")
        labels["Label"].setText("AI-generated" if self.audio["ai_generated"] else "Recording / import")

    def _push(self, op: dict, result: np.ndarray | None = None):
        """Apply one operation and make it undoable."""
        if not self.audio:
            return
        try:
            result = result if result is not None else audio_service.apply_edit_ops(self.current, self.sr, [op])
        except Exception as exc:
            self.error(exc)
            return
        if result.size == 0:
            self.error("That edit would remove all audio")
            return
        self.ops.append(op)
        self.states.append(result)
        self.redo_ops.clear()
        self._refresh_view()

    def undo(self):
        if self.ops:
            self.redo_ops.append(self.ops.pop())
            self.states.pop()
            self._refresh_view()

    def redo(self):
        if self.redo_ops:
            op = self.redo_ops.pop()
            self.ops.append(op)
            self.states.append(audio_service.apply_edit_ops(self.current, self.sr, [op]))
            self._refresh_view()

    # ------------------------------------------------------------ selection helpers

    def _selection(self, require=True):
        sel = self.waveform.selection
        if sel is None and require:
            self.error("Select a region first (drag on the waveform)")
        return sel

    def _range(self):
        """Selection, or the whole file when nothing is selected."""
        return self.waveform.selection or (0.0, self.waveform.duration)

    def select_all(self):
        if self.audio:
            self.waveform.select(0.0, self.waveform.duration)

    def _cursor_moved(self, seconds, move_waveform=False):
        if move_waveform:
            self.waveform.cursor_time = seconds
            self.waveform.update()
        self.timeline.set_cursor(seconds)
        self._update_properties()

    def _seek(self, seconds):
        self.waveform.cursor_time = seconds
        self.waveform.update()
        self._cursor_moved(seconds)

    # ------------------------------------------------------------ editing operations

    def _clip_selection(self) -> str | None:
        sel = self._selection()
        if not sel:
            return None
        a, b = (int(t * self.sr) for t in sel)
        return audio_service.save_clip(self.current[a:b], self.sr)

    def copy(self):
        path = self._clip_selection()
        if path:
            self.clip_path = path

    def cut(self):
        sel = self._selection()
        if sel:
            self.clip_path = self._clip_selection()
            self._push({"op": "cut", "start": sel[0], "end": sel[1]})
            self.waveform.select(sel[0], sel[0])

    def paste(self):
        if not self.clip_path:
            self.error("Nothing copied yet")
            return
        at = self.waveform.cursor_time
        self._push({"op": "paste", "at": at, "clip": self.clip_path})

    def delete(self):
        sel = self._selection()
        if sel:
            self._push({"op": "delete", "start": sel[0], "end": sel[1]})
            self.waveform.select(sel[0], sel[0])

    def crop(self):
        sel = self._selection()
        if sel:
            self._push({"op": "crop", "start": sel[0], "end": sel[1]})
            self.waveform.select(0, 0)

    def duplicate(self):
        sel = self._selection()
        if sel:
            self._push({"op": "duplicate", "start": sel[0], "end": sel[1]})

    def move_selection(self):
        sel = self._selection()
        if sel:
            self._push({"op": "move", "start": sel[0], "end": sel[1], "to": self.waveform.cursor_time})

    def insert_silence(self):
        seconds, ok = QInputDialog.getDouble(self, "Insert silence", "Seconds:", 0.5, 0.01, 60, 2)
        if ok:
            self._push({"op": "silence", "at": self.waveform.cursor_time, "duration": seconds})

    def volume(self):
        db, ok = QInputDialog.getDouble(self, "Volume", "Gain (dB, negative is quieter):", -3.0, -40, 20, 1)
        if ok:
            self._apply_range_op("gain", db=db)

    def _apply_range_op(self, kind, **extra):
        if self.audio:
            start, end = self._range()
            self._push({"op": kind, "start": start, "end": end, **extra})

    def enhance(self, steps: dict | None = None):
        if not self.audio:
            return
        start, end = self._range()
        op = {"op": "enhance", "start": start, "end": end}
        if steps:
            op["steps"] = steps
        else:
            op["preset"] = self.preset.currentText()
        current, sr = self.current, self.sr
        self.run(lambda: audio_service.apply_edit_ops(current, sr, [op]), lambda y: self._push(op, y))

    def join(self):
        dialog = LibraryDialog(self)
        audios_id = dialog.selected() if dialog.exec() else None
        if audios_id:
            other = audio_service.get(audios_id)
            self._push({"op": "append", "clip": other["path"], "gap": 0.3})

    def split(self):
        """Render the current edit and split it at the cursor into two new library files."""
        if not self.audio:
            return
        at, ops, audios_id = self.waveform.cursor_time, list(self.ops), self.audio["audios_id"]
        self.run(lambda: audio_service.split(audio_service.materialize(audios_id, ops)["audios_id"], at),
                 lambda parts: (self.state.notify("audio"), self.open_audio(parts[0]["audios_id"])))

    # ------------------------------------------------------------ playback

    def _ensure_preview(self):
        if self._preview_dirty and self.audio:
            if not self.ops:
                self._preview_path = self.audio["path"]
            else:
                self._preview_path = audio_service.save_clip(self.current, self.sr)
            self.player.load(self._preview_path, self.audio["name"])
            self._preview_dirty = False

    def fade_in(self):
        self._apply_range_op("fade_in")

    def fade_out(self):
        self._apply_range_op("fade_out")

    def normalize(self):
        self._apply_range_op("normalize", peak_db=-1.0)

    def zoom_in(self):
        self.waveform.zoom(0.5)

    def zoom_out(self):
        self.waveform.zoom(2.0)

    def zoom_fit(self):
        self.waveform.set_view(0, self.waveform.duration)

    def toggle_play(self):
        if not self.audio:
            return
        if self.player.is_playing():
            self.player.toggle()
            return
        self._ensure_preview()
        if self.waveform.selection and self.loop.isChecked():
            self.play_selection()
        else:
            self.player.play(self.waveform.cursor_time)

    def play_from_cursor(self):
        if self.audio:
            self._ensure_preview()
            self.player.play(self.waveform.cursor_time)

    def play_selection(self):
        sel = self._selection()
        if sel:
            self._ensure_preview()
            self.player.play_range(sel[0], sel[1], loop=self.loop.isChecked())

    def _on_play_position(self, seconds):
        self.waveform.set_playhead(seconds if self.player.is_playing() else None)
        self.timeline.set_cursor(seconds)

    # ------------------------------------------------------------ output

    def render_edits(self):
        if not self.audio:
            return
        if not self.ops:
            self.error("No edits to render yet")
            return
        audios_id, ops = self.audio["audios_id"], list(self.ops)
        job = audio_service.process_async(AudioProcessRequest(audios_id=audios_id, ops=ops))
        self.follow(job, lambda r: (self.state.notify("audio"), self._rendered(r["audio"])))

    def _rendered(self, audio):
        self.prop_labels["Edits"].setText(f"Rendered as “{audio['name']}” (#{audio['audios_id']})")

    def export(self):
        if not self.audio:
            return
        formats = list(EXPORT_FORMATS)
        default = system_service.get_setting("export_format")
        fmt, ok = QInputDialog.getItem(self, "Export", "Format:", formats,
                                       formats.index(default) if default in formats else 0, False)
        if not ok:
            return
        start = Path(system_service.get_setting("output_dir") or ".") / f"{self.audio['name']}.{fmt}"
        path, _ = QFileDialog.getSaveFileName(self, "Export audio", str(start), f"*.{fmt}")
        if not path:
            return
        audios_id, ops = self.audio["audios_id"], list(self.ops)
        self.run(lambda: audio_service.export(
            AudioExportRequest(audios_id=audio_service.materialize(audios_id, ops)["audios_id"], format=fmt), path),
                 lambda p: self.prop_labels["Edits"].setText(f"Exported to {p}"))

    def autosave(self):
        """Persist the edit list into the audio's project (nothing to do without a project)."""
        if self.audio and self.audio.get("projects_id") and self.ops != self._saved_ops:
            try:
                project_service.save_edit_ops(self.audio["projects_id"], self.audio["audios_id"], self.ops)
                self._saved_ops = list(self.ops)
            except Exception as exc:
                logger.warning(f"Editor autosave failed: {exc}")
