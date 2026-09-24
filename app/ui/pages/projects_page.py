"""Projects: create, open, rename, duplicate, delete and export."""

from datetime import datetime

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.constants.project_type import ProjectType
from app.services.project_service import project_service
from app.ui.pages import BasePage
from app.utils.time import local_display

COLUMNS = ("Project", "Type", "Created", "Updated", "Status")


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New project")
        self.name = QLineEdit()
        self.kind = QComboBox()
        self.kind.addItems([t.title() for t in ProjectType.ALL])
        self.description = QLineEdit()
        form = QFormLayout(self)
        form.addRow("Name", self.name)
        form.addRow("Type", self.kind)
        form.addRow("Description", self.description)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)


class ProjectsPage(BasePage):
    title = "Projects"

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.projects: list[dict] = []
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda _i: self.open())
        self.root.addWidget(self.table, 1)
        actions = QHBoxLayout()
        for label, slot in (("New", self.new), ("Open", self.open), ("Rename", self.rename),
                            ("Duplicate", self.duplicate), ("Export…", self.export), ("Delete", self.delete),
                            ("Close project", self.close_project)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch()
        self.root.addLayout(actions)

    def refresh(self):
        self.run(project_service.list_projects, self._show, busy=False)

    def _show(self, projects):
        self.projects = projects
        self.table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            name = project["name"] + ("  (open)" if project["projects_id"] == self.state.projects_id else "")
            values = (name, project["project_type"].title(), _date(project["created_at"]),
                      _date(project["updated_at"]), project["status_label"])
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _current(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.projects):
            return self.projects[row]
        self.error("Select a project first")
        return None

    def _changed(self, _result=None):
        self.state.notify("projects")
        self.refresh()

    def new(self):
        dialog = NewProjectDialog(self)
        if dialog.exec():
            name, kind, desc = dialog.name.text(), dialog.kind.currentText().lower(), dialog.description.text()
            self.run(lambda: project_service.create_project(name, kind, desc),
                     lambda p: (self.state.set_project(p["projects_id"]), self._changed()))

    def open(self):
        project = self._current()
        if project:
            self.state.set_project(project["projects_id"])
            self.state.navigate.emit("studio")

    def close_project(self):
        self.state.set_project(None)
        self.refresh()

    def rename(self):
        project = self._current()
        if project:
            name, ok = QInputDialog.getText(self, "Rename project", "Name:", text=project["name"])
            if ok:
                self.run(lambda: project_service.rename_project(project["projects_id"], name), self._changed)

    def duplicate(self):
        project = self._current()
        if project:
            self.run(lambda: project_service.duplicate_project(project["projects_id"]), self._changed)

    def export(self):
        project = self._current()
        if project:
            path, _ = QFileDialog.getSaveFileName(self, "Export project", f"{project['name']}.zip", "*.zip")
            if path:
                self.run(lambda: project_service.export_project(project["projects_id"], path),
                         lambda p: QMessageBox.information(self, "Export", f"Exported to {p}"))

    def delete(self):
        project = self._current()
        if project and QMessageBox.question(
            self, "Delete project",
            f"Delete “{project['name']}” with its scripts, takes and audio files? This cannot be undone.",
        ) == QMessageBox.Yes:
            if self.state.projects_id == project["projects_id"]:
                self.state.set_project(None)
            self.run(lambda: project_service.delete_project(project["projects_id"]), self._changed)


def _date(value: str | None) -> str:
    return local_display(datetime.fromisoformat(value)) if value else ""
