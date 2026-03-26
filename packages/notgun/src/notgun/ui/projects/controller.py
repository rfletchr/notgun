from __future__ import annotations
import logging
import typing
from qtpy import QtGui, QtCore, QtWidgets

import notgun.ui.projects.view
import notgun.ui.projects.model

if typing.TYPE_CHECKING:
    import notgun.projects

logger = logging.getLogger("notgun.ui.logger.controller")


class ProjectsController(QtCore.QObject):
    projectActivated = QtCore.Signal(object)
    projectClicked = QtCore.Signal(object)

    def __init__(
        self,
        view: typing.Union[notgun.ui.projects.view.ProjectsView, None] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.view = view or notgun.ui.projects.view.ProjectsView()
        self.model = notgun.ui.projects.model.ProjectsModel()
        self.view.setModel(self.model)

        self.view.activated.connect(self.onProjectActivated)
        self.view.clicked.connect(self.onProjectClicked)

    def onProjectActivated(self, index: QtCore.QModelIndex):
        project = self.model.projectFromIndex(index)
        if project is None:
            return
        self.projectActivated.emit(project)

    def onProjectClicked(self, index: QtCore.QModelIndex):
        project = self.model.projectFromIndex(index)
        if project is None:
            return
        self.projectClicked.emit(project)

    def populate(self, projects_dir: str):
        logger.debug(f"Populating projects from directory: {projects_dir}")
        self.model.populate(projects_dir)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    controller = ProjectsController()
    controller.populate("/home/rob/Development/notgun/example")
    controller.view.show()
    sys.exit(app.exec())
