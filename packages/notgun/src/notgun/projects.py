from notgun.launcher import Program
import json
import os
import typing
import notgun.templates
import notgun.adapters
import notgun.workareas

if typing.TYPE_CHECKING:
    import notgun.launcher


__CURRENT_PIPELINE: "Project|None" = None


def get_current():
    return __CURRENT_PIPELINE


def set_current(pipeline: "Project|None"):
    global __CURRENT_PIPELINE
    __CURRENT_PIPELINE = pipeline


class Project:
    def __init__(
        self,
        projects_root: str,
        project_name: str,
        templates: notgun.templates.PathTemplateDict,
        programs: dict[str, "notgun.launcher.Program"],
        root_workarea: notgun.workareas.WorkArea,
    ):
        self._templates = templates.copy()
        self._name = project_name
        self._root = projects_root
        self._programs = dict[str, Program](programs)
        self._app_adpater: notgun.adapters.ApplicationAdapter | None = None
        self._root_workarea: notgun.workareas.WorkArea = root_workarea
        self._metadata_cache: dict | None = None

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
        if self._metadata_cache is not None:
            return self._metadata_cache

        path = os.path.join(self._root, self._name, "init", "project.json")
        try:
            with open(path) as f:
                self._metadata_cache = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._metadata_cache = {"name": self._name}

        return self._metadata_cache

    def label(self) -> str:
        meta = self.metadata()
        return meta.get("name", self._name)

    def image_path(self):
        meta = self.metadata()
        image_path = meta.get("image")
        if not image_path:
            return None
        if not os.path.isabs(image_path):
            image_path = os.path.join(self._root, self._name, "init", image_path)

        return image_path

    def workarea(self) -> notgun.workareas.WorkArea:
        return self._root_workarea

    def workarea_from_path(self, path: str):
        return notgun.workareas.workarea_from_path(path, self._root_workarea.schema)
