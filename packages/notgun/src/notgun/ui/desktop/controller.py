import os
import platform
import subprocess
import logging

from qtpy import QtCore, QtGui, QtWidgets

import notgun.bootstrap
import notgun.projects
import notgun.workareas
import notgun.ui.desktop.view
import notgun.ui.workfiles
import notgun.ui.workareas.controller
import notgun.ui.projects.controller
import notgun.ui.logger.controller
import notgun.ui.process_manager.controller

logger = logging.getLogger(__name__)


def get_log_directory():
    return os.path.join(os.path.expanduser("~"), ".notgun", "logs")


class DesktopController(QtCore.QObject):
    def __init__(
        self,
        projects_dir: str,
        view: notgun.ui.desktop.view.DesktopView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self._projects_dir = projects_dir
        self._active_project: notgun.projects.Project | None = None

        self.view = view or notgun.ui.desktop.view.DesktopView()

        self.project_controller = notgun.ui.projects.controller.ProjectsController(
            view=self.view.getProjectView()
        )
        self.workarea_controller = notgun.ui.workareas.controller.WorkareasController(
            view=self.view.getWorkareaView()
        )

        self.logger_controller = notgun.ui.logger.controller.LogController(
            view=self.view.getLoggerView()
        )
        self.logger_controller.attachToLogger(logging.getLogger())

        self.process_info_controller = (
            notgun.ui.process_manager.controller.ProcessManagerController(
                log_directory=get_log_directory(),
                view=self.view.getProcessManagerView(),
            )
        )
        self.project_controller.projectClicked.connect(self.onProjectClicked)
        self.workarea_controller.contextMenuRequested.connect(
            self.onWorkareaContextMenuRequested
        )

    def shutdown(self):
        self.workarea_controller.shutdown()
        self.logger_controller.shutdown()

    def populate(self, projects_dir: str | None = None):
        self.project_controller.populate(projects_dir or self._projects_dir)

    def onProjectClicked(self, project: notgun.projects.Project):
        self._active_project = project
        self.workarea_controller.populate(project.workarea())

    def onWorkareaContextMenuRequested(self, pos: QtCore.QPoint, obj: object):
        if isinstance(obj, notgun.workareas.WorkArea):
            menu = QtWidgets.QMenu()
            open_in_explorer_action = menu.addAction("Open in File Explorer")

            if obj.schema.workfiles:
                new_workfile_action = menu.addAction("New Workfile")
            else:
                new_workfile_action = None

            if action := menu.exec(pos):  # type: ignore
                if action == open_in_explorer_action:
                    open_path_in_file_explorer(obj.path)
                elif action == new_workfile_action:
                    self.onNewWorkfileRequested(obj, pos=pos)

        elif isinstance(obj, notgun.workareas.WorkfileGroup):
            menu = QtWidgets.QMenu()
            open_in_explorer_action = menu.addAction("Open in File Explorer")

            if action := menu.exec(pos):  # type: ignore
                if action == open_in_explorer_action:
                    open_path_in_file_explorer(obj.workfiles[0].path)

    def onNewWorkfileRequested(
        self, workarea: notgun.workareas.WorkArea, pos: QtCore.QPoint | None = None
    ):
        if not workarea.schema.workfiles:
            return
        if not self._active_project:
            return

        result = notgun.ui.workfiles.NewWorkfileDialog.pickFromWorkarea(workarea)
        if result is None:
            return

        instruction = notgun.bootstrap.NewFileInstruction(result.path)
        bootstrap = notgun.bootstrap.BootstrapData(
            self._projects_dir,
            self._active_project.name(),
            instruction=instruction,
        )

        self.process_info_controller.launchProgram(
            result.workfile_type.program,
            bootstrap=bootstrap,
        )

    def openWorkfileRequested(self, workfile: notgun.workareas.Workfile):
        if not self._active_project:
            return

        instruction = notgun.bootstrap.OpenFileInstruction(workfile.path)
        bootstrap = notgun.bootstrap.BootstrapData(
            self._projects_dir,
            self._active_project.name(),
            instruction=instruction,
        )

        self.process_info_controller.launchProgram(
            workfile.schema.program,
            bootstrap=bootstrap,
        )


def open_path_in_file_explorer(path: str):
    if platform.system() == "Windows":
        subprocess.run(["explorer", path])
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", path])
    else:  # Linux and other Unix-like systems
        subprocess.run(["xdg-open", path])


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Notgun Launcher")
    controller = DesktopController("/home/rob/Development/notgun/example")
    controller.populate()
    controller.view.show()
    app.aboutToQuit.connect(controller.shutdown)

    logger.info("Notgun Launcher started.")

    sys.exit(app.exec())
