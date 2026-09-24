"""Script to Audio: script editor, structure, speaker→voice mapping, per-section settings and takes."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
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
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import EMOTIONS, ENHANCE_PRESETS, STYLES
from app.models.request import SectionRequest
from app.services.audio_service import audio_service
from app.services.script_service import DEFAULT_SPEAKER, script_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.model_selector import ModelSelector
from app.ui.widgets.voice_selector import VoiceSelector
from app.utils.time import format_duration

EXAMPLE = """Lesson 1

Introduction

Teacher: Welcome to today's lesson.

Student: What does this concept mean?

Teacher: It means sound travels as a wave.

Summary

Narrator: That's all for today. [pause 1s] See you next time.
"""


class ScriptPage(BasePage):
    title = "Script to Audio"

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.script: dict | None = None
        self.section: dict | None = None
        self._loading = False

        splitter = QSplitter(Qt.Horizontal)
        self.root.addWidget(splitter, 1)

        # Left: script list
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.script_list = QListWidget()
        self.script_list.currentItemChanged.connect(self._select_script)
        new = QPushButton("New script")
        new.clicked.connect(self.new_script)
        delete = QPushButton("Delete")
        delete.clicked.connect(self.delete_script)
        lv.addWidget(QLabel("Scripts"))
        lv.addWidget(self.script_list)
        row = QHBoxLayout()
        row.addWidget(new)
        row.addWidget(delete)
        lv.addLayout(row)
        splitter.addWidget(left)

        # Center: editor
        center = QWidget()
        cv = QVBoxLayout(center)
        cv.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Script title")
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Headings: 'Lesson 1', 'Chapter 2', 'Introduction', 'Section 1', or '# Title' / '## Section'.\n"
            "Speakers: 'Teacher: line'.  Pauses: [pause 800ms] or a line with [pause 2s].")
        self.editor.textChanged.connect(self._schedule_save)
        self.title_edit.textEdited.connect(self._schedule_save)
        cv.addWidget(self.title_edit)
        cv.addWidget(self.editor, 1)
        self.save_state = QLabel("")
        self.save_state.setObjectName("Hint")
        cv.addWidget(self.save_state)
        splitter.addWidget(center)

        # Right: tabs
        tabs = QTabWidget()
        tabs.addTab(self._structure_tab(), "Structure")
        tabs.addTab(self._speakers_tab(), "Speakers")
        tabs.addTab(self._section_tab(), "Section")
        tabs.addTab(self._settings_tab(), "Script settings")
        self.tabs = tabs
        splitter.addWidget(tabs)
        splitter.setSizes([180, 560, 420])

        bottom = QHBoxLayout()
        self.generate_all_button = QPushButton("Generate all")
        self.generate_all_button.clicked.connect(lambda: self.generate_all(False))
        regen_all = QPushButton("Regenerate all")
        regen_all.clicked.connect(lambda: self.generate_all(True))
        render = QPushButton("Render final audio")
        render.clicked.connect(self.render)
        open_editor = QPushButton("Open final in editor")
        open_editor.clicked.connect(self._open_final)
        for button in (self.generate_all_button, regen_all, render, open_editor):
            bottom.addWidget(button)
        bottom.addStretch()
        self.root.addLayout(bottom)
        self.player = AudioPlayer()
        self.root.addWidget(self.player)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self.save)

        state.open_script.connect(self.open_script)
        state.project_changed.connect(lambda _p: self.refresh())
        state.data_changed.connect(lambda what: self._voices_changed() if what == "voices" else None)

    # ------------------------------------------------------------ tabs

    def _structure_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Structure", "Speaker", "Take"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.currentItemChanged.connect(self._select_section)
        self.tree.itemActivated.connect(lambda item, _c: self._play_section(item))
        layout.addWidget(self.tree)
        row = QHBoxLayout()
        up = QPushButton("Move up")
        up.clicked.connect(lambda: self.move_section(-1))
        down = QPushButton("Move down")
        down.clicked.connect(lambda: self.move_section(1))
        row.addWidget(up)
        row.addWidget(down)
        row.addStretch()
        layout.addLayout(row)
        self.summary = QLabel("")
        layout.addWidget(self.summary)
        return widget

    def _speakers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.speaker_table = QTableWidget(0, 2)
        self.speaker_table.setHorizontalHeaderLabels(["Speaker", "Voice"])
        self.speaker_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.speaker_table)
        row = QHBoxLayout()
        auto = QPushButton("Auto-assign voices")
        auto.clicked.connect(self.auto_map)
        save = QPushButton("Apply mapping")
        save.clicked.connect(self.save_mapping)
        row.addWidget(auto)
        row.addWidget(save)
        row.addStretch()
        layout.addLayout(row)
        hint = QLabel("“Narrator (default)” is used for lines without a speaker and for intro/outro.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        return widget

    def _section_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.section_label = QLabel("Select a section in Structure")
        self.section_label.setWordWrap(True)
        self.section_voice = VoiceSelector(none_label="Use speaker mapping")
        self.section_speed = self._spin(0.0, 2.0)
        self.section_pitch = self._spin(0.0, 2.0)
        self.section_emotion = QComboBox()
        self.section_emotion.addItem("Script default", None)
        for emotion in EMOTIONS:
            self.section_emotion.addItem(emotion, emotion)
        self.section_style = QComboBox()
        self.section_style.addItem("Script default", None)
        for style in STYLES:
            self.section_style.addItem(style, style)
        self.section_pause = QSpinBox()
        self.section_pause.setRange(0, 20000)
        self.section_pause.setSingleStep(100)
        self.section_pause.setSuffix(" ms after")
        form.addRow(self.section_label)
        form.addRow("Voice", self.section_voice)
        form.addRow("Speed", self.section_speed)
        form.addRow("Pitch", self.section_pitch)
        form.addRow("Emotion", self.section_emotion)
        form.addRow("Style", self.section_style)
        form.addRow("Pause", self.section_pause)
        layout.addLayout(form)
        row = QHBoxLayout()
        apply = QPushButton("Apply")
        apply.clicked.connect(self.save_section)
        generate = QPushButton("Generate take")
        generate.clicked.connect(self.generate_section)
        row.addWidget(apply)
        row.addWidget(generate)
        layout.addLayout(row)
        layout.addWidget(QLabel("Takes (only the selected take is rendered)"))
        self.takes = QListWidget()
        self.takes.itemActivated.connect(self._play_take)
        layout.addWidget(self.takes)
        row2 = QHBoxLayout()
        for label, slot in (("Play", lambda: self._play_take(self.takes.currentItem())),
                            ("Use this take", self.select_take), ("Delete take", self.delete_take)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            row2.addWidget(button)
        layout.addLayout(row2)
        return widget

    def _settings_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        self.default_model = ModelSelector()
        self.default_speed = self._spin(0.0, 2.0)
        self.default_emotion = QComboBox()
        self.default_emotion.addItems(list(EMOTIONS))
        self.default_style = QComboBox()
        self.default_style.addItems(list(STYLES))
        self.final_preset = QComboBox()
        self.final_preset.addItems(list(ENHANCE_PRESETS))
        self.speak_headings = QCheckBox("Read headings aloud")
        self.intro = QPlainTextEdit()
        self.intro.setMaximumHeight(60)
        self.outro = QPlainTextEdit()
        self.outro.setMaximumHeight(60)
        form.addRow("Model", self.default_model)
        form.addRow("Speed", self.default_speed)
        form.addRow("Emotion", self.default_emotion)
        form.addRow("Style", self.default_style)
        form.addRow("Final clean-up", self.final_preset)
        form.addRow("", self.speak_headings)
        form.addRow("Intro text", self.intro)
        form.addRow("Outro text", self.outro)
        save = QPushButton("Save settings")
        save.clicked.connect(self.save_settings)
        form.addRow(save)
        return widget

    def _spin(self, low, high):
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setSingleStep(0.05)
        spin.setSpecialValueText("default")
        return spin

    # ------------------------------------------------------------ loading

    def refresh(self):
        self.default_model.refresh()
        self.section_voice.refresh()
        self.run(lambda: script_service.list_scripts(self.state.projects_id), self._show_list, busy=False)

    def _show_list(self, scripts):
        current = self.script["scripts_id"] if self.script else None
        self.script_list.blockSignals(True)
        self.script_list.clear()
        for script in scripts:
            item = QListWidgetItem(script["title"])
            item.setData(Qt.UserRole, script["scripts_id"])
            self.script_list.addItem(item)
            if script["scripts_id"] == current:
                self.script_list.setCurrentItem(item)
        self.script_list.blockSignals(False)
        if current is None and scripts:
            self.script_list.setCurrentRow(0)

    def open_script(self, scripts_id: int):
        self.run(lambda: script_service.get(scripts_id), self._show_script)

    def _select_script(self, item, _previous=None):
        if item is not None:
            self.save()
            self.open_script(item.data(Qt.UserRole))

    def _show_script(self, script):
        self._loading = True
        self.script = script
        if self.title_edit.text() != script["title"]:
            self.title_edit.setText(script["title"])
        if self.editor.toPlainText() != script["body"]:
            self.editor.setPlainText(script["body"])
        settings = script["settings"] or {}
        self.default_model.set_model_key(settings.get("model_key"))
        self.default_speed.setValue(settings.get("speed") or 0.0)
        self.default_emotion.setCurrentText(settings.get("emotion") or "neutral")
        self.default_style.setCurrentText(settings.get("style") or "default")
        self.final_preset.setCurrentText(settings.get("preset") or "Raw")
        self.speak_headings.setChecked(bool(settings.get("speak_headings")))
        self.intro.setPlainText(settings.get("intro_text") or "")
        self.outro.setPlainText(settings.get("outro_text") or "")
        self._loading = False
        self._show_structure()
        self._show_speakers()
        if script["final_audios_id"]:
            try:
                final = audio_service.get(script["final_audios_id"])
                self.player.load(final["path"], f"{script['title']} (final)")
            except Exception:
                self.player.load(None)

    def _show_structure(self):
        selected = self.section["script_sections_id"] if self.section else None
        self.tree.blockSignals(True)
        self.tree.clear()
        chapters, headings = {}, {}
        generated = 0
        for section in self.script["sections"]:
            chapter = chapters.get(section["chapter"])
            if chapter is None:
                chapter = QTreeWidgetItem(self.tree, [section["chapter"] or "(no chapter)"])
                chapters[section["chapter"]] = chapter
                chapter.setExpanded(True)
            key = (section["chapter"], section["heading"])
            heading = headings.get(key)
            if heading is None:
                heading = QTreeWidgetItem(chapter, [section["heading"] or "(no heading)"])
                headings[key] = heading
                heading.setExpanded(True)
            take = next((t for t in section["takes"] if t["selected"]), None)
            generated += take is not None
            text = section["text"] if len(section["text"]) < 70 else section["text"][:67] + "…"
            item = QTreeWidgetItem(heading, [text, section["speaker"],
                                             f"#{take['take_number']}" if take else "—"])
            item.setData(0, Qt.UserRole, section["script_sections_id"])
            if section["script_sections_id"] == selected:
                self.tree.setCurrentItem(item)
        self.tree.blockSignals(False)
        total = len(self.script["sections"])
        self.summary.setText(f"{total} sections · {generated} generated · "
                             f"{len(self.script['speakers'])} speaker(s)")

    def _show_speakers(self):
        mapping = self.script["speaker_map"] or {}
        speakers = [DEFAULT_SPEAKER] + self.script["speakers"]
        self.speaker_table.setRowCount(len(speakers))
        for row, speaker in enumerate(speakers):
            name = _readonly_item("Narrator (default)" if speaker == DEFAULT_SPEAKER else speaker)
            name.setData(Qt.UserRole, speaker)
            self.speaker_table.setItem(row, 0, name)
            selector = VoiceSelector(none_label="Default voice")
            selector.set_voices_id(mapping.get(speaker))
            self.speaker_table.setCellWidget(row, 1, selector)

    def _voices_changed(self):
        self.section_voice.refresh()
        if self.script:
            self._show_speakers()

    # ------------------------------------------------------------ editing

    def new_script(self):
        title, ok = QInputDialog.getText(self, "New script", "Title:", text="Untitled script")
        if ok and title.strip():
            self.run(lambda: script_service.create(title, EXAMPLE, projects_id=self.state.projects_id),
                     lambda s: (self._show_script(s), self.refresh()))

    def delete_script(self):
        if not self.script:
            return
        if QMessageBox.question(self, "Delete script",
                                f"Delete “{self.script['title']}” and all its generated takes?") != QMessageBox.Yes:
            return
        scripts_id = self.script["scripts_id"]
        self.script = None
        self.editor.clear()
        self.tree.clear()
        self.run(lambda: script_service.delete(scripts_id), lambda _r: self.refresh())

    def _schedule_save(self):
        if not self._loading and self.script:
            self.save_state.setText("Editing…")
            self._save_timer.start()

    def save(self):
        if not self.script or self._loading:
            return
        self._save_timer.stop()
        scripts_id, title, body = self.script["scripts_id"], self.title_edit.text() or "Untitled", \
            self.editor.toPlainText()
        if title == self.script["title"] and body == self.script["body"]:
            return
        self.run(lambda: script_service.update(scripts_id, title=title, body=body), self._saved, busy=False)

    def _saved(self, script):
        if self.script and script["scripts_id"] == self.script["scripts_id"]:
            self.script = script
            self._show_structure()
            self._show_speakers()
            self.save_state.setText("Saved")
            item = self.script_list.currentItem()
            if item and item.text() != script["title"]:
                item.setText(script["title"])

    def save_settings(self):
        if not self.script:
            return
        settings = {
            "model_key": self.default_model.model_key(),
            "speed": self.default_speed.value() or None,
            "emotion": self.default_emotion.currentText(),
            "style": self.default_style.currentText(),
            "preset": self.final_preset.currentText(),
            "speak_headings": self.speak_headings.isChecked(),
            "intro_text": self.intro.toPlainText().strip(),
            "outro_text": self.outro.toPlainText().strip(),
        }
        scripts_id = self.script["scripts_id"]
        self.run(lambda: script_service.update(scripts_id, settings=settings), self._show_script)

    def _mapping_from_table(self) -> dict:
        mapping = {}
        for row in range(self.speaker_table.rowCount()):
            speaker = self.speaker_table.item(row, 0).data(Qt.UserRole)
            mapping[speaker] = self.speaker_table.cellWidget(row, 1).voices_id()
        return mapping

    def save_mapping(self):
        if self.script:
            scripts_id, mapping = self.script["scripts_id"], self._mapping_from_table()
            self.run(lambda: script_service.map_speakers(scripts_id, mapping), self._show_script)

    def auto_map(self):
        if self.script:
            scripts_id = self.script["scripts_id"]
            voices = [v["voices_id"] for v in voice_service.list_voices()]
            self.run(lambda: script_service.auto_map_speakers(scripts_id, voices), self._show_script)

    def move_section(self, delta: int):
        if not self.script or not self.section:
            return
        ids = [s["script_sections_id"] for s in self.script["sections"]]
        index = ids.index(self.section["script_sections_id"])
        target = index + delta
        if 0 <= target < len(ids):
            ids[index], ids[target] = ids[target], ids[index]
            scripts_id = self.script["scripts_id"]
            self.run(lambda: script_service.reorder(scripts_id, ids), self._show_script)

    # ------------------------------------------------------------ sections / takes

    def _section_by_id(self, section_id):
        return next((s for s in self.script["sections"] if s["script_sections_id"] == section_id), None)

    def _select_section(self, item, _previous=None):
        section_id = item.data(0, Qt.UserRole) if item else None
        self.section = self._section_by_id(section_id) if section_id else None
        self._show_section()

    def _show_section(self):
        section = self.section
        self.takes.clear()
        if not section:
            self.section_label.setText("Select a section in Structure")
            return
        speaker = f"{section['speaker']}: " if section["speaker"] else ""
        self.section_label.setText(f"{speaker}{section['text']}")
        self.section_voice.set_voices_id(section["voices_id"])
        self.section_speed.setValue(section["speed"] or 0.0)
        self.section_pitch.setValue(section["pitch"] or 0.0)
        self.section_emotion.setCurrentIndex(max(0, self.section_emotion.findData(section["emotion"])))
        self.section_style.setCurrentIndex(max(0, self.section_style.findData(section["style"])))
        self.section_pause.setValue(section["pause_after_ms"] or 0)
        for take in section["takes"]:
            label = f"Take {take['take_number']}" + ("  ✓ selected" if take["selected"] else "")
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, take)
            self.takes.addItem(item)

    def save_section(self):
        if not self.section:
            return
        section_id = self.section["script_sections_id"]
        fields = {
            "voices_id": self.section_voice.voices_id(),
            "speed": self.section_speed.value() or None,
            "pitch": self.section_pitch.value() or None,
            "emotion": self.section_emotion.currentData(),
            "style": self.section_style.currentData(),
            "pause_after_ms": self.section_pause.value(),
        }
        self.run(lambda: script_service.update_section(SectionRequest(script_sections_id=section_id, **fields)),
                 self._section_updated)

    def _section_updated(self, section):
        for index, existing in enumerate(self.script["sections"]):
            if existing["script_sections_id"] == section["script_sections_id"]:
                self.script["sections"][index] = section
        self.section = section
        self._show_structure()
        self._show_section()

    def generate_section(self):
        if not self.section:
            return
        job = script_service.generate_section_async(self.section["script_sections_id"])
        self.follow(job, lambda r: (self._section_updated(r["section"]), self._play_take_audio(
            r["section"]["selected_audios_id"])))

    def select_take(self):
        item = self.takes.currentItem()
        if item:
            takes_id = item.data(Qt.UserRole)["takes_id"]
            self.run(lambda: script_service.select_take(takes_id), self._section_updated)

    def delete_take(self):
        item = self.takes.currentItem()
        if item:
            takes_id = item.data(Qt.UserRole)["takes_id"]
            self.run(lambda: script_service.delete_take(takes_id), self._section_updated)

    def _play_take(self, item):
        if item:
            self._play_take_audio(item.data(Qt.UserRole)["audios_id"])

    def _play_section(self, item):
        section = self._section_by_id(item.data(0, Qt.UserRole)) if item else None
        if section and section["selected_audios_id"]:
            self._play_take_audio(section["selected_audios_id"])

    def _play_take_audio(self, audios_id):
        if audios_id:
            audio = audio_service.get(audios_id)
            self.player.load(audio["path"], audio["name"])
            self.player.play()

    # ------------------------------------------------------------ whole script

    def generate_all(self, regenerate: bool):
        if not self.script:
            return
        self.save()
        job = script_service.generate_all_async(self.script["scripts_id"], regenerate)
        self.follow(job, lambda r: self._show_script(r["script"]))

    def render(self):
        if not self.script:
            return
        self.save()
        job = script_service.render_async(self.script["scripts_id"])
        self.follow(job, self._rendered)

    def _rendered(self, result):
        audio = result["audio"]
        self.script["final_audios_id"] = audio["audios_id"]
        self.player.load(audio["path"], f"{self.script['title']} (final) · {format_duration(audio['duration'])}")
        self.player.play()
        self.state.notify("audio")

    def _open_final(self):
        if self.script and self.script.get("final_audios_id"):
            self.state.open_audio.emit(self.script["final_audios_id"])


def _readonly_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    return item
