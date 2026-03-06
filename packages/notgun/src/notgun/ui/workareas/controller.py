from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas
import notgun.ui.workareas.view
import notgun.ui.workareas.model


class WorkAreaController(QtCore.QObject):
    workAreaActivated = QtCore.Signal(notgun.workareas.WorkArea)
    workAreaClicked = QtCore.Signal(notgun.workareas.WorkArea)

    def __init__(
        self,
        view: notgun.ui.workareas.view.WorkAreaView | None = None,
        parent=None,
    ):
        super(WorkAreaController, self).__init__(parent)
        self._model = notgun.ui.workareas.model.WorkAreaModel()
        self._model.locationCountChanged.connect(self.onWorkAreaCountChanged)
        self._model.busy.connect(self.onBusyChanged)

        self.view = view or notgun.ui.workareas.view.WorkAreaView()
        self.view.setModel(self._model)

        self.view.clicked.connect(self.onWorkAreaClicked)
        self.view.activated.connect(self.onWorkAreaActivated)

    def populate(self, workarea: notgun.workareas.WorkArea):
        self._model.scan(workarea)

    def onWorkAreaCountChanged(self, count):
        self.view.setStatus(f"Found {count} locations...")

    def onWorkAreaActivated(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        work_area = self._model.workAreaFromIndex(index)
        if work_area is None:
            return

        self.workAreaActivated.emit(work_area)

    def onWorkAreaClicked(self, index: QtCore.QModelIndex):
        print("WorkAreaController: onWorkAreaClicked", index)
        if not index.isValid():
            return

        work_area = self._model.workAreaFromIndex(index)
        if work_area is None:
            print(
                "WorkAreaController: onWorkAreaClicked - no work area found for index",
                index,
            )
            return

        self.workAreaClicked.emit(work_area)

    def onBusyChanged(self, busy):
        if busy:
            self.view.setStatus("Scanning for locations...")
        else:
            self.view.setStatus("Scan complete.")


if __name__ == "__main__":
    from qtpy import QtWidgets
    import notgun.bootstrap

    data = notgun.bootstrap.BootstrapData(
        "/home/rob/Development/notgun/example", "project_1"
    )
    pipeline = notgun.bootstrap.init(data)

    app = QtWidgets.QApplication([])
    controller = WorkAreaController()
    controller.populate(pipeline.root_workarea())
    controller.view.show()
    app.exec()
