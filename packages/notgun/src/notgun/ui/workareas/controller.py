import time
import queue

from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas
import notgun.ui.workareas.view
import notgun.ui.workareas.model
import notgun.ui.deferred_item_model


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
        self.model = notgun.ui.deferred_item_model.DeferredItemModel()

        self.proxy_model = notgun.ui.workareas.model.WorkareaFilterModel()
        self.proxy_model.setSourceModel(self.model)

        self.debounce_timer = QtCore.QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.onDebounceTimeout)
        self.search_query = ""

        self.view = view or notgun.ui.workareas.view.WorkareasView()
        self.view.setModel(self.proxy_model)

        self.scanner_queue = queue.Queue[notgun.workareas.WorkArea]()
        self.scanner_thread = WorkareaScannerThread(self.scanner_queue)
        self.scanner_thread.workareaScanned.connect(self.onWorkareaScanned)
        self.scanner_thread.start()

        self.view.itemClicked.connect(self.onItemClicked)
        self.view.itemActivated.connect(self.onItemActivated)
        self.view.searchTextChanged.connect(self.onSearchTextChanged)
        self.view.contextMenuRequested.connect(self.onContextMenuRequested)

    def onWorkareaScanned(self, path: str):
        item = self.model.itemById(path)
        if not item:
            return

        item.fetch()

    def onSearchTextChanged(self, text: str):
        self.search_query = text
        self.debounce_timer.start(300)  # debounce for 300ms

    def onDebounceTimeout(self):
        self.proxy_model.setFilterWildcard(self.search_query)
        if self.search_query:
            self.view.item_view.expandAll()

    def populate(self, root_workarea: notgun.workareas.WorkArea):
        self.model.clear()
        item = notgun.ui.workareas.model.WorkareaModelItem(root_workarea)
        self.model.appendRow(item)
        # self.scanner_queue.put_nowait(root_workarea)

    def shutdown(self):
        self.scanner_thread.requestInterruption()
        self.scanner_thread.wait(2)

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


class WorkareaScannerThread(QtCore.QThread):
    """
    Consumes workareas from the given Queue and walks their children.
    Each walked workareas path is emitted so that a model can be notified to update.
    """

    workareaScanned = QtCore.Signal(str)  # type: ignore

    def __init__(self, work_queue: queue.Queue[notgun.workareas.WorkArea], parent=None):
        super().__init__(parent=parent)
        self.work_queue = work_queue

    def run(self):
        while not self.isInterruptionRequested():
            try:
                workarea = self.work_queue.get_nowait()
            except queue.Empty:
                continue

            for workarea in populate_workarea(workarea):
                self.workareaScanned.emit(workarea.path)

            time.sleep(1)


def populate_workarea(root: notgun.workareas.WorkArea):
    """
    This helper function recursively walks down a workarea tree and loads its children.
    yielding the workareas as they're loaded.


    """
    children = root.workareas()
    root.workfile_groups()

    yield root

    for child in children:
        yield from populate_workarea(child)


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
