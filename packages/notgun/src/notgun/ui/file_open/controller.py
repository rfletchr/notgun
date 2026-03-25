from qtpy import QtWidgets, QtGui, QtCore
import os
import notgun.projects
import notgun.workareas
import notgun.ui.workareas.controller
import notgun.ui.workareas.view
import notgun.ui.file_open.view


class FileOpenController(QtCore.QObject):
    @classmethod
    def current(cls):
        project = notgun.projects.get_current()
        if project is None:
            raise ValueError("No Project is setup.")

        return cls(project)

    def __init__(
        self,
        project: notgun.projects.Project,
        view: notgun.ui.workareas.view.WorkareasView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.project = project
        self.view = view or notgun.ui.file_open.view.FileOpenView()

        self.controller = notgun.ui.workareas.controller.WorkareasController(
            self.view.workarea_view,
            use_async_model=False,
        )
        self.controller.itemActivated.connect(self.onItemActivated)
        self._workarea: notgun.workareas.WorkArea | None = None

    def onFileOpenRequested(self, workfile: notgun.workareas.Workfile):
        self.project.app().open(workfile.path)

    def onGotoParentWorkarea(self):
        if not self._workarea:
            return

        if not self._workarea.parent:
            return

        self._workarea = self._workarea.parent
        self.controller.populate(self._workarea)

    def onItemActivated(self, obj):
        if isinstance(obj, notgun.workareas.Workfile):
            print("workfile activated", obj)
        if isinstance(obj, notgun.workareas.WorkfileGroup):
            print("group activated", obj)

    def populate(self):
        filepath = os.path.dirname(self.project.app().filepath())
        self._workarea = self.project.workarea_from_path(filepath)
        print("workarea", self._workarea)
        if self._workarea:
            self.controller.populate(self._workarea)
