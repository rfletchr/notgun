import os
import queue
import enum
import logging
import threading
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


class WorkAreaModel(QtGui.QStandardItemModel):
    # this signal forwards the scan request to the background thread.
    __sendToThreadSignal = QtCore.Signal(notgun.workareas.WorkArea)
    itemCounterChanged = QtCore.Signal(int)

    def __init__(
        self, icon_provider: QtWidgets.QFileIconProvider | None = None, parent=None
    ):
        super().__init__(parent=parent)
        self.setHorizontalHeaderLabels(["Name"])
        self.icon_provider = icon_provider or QtWidgets.QFileIconProvider()

        self.__worker = BackgroundScanner()
        self.__worker.workareaFound.connect(self.onWorkareaFound)
        self.__worker.workfileGroupFound.connect(self.onWorkfileGroupFound)

        self.__sendToThreadSignal.connect(self.__worker.scan)

        self.__scanner_thread = QtCore.QThread()
        self.__scanner_thread.setObjectName("WorkAreaModelThread")
        self.__worker.moveToThread(self.__scanner_thread)

        self.__icon_loader_thread = IconLoaderThread()
        self.__icon_loader_thread.setObjectName("IconLoaderThread")
        self.__icon_loader_thread.imageLoaded.connect(self.onImageLoaded)
        self.__icon_loader_thread.start()

        self.__path_to_item = dict[str, QtGui.QStandardItem]()

    def clear(self):
        super().clear()
        self.setHorizontalHeaderLabels(["Name"])
        self.__path_to_item.clear()
        self.__worker.cancel_event.set()

    def scan(self, root_workarea: notgun.workareas.WorkArea):
        if not self.__scanner_thread.isRunning():
            self.__scanner_thread.start()

        self.__sendToThreadSignal.emit(root_workarea)

    def shutdown(self):
        self.__worker.cancel_event.set()
        self.__icon_loader_thread.cancel_event.set()

        self.__scanner_thread.quit()
        self.__scanner_thread.wait()

        self.__icon_loader_thread.quit()
        self.__icon_loader_thread.wait()

    def onImageLoaded(self, path: str, image: QtGui.QImage):
        if path not in self.__path_to_item:
            return

        item = self.__path_to_item[path]
        icon = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
        item.setIcon(icon)

    def onWorkareaFound(self, workarea: notgun.workareas.WorkArea):
        if workarea.path in self.__path_to_item:
            return

        if workarea.parent is None or workarea.parent.path not in self.__path_to_item:
            parent_item = self.invisibleRootItem()
        else:
            parent_item = self.__path_to_item[workarea.parent.path]

        item = QtGui.QStandardItem(workarea.name)
        item.setEditable(False)
        item.setData(ItemType.Workarea, ModelRole.Type)
        item.setData(workarea.path, ModelRole.Path)
        item.setData(workarea, ModelRole.Data)

        icon = self.icon_provider.icon(QtWidgets.QFileIconProvider.IconType.Folder)
        item.setIcon(icon)

        parent_item.appendRow(item)

        self.__path_to_item[workarea.path] = item
        self.__icon_loader_thread.work_queue.put(workarea.path)

    def onWorkfileGroupFound(self, group: notgun.workareas.WorkfileGroup):
        if group.parent is None:
            logger.warning(
                f"WorkfileGroup {group.name} has no parent. This should not happen."
            )
            return

        parent_item = self.__path_to_item[group.parent.path]

        parent_path = parent_item.data(ModelRole.Path)
        path = os.path.join(parent_path, group.name + "." + group.filetype)

        item = QtGui.QStandardItem(os.path.basename(path))
        item.setEditable(False)
        item.setData(ItemType.WorkfileGroup, ModelRole.Type)
        item.setData(path, ModelRole.Path)
        item.setData(group, ModelRole.Data)

        file_info = QtCore.QFileInfo(path)
        icon = self.icon_provider.icon(file_info)
        item.setIcon(icon)

        parent_item.appendRow(item)


class BackgroundScanner(QtCore.QObject):
    workareaFound = QtCore.Signal(notgun.workareas.WorkArea)
    workfileGroupFound = QtCore.Signal(notgun.workareas.WorkfileGroup)
    itemCounterChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cancel_event = threading.Event()
        self.item_count = 0

    def scan(self, root_workarea: notgun.workareas.WorkArea):
        logger.debug(f"Starting scan of workarea: {root_workarea.path}")
        self.cancel_event.clear()
        for workarea in root_workarea.workareas():
            self.recursive_scan(workarea)

        logger.debug(
            f"Workarea scan completed. Found {self.item_count} items in total."
        )

    def recursive_scan(self, workarea: notgun.workareas.WorkArea):
        if self.cancel_event.is_set():
            return

        self.workareaFound.emit(workarea)

        self.iterateItemCount()

        for group in workarea.workfile_groups():
            self.workfileGroupFound.emit(group)
            self.iterateItemCount()

        for child in workarea.workareas():
            self.recursive_scan(child)

    def iterateItemCount(self):
        self.item_count = self.item_count + 1
        self.itemCounterChanged.emit(self.item_count)


class IconLoaderThread(QtCore.QThread):
    """
    Each workarea can have a .metadata directory with a thumbnail.png file.
    This class checks for this file and loads it if it exists.
    """

    imageLoaded = QtCore.Signal(str, QtGui.QImage)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.cancel_event = threading.Event()
        self.work_queue = queue.Queue()

    def run(self):
        while not self.cancel_event.is_set():
            try:
                path = self.work_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            thumbnail_path = os.path.join(path, ".metadata", "thumbnail.png")
            if os.path.exists(thumbnail_path):
                image = QtGui.QImage(thumbnail_path)
                self.imageLoaded.emit(path, image)
