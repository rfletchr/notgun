from __future__ import annotations
import os
import typing

from qtpy import QtCore, QtWidgets, QtGui

import notgun.workareas
import notgun.projects
import notgun.ui.file_manager.view
import notgun.ui.file_manager.model
import notgun.ui.workfiles


class ChangeWorkareaCommand(QtGui.QUndoCommand):  # type: ignore[attr-defined]
    def __init__(
        self,
        controller: FileManagerController,
        old_workarea: notgun.workareas.WorkArea,
        new_workarea: notgun.workareas.WorkArea,
    ):
        super().__init__(f"Navigate to {new_workarea.name}")
        self._controller = controller
        self._old = old_workarea
        self._new = new_workarea

    def redo(self):
        self._controller._applyWorkarea(self._new)

    def undo(self):
        self._controller._applyWorkarea(self._old)


class FileManagerController(QtCore.QObject):
    def __init__(
        self,
        view: typing.Union[notgun.ui.file_manager.view.FileManagerView, None] = None,
        workfile_action_handler: typing.Union[WorkareaActionHandler, None] = None,
    ):
        super().__init__()

        self._active_project: typing.Union[notgun.projects.Project, None] = None
        self._active_workarea: typing.Union[notgun.workareas.WorkArea, None] = None

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setInterval(5000)
        self._refresh_timer.timeout.connect(self.refresh)
        # self._refresh_timer.start()

        self.path_model = notgun.ui.file_manager.model.WorkareaPathModel()
        self.projects_model = notgun.ui.file_manager.model.ProjectsModel()
        self.workarea_model = notgun.ui.file_manager.model.WorkareaModel()

        self.workarea_filter_model = QtCore.QSortFilterProxyModel()
        self.workarea_filter_model.setSourceModel(self.workarea_model)
        self.workarea_filter_model.setRecursiveFilteringEnabled(True)
        self.workarea_filter_model.setFilterCaseSensitivity(
            QtCore.Qt.CaseSensitivity.CaseInsensitive
        )

        self.undo_stack = QtGui.QUndoStack(self)  # type: ignore[attr-defined]

        self.action_handler = workfile_action_handler or WorkareaActionHandler()
        self.action_handler.refreshRequested.connect(self.refresh)

        self.view = view or notgun.ui.file_manager.view.FileManagerView()
        self._applyStylesheet()
        self.view.setPathModel(self.path_model)
        self.view.setProjectsModel(self.projects_model)
        self.view.setWorkareasModel(self.workarea_filter_model)

        self.view.projectItemClicked.connect(self.onProjectItemClicked)
        self.view.workareaItemActivated.connect(self.onWorkareaItemActivated)
        self.view.workareaItemRightClicked.connect(self.onWorkareaItemRightClicked)
        self.view.pathItemClicked.connect(self.onPathItemClicked)
        self.view.searchChanged.connect(self.onSearchChanged)

        goto_parent_action = QtGui.QAction("Go to Parent", self.view)  # type: ignore[attr-defined]
        goto_parent_action.setShortcut(QtGui.QKeySequence("Backspace"))
        goto_parent_action.setEnabled(False)
        goto_parent_action.triggered.connect(self.undo_stack.undo)
        self.undo_stack.canUndoChanged.connect(goto_parent_action.setEnabled)
        self.view.addAction(goto_parent_action)

    def _applyStylesheet(self):
        stylesheet_path = os.path.join(
            os.path.dirname(__file__),
            "stylesheet.qss",
        )
        if not os.path.exists(stylesheet_path):
            return
        with open(stylesheet_path, encoding="utf-8") as fh:
            self.view.setStyleSheet(fh.read())

    def setProjectsDir(self, projects_dir: str):
        self.projects_model.populate(projects_dir)

    def onSearchChanged(self, text: str):
        self.workarea_filter_model.setFilterFixedString(text)

    def onProjectItemClicked(self, index: QtCore.QModelIndex):
        project: notgun.projects.Project = index.data(QtCore.Qt.ItemDataRole.UserRole)
        self._active_project = project
        self.undo_stack.clear()
        self.setWorkarea(project.workarea())

    def _applyWorkarea(self, workarea: notgun.workareas.WorkArea):
        self._active_workarea = workarea
        self.workarea_model.setWorkarea(workarea)
        self.path_model.setWorkarea(workarea)

    def setWorkarea(self, workarea: notgun.workareas.WorkArea):

        if self._active_workarea is None:
            self._applyWorkarea(workarea)
        else:
            self.undo_stack.push(
                ChangeWorkareaCommand(self, self._active_workarea, workarea)
            )

    def refresh(self):
        if self._active_workarea is not None:
            self._applyWorkarea(self._active_workarea)

    def onWorkareaItemActivated(self, index: QtCore.QModelIndex):
        workarea = index.data(notgun.ui.file_manager.model.ModelRole.Data)

        if isinstance(workarea, notgun.workareas.WorkArea):
            self.setWorkarea(workarea)
            self.view.clearFilter()
        elif isinstance(workarea, notgun.workareas.WorkfileGroup):
            self.action_handler.onWorkfileGroupActivated(workarea)

    def onWorkareaItemRightClicked(self, index: QtCore.QModelIndex, pos: QtCore.QPoint):
        backing_item = (
            index.data(notgun.ui.file_manager.model.ModelRole.Data)
            or self._active_workarea
        )
        self.action_handler.onContextMenuRequested(backing_item, pos)

    def onPathItemClicked(self, index: QtCore.QModelIndex):
        item_type = index.data(notgun.ui.file_manager.model.ModelRole.Type)
        if item_type == notgun.ui.file_manager.model.PathItemType.Spacer:
            self.onWorkareaSwitchMenuRequested(index)
            return

        workarea: notgun.workareas.WorkArea = index.data(
            notgun.ui.file_manager.model.ModelRole.Data
        )

        if isinstance(workarea, notgun.workareas.WorkArea):
            self.setWorkarea(workarea)

    def onWorkareaSwitchMenuRequested(self, index: QtCore.QModelIndex):
        workarea = index.data(notgun.ui.file_manager.model.ModelRole.Data)
        if not isinstance(workarea, notgun.workareas.WorkArea):
            return

        parent = workarea.parent
        if not isinstance(parent, notgun.workareas.WorkArea):
            return

        siblings = parent.workareas()
        if not siblings:
            return

        menu = QtWidgets.QMenu(self.view)
        for sibling in siblings:
            action = menu.addAction(sibling.name)
            action.setData(sibling)

            if sibling.path == workarea.path:
                font = action.font()
                font.setBold(True)
                action.setFont(font)

        item_rect = self.view.path_view.visualRect(index)
        popup_pos = self.view.path_view.viewport().mapToGlobal(item_rect.bottomLeft())
        selected_action = menu.exec(popup_pos)
        if selected_action is None:
            return

        selected_workarea = selected_action.data()
        if isinstance(selected_workarea, notgun.workareas.WorkArea):
            self.setWorkarea(selected_workarea)


