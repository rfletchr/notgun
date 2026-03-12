import qtawesome as qta
from qtpy import QtGui, QtCore, QtWidgets

import notgun.ui.projects.model


DEFAULT_SIZE = 128


class ProjectsView(QtWidgets.QWidget):
    activated = QtCore.Signal(QtCore.QModelIndex)
    clicked = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.view = QtWidgets.QListView()
        self.view.setUniformItemSizes(True)

        self.view.activated.connect(self.activated)
        self.view.clicked.connect(self.onViewClicked)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)

    def onViewClicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        self.clicked.emit(index)

    def setModel(self, model: QtCore.QAbstractItemModel):
        self.view.setModel(model)
