import os
import dataclasses
import subprocess


DEFAULT_CLEAR_LIST = ("PYTHONPATH",)


@dataclasses.dataclass()
class Program:
    label: str
    executable: str
    args: list[str]
    set_env: dict[str, str] = dataclasses.field(default_factory=dict)
    append_env: dict[str, str] = dataclasses.field(default_factory=dict)
    prefix_env: dict[str, str] = dataclasses.field(default_factory=dict)
    clear_env: tuple[str, ...] = dataclasses.field(default=DEFAULT_CLEAR_LIST)


def launch_program(program: Program, env: dict[str, str] | None = None):
    env = env or os.environ.copy()
    for name in program.clear_env:
        env.pop(name, None)

    for name, value in program.append_env.items():
        value = str(value)

        current_value = env.get(name)
        if current_value:
            env[name] = f"{current_value}{os.pathsep}{value}"
        else:
            env[name] = value

    for name, value in program.prefix_env.items():
        current_value = env.get(name)
        if current_value:
            env[name] = f"{value}{os.pathsep}{current_value}"

    for name, value in program.set_env.items():
        env[name] = str(value)

    subprocess.run([program.executable, *program.args], env=env, start_new_session=True)
