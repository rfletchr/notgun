from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas
import notgun.ui.workareas.view
import notgun.ui.workareas.model


class WorkareasController(QtCore.QObject):
    itemClicked = QtCore.Signal(object)
    itemActivated = QtCore.Signal(object)
    contextMenuRequested = QtCore.Signal(QtCore.QPoint, object)

    def __init__(
        self,
        view: notgun.ui.workareas.view.WorkareasView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.model = notgun.ui.workareas.model.WorkAreaModel()

        self.proxy_model = notgun.ui.workareas.model.WorkareaFilterModel()
        self.proxy_model.setSourceModel(self.model)

        self.debounce_timer = QtCore.QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.onDebounceTimeout)
        self.search_query = ""

        self.view = view or notgun.ui.workareas.view.WorkareasView()
        self.view.setModel(self.proxy_model)

        self.view.itemClicked.connect(self.onItemClicked)
        self.view.itemActivated.connect(self.onItemActivated)
        self.view.searchTextChanged.connect(self.onSearchTextChanged)
        self.view.contextMenuRequested.connect(self.onContextMenuRequested)

    def onSearchTextChanged(self, text: str):
        self.search_query = text
        self.debounce_timer.start(300)  # debounce for 300ms

    def onDebounceTimeout(self):
        self.proxy_model.setFilterWildcard(self.search_query)
        if self.search_query:
            self.view.item_view.expandAll()

    def populate(self, root_workarea: notgun.workareas.WorkArea):
        self.model.clear()
        self.model.scan(root_workarea)

    def shutdown(self):
        self.model.shutdown()

    def onItemClicked(self, proxy_index: QtCore.QModelIndex):
        index = self.proxy_model.mapToSource(proxy_index)
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        data = item.data(notgun.ui.workareas.model.ModelRole.Data)
        if data is not None:
            self.itemClicked.emit(data)

    def onItemActivated(self, proxy_index: QtCore.QModelIndex):
        index = self.proxy_model.mapToSource(proxy_index)
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        data = item.data(notgun.ui.workareas.model.ModelRole.Data)
        if data is not None:
            self.itemActivated.emit(data)

    def onContextMenuRequested(
        self,
        global_pos: QtCore.QPoint,
        proxy_index: QtCore.QModelIndex,
    ):
        index = self.proxy_model.mapToSource(proxy_index)
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        data = item.data(notgun.ui.workareas.model.ModelRole.Data)
        if data is not None:
            self.contextMenuRequested.emit(global_pos, data)


class NewFileController(QtCore.QObject):
    def __init__(
        self,
        view: notgun.ui.workareas.view.NewFileView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.view = view or notgun.ui.workareas.view.NewFileView()
        self.apps_model = QtGui.QStandardItemModel()


if __name__ == "__main__":
    import notgun.bootstrap

    data = notgun.bootstrap.BootstrapData(
        "/home/rob/Development/notgun/example",
        "project_1",
    )

    project = notgun.bootstrap.init(data)

    app = QtWidgets.QApplication([])
    controller = WorkareasController()
    controller.populate(project.workarea())
    controller.view.show()

    app.aboutToQuit.connect(controller.shutdown)
    app.exec()
