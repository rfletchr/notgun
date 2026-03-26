from qtpy import QtCore, QtGui, QtWidgets

import notgun.ui.logger.view
import notgun.ui.process_manager.view
import notgun.ui.file_manager.view


class ProjectBrowserView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_manager_view = notgun.ui.file_manager.view.FileManagerView()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.file_manager_view)
        self.setLayout(layout)

    def setProjectsModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.file_manager_view.setProjectsModel(model)

    def setWorkareasModel(self, model: QtCore.QAbstractItemModel) -> None:
        self.file_manager_view.setWorkareasModel(model)


class DesktopView(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project_browser = ProjectBrowserView()
        self.logger_view = notgun.ui.logger.view.LogView()
        self.process_info_view = notgun.ui.process_manager.view.ProcessManagerView()
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)
        self.tabs.addTab(self.project_browser, "Projects")
        self.tabs.addTab(self.logger_view, "Logs")
        self.tabs.addTab(self.process_info_view, "Programs")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def getFileManagerView(self) -> notgun.ui.file_manager.view.FileManagerView:
        return self.project_browser.file_manager_view

    def getLoggerView(self) -> notgun.ui.logger.view.LogView:
        return self.logger_view

    def getProcessManagerView(
        self,
    ) -> notgun.ui.process_manager.view.ProcessManagerView:
        return self.process_info_view
