import argparse
import os
import sys
import qtawesome as qta

from qtpy.QtWidgets import QApplication

from notgun_launcher.controller import LauncherController

PROJECTS_DIR_ENV = "NOTGUN_PROJECTS_DIR"


def _load_stylesheet() -> str:
    path = os.path.join(os.path.dirname(__file__), "stylesheet.qss")
    print(path)
    try:
        with open(path) as f:
            print("qss loaded")

            return f.read()
    except OSError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="notgun launcher")
    parser.add_argument("projects_dir")
    args = parser.parse_args()

    projects_dir = args.projects_dir or os.environ.get(PROJECTS_DIR_ENV)
    if not projects_dir:
        print(
            f"error: provide projects_dir argument or set {PROJECTS_DIR_ENV}",
            file=sys.stderr,
        )
        return 1
    os.environ["QT_SCALE_FACTOR"] = "1.5"
    app = QApplication()
    app.setApplicationName("Notgun")
    app.setStyleSheet(_load_stylesheet())

    icon = qta.icon("fa6s.peace")
    app.setWindowIcon(icon)

    controller = LauncherController(projects_dir)
    controller.window.show()
    controller.window.setWindowIcon(icon)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
