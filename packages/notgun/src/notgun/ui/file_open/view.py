from qtpy import QtWidgets, QtGui, QtCore

import notgun.ui.workareas.view


class FileOpenView(QtWidgets.QWidget):
    gotoParentClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.goto_parent_button = QtWidgets.QPushButton("..")
        self.workarea_view = notgun.ui.workareas.view.WorkareasView()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.goto_parent_button)
        layout.addWidget(self.workarea_view)

        self.setLayout(layout)

        self.goto_parent_button.clicked.connect(self.gotoParentClicked)
