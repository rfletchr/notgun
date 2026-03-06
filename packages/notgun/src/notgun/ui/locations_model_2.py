from __future__ import annotations
import typing
from qtpy import QtCore, QtGui


import notgun.workareas


class LocationItem(QtGui.QStandardItem):
    def __init__(self, location: notgun.workareas.WorkArea, icon: QtGui.QIcon):
        super().__init__(location.name)
        self.setData(location, QtCore.Qt.ItemDataRole.UserRole)
        self.setEditable(False)
        self.setIcon(icon)
