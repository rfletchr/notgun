from qtpy import QtCore, QtGui, QtWidgets
import logging
import notgun.projects
import notgun.ui.launcher.view
import notgun.ui.workareas.controller
import notgun.ui.projects.controller
import notgun.ui.logger.controller


class LauncherController(QtCore.QObject):
    def __init__(
        self,
        view: QtWidgets.QWidget | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.view = view or notgun.ui.launcher.view.LauncherView()
        self.logger = logging.getLogger("notgun")

        self.project_controller = notgun.ui.projects.controller.ProjectsController(
            view=self.view.getProjectView()
        )
        self.workarea_controller = notgun.ui.workareas.controller.WorkAreaController(
            view=self.view.getWorkareaView()
        )

        self.logger_controller = notgun.ui.logger.controller.LogController(
            view=self.view.getLoggerView()
        )
        self.logger_controller.attachToLogger(self.logger)

        self.project_controller.projectClicked.connect(self.onProjectClicked)

    def shutdown(self):
        self.workarea_controller.shutdown()
        self.logger_controller.shutdown()

    def populate(self, projects_dir: str):
        self.project_controller.populate(projects_dir)

    def onProjectClicked(self, project: notgun.projects.Project):
        self.workarea_controller.populate(project.workarea())


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Notgun Launcher")
    controller = LauncherController()
    controller.populate("/home/rob/Development/notgun/example")
    controller.view.show()
    app.aboutToQuit.connect(controller.shutdown)

    controller.logger.info("Notgun Launcher started.")

    sys.exit(app.exec())
