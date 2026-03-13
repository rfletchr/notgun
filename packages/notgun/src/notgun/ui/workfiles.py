__all__ = ["NewFileDialog"]

from notgun.ui.workareas.view import NewFileDialog
import dataclasses
from qtpy import QtCore, QtGui, QtWidgets

import notgun.workareas


class NewWorkfileView(QtWidgets.QWidget):
    workfileTypeChanged = QtCore.Signal(str)
    workfileNameChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # pick from a set of pre-existing options
        self.workfile_type_combo = QtWidgets.QComboBox()
        self.workfile_type_combo.setEditable(False)
        self.workfile_type_combo.setMinimumContentsLength(15)
        self.workfile_type_combo.currentTextChanged.connect(self.workfileTypeChanged)

        self.name_combo = QtWidgets.QComboBox()
        self.name_combo.setEditable(False)
        self.name_combo.setMinimumContentsLength(25)
        self.name_combo.currentTextChanged.connect(self.workfileNameChanged)

        self.extension_box = QtWidgets.QLineEdit()
        self.extension_box.setReadOnly(True)

        editor_layout = QtWidgets.QHBoxLayout(self)
        editor_layout.addWidget(self.workfile_type_combo)
        editor_layout.addWidget(self.name_combo)
        editor_layout.addWidget(self.extension_box)

    def allowNameEditing(self, allow: bool):
        self.name_combo.setEditable(allow)

    def setExtension(self, ext: str):
        self.extension_box.setText(ext)

    def setWorkfileTypes(self, types: list[str]):
        self.workfile_type_combo.clear()
        self.workfile_type_combo.addItems(types)

    def setNames(self, names: list[str]):
        self.name_combo.clear()
        self.name_combo.addItems(names)

    def setNameValidator(self, validator: QtGui.QValidator):
        self.name_combo.setValidator(validator)


@dataclasses.dataclass
class NewWorkfileResult:
    workarea: notgun.workareas.WorkArea
    workfile_type: notgun.workareas.WorkfileSchema
    name: str
    version: int
    path: str


class NewWorkfileController(QtCore.QObject):
    def __init__(
        self,
        view: NewWorkfileView | None = None,
        parent=None,
    ):
        super().__init__(parent=parent)

        self._active_workarea: notgun.workareas.WorkArea | None = None
        self._workfile_type: notgun.workareas.WorkfileSchema | None = None
        self._workfile_name: str = ""

        self.validator = QtGui.QRegularExpressionValidator()

        self.view = view or NewWorkfileView()
        self.view.setNameValidator(self.validator)
        self.view.workfileTypeChanged.connect(self.onWorkfileTypeChanged)
        self.view.workfileNameChanged.connect(self.onWorkfileNameChanged)

    def resetView(self):
        self.view.setWorkfileTypes([])
        self.view.setNames([])
        self.view.setExtension("")
        self.view.allowNameEditing(False)

    def setWorkarea(self, workarea: notgun.workareas.WorkArea):
        self.resetView()
        self._active_workarea = workarea

        workfile_types = list(workarea.schema.workfiles.keys())
        if workfile_types:
            self.view.setWorkfileTypes(workfile_types)
            self.onWorkfileTypeChanged(workfile_types[0])

    def onWorkfileTypeChanged(self, type_name: str):
        assert self._active_workarea is not None, "No active workarea set"

        self._workfile_type = self._active_workarea.schema.workfiles[type_name]

        self.view.setExtension(self._workfile_type.extension)

        self._active_workarea.invalidate_groups()

        suggested_name = self._workfile_type.naming_pattern.format(
            **self._active_workarea.fields
        )

        existing_names = [suggested_name]
        for group in self._active_workarea.workfile_groups():
            if group.filetype == self._workfile_type.extension:
                if group.name not in existing_names:
                    existing_names.append(group.name)

        self.view.setNames(list(existing_names))
        self.view.allowNameEditing(self._workfile_type.name_is_editable)

        self.validator.setRegularExpression(
            QtCore.QRegularExpression(self._workfile_type.validation_regex)
        )

    def onWorkfileNameChanged(self, name: str):
        self._workfile_name = name

    def result(self) -> NewWorkfileResult | None:
        if self._active_workarea is None:
            raise ValueError("No active workarea set")

        if self._workfile_type is None:
            raise ValueError("No workfile type selected")

        if not self._workfile_name:
            raise ValueError("No workfile name set")

        version = self._active_workarea.next_workfile_version(
            self._workfile_name,
            self._workfile_type.extension,
        )
        fields = self._active_workarea.fields.copy()
        fields["name"] = self._workfile_name
        fields["version"] = version
        fields["ext"] = self._workfile_type.extension

        path = self._workfile_type.template.format(fields)

        return NewWorkfileResult(
            self._active_workarea,
            self._workfile_type,
            self._workfile_name,
            version,
            path,
        )


class NewWorkfileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.view = NewWorkfileView()
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view, stretch=1)
        layout.addWidget(self.button_box, stretch=0)

    @classmethod
    def pickFromWorkarea(
        cls,
        workarea: notgun.workareas.WorkArea,
        parent: QtWidgets.QWidget | None = None,
    ) -> NewWorkfileResult | None:
        dialog = cls(parent=parent)
        controller = NewWorkfileController(view=dialog.view)
        controller.setWorkarea(workarea)

        if dialog.exec() == dialog.DialogCode.Accepted:
            return controller.result()
