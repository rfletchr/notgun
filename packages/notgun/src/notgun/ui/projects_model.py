import typing
import os
import enum
import dataclasses

from qtpy import QtGui

import notgun.bootstrap
import notgun.projects


class ProjectStatus(enum.Enum):
    OK = enum.auto()
    LOCKED = enum.auto()
    ERROR = enum.auto()


@dataclasses.dataclass
class ProjectItem:
    name: str
    status: ProjectStatus
    pipeline: notgun.projects.Project | None = None
    error: str | None = None
    pixmap: QtGui.QPixmap | None = None


def scan_directory(projects_dir: str, icon_size: int) -> typing.Iterator[ProjectItem]:
    for name in sorted(os.listdir(projects_dir)):
        if os.path.isfile(os.path.join(projects_dir, name)):
            continue

        status = ProjectStatus.OK
        pipeline = None
        label = name
        error = None
        pixmap = None

        if os.access(os.path.join(projects_dir, name), os.X_OK):
            data = notgun.bootstrap.BootstrapData(projects_dir, name)
            try:
                pipeline = notgun.bootstrap.init(data)
                label = pipeline.label()
                image_path = pipeline.image_path()
                if os.path.isfile(image_path):
                    pixmap = QtGui.QPixmap(image_path)
                status = ProjectStatus.OK

            except Exception as e:
                status = ProjectStatus.ERROR
                error = str(e)
        else:
            status = ProjectStatus.LOCKED

        yield ProjectItem(label, status, pipeline, error, pixmap)
