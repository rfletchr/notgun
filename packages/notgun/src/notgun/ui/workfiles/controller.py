from qtpy import QtGui, QtCore, QtWidgets

import notgun.templates
import notgun.ui.workfiles.model
import notgun.ui.workfiles.view


class WorkfilesViewController:
    stackActivated = QtCore.Signal(notgun.ui.workfiles.model.WorkfileStack)
    stackClicked = QtCore.Signal(notgun.ui.workfiles.model.WorkfileStack)

    def __init__(
        self,
        view: notgun.ui.workfiles.view.WorkfilesView | None = None,
        icon_provider: QtWidgets.QFileIconProvider | None = None,
    ):
        self.model = notgun.ui.workfiles.model.WorkFilesModel(icon_provider)

        self.view = view or notgun.ui.workfiles.view.WorkfilesView()
        self.view.setModel(self.model)

    def populate(self, template: notgun.templates.PathTemplate, fields: dict[str, str]):
        self.model.scan(template, fields)

    def clear(self):
        self.model.clear()

    def onStackActivated(self, index: QtCore.QModelIndex):
        stack = self.model.stackFromIndex(index)
        if stack:
            self.stackActivated.emit(stack)

    def onStackClicked(self, index: QtCore.QModelIndex):
        stack = self.model.stackFromIndex(index)
        if stack:
            self.stackClicked.emit(stack)
