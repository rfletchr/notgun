from keyring.backend import log
import os
import argparse
import dataclasses
import subprocess
import glob
import json
import sys
import tempfile
import time
import logging

logger = logging.getLogger(__name__)

DEFAULT_CLEAR_LIST = ("PYTHONPATH",)


@dataclasses.dataclass(frozen=True)
class ProcessInfo:
    label: str
    pid: int
    log_file: str
    timestamp: int
    return_code: int | None = None

    @classmethod
    def iter(cls, log_directory: str):
        for metadata_file in glob.glob(os.path.join(log_directory, "*.json")):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            label = metadata["label"]
            pid = metadata["pid"]

            base_name = os.path.splitext(os.path.basename(metadata_file))[0]
            log_file = os.path.join(log_directory, f"{base_name}.log")
            return_code_file = os.path.join(log_directory, f"{base_name}.returncode")

            timestamp_str = base_name.split("_")[0]
            timestamp = int(timestamp_str)

            return_code = None
            if os.path.isfile(return_code_file):
                with open(return_code_file, "r") as f:
                    return_code_str = f.read().strip()
                    if return_code_str.isdigit():
                        return_code = int(return_code_str)

            yield cls(label, pid, log_file, timestamp, return_code=return_code)


@dataclasses.dataclass()
class Program:
    label: str
    executable: str
    args: list[str]
    file_types: list[str]

    set_env: dict[str, str] = dataclasses.field(default_factory=dict)
    append_env: dict[str, str] = dataclasses.field(default_factory=dict)
    prefix_env: dict[str, str] = dataclasses.field(default_factory=dict)
    clear_env: tuple[str, ...] = dataclasses.field(default=DEFAULT_CLEAR_LIST)


def launch_program(
    program: Program,
    log_directory: str,
    cwd: str | None = None,
    label: str | None = None,
    env: dict[str, str] | None = None,
):

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

    cmd = [program.executable, *program.args]

    cwd = cwd or os.getcwd()
    label = label or program.label
    launch_in_watchdog(label, cmd, env, log_directory, cwd)


def launch_in_watchdog(
    label: str, cmd: list[str], env: dict[str, str], log_directory: str, cwd: str
):
    with tempfile.NamedTemporaryFile("w", delete=False) as spec_fh:
        json.dump(
            {
                "label": label,
                "cmd": cmd,
                "env": env,
            },
            spec_fh,
        )

        watchdog_cmd = [
            sys.executable,
            __file__,
            spec_fh.name,
            log_directory,
        ]

        subprocess.Popen(
            watchdog_cmd,
            start_new_session=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )


def execute_and_watch(label, cmd: list[str], env: dict[str, str], log_directory: str):
    """
    start a process and write its PID to a file in the log directory for monitoring purposes.
    stdout and stderr are redirected to a log file in the same directory.
    """

    os.makedirs(log_directory, exist_ok=True)

    watchdog_pid = os.getpid()
    timestap = int(time.time())

    unique_name = f"{timestap}_{watchdog_pid}"

    metadata_file = os.path.join(log_directory, f"{unique_name}.json")

    with open(metadata_file, "w") as f:
        json.dump({"label": label, "pid": watchdog_pid}, f)

    log_file = os.path.join(log_directory, f"{unique_name}.log")
    return_code_file = os.path.join(log_directory, f"{unique_name}.returncode")

    with open(log_file, "w") as log_fh:
        process = subprocess.Popen(cmd, env=env, stdout=log_fh, stderr=log_fh)

        return_code = process.wait()

        with open(return_code_file, "w") as return_code_fh:
            return_code_fh.write(str(return_code))

        log_fh.write(f"\nProcess exited with return code {return_code}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notgun Process Watchdog")
    parser.add_argument("spec")
    parser.add_argument("log_directory")

    args = parser.parse_args()
    print(f"Spec file: {args.spec}")

    with open(args.spec, "r") as spec_fh:
        spec = json.load(spec_fh)

    cmd = spec["cmd"]
    env = spec["env"]
    label = spec["label"]

    execute_and_watch(label, cmd, env, args.log_directory)
