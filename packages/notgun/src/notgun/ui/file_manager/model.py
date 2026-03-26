import os
import enum
import typing
import logging

import notgun.projects
import notgun.ui.deferred_item_model
import notgun.ui.file_manager.icons

from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas

logger = logging.getLogger(__name__)


class IconProvider(QtWidgets.QFileIconProvider):
    def icon(self, file_info: QtCore.QFileInfo) -> QtGui.QIcon:
        if file_info.isFile():
            try:
                extension = file_info.suffix().lstrip(".")
                return notgun.ui.file_manager.icons.get_icon(f"{extension}.png")
            except Exception:
                return super().icon(file_info)
        else:
            return super().icon(file_info)


class ModelRole(enum.IntEnum):
    Type = QtCore.Qt.ItemDataRole.UserRole
    Path = QtCore.Qt.ItemDataRole.UserRole + 1
    Data = QtCore.Qt.ItemDataRole.UserRole + 2


class ItemType(enum.IntEnum):
    Workarea = 0
    WorkfileGroup = 1
    Workfile = 2


class PathItemType(enum.IntEnum):
    Workarea = 0
    Spacer = 1


DataTypes = typing.Union[
    notgun.workareas.WorkArea,
    notgun.workareas.WorkfileGroup,
    notgun.workareas.Workfile,
]


class WorkareaFilterModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setRecursiveFilteringEnabled(True)
        self.protected_index: typing.Optional[QtCore.QModelIndex] = None

    def setProtectedIndex(self, index: QtCore.QModelIndex):
        self.protected_index = index
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QtCore.QModelIndex
    ) -> bool:
        if self.protected_index and source_parent == self.protected_index:
            print("accepting protected index", source_parent.data(ModelRole.Path))
            return True
        return super().filterAcceptsRow(source_row, source_parent)


class WorkareaModelItem(notgun.ui.deferred_item_model.DeferredItem):
    def __init__(self, item: DataTypes):
        super().__init__()
        self.setData(item, ModelRole.Data)

        if isinstance(item, notgun.workareas.WorkArea):
            self.setData(item.name, QtCore.Qt.ItemDataRole.DisplayRole)
            self.setData(item.path, ModelRole.Path)
            self.setData(ItemType.Workarea, ModelRole.Type)

        elif isinstance(item, notgun.workareas.WorkfileGroup):
            path = item.latest_workfile().path
            name = os.path.basename(path)
            self.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            self.setData(path, ModelRole.Path)
            self.setData(ItemType.WorkfileGroup, ModelRole.Type)

        elif isinstance(item, notgun.workareas.Workfile):
            name = os.path.basename(item.path)
            self.setData(name, QtCore.Qt.ItemDataRole.DisplayRole)
            self.setData(item.path, ModelRole.Path)
            self.setData(ItemType.Workfile, ModelRole.Type)

        self.setEditable(False)
        self._fetched = False

    def item(self) -> DataTypes:
        return self.data(ModelRole.Data)

    def canFetchMore(self) -> bool:
        if isinstance(self.item(), notgun.workareas.WorkArea):
            return not self._fetched
        return False

    def fetch(self) -> None:
        self._fetched = True
        workarea: notgun.workareas.WorkArea = self.data(ModelRole.Data)

        for child_workarea in workarea.workareas():
            self.appendRow(WorkareaModelItem(child_workarea))

        for group in workarea.workfile_groups():
            group_item = WorkareaModelItem(group)
            self.appendRow(group_item)

            # for workfile in group.workfiles:
            #     group_item.appendRow(WorkareaModelItem(workfile))

    def hasUniqueId(self):
        return True

    def uniqueId(self):
        return self.data(ModelRole.Path)


class WorkareaModel(notgun.ui.deferred_item_model.DeferredItemModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.icon_provider = IconProvider()
        self.rowsInserted.connect(self.onRowsInserted)

    def setWorkarea(self, workarea: notgun.workareas.WorkArea):
        self.clear()
        item = WorkareaModelItem(workarea)
        self.appendRow(item)

    def onRowsInserted(self, parent: QtCore.QModelIndex, first: int, last: int) -> None:
        for row in range(first, last + 1):
            index = self.index(row, 0, parent)
            item = self.itemFromIndex(index)
            path = item.data(ModelRole.Path)
            file_info = QtCore.QFileInfo(path)
            icon = self.icon_provider.icon(file_info)
            item.setIcon(icon)


class WorkareaPathModelItem(QtGui.QStandardItem):
    def __init__(self, workarea: notgun.workareas.WorkArea):
        super().__init__(workarea.metadata().name)
        self.setData(workarea, ModelRole.Data)
        self.setData(PathItemType.Workarea, ModelRole.Type)
        self.setEditable(False)
        self.setIcon(QtGui.QIcon.fromTheme("folder"))


class SpacerPickerItem(QtGui.QStandardItem):
    def __init__(self, workarea: notgun.workareas.WorkArea):
        super().__init__(">")
        self.setData(workarea, ModelRole.Data)
        self.setData(PathItemType.Spacer, ModelRole.Type)
        self.setEditable(False)


class WorkareaPathModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def setWorkarea(self, workarea: notgun.workareas.WorkArea):
        self.clear()
        path = []
        current = workarea
        while current is not None:
            path.append(current)
            current = current.parent

        for workarea in reversed(path):
            item = WorkareaPathModelItem(workarea)
            self.appendRow(item)

            spacer_item = SpacerPickerItem(workarea)
            self.appendRow(spacer_item)


class ProjectsModel(QtGui.QStandardItemModel):
    def populate(self, projects_dir: str):
        self.clear()
        self.setHorizontalHeaderLabels(["Projects"])
        for project in notgun.projects.iter_projects(projects_dir):
            item = QtGui.QStandardItem(project.label())
            item.setIcon(QtGui.QIcon.fromTheme("folder"))
            item.setEditable(False)
            item.setData(project, QtCore.Qt.ItemDataRole.UserRole)
            self.appendRow(item)

    def projectFromIndex(
        self, index: QtCore.QModelIndex
    ) -> typing.Optional[notgun.projects.Project]:
        if not index.isValid():
            return None

        project = index.data(QtCore.Qt.ItemDataRole.UserRole)
        if isinstance(project, notgun.projects.Project):
            return project

        return None
