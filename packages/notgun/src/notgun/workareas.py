from __future__ import annotations
import typing
import dataclasses

import notgun.templates


@dataclasses.dataclass
class ProjectSchema:
    label: str
    template: notgun.templates.PathTemplate
    token: str | None = None
    children: list[ProjectSchema] = dataclasses.field(default_factory=list)
    workfiles_template: notgun.templates.PathTemplate | None = None
    icon_name: str = "fa6s.folder"

    def __repr__(self):
        return f"ProjectSchema(label={self.label})"


class WorkArea:
    def __init__(
        self,
        schema: ProjectSchema,
        name: str,
        path: str,
        fields: dict[str, int | str],
        parent: "WorkArea|None" = None,
    ):
        self._schema = schema
        self._name = name
        self._path = path
        self._fields = fields
        self._parent = parent
        self._workareas: list[WorkArea] | None = None
        self._workfile_groups: list[WorkfileGroup] | None = None

    @property
    def schema(self) -> ProjectSchema:
        return self._schema

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> str:
        return self._path

    @property
    def fields(self) -> dict[str, int | str]:
        return self._fields

    @property
    def parent(self) -> "WorkArea|None":
        return self._parent

    def workareas(self) -> list[WorkArea]:
        if self._workareas is None:
            self._workareas = list(iter_workareas(self))
        return self._workareas

    def workfile_groups(self) -> list[WorkfileGroup]:
        if self._workfile_groups is None:
            self._workfile_groups = list(iter_workfile_groups(self))
        return self._workfile_groups

    def __repr__(self):
        return f"WorkArea(schema={self.schema.label}, path={self.path})"


@dataclasses.dataclass
class Workfile:
    path: str
    fields: dict[str, int | str]


@dataclasses.dataclass
class WorkfileGroup:
    name: str
    ext: str
    workfiles: list[Workfile] = dataclasses.field(default_factory=list)
    parent: WorkArea | None = None


def workarea_from_path(
    path: str,
    root_type: ProjectSchema,
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


def iter_workareas(parent_workarea: WorkArea) -> typing.Iterator[WorkArea]:
    for child in parent_workarea.schema.children:
        if child.token is None:
            path = child.template.format(parent_workarea.fields)
            resolved_fields = child.template.parse(path)
            if resolved_fields is None:
                continue

            name = child.label
            yield WorkArea(child, name, path, resolved_fields, parent=parent_workarea)
        else:
            child_fields = parent_workarea.fields.copy()
            child_fields[child.token] = "*"

            for path in sorted(child.template.glob(child_fields)):
                resolved_fields = child.template.parse(path)

                if resolved_fields is None:
                    continue

                name = resolved_fields[child.token]

                yield WorkArea(
                    child, name, path, resolved_fields, parent=parent_workarea
                )


def iter_workfile_groups(parent_workarea: WorkArea) -> typing.Iterator[WorkfileGroup]:
    if parent_workarea.schema.workfiles_template is None:
        return

    template = parent_workarea.schema.workfiles_template
    search_fields = {**parent_workarea.fields}
    search_fields.pop("version", None)
    search_fields.pop("name", None)
    search_fields.pop("ext", None)

    memo = dict[tuple[str, str], WorkfileGroup]()
    for path in sorted(template.glob(search_fields)):
        path_fields = template.parse(path)
        if path_fields is None:
            continue

        name = path_fields["name"]
        ext = path_fields["ext"]
        key = (name, ext)
        if key not in memo:
            memo[key] = WorkfileGroup(name, ext, parent=parent_workarea)

        memo[key].workfiles.append(Workfile(path, path_fields))

    for group in memo.values():
        yield group
