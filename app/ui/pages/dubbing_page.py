"""Video Dubbing Page: timeline alignment, speaker assignment, line synthesis, and video remuxing."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import EMOTIONS
from app.models.request import (
    DubbingImportRequest,
    DubbingProjectRequest,
    DubbingRenderRequest,
    DubbingSegmentRequest,
)
from app.services.audio_service import audio_service
from app.services.dubbing_service import dubbing_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.select import Select
from app.utils import ffmpeg
from app.utils.subtitles import ms_to_timestamp


class DubbingPage(BasePage):
    title = "Video Dubbing Studio"
    subtitle = "Multi-speaker video dubbing: align subtitles, map voices, detect duration conflicts, and render synchronized video."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.project: dict | None = None
        self.active_segment_id: int | None = None
        self._loading = False

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.root.addWidget(splitter, 1)

        # ------------------------------------------------------------ Left: Project list
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self._select_project)

        new_btn = QPushButton("Import Video / Media…")
        new_btn.setObjectName("Primary")
        new_btn.clicked.connect(self.new_project_dialog)
        del_btn = QPushButton("Delete Project")
        del_btn.clicked.connect(self.delete_project)

        lv.addWidget(QLabel("Dubbing Projects"))
        lv.addWidget(self.project_list)
        btn_row = QHBoxLayout()
        btn_row.addWidget(new_btn)
        btn_row.addWidget(del_btn)
        lv.addLayout(btn_row)
        splitter.addWidget(left)

        # ------------------------------------------------------------ Center: Timeline & Segments
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)

        # Project Info Header
        self.project_info = QLabel("Select or import a media file to start dubbing")
        self.project_info.setObjectName("Hint")
        cv.addWidget(self.project_info)

        # Actions toolbar
        toolbar = QHBoxLayout()
        self.import_subs_btn = QPushButton("Import SRT / VTT…")
        self.import_subs_btn.clicked.connect(self.import_subtitles_dialog)
        self.export_subs_btn = QPushButton("Export Subtitles…")
        self.export_subs_btn.clicked.connect(self.export_subtitles_dialog)
        self.auto_map_btn = QPushButton("Auto-Assign Voices")
        self.auto_map_btn.clicked.connect(self.auto_assign_voices)
        self.gen_all_btn = QPushButton("Generate All Lines")
        self.gen_all_btn.setObjectName("Primary")
        self.gen_all_btn.clicked.connect(self.generate_all_lines)

        toolbar.addWidget(self.import_subs_btn)
        toolbar.addWidget(self.export_subs_btn)
        toolbar.addWidget(self.auto_map_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.gen_all_btn)
        cv.addLayout(toolbar)

        # Timeline Segments Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "Start", "End", "Speaker", "Dialogue Text", "Audio Dur", "Timing Status"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._table_selection_changed)
        cv.addWidget(self.table, 1)

        splitter.addWidget(center)

        # ------------------------------------------------------------ Right: Tabs
        tabs = QTabWidget()
        tabs.addTab(self._segment_tab(), "Segment Editor")
        tabs.addTab(self._speakers_tab(), "Speaker Mapping")
        tabs.addTab(self._render_tab(), "Render Video")
        self.tabs = tabs
        splitter.addWidget(tabs)

        splitter.setSizes([200, 600, 380])
        self.refresh()

    # ---------------------------------------------------------------- Tabs UI

    def _segment_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        form = QFormLayout()
        self.seg_start = QSpinBox()
        self.seg_start.setRange(0, 10_000_000)
        self.seg_start.setSingleStep(500)
        self.seg_start.setSuffix(" ms")
        self.seg_end = QSpinBox()
        self.seg_end.setRange(0, 10_000_000)
        self.seg_end.setSingleStep(500)
        self.seg_end.setSuffix(" ms")
        self.seg_speaker = QLineEdit()

        self.seg_voice = Select()
        self.seg_speed = QDoubleSpinBox()
        self.seg_speed.setRange(0.5, 2.0)
        self.seg_speed.setSingleStep(0.05)
        self.seg_speed.setValue(1.0)

        self.seg_emotion = Select()
        self.seg_emotion.addItems(EMOTIONS)
        self.seg_emotion.setCurrentText("neutral")

        form.addRow("Start Time:", self.seg_start)
        form.addRow("End Time:", self.seg_end)
        form.addRow("Speaker:", self.seg_speaker)
        form.addRow("Voice:", self.seg_voice)
        form.addRow("Speed:", self.seg_speed)
        form.addRow("Emotion:", self.seg_emotion)
        layout.addLayout(form)

        layout.addWidget(QLabel("Target Dialogue Text:"))
        self.seg_text = QPlainTextEdit()
        self.seg_text.setFixedHeight(90)
        layout.addWidget(self.seg_text)

        self.conflict_badge = QLabel("Select a segment")
        self.conflict_badge.setObjectName("Hint")
        layout.addWidget(self.conflict_badge)

        btn_row = QHBoxLayout()
        self.save_seg_btn = QPushButton("Save Segment")
        self.save_seg_btn.clicked.connect(self.save_active_segment)
        self.gen_seg_btn = QPushButton("Generate Line")
        self.gen_seg_btn.setObjectName("Primary")
        self.gen_seg_btn.clicked.connect(self.generate_active_segment)
        btn_row.addWidget(self.save_seg_btn)
        btn_row.addWidget(self.gen_seg_btn)
        layout.addLayout(btn_row)

        self.player = AudioPlayer()
        layout.addWidget(self.player)
        layout.addStretch()
        return w

    def _speakers_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel("Map detected speakers to voices:"))
        self.speakers_table = QTableWidget()
        self.speakers_table.setColumnCount(2)
        self.speakers_table.setHorizontalHeaderLabels(["Speaker", "Assigned Voice"])
        self.speakers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.speakers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.speakers_table, 1)

        save_map_btn = QPushButton("Save Speaker Assignments")
        save_map_btn.clicked.connect(self.save_speaker_map)
        layout.addWidget(save_map_btn)
        return w

    def _render_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()

        self.bg_mode = Select()
        self.bg_mode.addItems(["Duck Original Audio (-12 dB)", "Replace Original Audio", "Mute Original Audio"])

        self.video_quality = Select()
        self.video_quality.addItems(["Lossless Stream Copy (fastest)", "Re-encode Video (x264)"])

        self.bitrate = Select()
        self.bitrate.addItems(["192k", "256k", "320k"])

        form.addRow("Background Audio:", self.bg_mode)
        form.addRow("Video Quality:", self.video_quality)
        form.addRow("Audio Bitrate:", self.bitrate)
        layout.addLayout(form)

        self.render_btn = QPushButton("Render Synchronized Video")
        self.render_btn.setObjectName("Primary")
        self.render_btn.clicked.connect(self.render_final_video)
        layout.addWidget(self.render_btn)

        self.output_label = QLabel("Output video not rendered yet.")
        self.output_label.setObjectName("Hint")
        self.output_label.setWordWrap(True)
        layout.addWidget(self.output_label)

        layout.addStretch()
        return w

    # ------------------------------------------------------------ Data Loading

    def refresh(self):
        projects = self.run(dubbing_service.list_projects) or []
        self._loading = True
        self.project_list.clear()
        selected_row = 0
        for i, p in enumerate(projects):
            item = QListWidgetItem(p["title"])
            item.setData(Qt.ItemDataRole.UserRole, p["dubbing_projects_id"])
            self.project_list.addItem(item)
            if self.project and p["dubbing_projects_id"] == self.project.get("dubbing_projects_id"):
                selected_row = i
        self._loading = False
        if projects:
            self.project_list.setCurrentRow(selected_row)
        else:
            self.project = None
            self._render_project_ui()

    def _select_project(self, current: QListWidgetItem | None):
        if self._loading or not current:
            return
        proj_id = current.data(Qt.ItemDataRole.UserRole)
        self.project = self.run(lambda: dubbing_service.get(proj_id))
        self._render_project_ui()

    def _render_project_ui(self):
        if not self.project:
            self.project_info.setText("No project loaded")
            self.table.setRowCount(0)
            return

        p = self.project
        meta = []
        if p.get("video_width") and p.get("video_height"):
            meta.append(f"{p['video_width']}x{p['video_height']}")
        if p.get("video_fps"):
            meta.append(f"{p['video_fps']} fps")
        if p.get("duration_seconds"):
            meta.append(f"{round(p['duration_seconds'], 1)} s")

        media_name = Path(p.get("source_media_path", "")).name
        self.project_info.setText(f"{p['title']}  •  {media_name} ({', '.join(meta)})")

        # Populate table
        segments = p.get("segments", [])
        self.table.setRowCount(len(segments))
        for row, s in enumerate(segments):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(ms_to_timestamp(s["start_ms"])))
            self.table.setItem(row, 2, QTableWidgetItem(ms_to_timestamp(s["end_ms"])))
            self.table.setItem(row, 3, QTableWidgetItem(s.get("speaker") or "Narrator"))
            self.table.setItem(row, 4, QTableWidgetItem(s.get("target_text") or s.get("source_text") or ""))

            gen_dur = f"{s['generated_duration_ms']} ms" if s.get("generated_duration_ms") else "—"
            self.table.setItem(row, 5, QTableWidgetItem(gen_dur))

            conflict_type = s.get("conflict_type", "none")
            status_item = QTableWidgetItem(s.get("conflict_message") or "—")
            if conflict_type == "overflow":
                status_item.setForeground(Qt.GlobalColor.red)
            elif conflict_type == "underflow":
                status_item.setForeground(Qt.GlobalColor.cyan)
            elif conflict_type == "ok":
                status_item.setForeground(Qt.GlobalColor.green)
            self.table.setItem(row, 6, status_item)

        # Populate voices dropdown
        voices = voice_service.list_voices()
        self.seg_voice.clear()
        for v in voices:
            self.seg_voice.addItem(f"{v['name']} ({v['voice_type']})", v["voices_id"])

        # Output video label
        if p.get("output_video_path"):
            self.output_label.setText(f"Exported Video:\n{p['output_video_path']}")
        else:
            self.output_label.setText("Output video not rendered yet.")

        # Populate speakers table
        speakers = p.get("speakers", [])
        self.speakers_table.setRowCount(len(speakers))
        speaker_map = p.get("speaker_map") or {}
        for r, spk in enumerate(speakers):
            self.speakers_table.setItem(r, 0, QTableWidgetItem(spk))
            selector = Select()
            for v in voices:
                selector.addItem(f"{v['name']} ({v['voice_type']})", v["voices_id"])
            if spk in speaker_map and speaker_map[spk]:
                idx = selector.findData(speaker_map[spk])
                if idx >= 0:
                    selector.setCurrentIndex(idx)
            self.speakers_table.setCellWidget(r, 1, selector)

        if segments:
            self.table.selectRow(0)

    # ------------------------------------------------------------ Table Selection

    def _table_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows or not self.project:
            return
        idx = rows[0].row()
        segments = self.project.get("segments", [])
        if idx >= len(segments):
            return
        seg = segments[idx]
        self.active_segment_id = seg["dubbing_segments_id"]

        self.seg_start.setValue(seg["start_ms"])
        self.seg_end.setValue(seg["end_ms"])
        self.seg_speaker.setText(seg.get("speaker") or "Narrator")
        self.seg_text.setPlainText(seg.get("target_text") or seg.get("source_text") or "")
        self.seg_speed.setValue(seg.get("speed") or 1.0)
        self.seg_emotion.setCurrentText(seg.get("emotion") or "neutral")
        if seg.get("voices_id"):
            idx = self.seg_voice.findData(seg["voices_id"])
            if idx >= 0:
                self.seg_voice.setCurrentIndex(idx)

        self.conflict_badge.setText(seg.get("conflict_message") or "")
        if seg.get("audios_id"):
            audio_row = audio_service.get(seg["audios_id"])
            if audio_row and Path(audio_row["file_path"]).is_file():
                self.player.load(audio_row["file_path"])
        else:
            self.player.load("")

    # ------------------------------------------------------------ User Actions

    def new_project_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video or Audio to Dub",
            "",
            "Media Files (*.mp4 *.mkv *.mov *.avi *.webm *.wav *.mp3);;All Files (*.*)",
        )
        if not file_path:
            return
        path = Path(file_path)
        title = path.stem
        req = DubbingProjectRequest(title=title, source_media_path=str(path.resolve()))
        res = self.run(lambda: dubbing_service.save(req))
        if res:
            self.project = res
            self.refresh()

    def delete_project(self):
        if not self.project:
            return
        if QMessageBox.question(self, "Delete Dubbing Project", f"Delete '{self.project['title']}'?") != QMessageBox.StandardButton.Yes:
            return
        dubbing_service.delete(self.project["dubbing_projects_id"])
        self.project = None
        self.refresh()

    def import_subtitles_dialog(self):
        if not self.project:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Subtitles", "", "Subtitle Files (*.srt *.vtt);;All Files (*.*)"
        )
        if not file_path:
            return
        content = Path(file_path).read_text(encoding="utf-8", errors="replace")
        fmt = "vtt" if file_path.lower().endswith(".vtt") else "srt"
        req = DubbingImportRequest(
            dubbing_projects_id=self.project["dubbing_projects_id"],
            content=content,
            format=fmt,
            replace_existing=True,
        )
        self.project = self.run(lambda: dubbing_service.import_subtitles(
            dubbing_projects_id=req.dubbing_projects_id, content=req.content, format=req.format, replace_existing=True
        ))
        self._render_project_ui()

    def export_subtitles_dialog(self):
        if not self.project:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Subtitles", f"{self.project['title']}.srt", "SRT Subtitles (*.srt);;WebVTT (*.vtt)"
        )
        if not file_path:
            return
        fmt = "vtt" if file_path.lower().endswith(".vtt") else "srt"
        text = dubbing_service.export_subtitles(self.project["dubbing_projects_id"], format=fmt)
        Path(file_path).write_text(text, encoding="utf-8")
        QMessageBox.information(self, "Exported", f"Subtitles saved to:\n{file_path}")

    def save_active_segment(self):
        if not self.active_segment_id:
            return
        req = DubbingSegmentRequest(
            dubbing_segments_id=self.active_segment_id,
            start_ms=self.seg_start.value(),
            end_ms=self.seg_end.value(),
            speaker=self.seg_speaker.text().strip(),
            target_text=self.seg_text.toPlainText().strip(),
            voices_id=self.seg_voice.currentData(),
            speed=self.seg_speed.value(),
            emotion=self.seg_emotion.currentText(),
        )
        dubbing_service.save_segment(req)
        self.project = dubbing_service.get(self.project["dubbing_projects_id"])
        self._render_project_ui()

    def generate_active_segment(self):
        if not self.active_segment_id:
            return
        self.save_active_segment()
        self.run(lambda: dubbing_service.generate_segment(self.active_segment_id))
        self.project = dubbing_service.get(self.project["dubbing_projects_id"])
        self._render_project_ui()

    def generate_all_lines(self):
        if not self.project:
            return
        self.run(lambda: dubbing_service.generate_all(self.project["dubbing_projects_id"], overwrite_existing=False))
        self.project = dubbing_service.get(self.project["dubbing_projects_id"])
        self._render_project_ui()

    def auto_assign_voices(self):
        if not self.project:
            return
        self.project = self.run(lambda: dubbing_service.auto_map_speakers(self.project["dubbing_projects_id"]))
        self._render_project_ui()

    def save_speaker_map(self):
        if not self.project:
            return
        new_map = {}
        for r in range(self.speakers_table.rowCount()):
            spk = self.speakers_table.item(r, 0).text()
            sel = self.speakers_table.cellWidget(r, 1)
            if sel and sel.currentData():
                new_map[spk] = sel.currentData()
        req = DubbingProjectRequest(
            dubbing_projects_id=self.project["dubbing_projects_id"],
            speaker_map=new_map,
        )
        self.project = dubbing_service.save(req)
        QMessageBox.information(self, "Saved", "Speaker assignments saved.")

    def render_final_video(self):
        if not self.project:
            return
        if not ffmpeg.available():
            QMessageBox.warning(self, "FFmpeg Required", "FFmpeg is required for video remuxing.")
            return

        mode_str = "duck"
        if "Replace" in self.bg_mode.currentText():
            mode_str = "replace"
        elif "Mute" in self.bg_mode.currentText():
            mode_str = "mute"

        q_str = "copy" if "Copy" in self.video_quality.currentText() else "reencode"
        req = DubbingRenderRequest(
            dubbing_projects_id=self.project["dubbing_projects_id"],
            background_audio_mode=mode_str,
            video_quality=q_str,
            audio_bitrate=self.bitrate.currentText(),
        )
        self.project = self.run(lambda: dubbing_service.render_video(req))
        self._render_project_ui()
        if self.project and self.project.get("output_video_path"):
            QMessageBox.information(self, "Success", f"Synchronized video rendered successfully!\n\n{self.project['output_video_path']}")

