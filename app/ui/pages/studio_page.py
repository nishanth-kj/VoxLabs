"""Studio: one project at a glance — script, voices, takes, timeline and transport."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.exceptions import AppError
from app.models.request import SectionRequest
from app.services.audio_service import audio_service
from app.services.project_service import project_service
from app.services.script_service import script_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.timeline import TimelineWidget
from app.ui.widgets.voice_selector import VoiceSelector
from app.ui.widgets.waveform import WaveformWidget
from app.utils import audio as au
from app.utils.time import format_duration


class StudioPage(BasePage):
    title = "Studio"
    subtitle = "The whole production at a glance: sections, voices, timeline and final render."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.script: dict | None = None
        self.clips: list[dict] = []

        header = QHBoxLayout()
        self.project_box = QComboBox()
        self.project_box.setMinimumWidth(220)
        self.project_box.activated.connect(self._project_chosen)
        self.script_box = QComboBox()
        self.script_box.setMinimumWidth(220)
        self.script_box.activated.connect(lambda _i: self._load_script(self.script_box.currentData()))
        header.addWidget(QLabel("Project"))
        header.addWidget(self.project_box)
        header.addWidget(QLabel("Script / lesson"))
        header.addWidget(self.script_box)
        header.addStretch()
        edit = QPushButton("Edit script")
        edit.clicked.connect(lambda: self.script and self.state.open_script.emit(self.script["scripts_id"]))
        header.addWidget(edit)
        self.root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Vertical)
        top = QSplitter(Qt.Orientation.Horizontal)
        self.sections = QTableWidget(0, 4)
        self.sections.setHorizontalHeaderLabels(["Section", "Speaker", "Text", "Take"])
        self.sections.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.sections.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sections.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sections.currentCellChanged.connect(lambda row, *_: self._select_row(row))
        top.addWidget(self.sections)

        voice_box = QGroupBox("Voice")
        vf = QFormLayout(voice_box)
        self.section_info = QLabel("Select a section")
        self.section_info.setWordWrap(True)
        self.voice = VoiceSelector(none_label="Use speaker mapping")
        apply_voice = QPushButton("Use voice for this section")
        apply_voice.clicked.connect(self._apply_voice)
        generate = QPushButton("Generate new take")
        generate.clicked.connect(self._generate_section)
        self.mapping = QLabel("")
        self.mapping.setWordWrap(True)
        vf.addRow(self.section_info)
        vf.addRow("Voice", self.voice)
        vf.addRow(apply_voice)
        vf.addRow(generate)
        vf.addRow("Speakers", self.mapping)
        top.addWidget(voice_box)
        top.setSizes([760, 320])
        splitter.addWidget(top)

        timeline_box = QWidget()
        tl = QVBoxLayout(timeline_box)
        tl.setContentsMargins(0, 0, 0, 0)
        self.timeline = TimelineWidget(show_clips=True)
        self.timeline.clip_clicked.connect(self._clip_clicked)
        self.waveform = WaveformWidget()
        self.waveform.setMinimumHeight(110)
        self.waveform.view_changed.connect(self.timeline.set_view)
        self.timeline.seek_requested.connect(lambda t: self.player.seek(t))
        tl.addWidget(self.timeline)
        tl.addWidget(self.waveform, 1)
        splitter.addWidget(timeline_box)
        splitter.setSizes([420, 220])
        self.root.addWidget(splitter, 1)

        controls = QHBoxLayout()
        self.player = AudioPlayer()
        self.player.position_changed.connect(self._on_position)
        gen_missing = QPushButton("Generate missing")
        gen_missing.clicked.connect(lambda: self._generate_all(False))
        render = QPushButton("Render")
        render.clicked.connect(self._render)
        editor = QPushButton("Open in editor")
        editor.clicked.connect(lambda: self.script and self.script.get("final_audios_id")
                               and self.state.open_audio.emit(self.script["final_audios_id"]))
        controls.addWidget(self.player, 1)
        for button in (gen_missing, render, editor):
            controls.addWidget(button)
        self.root.addLayout(controls)

        state.project_changed.connect(lambda _p: self.refresh() if self.isVisible() else None)

    # ------------------------------------------------------------ loading

    def refresh(self):
        self.voice.refresh()
        self.run(project_service.list_projects, self._show_projects, busy=False)

    def _show_projects(self, projects):
        self.project_box.clear()
        self.project_box.addItem("All scripts (no project)", None)
        for project in projects:
            self.project_box.addItem(f"{project['name']} · {project['project_type']}", project["projects_id"])
        index = self.project_box.findData(self.state.projects_id)
        self.project_box.setCurrentIndex(max(index, 0))
        self._load_scripts()

    def _project_chosen(self, _index):
        self.state.set_project(self.project_box.currentData())
        self._load_scripts()

    def _load_scripts(self):
        projects_id = self.project_box.currentData()
        self.run(lambda: script_service.list_scripts(projects_id), self._show_scripts, busy=False)

    def _show_scripts(self, scripts):
        current = self.script["scripts_id"] if self.script else None
        self.script_box.clear()
        for script in scripts:
            self.script_box.addItem(script["title"], script["scripts_id"])
        index = self.script_box.findData(current)
        if scripts:
            self.script_box.setCurrentIndex(max(index, 0))
            self._load_script(self.script_box.currentData())
        else:
            self.script = None
            self.sections.setRowCount(0)
            self.timeline.set_clips([])
            self.waveform.clear()

    def _load_script(self, scripts_id):
        if scripts_id is None:
            return
        self.run(lambda: self._fetch(scripts_id), self._show_script)

    def _fetch(self, scripts_id):
        """Runs off the UI thread: script, clip layout, voice names and the decoded final render."""
        script = script_service.get(scripts_id)
        final = None
        if script.get("final_audios_id"):
            try:
                audio = audio_service.get(script["final_audios_id"])
                final = (audio, *au.load(audio["path"]))
            except AppError:
                final = None
        voices = {v["voices_id"]: v["name"] for v in voice_service.list_voices()}
        return script, script_service.timeline(scripts_id), voices, final

    def _show_script(self, data):
        script, self.clips, names, final = data
        self.script = script
        self.sections.setRowCount(len(script["sections"]))
        for row, section in enumerate(script["sections"]):
            take = next((t for t in section["takes"] if t["selected"]), None)
            values = [section["heading"] or section["chapter"], section["speaker"], section["text"],
                      f"#{take['take_number']} of {len(section['takes'])}" if take else "not generated"]
            for col, value in enumerate(values):
                self.sections.setItem(row, col, QTableWidgetItem(value))
        self.timeline.set_clips(self.clips)
        mapping = script["speaker_map"] or {}
        self.mapping.setText("\n".join(f"{'Narrator' if k == '*' else k} → {names.get(v, 'default')}"
                                       for k, v in mapping.items()) or "Default voice for everyone")
        if final:
            audio, y, sr = final
            self.waveform.set_audio(y, sr)
            self.player.load(audio["path"], f"{script['title']} · {format_duration(audio['duration'])}")
        else:
            self.waveform.clear()
            self.player.load(None)
        if self.clips:
            self.timeline.set_view(0, self.clips[-1]["end"])

    # ------------------------------------------------------------ interaction

    def _section(self, row):
        if self.script and 0 <= row < len(self.script["sections"]):
            return self.script["sections"][row]
        return None

    def _select_row(self, row):
        section = self._section(row)
        if section:
            self.section_info.setText(section["text"])
            self.voice.set_voices_id(section["voices_id"])

    def _clip_clicked(self, clip):
        for row, section in enumerate(self.script["sections"] if self.script else []):
            if section["script_sections_id"] == clip["key"]:
                self.sections.selectRow(row)
        if clip["audios_id"]:
            audio = audio_service.get(clip["audios_id"])
            self.player.load(audio["path"], audio["name"])
            self.player.play()

    def _on_position(self, seconds):
        self.waveform.set_playhead(seconds)
        self.timeline.set_cursor(seconds)

    def _apply_voice(self):
        section = self._section(self.sections.currentRow())
        if section and self.script:
            voices_id, scripts_id = self.voice.voices_id(), self.script["scripts_id"]
            self.run(lambda: script_service.update_section(
                SectionRequest(script_sections_id=section["script_sections_id"], voices_id=voices_id)),
                     lambda _s: self._load_script(scripts_id))

    def _generate_section(self):
        section = self._section(self.sections.currentRow())
        if section and self.script:
            scripts_id = self.script["scripts_id"]
            job = script_service.generate_section_async(section["script_sections_id"])
            self.follow(job, lambda _r: self._load_script(scripts_id))

    def _generate_all(self, regenerate):
        if self.script:
            scripts_id = self.script["scripts_id"]
            job = script_service.generate_all_async(scripts_id, regenerate)
            self.follow(job, lambda _r: self._load_script(scripts_id))

    def _render(self):
        if self.script:
            scripts_id = self.script["scripts_id"]
            job = script_service.render_async(scripts_id)
            self.follow(job, lambda _r: (self._load_script(scripts_id), self.state.notify("audio")))
