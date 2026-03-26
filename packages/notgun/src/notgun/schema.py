from __future__ import annotations
import typing
import dataclasses

import notgun.templates

if typing.TYPE_CHECKING:
    import notgun.launcher

DEFAULT_VALIDATION_REGEX = r"^[a-zA-Z][a-zA-Z0-9]+(_[a-zA-Z0-9]+)?$"


@dataclasses.dataclass
class PublishSchema:
    template: notgun.templates.PathTemplate
    publish_type: str
    default_fields: dict[str, typing.Any]


PublishSchemaKey = tuple[tuple[str, ...], tuple[str, ...]]
PublishSchemaDict = dict[PublishSchemaKey, PublishSchema]


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
    parent: WorkareaSchema
    name_is_editable: bool = False
    validation_regex: str = DEFAULT_VALIDATION_REGEX


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
    identity_token: typing.Union[str, None] = None
    workareas: list[WorkareaSchema] = dataclasses.field(default_factory=list)
    workfiles: dict[str, WorkfileSchema] = dataclasses.field(default_factory=dict)
    publishes: PublishSchemaDict = dataclasses.field(default_factory=dict)
    parent: typing.Union[WorkareaSchema, None] = None

    def add_child(
        self,
        label: str,
        template: notgun.templates.PathTemplate,
        identity_token: typing.Union[str, None] = None,
    ) -> WorkareaSchema:
        result = WorkareaSchema(
            label,
            template,
            identity_token=identity_token,
            parent=self,
        )
        self.workareas.append(result)
        return result

    def add_workfile(
        self,
        name: str,
        template: notgun.templates.PathTemplate,
        program: notgun.launcher.Program,
        naming_pattern: str,
        extension: str,
        name_is_editable: bool = False,
        validation_regex: str = DEFAULT_VALIDATION_REGEX,
    ) -> WorkfileSchema:
        result = self.workfiles[name] = WorkfileSchema(
            template,
            program,
            naming_pattern,
            extension,
            self,
            name_is_editable,
            validation_regex=validation_regex,
        )
        return result

    def add_publish(
        self,
        workfile_names: tuple[str, ...],
        task_names: tuple[str, ...],
        template: notgun.templates.PathTemplate,
        publish_type: str,
        default_fields: dict[str, typing.Any],
    ) -> PublishSchema:
        result = PublishSchema(template, publish_type, dict(**default_fields))

        key = (tuple(workfile_names), tuple(task_names))
        self.publishes[key] = result
