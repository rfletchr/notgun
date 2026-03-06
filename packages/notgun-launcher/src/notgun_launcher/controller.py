import os

from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas
import notgun_launcher.view
import notgun.ui.workareas.controller
import notgun.ui.projects.controller
import notgun.ui.projects.model
import notgun.ui.workfiles.controller


class MainController:
    def __init__(
        self, projects_dir: str, view: notgun_launcher.view.MainView | None = None
    ):
        self.view = view or notgun_launcher.view.MainView()

        self.projects_controller = notgun.ui.projects.controller.ProjectsController(
            projects_dir,
            self.view.projects_view,
        )

        self.workareas_controller = notgun.ui.workareas.controller.WorkAreaController(
            self.view.work_areas_container.workareas_view,
        )

        self.workfiles_controller = (
            notgun.ui.workfiles.controller.WorkfilesViewController(
                self.view.work_areas_container.workfiles_view
            )
        )

        self.projects_controller.projectActivated.connect(self.onProjectClicked)
        self.projects_controller.projectClicked.connect(self.onProjectClicked)

        self.workareas_controller.workAreaClicked.connect(self.onWorkAreaClicked)
        self.view.backButtonClicked.connect(self.onBackButtonClicked)

    def populate(self):
        self.projects_controller.populate()

    def onProjectClicked(self, project_wrapper: notgun.ui.projects.model.ProjectItem):

        if not project_wrapper.project:
            QtWidgets.QMessageBox.critical(
                self.view,
                "Error",
                f"Project '{project_wrapper.name}' is in an error state and cannot be opened.\n\nError details:\n{project_wrapper.error}",
            )
            return

        self.workfiles_controller.clear()
        self.workareas_controller.populate(project_wrapper.project.root_workarea())
        self.view.showWorkAreasView()

        self.view.work_areas_container.setTitle(project_wrapper.name)
        if project_wrapper.pixmap:
            # TODO: make this its own method.
            self.view.work_areas_container.setPixmap(
                project_wrapper.pixmap.scaledToHeight(
                    64, QtCore.Qt.TransformationMode.SmoothTransformation
                )
            )

    def onWorkAreaClicked(self, work_area: notgun.workareas.WorkArea):
        self.workfiles_controller.clear()

        if not work_area.type.workfiles_template:
            return

        print(
            "MainController: onWorkAreaClicked - populating workfiles view with template",
            work_area.type.workfiles_template,
            "and fields",
            work_area.fields,
        )

        self.workfiles_controller.populate(
            work_area.type.workfiles_template,
            work_area.fields,
        )

    def onBackButtonClicked(self):
        self.view.showProjectsView()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    controller = MainController("/home/rob/Development/notgun/example")
    controller.populate()

    controller.view.show()
    app.exec()
