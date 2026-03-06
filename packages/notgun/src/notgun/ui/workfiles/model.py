import enum
import dataclasses
from qtpy import QtCore, QtGui, QtWidgets

import notgun.templates


@dataclasses.dataclass
class WorkfileItem:
    name: str
    version: int
    ext: str
    path: str
    fields: dict[str, str | int]


@dataclasses.dataclass
class WorkfileStack:
    name: str
    ext: str
    files: list[WorkfileItem] = dataclasses.field(default_factory=list)
    label: str = dataclasses.field(init=False)

    def __post_init__(self):
        self.label = f"{self.name}.{self.ext}"


class ModelRoles(enum.IntEnum):
    StackRole = QtCore.Qt.ItemDataRole.UserRole + 1
    FilesRole = QtCore.Qt.ItemDataRole.UserRole + 2


class WorkFilesModel(QtCore.QAbstractListModel):
    def __init__(
        self, icon_provider: QtWidgets.QFileIconProvider | None = None, parent=None
    ):
        super().__init__(parent)
        self._stacks = list[WorkfileStack]()
        self._icon_provider = icon_provider or QtWidgets.QFileIconProvider()

    def rowCount(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> int:
        return len(self._stacks)

    def data(
        self, index: QtCore.QModelIndex, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ) -> object:
        if not index.isValid():
            return None

        stack = self._stacks[index.row()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return stack.label

        elif role == ModelRoles.FilesRole:
            return stack.files.copy()

        elif role == ModelRoles.StackRole:
            return stack

        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            if stack.files:
                file_info = QtCore.QFileInfo(stack.files[0].path)
                return self._icon_provider.icon(file_info)
            else:
                return self._icon_provider.icon(
                    QtWidgets.QFileIconProvider.IconType.File
                )

    def scan(self, template: notgun.templates.PathTemplate, fields: dict[str, str]):
        self.beginResetModel()
        self._stacks = scan(template, fields)
        self.endResetModel()

    def stackFromIndex(self, index: QtCore.QModelIndex) -> WorkfileStack | None:
        if not index.isValid():
            return None
        stack = self._stacks[index.row()]
        return stack

    def filesFromIndex(self, index: QtCore.QModelIndex) -> list[WorkfileItem] | None:
        stack = self.stackFromIndex(index)
        if stack is None:
            return None
        return stack.files

    def clear(self):
        self.beginResetModel()
        self._stacks.clear()
        self.endResetModel()


def scan(
    template: notgun.templates.PathTemplate, fields: dict[str, str]
) -> list[WorkfileStack]:
    """
    Scan the filesystem for workfiles matching the given template and fields.

    - name, version and ext are 'wildcards'
    - files are grouped into 'stacks' based on their name and extension

    """

    fields.pop("version", None)
    fields.pop("name", None)
    fields.pop("ext", None)

    token_names = template.token_names()

    if any(
        (
            "version" not in token_names,
            "name" not in token_names,
            "ext" not in token_names,
        )
    ):
        raise ValueError("Template must contain 'name', 'version' and 'ext' tokens")

    result = dict[tuple[str, str], WorkfileStack]()

    for path in template.glob(fields):
        path_fields = template.parse(path)

        if path_fields is None:
            continue

        name = path_fields["name"]
        ext = path_fields["ext"].lower()

        key = (name, ext)
        if key not in result:
            stack = result[key] = WorkfileStack(name, ext)
        else:
            stack = result[key]

        workfile = WorkfileItem(
            name=name,
            version=path_fields["version"],
            ext=ext,
            path=path,
            fields=path_fields,
        )
        stack.files.append(workfile)

    for stack in result.values():
        stack.files.sort(key=lambda x: x.version, reverse=True)

    return list(result.values())
