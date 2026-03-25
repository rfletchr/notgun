from __future__ import annotations
import typing
import threading
import dataclasses

import notgun.schema


class WorkArea:
    def __init__(
        self,
        schema: notgun.schema.WorkareaSchema,
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
        self._lock = threading.Lock()

    @property
    def schema(self) -> notgun.schema.WorkareaSchema:
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

    def workareas(self) -> tuple[WorkArea]:
        with self._lock:
            if self._workareas is None:
                self._workareas = tuple(iter_workareas(self))
            return self._workareas

    def workfile_groups(self) -> tuple[WorkfileGroup]:
        with self._lock:
            if self._workfile_groups is None:
                self._workfile_groups = tuple(iter_workfile_groups(self))
            return self._workfile_groups

    def next_workfile_version(self, name: str, ext: str) -> int:
        self.invalidate_groups()
        version = 0
        for group in self.workfile_groups():
            if group.name == name and group.filetype == ext:
                for workfile in group.workfiles:
                    version = max(version, workfile.version())

        return version + 1

    def supported_filetypes(self) -> list[str]:
        return list(self.schema.workfiles.keys())

    def invalidate_groups(self):
        with self._lock:
            self._workfile_groups = None

    def __repr__(self):
        return f"WorkArea(schema={self.schema.label}, path={self.path})"


@dataclasses.dataclass
class Workfile:
    schema: notgun.schema.WorkfileSchema
    path: str
    fields: dict[str, int | str]
    group: WorkfileGroup

    def version(self) -> int:
        return int(self.fields["version"])


@dataclasses.dataclass
class WorkfileGroup:
    name: str
    filetype: str
    workfiles: list[Workfile] = dataclasses.field(default_factory=list)
    parent: WorkArea | None = None


def workarea_from_path(
    path: str,
    root_type: notgun.schema.WorkareaSchema,
    parent: WorkArea | None = None,
):
    # if its a full match then we've found the location.
    if fields := root_type.template.fullmatch(path):
        name = fields[root_type.identity_token]  # type: ignore
        return WorkArea(root_type, name, path, fields, parent)

    partial_match = root_type.template.match(path)
    if not isinstance(partial_match, dict):
        return

    parent = WorkArea(
        root_type,
        partial_match.get(root_type.identity_token, root_type.label),
        root_type.template.format(partial_match),
        partial_match,
    )

    for child_type in root_type.workareas:
        if child := workarea_from_path(path, child_type, parent):
            return child


def iter_workareas(parent_workarea: WorkArea) -> typing.Iterator[WorkArea]:
    for child in parent_workarea.schema.workareas:
        if child.identity_token is None:
            path = child.template.format(parent_workarea.fields)
            resolved_fields = child.template.parse(path)
            if resolved_fields is None:
                continue

            name = child.label
            yield WorkArea(child, name, path, resolved_fields, parent=parent_workarea)
        else:
            child_fields = parent_workarea.fields.copy()
            child_fields[child.identity_token] = "*"

            for path in sorted(child.template.glob(child_fields)):
                resolved_fields = child.template.parse(path)

                if resolved_fields is None:
                    continue

                name = resolved_fields[child.identity_token]

                yield WorkArea(
                    child, name, path, resolved_fields, parent=parent_workarea
                )


def iter_workfile_groups(parent_workarea: WorkArea) -> typing.Iterator[WorkfileGroup]:
    if not parent_workarea.schema.workfiles:
        return
    for workfile_schema in parent_workarea.schema.workfiles.values():
        template = workfile_schema.template
        search_fields = {**parent_workarea.fields}
        search_fields.pop("version", None)
        search_fields.pop("name", None)
        search_fields.pop("extension", None)

        memo = dict[tuple[str, str], WorkfileGroup]()
        for path in sorted(template.glob(search_fields)):
            path_fields = template.parse(path)
            if path_fields is None:
                continue

            name = path_fields["name"]
            ext = path_fields["extension"]
            key = (name, ext)
            if key not in memo:
                memo[key] = WorkfileGroup(name, ext, parent=parent_workarea)

            group = memo[key]
            group.workfiles.append(Workfile(workfile_schema, path, path_fields, group))

        for group in memo.values():
            yield group
