from __future__ import annotations
import json
import os
import fnmatch
import typing
import threading
import dataclasses

import notgun.schema

if typing.TYPE_CHECKING:
    import notgun.projects


class WorkareaMetadata(typing.NamedTuple):
    name: str
    image_path: typing.Union[str, None]


class WorkArea:
    def __init__(
        self,
        schema: notgun.schema.WorkareaSchema,
        name: str,
        path: str,
        fields: dict[str, typing.Union[int, str]],
        project: "notgun.projects.Project",
        parent: typing.Union[WorkArea, None] = None,
    ):
        self._schema = schema
        self._name = name
        self._path = path
        self._fields = fields
        self._parent = parent
        self._workareas: typing.Union[tuple[WorkArea, ...], None] = None
        self._workfile_groups: typing.Union[tuple[WorkfileGroup, ...], None] = None
        self._lock = threading.Lock()
        self._project = project
        self._metadata: typing.Union[WorkareaMetadata, None] = None

    @property
    def schema(self) -> notgun.schema.WorkareaSchema:
        return self._schema

    @property
    def name(self) -> str:
        return self.metadata().name

    @property
    def path(self) -> str:
        return self._path

    @property
    def fields(self) -> dict[str, typing.Union[int, str]]:
        return self._fields

    @property
    def parent(self) -> typing.Union[WorkArea, None]:
        return self._parent

    @property
    def project(self) -> "notgun.projects.Project":
        return self._project

    def metadata(self) -> WorkareaMetadata:
        if self._metadata is None:
            path = os.path.join(self.path, ".metadata", "metadata.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                    self._metadata = WorkareaMetadata(
                        name=data.get("name", self._name),
                        image_path=data.get("image_path"),
                    )
            else:
                self._metadata = WorkareaMetadata(name=self._name, image_path=None)
        return self._metadata

    def workareas(self) -> tuple[WorkArea, ...]:
        with self._lock:
            if self._workareas is None:
                self._workareas = tuple(iter_workareas(self.project, self))

            return self._workareas

    def workfile_groups(self) -> tuple[WorkfileGroup, ...]:
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

    def invalidate_workareas(self):
        with self._lock:
            self._workareas = None

    def __repr__(self):
        return f"WorkArea(schema={self.schema.label}, path={self.path})"


@dataclasses.dataclass
class Workfile:
    schema: notgun.schema.WorkfileSchema
    path: str
    fields: dict[str, typing.Union[int, str]]
    group: WorkfileGroup

    def version(self) -> int:
        return int(self.fields["version"])


@dataclasses.dataclass
class WorkfileGroup:
    name: str
    filetype: str
    workarea: WorkArea
    workfiles: list[Workfile] = dataclasses.field(default_factory=list)

    def latest_workfile(self) -> Workfile:
        return max(self.workfiles, key=lambda wf: wf.version())


def get_workarea_name(
    schema: notgun.schema.WorkareaSchema, fields: dict[str, typing.Union[int, str]]
) -> str:
    if schema.identity_token is not None:
        return fields[schema.identity_token]  # type: ignore
    else:
        return schema.label


def workarea_from_path(
    path: str,
    root_type: notgun.schema.WorkareaSchema,
    project: "notgun.projects.Project",
    parent: typing.Union[WorkArea, None] = None,
):
    # if its a full match then we've found the location.
    if fields := root_type.template.fullmatch(path):
        name = get_workarea_name(root_type, fields)

        if not root_type.match_name(name):
            return

        return WorkArea(
            root_type,
            name,
            path,
            fields,
            project,
            parent=parent,
        )

    partial_match = root_type.template.match(path)
    if not isinstance(partial_match, dict):
        return

    if root_type.identity_token:
        name = get_workarea_name(root_type, partial_match)
        if not root_type.match_name(name):
            return

    parent = WorkArea(
        root_type,
        partial_match.get(root_type.identity_token, root_type.label),
        root_type.template.format(partial_match),
        partial_match,
        project,
        parent=parent,
    )

    for child_type in root_type.workareas:
        if child := workarea_from_path(path, child_type, project, parent):
            return child


def iter_workareas(
    project: "notgun.projects.Project",
    parent_workarea: WorkArea,
) -> typing.Iterator[WorkArea]:
    for child in parent_workarea.schema.workareas:
        if child.identity_token is None:
            path = child.template.format(parent_workarea.fields)
            resolved_fields = child.template.parse(path)
            if resolved_fields is None:
                continue

            name = child.label
            yield WorkArea(child, name, path, resolved_fields, project, parent_workarea)
        else:
            child_fields = parent_workarea.fields.copy()
            child_fields[child.identity_token] = "*"

            for path in sorted(child.template.glob(child_fields)):
                resolved_fields = child.template.parse(path)

                if resolved_fields is None:
                    continue

                name = resolved_fields[child.identity_token]

                yield WorkArea(
                    child, name, path, resolved_fields, project, parent=parent_workarea
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
                memo[key] = WorkfileGroup(name, ext, parent_workarea)

            group = memo[key]
            group.workfiles.append(Workfile(workfile_schema, path, path_fields, group))

        for group in memo.values():
            yield group
