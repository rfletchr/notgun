"""
A model that lists workfiles in a directory based on a given template.
Workfiles are grouped by their name
"""

from __future__ import annotations
from curses import version
import os
import dataclasses

from qtpy import QtCore
import qtawesome as qta

import notgun.templates

ItemDataRole = QtCore.Qt.ItemDataRole
IndexTypes = QtCore.QModelIndex | QtCore.QPersistentModelIndex


@dataclasses.dataclass
class WorkfileItem:
    path: str
    version: int


class WorkfileGroup:
    def __init__(self, name: str, ext: str):
        self.name = name
        self.ext = ext
        self.label = f"{name}.{ext}"

        self.items: list[WorkfileItem] = []


class WorkfilesModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: list[WorkfileGroup] = []
        self._file_icon = qta.icon("fa6s.file", color="darkgrey")

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        return len(self._groups)

    def data(self, index: IndexTypes, role=ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        group = self._groups[index.row()]

        if role == ItemDataRole.DisplayRole:
            return group.label

        elif role == ItemDataRole.UserRole:
            return group

        elif role == ItemDataRole.DecorationRole:
            return self._file_icon

        return None

    def scan(self, template: notgun.templates.PathTemplate, fields: dict[str, str]):
        self.beginResetModel()
        self._groups = scan(template, fields)
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self._groups = []
        self.endResetModel()


def scan(
    template: notgun.templates.PathTemplate, fields: dict[str, str]
) -> list[WorkfileGroup]:
    groups = dict[tuple[str, str], WorkfileGroup]()

    fields.pop("name", None)
    fields.pop("version", None)
    fields.pop("ext", None)

    for path in template.glob(fields):
        path_fields = template.parse(path)

        if not path_fields:
            continue

        if not os.path.isfile(path):
            continue

        key = (path_fields["name"], path_fields["ext"].lower())
        if key not in groups:
            groups[key] = WorkfileGroup(path_fields["name"], path_fields["ext"].lower())

        groups[key].items.append(WorkfileItem(path, path_fields["version"]))

    for group in groups.values():
        group.items.sort(key=lambda item: item.version, reverse=True)

    return list(groups.values())
