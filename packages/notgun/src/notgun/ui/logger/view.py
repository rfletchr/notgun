from qtpy import QtCore, QtGui, QtWidgets


class LogView(QtWidgets.QTableView):
    """A Qt view that displays LogRecords from a model."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(False)

        self.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch
        )

    def setModel(self, model: QtCore.QAbstractTableModel) -> None:
        super().setModel(model)
