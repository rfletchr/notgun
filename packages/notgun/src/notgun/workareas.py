from __future__ import annotations

import typing
import dataclasses

import notgun.templates


@dataclasses.dataclass
class WorkAreaType:
    label: str
    template: notgun.templates.PathTemplate
    token: str
    children: list[WorkAreaType] = dataclasses.field(default_factory=list)
    workfiles_template: notgun.templates.PathTemplate | None = None
    icon_name: str = "fa6s.folder"

    def __repr__(self):
        return f"WorkAreaType(label={self.label})"


@dataclasses.dataclass
class WorkArea:
    type: WorkAreaType
    name: str
    path: str
    fields: dict[str, int | str]
    parent: "WorkArea|None" = None

    def ls(self) -> typing.Iterator[WorkArea]:
        for child in self.type.children:
            child_fields = self.fields.copy()
            child_fields[child.token] = "*"

            for path in sorted(child.template.glob(child_fields)):
                resolved_fields = child.template.parse(path)

                if resolved_fields is None:
                    continue

                name = resolved_fields[child.token]

                yield WorkArea(child, name, path, resolved_fields, parent=self)

    def __repr__(self):
        return f"Workarea(type={self.type.label}, path={self.path})"


def workarea_from_path(
    path: str,
    root_type: WorkAreaType,
    parent: WorkArea | None = None,
):
    # if its a full match then we've found the location.
    if fields := root_type.template.fullmatch(path):
        name = fields[root_type.token]
        return WorkArea(root_type, name, path, fields, parent)

    partial_match = root_type.template.match(path)
    if not partial_match:
        return

    parent = WorkArea(
        root_type,
        partial_match[root_type.token],
        root_type.template.format(partial_match),
        partial_match,
    )

    for child_type in root_type.children:
        if child := workarea_from_path(path, child_type, parent):
            return child
