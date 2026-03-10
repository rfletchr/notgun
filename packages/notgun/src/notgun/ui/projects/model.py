import typing
import os

from qtpy import QtGui, QtCore

import notgun.bootstrap
import notgun.projects


class ProjectsModel(QtGui.QStandardItemModel):
    def populate(self, projects_dir: str):
        self.clear()
        self.setHorizontalHeaderLabels(["Projects"])
        for project in iter_projects(projects_dir):
            item = QtGui.QStandardItem(project.label())
            item.setEditable(False)
            item.setData(project, QtCore.Qt.ItemDataRole.UserRole)
            self.appendRow(item)

    def projectFromIndex(
        self, index: QtCore.QModelIndex
    ) -> typing.Optional[notgun.projects.Project]:
        if not index.isValid():
            return None

        project = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(project, notgun.projects.Project):
            return project

        return None


def iter_projects(projects_dir: str) -> typing.Iterator[notgun.projects.Project]:
    for name in sorted(os.listdir(projects_dir)):
        if os.path.isfile(os.path.join(projects_dir, name)):
            continue

        path = os.path.join(projects_dir, name)

        if os.access(path, os.X_OK):
            if not os.path.isdir(path):
                continue

            if not notgun.bootstrap.has_bootstrap(projects_dir, name):
                continue

            data = notgun.bootstrap.BootstrapData(projects_dir, name)
            try:
                project = notgun.bootstrap.init(data)
                yield project
            except Exception:
                # TODO: log this error
                continue
