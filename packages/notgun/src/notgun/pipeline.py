import json
import os
import typing
import notgun.context
import notgun.templates
import notgun.adapters

if typing.TYPE_CHECKING:
    import notgun.launcher

EPISODIC_CONTEXT_NAMES = (
    "project",
    "episode",
    "sequence",
    "asset_type",
    "shot",
    "asset",
    "shot_task",
    "asset_task",
)

DEFAULT_CONTEXT_NAMES = (
    "project",
    "sequence",
    "asset_type",
    "shot",
    "asset",
    "shot_task",
    "asset_task",
)

__CURRENT_PIPELINE: "Pipeline|None" = None


def get_current():
    return __CURRENT_PIPELINE


def set_current(pipeline: "Pipeline|None"):
    global __CURRENT_PIPELINE
    __CURRENT_PIPELINE = pipeline


class Pipeline:
    def __init__(
        self,
        projects_root: str,
        project_name: str,
        templates: notgun.templates.PathTemplateDict,
        context_names: list[str] | tuple[str, ...],
        programs: dict[str, "notgun.launcher.Program"],
    ):
        self._templates = templates.copy()
        self._name = project_name
        self._root = projects_root
        self._context_names = tuple[str, ...](context_names)
        self._programs = dict(programs)
        self._app_adpater: notgun.adapters.ApplicationAdapter | None = None

        for name in context_names:
            if name not in templates and name != "episode":
                raise KeyError(f"Missing Template: {name}")

    def name(self):
        return self._name

    def directory(self):
        return os.path.join(self._root, self._name)

    def templates(self):
        return self._templates.copy()

    def programs(self) -> dict[str, "notgun.launcher.Program"]:
        return self._programs.copy()

    def app(self) -> notgun.adapters.ApplicationAdapter:
        if self._app_adpater is None:
            raise ValueError("Host adapater not set")

        return self._app_adpater

    def set_app(self, app: notgun.adapters.ApplicationAdapter):
        self._app_adpater = app

    def metadata(self) -> dict:
        path = os.path.join(self._root, self._name, "init", "project.json")
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {"name": self._name}

    def context_from_path(self, path: str):
        for template_name in reversed(self._context_names):
            fields = self._templates[template_name].parse(path)
            if not fields:
                continue

            return notgun.context.Context(**fields)

    def path_from_context(self, context: notgun.context.Context):
        fields = context.as_dict()
        field_names = set(fields.keys())

        for template_name in reversed(self._context_names):
            template = typing.cast(
                notgun.templates.PathTemplate, self._templates[template_name]
            )
            if template.token_names().issubset(field_names):
                return template.format(fields)
