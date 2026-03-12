from __future__ import annotations
import typing
import dataclasses

import notgun.templates

if typing.TYPE_CHECKING:
    import notgun.launcher


@dataclasses.dataclass
class WorkareaSchema:
    """
    Attributes:
        label: The display name for this workarea type.
        template: The path template that defines the structure of this workarea.
        identity_token: The name of the token in the template that identifies this workarea.
        workareas: A list of child workarea schemas that can exist within this workarea.
        workfiles: A mapping of workfile type to workfile schemas that can exist within this workarea.
        icon_name: The name of the icon to represent this workarea in the UI
    """

    label: str
    template: notgun.templates.PathTemplate
    identity_token: str | None = None
    workareas: list[WorkareaSchema] = dataclasses.field(default_factory=list)
    workfiles: dict[str, WorkfileSchema] = dataclasses.field(default_factory=dict)
    icon_name: str = "fa6s.folder"


@dataclasses.dataclass
class WorkfileSchema:
    """
    Attributes:
        template: The path template that defines the structure of workfiles of this type.
        program: The program that should be launched to open workfiles of this type.
        naming_pattern: the naming pattern for files of this type.
        extension: the file extension for files of this type.
        name_is_editable: whether the name should be user editable when creating a new workfile of this type.
        validation_regex: a regular expression to validate the name of the workfile.
    """

    template: notgun.templates.PathTemplate
    program: notgun.launcher.Program
    naming_pattern: str
    extension: str
    name_is_editable: bool = False
    validation_regex: str = r"^[a-zA-Z][a-zA-Z0-9]+(_[a-zA-Z0-9]+)?$"


class WorkArea:
    def __init__(
        self,
        schema: WorkareaSchema,
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
    def schema(self) -> WorkareaSchema:
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
        self._workfile_groups = None

    def __repr__(self):
        return f"WorkArea(schema={self.schema.label}, path={self.path})"


@dataclasses.dataclass
class Workfile:
    schema: WorkfileSchema
    path: str
    fields: dict[str, int | str]

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
    root_type: WorkareaSchema,
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
        partial_match[root_type.identity_token],  # type: ignore
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

            memo[key].workfiles.append(Workfile(workfile_schema, path, path_fields))

        for group in memo.values():
            yield group
