from qtpy import QtCore, QtWidgets

import notgun.ui.workareas.model


class ActiveView(QtWidgets.QWidget):
    clicked = QtCore.Signal(QtCore.QModelIndex)
    activated = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(ActiveView, self).__init__(parent)
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")

        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterRole(notgun.ui.workareas.model.PATH_ROLE)
        self.proxy_model.setDynamicSortFilter(True)

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel(self.proxy_model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tree_view)

        self.search_bar.textChanged.connect(self.onTextChanged)
        self.tree_view.clicked.connect(self.onItemClicked)
        self.tree_view.activated.connect(self.onItemActivated)

    def onTextChanged(self, text):
        if self.proxy_model.sourceModel() is not None:
            self.proxy_model.setFilterWildcard(text)
            self.tree_view.expandAll()

        if text == "":
            self.tree_view.collapseAll()

    def onItemClicked(self, index):
        if not self.proxy_model.sourceModel():
            return
        if not index.isValid():
            return
        source_index = self.proxy_model.mapToSource(index)
        self.clicked.emit(source_index)

    def onItemActivated(self, index):
        if not self.proxy_model.sourceModel():
            return
        if not index.isValid():
            return
        source_index = self.proxy_model.mapToSource(index)
        self.activated.emit(source_index)

    def setModel(self, model):
        self.proxy_model.setSourceModel(model)


class WorkAreaView(QtWidgets.QWidget):
    clicked = QtCore.Signal(QtCore.QModelIndex)
    activated = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(WorkAreaView, self).__init__(parent)
        self._active_view = ActiveView()
        self._status_label = QtWidgets.QLabel("")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._active_view)
        layout.addWidget(self._status_label)

        self._active_view.clicked.connect(self.clicked.emit)
        self._active_view.activated.connect(self.activated.emit)

    def setModel(self, model):
        self._active_view.setModel(model)

    def setStatus(self, text):
        self._status_label.setText(text)
