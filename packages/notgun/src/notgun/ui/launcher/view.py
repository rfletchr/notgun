from qtpy import QtCore, QtGui, QtWidgets

import notgun.ui.workareas.view
import notgun.ui.projects.view
import notgun.ui.logger.view


class ProjectBrowserView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.workarea_browser = notgun.ui.workareas.view.WorkareasView()
        self.project_browser = notgun.ui.projects.view.ProjectsView()

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.project_browser)
        self.splitter.addWidget(self.workarea_browser)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def setProjectsModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.project_browser.setModel(model)

    def setWorkareasModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.workarea_browser.setModel(model)


class LauncherView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_browser = ProjectBrowserView()
        self.logger_view = notgun.ui.logger.view.LogView()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.tabs.addTab(self.project_browser, "Projects")
        self.tabs.addTab(self.logger_view, "Logs")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def getWorkareaView(self) -> ProjectBrowserView:
        return self.project_browser.workarea_browser

    def getProjectView(self) -> ProjectBrowserView:
        return self.project_browser.project_browser

    def getLoggerView(self) -> notgun.ui.logger.view.LogView:
        return self.logger_view
