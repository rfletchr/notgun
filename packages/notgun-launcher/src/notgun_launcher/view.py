import qtawesome as qta
from qtpy import QtCore, QtGui, QtWidgets

import notgun.ui.workareas.view
import notgun.ui.projects.view
import notgun.ui.workfiles.view


class WorkAreasContainer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap_label = QtWidgets.QLabel()
        self.title_label = QtWidgets.QLabel()
        self.back_button = QtWidgets.QPushButton("Back")

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.pixmap_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.back_button)

        self.workareas_view = notgun.ui.workareas.view.WorkAreaView()
        self.workfiles_view = notgun.ui.workfiles.view.WorkfilesView()

        inner_layout = QtWidgets.QHBoxLayout()
        inner_layout.addWidget(self.workareas_view, 2)
        inner_layout.addWidget(self.workfiles_view, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addLayout(inner_layout)

    def setTitle(self, title: str):
        self.title_label.setText(title)

    def setPixmap(self, pixmap: QtGui.QPixmap):
        self.pixmap_label.setPixmap(pixmap)


class MainView(QtWidgets.QWidget):
    backButtonClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.projects_view = notgun.ui.projects.view.ProjectsView()
        self.work_areas_container = WorkAreasContainer()

        self.stack_view = QtWidgets.QStackedWidget()
        self.stack_view.addWidget(self.projects_view)
        self.stack_view.addWidget(self.work_areas_container)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.stack_view)

        self.work_areas_container.back_button.clicked.connect(
            self.backButtonClicked.emit
        )

    def setProjectModel(self, model: QtCore.QAbstractItemModel):
        self.projects_view.setModel(model)

    def setWorkAreaModel(self, model: QtCore.QAbstractItemModel):
        self.work_areas_container.workareas_view.setModel(model)

    def showProjectsView(self):
        self.stack_view.setCurrentWidget(self.projects_view)

    def showWorkAreasView(self):
        self.stack_view.setCurrentWidget(self.work_areas_container)
