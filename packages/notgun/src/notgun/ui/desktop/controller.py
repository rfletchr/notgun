import os
import platform
import subprocess
import logging
import typing

from qtpy import QtCore, QtGui, QtWidgets

import notgun.projects
import notgun.workareas
import notgun.bootstrap
import notgun.ui.desktop.view
import notgun.ui.file_manager.controller
import notgun.ui.logger.controller
import notgun.ui.process_manager.controller
import notgun.ui.workfiles


logger = logging.getLogger(__name__)


def get_log_directory():
    return os.path.join(os.path.expanduser("~"), ".notgun", "logs")


class DesktopController(QtCore.QObject):
    def __init__(
        self,
        projects_dir: str,
        view: typing.Union[notgun.ui.desktop.view.DesktopView, None] = None,
        parent: typing.Union[QtWidgets.QWidget, None] = None,
    ):
        super().__init__(parent=parent)
        self._projects_dir: str = projects_dir
        self._active_project: typing.Union[notgun.projects.Project, None] = None

        self.view: notgun.ui.desktop.view.DesktopView = (
            view or notgun.ui.desktop.view.DesktopView()
        )

        self.file_manager_controller = (
            notgun.ui.file_manager.controller.FileManagerController(
                view=self.view.getFileManagerView()
            )
        )

        self.file_manager_controller.action_handler.requestNewWorkfile.connect(
            self.onRequestNewWorkfile
        )
        self.file_manager_controller.action_handler.requestOpenWorkfile.connect(
            self.onRequestOpenWorkfile
        )

        self.logger_controller = notgun.ui.logger.controller.LogController(
            view=self.view.getLoggerView()
        )

        self.logger_controller.attachToLogger(logging.getLogger())

        self.process_manager_controller = (
            notgun.ui.process_manager.controller.ProcessManagerController(
                log_directory=get_log_directory(),
                view=self.view.getProcessManagerView(),
            )
        )

    def shutdown(self):
        self.logger_controller.shutdown()

    def populate(self, projects_dir: typing.Union[str, None] = None):
        self.file_manager_controller.setProjectsDir(projects_dir or self._projects_dir)

    def onRequestNewWorkfile(self, result: notgun.ui.workfiles.NewWorkfileResult):
        program = result.workfile_type.program

        instruction = notgun.bootstrap.NewFileInstruction(result.path)
        bootstrap = notgun.bootstrap.BootstrapData(
            result.workarea.project.projects_root(),
            result.workarea.project.filesystem_name(),
            instruction,
        )

        self.process_manager_controller.launchProgram(program, bootstrap=bootstrap)

    def onRequestOpenWorkfile(self, workfile: notgun.workareas.Workfile):
        program = workfile.schema.program

        instruction = notgun.bootstrap.OpenFileInstruction(workfile.path)
        bootstrap = notgun.bootstrap.BootstrapData(
            workfile.group.workarea.project.projects_root(),
            workfile.group.workarea.project.filesystem_name(),
            instruction,
        )

        self.process_manager_controller.launchProgram(program, bootstrap=bootstrap)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Notgun Launcher")
    controller = DesktopController("/scratch/robert.fletcher/git/notgun/example")
    controller.populate()
    controller.view.show()
    app.aboutToQuit.connect(controller.shutdown)

    logger.info("Notgun Launcher started.")

    sys.exit(app.exec())
