from qtpy import QtCore, QtGui, QtWidgets


class ProcessManagerView(QtWidgets.QWidget):
    itemClicked = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.text_view = QtWidgets.QTextEdit()
        self.text_view.setReadOnly(True)

        self.item_view = QtWidgets.QTableView()

        header = self.item_view.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        self.item_view.verticalHeader().setVisible(False)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.item_view)
        self.splitter.addWidget(self.text_view)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        self.item_view.clicked.connect(self.itemClicked.emit)

    def isBarAtBottom(self):
        scrollbar = self.text_view.verticalScrollBar()
        value = scrollbar.value()
        maximum = scrollbar.maximum()
        return value >= maximum - 5

    def scrollToBottom(self):
        self.text_view.verticalScrollBar().setValue(
            self.text_view.verticalScrollBar().maximum()
        )

    def setDocument(self, document: QtGui.QTextDocument):
        self.text_view.setDocument(document)

    def setModel(self, model: QtCore.QAbstractItemModel):
        self.item_view.setModel(model)