ObjectType = typing.Union[
    notgun.workareas.WorkArea,
    notgun.workareas.WorkfileGroup,
    None,
]


class WorkareaActionHandler(QtCore.QObject):
    refreshRequested = QtCore.Signal()  # type: ignore
    requestOpenWorkfile = QtCore.Signal(notgun.workareas.Workfile)  # type: ignore
    requestNewWorkfile = QtCore.Signal(notgun.ui.workfiles.NewWorkfileResult)  # type: ignore

    def __init__(self, parent=None):
        super().__init__(parent)
        self.open_icon = QtGui.QIcon.fromTheme("document-open")  # type: ignore
        self.new_icon = QtGui.QIcon.fromTheme("document-new")  # type: ignore
        self.folder_icon = QtGui.QIcon.fromTheme("folder")  # type: ignore
        self.list_icon = QtGui.QIcon.fromTheme("view-list")  # type: ignore
        self.refresh_icon = QtGui.QIcon.fromTheme("view-refresh")  # type: ignore

    def onWorkfileGroupActivated(self, workfile_group: notgun.workareas.WorkfileGroup):
        latest_workfile = workfile_group.latest_workfile()
        if latest_workfile is not None:
            self.requestOpenWorkfile.emit(latest_workfile)

    def onContextMenuRequested(self, obj: ObjectType, pos: QtCore.QPoint):
        menu = QtWidgets.QMenu()
        style = menu.style()

        # get new icon from theme, fallback to standard icon if not found
        new_icon = QtGui.QIcon.fromTheme("document-new")
        if new_icon.isNull():
            new_icon = style.standardIcon(style.StandardPixmap.SP_FileDialogNewFolder)  # type: ignore[attr-defined]

        if isinstance(obj, notgun.workareas.WorkArea):
            refresh_action = menu.addAction("Refresh")
            refresh_action.setIcon(self.refresh_icon)
            refresh_action.triggered.connect(self.refreshRequested)

            open_dir_action = menu.addAction("Open in File Explorer")
            open_dir_action.setIcon(self.folder_icon)

            open_dir_action.setData(obj.path)
            open_dir_action.triggered.connect(self.onOpenPathActionTriggered)

            if obj.schema.workfiles:
                new_menu = menu.addMenu("Create New")
                new_menu.setIcon(self.new_icon)
                for workfile_type in obj.schema.workfiles:
                    action = new_menu.addAction(workfile_type)
                    action.setData((obj, workfile_type))
                    action.triggered.connect(self.onNewWorkfileActionTriggered)

                open_menu = menu.addMenu("Open")
                open_menu.setIcon(self.open_icon)
                for workfile_group in obj.workfile_groups():
                    group_menu = open_menu.addMenu(workfile_group.name)
                    group_menu.setIcon(self.list_icon)
                    for workfile in reversed(workfile_group.workfiles):
                        action = group_menu.addAction(os.path.basename(workfile.path))
                        action.setIcon(self.open_icon)
                        action.setData(workfile)
                        action.triggered.connect(self.onOpenWorkfileActionTriggered)

        elif isinstance(obj, notgun.workareas.WorkfileGroup):
            open_action = menu.addAction("Open")
            open_action.setIcon(self.open_icon)
            latest_workfile = obj.latest_workfile()
            if latest_workfile is not None:
                open_action.setData(latest_workfile)
                open_action.triggered.connect(self.onOpenWorkfileActionTriggered)

            open_version_menu = menu.addMenu("Versions")
            open_version_menu.setIcon(self.list_icon)

            for workfile in reversed(obj.workfiles):
                action = open_version_menu.addAction(os.path.basename(workfile.path))
                action.setIcon(self.open_icon)
                action.setData(workfile)
                action.triggered.connect(self.onOpenWorkfileActionTriggered)

        menu.exec(pos)

    def onOpenPathActionTriggered(self):
        action: QtWidgets.QAction = self.sender()  # type: ignore
        if not isinstance(action, QtWidgets.QAction):  # type: ignore
            return

        path = action.data()
        if not isinstance(path, str):
            return

        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    def onOpenWorkfileActionTriggered(self):
        action: QtWidgets.QAction = self.sender()  # type: ignore
        if not isinstance(action, QtWidgets.QAction):  # type: ignore
            return

        workfile = action.data()
        if not isinstance(workfile, notgun.workareas.Workfile):
            return

        self.requestOpenWorkfile.emit(workfile)

    def onNewWorkfileActionTriggered(self):
        action: QtWidgets.QAction = self.sender()  # type: ignore
        if not isinstance(action, QtWidgets.QAction):  # type: ignore
            return

        workarea, workfile_type = action.data()

        result = notgun.ui.workfiles.NewWorkfileDialog.pickFromWorkarea(
            workarea,
            workfile_type,
        )
        if result is not None:
            self.requestNewWorkfile.emit(result)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    # apply_dark_palette(app)
    controller = FileManagerController()
    controller.setProjectsDir("/home/user/Development/notgun/example")
    controller.view.show()
    sys.exit(app.exec())
