from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas
import notgun.ui.workareas.view
import notgun.ui.workareas.model


class WorkAreaController(QtCore.QObject):
    def __init__(
        self,
        view: notgun.ui.workareas.view.WorkareasView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.model = notgun.ui.workareas.model.WorkAreaModel()

        self.view = view or notgun.ui.workareas.view.WorkareasView()
        self.view.setModel(self.model)

        self.view.itemClicked.connect(self.onWorkareaItemClicked)

    def populate(self, root_workarea: notgun.workareas.WorkArea):
        self.model.clear()
        self.model.scan(root_workarea)

    def shutdown(self):
        self.model.shutdown()

    def onWorkareaItemClicked(self, index: QtCore.QModelIndex):
        item = self.model.itemFromIndex(index)
        if item is None:
            return

        data = item.data(notgun.ui.workareas.model.ModelRole.Data)

        if not isinstance(data, notgun.workareas.WorkArea):
            return


if __name__ == "__main__":
    import notgun.bootstrap

    data = notgun.bootstrap.BootstrapData(
        "/home/rob/Development/notgun/example",
        "project_1",
    )

    project = notgun.bootstrap.init(data)

    app = QtWidgets.QApplication([])
    controller = WorkAreaController()
    controller.populate(project.workarea())
    controller.view.show()

    app.aboutToQuit.connect(controller.shutdown)
    app.exec()
