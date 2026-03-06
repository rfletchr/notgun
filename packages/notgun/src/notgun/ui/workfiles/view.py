from qtpy import QtGui, QtCore, QtWidgets


class WorkfilesView(QtWidgets.QWidget):
    activated = QtCore.Signal(QtCore.QModelIndex)
    clicked = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proxy_model = QtCore.QSortFilterProxyModel()

        self.view = QtWidgets.QListView()
        self.view.setAlternatingRowColors(True)
        self.view.setModel(self.proxy_model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)

        self.view.activated.connect(self.onActivated)
        self.view.clicked.connect(self.onClicked)

    def setModel(self, model: QtCore.QAbstractItemModel):
        self.proxy_model.setSourceModel(model)

    def onActivated(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        self.activated.emit(self.proxy_model.mapToSource(index))

    def onClicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        self.clicked.emit(self.proxy_model.mapToSource(index))
