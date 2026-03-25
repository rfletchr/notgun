import os
import queue
import enum
import logging
import threading

import notgun.ui.deferred_item_model

from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas

logger = logging.getLogger(__name__)


class ModelRole(enum.IntEnum):
    Type = QtCore.Qt.ItemDataRole.UserRole
    Path = QtCore.Qt.ItemDataRole.UserRole + 1
    Data = QtCore.Qt.ItemDataRole.UserRole + 2


class ItemType(enum.IntEnum):
    Workarea = 0
    WorkfileGroup = 1


class WorkareaFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self.setFilterRole(ModelRole.Path)
        self.setRecursiveFilteringEnabled(True)
        self.setDynamicSortFilter(True)


class WorkareaModelItem(notgun.ui.deferred_item_model.DeferredItem):
    def __init__(self, workarea: notgun.workareas.WorkArea):
        super().__init__(workarea.name)
        self.setData(workarea, ModelRole.Data)
        self.setData(workarea.path, ModelRole.Path)
        self.setData(ItemType.Workarea, ModelRole.Type)
        self.setEditable(False)

        self._fetched = False

    def canFetchMore(self) -> bool:
        return not self._fetched

    def fetch(self) -> None:
        self._fetched = True
        workarea: notgun.workareas.WorkArea = self.data(ModelRole.Data)
        for workarea in workarea.workareas():
            self.appendRow(WorkareaModelItem(workarea))

    def hasUniqueId(self):
        return True

    def uniqueId(self):
        return self.data(ModelRole.Path)
