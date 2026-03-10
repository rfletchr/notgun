from qtpy import QtCore, QtWidgets

import notgun.ui.workareas.model

ContextMenuPolicy = QtCore.Qt.ContextMenuPolicy


class WorkareasView(QtWidgets.QWidget):
    itemClicked = QtCore.Signal(QtCore.QModelIndex)
    itemActivated = QtCore.Signal(QtCore.QModelIndex)
    contextMenuRequested = QtCore.Signal(QtCore.QPoint, QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive
        )
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setSortRole(notgun.ui.workareas.model.ModelRole.Path)
        self.proxy_model.setFilterRole(notgun.ui.workareas.model.ModelRole.Path)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.onSearchTextChanged)

        self.item_view = QtWidgets.QTreeView()
        self.item_view.setHeaderHidden(True)
        self.item_view.clicked.connect(self.itemClicked)
        self.item_view.activated.connect(self.itemActivated)
        self.item_view.setContextMenuPolicy(ContextMenuPolicy.CustomContextMenu)
        self.item_view.setAlternatingRowColors(True)
        self.item_view.setModel(self.proxy_model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.item_view)

        # connect signals
        self.item_view.clicked.connect(self.itemClicked)
        self.item_view.activated.connect(self.itemActivated)
        self.item_view.customContextMenuRequested.connect(self.onContextMenuRequested)

    def onSearchTextChanged(self, text: str):
        self.proxy_model.setFilterWildcard(text)

        if text:
            self.item_view.expandAll()

    def onContextMenuRequested(self, pos: QtCore.QPoint):
        index = self.item_view.indexAt(pos)
        if not index.isValid():
            return

        global_pos = self.item_view.viewport().mapToGlobal(pos)
        self.contextMenuRequested.emit(global_pos, index)

    def setModel(self, model: notgun.ui.workareas.model.WorkAreaModel):
        self.proxy_model.setSourceModel(model)
