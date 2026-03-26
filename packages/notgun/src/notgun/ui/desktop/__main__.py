import argparse
import sys
import logging


def parse_args():
    parser = argparse.ArgumentParser(description="Notgun Desktop")
    parser.add_argument(
        "--projects-dir",
        type=str,
        required=False,
    )
    return parser.parse_args()


def main(args):
    from qtpy import QtWidgets
    import notgun.ui.desktop.controller

    logging.basicConfig()

    app = QtWidgets.QApplication()
    # print("app start")

    # if args.projects_dir is None:
    #     projects_dir = QtWidgets.QFileDialog.getExistingDirectory(
    #         None,
    #         "Select Projects Directory",
    #     )
    #     if not projects_dir:
    #         print("No projects directory selected. Exiting.")
    #         return
    # else:
    #     projects_dir = args.projects_dir

    controller = notgun.ui.desktop.controller.DesktopController("/home/user/Development/notgun/example")
    app.aboutToQuit.connect(controller.shutdown)
    controller.view.show()
    controller.populate()



    return app.exec()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(main(args))
