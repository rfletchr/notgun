import importlib.util
import os
import json
import typing

import notgun.projects

BOOTSTRAP_ENV_VAR = "NOTGUN_BOOTSTRAP_PAYLOAD"


class BootstrapData(typing.NamedTuple):
    projects_dir: str
    project_name: str

    @classmethod
    def from_env(cls):
        payload = os.environ[BOOTSTRAP_ENV_VAR]
        data = json.loads(payload)
        return cls(data["projects_dir"], data["project_name"])

    def to_dict(self):
        return {
            "projects_dir": self.projects_dir,
            "project_name": self.project_name,
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_dict())


def has_bootstrap(projects_dir: str, project_name: str) -> bool:
    bootstrap_file = os.path.join(projects_dir, project_name, "init", "bootstrap.py")
    return os.path.isfile(bootstrap_file)


def init(data: BootstrapData, make_current: bool = False) -> notgun.projects.Project:
    bootstrap_file = os.path.join(
        data.projects_dir, data.project_name, "init", "bootstrap.py"
    )

    spec = importlib.util.spec_from_file_location(
        "_notgun_project_bootstrap", bootstrap_file
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load bootstrap file: {bootstrap_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pipeline = module.bootstrap(data)

    if pipeline and make_current:
        notgun.projects.set_current(pipeline)

    return pipeline


def init_from_env(make_current: bool = True) -> notgun.projects.Project:
    data = BootstrapData.from_env()
    return init(data, make_current=make_current)
