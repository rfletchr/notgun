import argparse
import sys
import logging


def parse_args():
    parser = argparse.ArgumentParser(description="Notgun Desktop")
    parser.add_argument(
        "--projects-dir",
        type=str,
        required=False,
        default="/mnt/projects",
    )
    return parser.parse_args()


def main(args):
    from qtpy import QtWidgets
    import notgun.ui.desktop.controller

    logging.basicConfig()

    app = QtWidgets.QApplication()
    projects_dir = args.projects_dir

    # use a standard icon for the apps icon for now
    app.setApplicationName("Notgun Desktop")
    app.setWindowIcon(app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

    controller = notgun.ui.desktop.controller.DesktopController(
        projects_dir=projects_dir,
    )
    app.aboutToQuit.connect(controller.shutdown)
    controller.view.show()
    controller.populate()

    return app.exec()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(main(args))
