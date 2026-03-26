import os
import logging
import typing

from qtpy import QtCore, QtGui, QtWidgets


import notgun.bootstrap
import notgun.launcher
import notgun.ui.process_manager.view
import notgun.ui.process_manager.model

logger = logging.getLogger(__name__)


class ProcessManagerController(QtCore.QObject):
    def __init__(
        self,
        log_directory: str,
        view: typing.Union[notgun.ui.process_manager.view.ProcessManagerView, None] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self._log_directory = log_directory

        self.model = notgun.ui.process_manager.model.ProcessInfoListModel()
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(
            notgun.ui.process_manager.model.ModelRoles.Timestamp
        )
        self.proxy_model.sort(0, QtCore.Qt.SortOrder.DescendingOrder)

        self.log_document = QtGui.QTextDocument()
        self.__process_info: typing.Union[notgun.launcher.ProcessInfo, None] = None

        self.view = view or notgun.ui.process_manager.view.ProcessManagerView()
        self.view.setModel(self.model)
        self.view.setDocument(self.log_document)

        self._refresh_timer = QtCore.QTimer()
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self.onRefreshTimer)
        self._refresh_timer.start()

        self.view.itemClicked.connect(self.onItemClicked)

    def onItemClicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        if index.column() != 1:
            index = index.sibling(index.row(), 1)

        self.__process_info = index.data(
            notgun.ui.process_manager.model.ModelRoles.ProcessInfo
        )
        self.onRefreshTimer()

    def onRefreshTimer(self):
        self.model.scan(self._log_directory)
        at_bottom = self.view.isBarAtBottom()

        if not self.__process_info:
            self.log_document.setPlainText("")
            return
        if not os.path.isfile(self.__process_info.log_file):
            self.log_document.setPlainText("Log file not found")
            return

        with open(self.__process_info.log_file, "r") as f:
            log_content = f.read()
            self.log_document.setPlainText(log_content)

        if at_bottom:
            self.view.scrollToBottom()

    def launchProgram(
        self,
        program: notgun.launcher.Program,
        env: typing.Union[dict[str, str], None] = None,
        cwd: typing.Union[str, None] = None,
        label: typing.Union[str, None] = None,
        bootstrap: typing.Union[notgun.bootstrap.BootstrapData, None] = None,
    ):
        env = env or os.environ.copy()

        if bootstrap:
            env[notgun.bootstrap.BOOTSTRAP_ENV_VAR] = bootstrap.to_json_str()

        notgun.launcher.launch_program(
            program,
            self._log_directory,
            cwd,
            label,
            env=env,
        )


if __name__ == "__main__":
    import sys
    import tempfile

    with tempfile.TemporaryDirectory() as log_directory:
        app = QtWidgets.QApplication(sys.argv)
        controller = ProcessManagerController(log_directory)
        controller.view.show()

        program = notgun.launcher.Program(
            "Ping Google", "ping", ["google.com", "-c", "25"], []
        )
        controller.launchProgram(program)
        controller.launchProgram(program)

        sys.exit(app.exec())
