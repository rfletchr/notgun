from qtpy import QtGui, QtCore, QtWidgets

import notgun.ui.projects.view
import notgun.ui.projects.model


class ProjectsController(QtCore.QObject):
    projectActivated = QtCore.Signal(notgun.ui.projects.model.ProjectItem)
    projectClicked = QtCore.Signal(notgun.ui.projects.model.ProjectItem)

    def __init__(
        self,
        projects_dir: str,
        view: notgun.ui.projects.view.ProjectsView | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.projects_dir = projects_dir
        self.view = view or notgun.ui.projects.view.ProjectsView()
        self.model = notgun.ui.projects.model.ProjectsModel(projects_dir)
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

    def populate(self):
        self.model.populate()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    controller = ProjectsController("/home/rob/Development/notgun/example")
    controller.populate()
    controller.view.show()
    sys.exit(app.exec())
