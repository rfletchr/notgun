from qtpy import QtCore, QtGui
import qtawesome as qta

import notgun.workareas
import concurrent.futures

PATH_ROLE = QtCore.Qt.ItemDataRole.DisplayRole + 1


class WorkAreaModel(QtGui.QStandardItemModel):
    busy = QtCore.Signal(bool)
    locationCountChanged = QtCore.Signal(int)

    class PrivateSignals(QtCore.QObject):
        location_ready = QtCore.Signal(notgun.workareas.WorkArea)

    def __init__(self, parent=None):
        super(WorkAreaModel, self).__init__(parent)
        self._private_signals = self.PrivateSignals()
        self._private_signals.location_ready.connect(self.onWorkAreaReady)

        self._scanning = False
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._total_locations = 0
        self._path_to_item = {}
        self._icon_cache = {}

    def getIconForWorkArea(self, work_area: notgun.workareas.WorkArea) -> QtGui.QIcon:
        icon_name = work_area.type.icon_name
        if icon_name in self._icon_cache:
            return self._icon_cache[icon_name]

        icon = qta.icon(icon_name, color="darkgray")
        self._icon_cache[icon_name] = icon
        return icon

    def data(
        self,
        index: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
        role: int = QtCore.Qt.ItemDataRole.DisplayRole,
    ):
        if not index.isValid():
            return None

        item = self.itemFromIndex(index)
        if item is None:
            return None

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            workarea = item.data(QtCore.Qt.UserRole)
            if workarea:
                return self.getIconForWorkArea(workarea)

        return super(WorkAreaModel, self).data(index, role)

    def onWorkAreaReady(self, location: notgun.workareas.WorkArea):
        item = WorkAreaItem(location)
        self._path_to_item[location.path] = item

        if location.parent and location.parent.path in self._path_to_item:
            parent_item = self._path_to_item[location.parent.path]
            parent_item.appendRow(item)
        else:
            self.invisibleRootItem().appendRow(item)

    def clear(self):
        super(WorkAreaModel, self).clear()
        self._path_to_item.clear()
        self._total_locations = 0
        self.locationCountChanged.emit(0)

    def workAreaFromIndex(
        self, index: QtCore.QModelIndex
    ) -> notgun.workareas.WorkArea | None:
        if not index.isValid():
            return None
        item = self.itemFromIndex(index)
        if item is None:
            return None
        location = item.data(QtCore.Qt.UserRole)
        return location

    def scan(self, location: notgun.workareas.WorkArea):
        if self._scanning:
            return

        self.clear()

        self._scanning = True
        self.busy.emit(True)
        self._executor.submit(self.__scan, location)

    def __scan(self, location: notgun.workareas.WorkArea):

        def _scan(parent):
            for child in parent.ls():
                self._private_signals.location_ready.emit(child)
                self._total_locations += 1
                self.locationCountChanged.emit(self._total_locations)
                _scan(child)

        _scan(location)
        self.busy.emit(False)
        self._scanning = False


class WorkAreaItem(QtGui.QStandardItem):
    def __init__(self, location: notgun.workareas.WorkArea):
        super(WorkAreaItem, self).__init__(location.name)
        self.setEditable(False)
        self.setData(location, QtCore.Qt.UserRole)
        self.setData(location.path, PATH_ROLE)


def scan(root_location: notgun.workareas.WorkArea, root_item: QtGui.QStandardItem):
    for location in root_location.ls():
        item = WorkAreaItem(location)
        root_item.appendRow(item)
        scan(location, item)
