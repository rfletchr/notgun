from PySide6.QtCore import Qt
import typing
import qtawesome as qta
from qtpy import QtCore, QtGui

import notgun.workareas

IndexType = QtCore.QModelIndex | QtCore.QPersistentModelIndex


class LocationItem(QtGui.QStandardItem):
    def __init__(self, location: notgun.workareas.WorkArea):
        super().__init__()
        self.setText(typing.cast(str, location.fields[location.type.token]))
        self.setData(location, QtCore.Qt.ItemDataRole.UserRole)
        self.setEditable(False)

        self.setIcon(qta.icon("fa6s.folder", color="darkgrey"))
        self._populated = False

    def hasChildren(self) -> bool:
        item = self.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(item, notgun.workareas.WorkArea):
            return False

        if not self._populated:
            return True

        return bool(self.rowCount())

    def fetchMore(self) -> None:
        item = self.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(item, notgun.workareas.WorkArea):
            return

        if self._populated:
            return

        for child in item.ls():
            self.appendRow(LocationItem(child))

        self._populated = True

    def canFetchMore(self) -> bool:
        item = self.data(QtCore.Qt.ItemDataRole.UserRole)
        if not isinstance(item, notgun.workareas.WorkArea):
            return False

        return not self._populated


class LocationModel(QtGui.QStandardItemModel):
    def hasChildren(self, /, parent: IndexType = QtCore.QModelIndex()) -> bool:
        if not parent.isValid():
            return True

        item = self.itemFromIndex(parent)
        if not isinstance(item, LocationItem):
            return super().hasChildren(parent)

        return item.hasChildren()

    def fetchMore(self, /, parent: IndexType = QtCore.QModelIndex()) -> None:
        if not parent.isValid():
            return
        item = self.itemFromIndex(parent)
        if not isinstance(item, LocationItem):
            return super().fetchMore(parent)

        item.fetchMore()

    def canFetchMore(self, /, parent: IndexType = QtCore.QModelIndex()) -> bool:
        if not parent.isValid():
            return False
        item = self.itemFromIndex(parent)
        if not isinstance(item, LocationItem):
            return super().canFetchMore(parent)

        return item.canFetchMore()
