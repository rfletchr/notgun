import os

from qtpy.QtCore import Qt, QModelIndex
from qtpy.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QMainWindow

import notgun.bootstrap
import notgun.launcher
import notgun.pipeline

from notgun_launcher.view import MainView


class LauncherController:
    def __init__(self, projects_dir: str):
        self._projects_dir = projects_dir
        self._current_project_name: str | None = None
        self._pipeline: notgun.pipeline.Pipeline | None = None
        self._pipelines: dict[str, notgun.pipeline.Pipeline] = {}

        self._projects_model = QStandardItemModel()
        self._programs_model = QStandardItemModel()

        self.central_widget = MainView()
        self.central_widget.projectsView.setModel(self._projects_model)
        self.central_widget.programsView.setModel(self._programs_model)

        self.central_widget.projectsView.activated.connect(self._onProjectActivated)
        self.central_widget.projectsView.refreshRequested.connect(self._load_projects)
        self.central_widget.programsView.activated.connect(self._onProgramActivated)
        self.central_widget.programsView.backRequested.connect(self._load_projects)
        self.central_widget.programsView.refreshRequested.connect(self._reload_programs)

        self.window = QMainWindow()
        self.window.setCentralWidget(self.central_widget)

        self._load_projects()

    def _find_project_names(self) -> list[str]:
        names = []
        try:
            for name in sorted(os.listdir(self._projects_dir)):
                dirname = os.path.join(self._projects_dir, name)
                if not os.access(dirname, os.X_OK):
                    continue

                bootstrap = os.path.join(dirname, "init", "bootstrap.py")
                if os.path.isfile(bootstrap):
                    names.append(name)
        except OSError:
            pass
        return names

    def _get_project_pixmap(self, pipeline: notgun.pipeline.Pipeline) -> QPixmap | None:
        image_path = pipeline.metadata().get("image")
        if not image_path:
            return None
        if not os.path.isabs(image_path):
            image_path = os.path.join(
                self._projects_dir, pipeline.name(), "init", image_path
            )
        if not os.path.isfile(image_path):
            return None
        pixmap = QPixmap(image_path)
        return pixmap if not pixmap.isNull() else None

    def _make_project_item(self, pipeline: notgun.pipeline.Pipeline) -> QStandardItem:
        meta = pipeline.metadata()
        item = QStandardItem(meta.get("name", pipeline.name()))
        item.setEditable(False)
        item.setData(pipeline.name(), Qt.ItemDataRole.UserRole)

        pixmap = self._get_project_pixmap(pipeline)
        if pixmap is not None:
            item.setIcon(QIcon(pixmap))

        return item

    def _load_projects(self):
        self._current_project_name = None
        self._pipeline = None
        self._pipelines = {}
        self._projects_model.clear()

        for name in self._find_project_names():
            data = notgun.bootstrap.BootstrapData(self._projects_dir, name)
            pipeline = notgun.bootstrap.init(data)
            self._pipelines[name] = pipeline
            self._projects_model.appendRow(self._make_project_item(pipeline))

        self.central_widget.showProjectList()

    def _load_programs(self):
        self._programs_model.clear()

        if self._pipeline is None:
            return

        for program in self._pipeline.programs().values():
            item = QStandardItem(program.label)
            item.setEditable(False)
            item.setData(program, Qt.ItemDataRole.UserRole)
            self._programs_model.appendRow(item)

        meta = self._pipeline.metadata()
        self.central_widget.programsView.setLabel(
            meta.get("name", self._pipeline.name())
        )
        self.central_widget.programsView.setIcon(
            self._get_project_pixmap(self._pipeline)
        )
        self.central_widget.showProgramList()

    def _reload_programs(self):
        if self._current_project_name is None:
            return
        data = notgun.bootstrap.BootstrapData(
            self._projects_dir, self._current_project_name
        )
        self._pipeline = notgun.bootstrap.init(data)
        self._pipelines[self._current_project_name] = self._pipeline
        self._load_programs()

    def _onProjectActivated(self, index: QModelIndex):
        name = index.data(Qt.ItemDataRole.UserRole)
        self._current_project_name = name
        self._pipeline = self._pipelines[name]
        self._load_programs()

    def _onProgramActivated(self, index: QModelIndex):
        if self._current_project_name is None:
            return

        program: notgun.launcher.Program = index.data(Qt.ItemDataRole.UserRole)

        env = os.environ.copy()
        env[notgun.bootstrap.BOOTSTRAP_ENV_VAR] = notgun.bootstrap.BootstrapData(
            self._projects_dir,
            self._current_project_name,
        ).to_json_str()

        notgun.launcher.launch_program(program, env=env)
