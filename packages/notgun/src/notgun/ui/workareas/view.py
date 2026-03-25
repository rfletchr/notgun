from qtpy import QtCore, QtWidgets, QtGui

ContextMenuPolicy = QtCore.Qt.ContextMenuPolicy


class WorkareasView(QtWidgets.QWidget):
    itemClicked = QtCore.Signal(QtCore.QModelIndex)
    itemActivated = QtCore.Signal(QtCore.QModelIndex)
    contextMenuRequested = QtCore.Signal(QtCore.QPoint, QtCore.QModelIndex)
    searchTextChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.searchTextChanged)

        self.item_view = QtWidgets.QTreeView()
        self.item_view.setHeaderHidden(True)
        self.item_view.setContextMenuPolicy(ContextMenuPolicy.CustomContextMenu)
        self.item_view.setAlternatingRowColors(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.item_view)

        # connect signals
        self.item_view.clicked.connect(self.itemClicked)
        self.item_view.activated.connect(self.itemActivated)
        self.item_view.customContextMenuRequested.connect(self.onContextMenuRequested)

    def onContextMenuRequested(self, pos: QtCore.QPoint):
        index = self.item_view.indexAt(pos)

        global_pos = self.item_view.viewport().mapToGlobal(pos)
        self.contextMenuRequested.emit(global_pos, index)

    def setModel(self, model: QtCore.QAbstractItemModel):
        self.item_view.setModel(model)


class NewFileView(QtWidgets.QWidget):
    appChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New File")

        self.app_combo = QtWidgets.QComboBox()
        self.app_combo.setEditable(False)
        self.app_combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.app_combo.currentTextChanged.connect(self.appChanged.emit)

        self.names_combo = QtWidgets.QComboBox()
        self.names_combo.setEditable(True)
        self.names_combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        self.extension_combo = QtWidgets.QComboBox()
        self.extension_combo.setEditable(False)
        self.extension_combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.app_combo, stretch=1)
        layout.addWidget(self.names_combo, stretch=5)
        layout.addWidget(self.extension_combo, stretch=1)

    def setApps(self, apps: list[str]):
        self.app_combo.clear()
        self.app_combo.addItems(apps)

    def setNames(self, names: list[str]):
        self.names_combo.clear()
        self.names_combo.addItems(names)

    def name(self) -> str:
        return self.names_combo.currentText()

    def setExtensions(self, extensions: list[str]):
        self.extension_combo.clear()
        self.extension_combo.addItems(extensions)

    def extension(self) -> str:
        return self.extension_combo.currentText()

    def setValidator(self, validator: QtGui.QValidator):
        self.names_combo.setValidator(validator)

    def sizeHint(self):
        font = self.font()
        metrics = QtGui.QFontMetrics(font)
        width = metrics.maxWidth() * 25

        base = super().sizeHint()
        return QtCore.QSize(width, base.height())


class NewFileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New File")

        self.view = NewFileView()
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def name(self) -> str:
        return self.view.names_combo.currentText()

    def extension(self) -> str:
        return self.view.extension_combo.currentText()

    def setName(self, name: str):
        index = self.view.names_combo.findText(name)
        if index != -1:
            self.view.names_combo.setCurrentIndex(index)
        else:
            self.view.names_combo.setEditText(name)

    def setNames(self, names: list[str]):
        self.view.setNames(names)

    def setExtensions(self, extensions: list[str]):
        self.view.setExtensions(extensions)

    def setExtension(self, extension: str):
        index = self.view.extension_combo.findText(extension)
        if index != -1:
            self.view.extension_combo.setCurrentIndex(index)

    def setValidator(self, validator: QtGui.QValidator):
        self.view.setValidator(validator)
