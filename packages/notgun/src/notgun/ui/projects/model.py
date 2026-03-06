import typing
import os
import enum
import dataclasses

from qtpy import QtGui, QtCore

import notgun.bootstrap
import notgun.projects


class ProjectStatus(enum.Enum):
    OK = enum.auto()
    LOCKED = enum.auto()
    ERROR = enum.auto()


@dataclasses.dataclass
class ProjectItem:
    name: str
    status: ProjectStatus
    project: notgun.projects.Project | None = None
    error: str | None = None
    pixmap: QtGui.QPixmap | None = None


class ProjectsModel(QtCore.QAbstractListModel):
    def __init__(self, projects_dir: str, parent=None):
        super().__init__(parent)
        self.projects_dir = projects_dir
        self.wrappers: list[ProjectItem] = []

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self.wrappers)

    def projectFromIndex(self, index: QtCore.QModelIndex) -> ProjectItem | None:
        if not index.isValid():
            return None
        return self.wrappers[index.row()]

    def data(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid():
            return None

        project = self.wrappers[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return project.name
        elif (
            role == QtCore.Qt.ItemDataRole.DecorationRole and project.pixmap is not None
        ):
            return project.pixmap
        elif role == QtCore.Qt.UserRole:
            return project

        return None

    def populate(self):
        self.beginResetModel()
        self.wrappers = list(scan_directory(self.projects_dir, icon_size=64))
        self.endResetModel()


def scan_directory(projects_dir: str, icon_size: int) -> typing.Iterator[ProjectItem]:
    for name in sorted(os.listdir(projects_dir)):
        if os.path.isfile(os.path.join(projects_dir, name)):
            continue

        status = ProjectStatus.OK
        pipeline = None
        label = name
        error = None
        pixmap = None
        path = os.path.join(projects_dir, name)

        if os.access(path, os.X_OK):
            if not os.path.isdir(path):
                continue

            if not notgun.bootstrap.has_bootstrap(projects_dir, name):
                continue

            data = notgun.bootstrap.BootstrapData(projects_dir, name)
            try:
                pipeline = notgun.bootstrap.init(data)
                label = pipeline.label()
                image_path = pipeline.image_path()
                if os.path.isfile(image_path):
                    pixmap = QtGui.QPixmap(image_path)
                status = ProjectStatus.OK

            except Exception as e:
                status = ProjectStatus.ERROR
                error = str(e)
        else:
            status = ProjectStatus.LOCKED

        if status == ProjectStatus.LOCKED:
            continue

        yield ProjectItem(label, status, pipeline, error, pixmap)
