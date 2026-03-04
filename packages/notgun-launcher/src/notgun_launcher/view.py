import qtawesome as qta

from qtpy.QtCore import Qt, QModelIndex, QSize, Signal
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListView,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

_HEADER_ICON_SIZE = 64
_BUTTON_ICON_SIZE = QSize(32, 32)


def _iconButton(icon_name: str) -> QPushButton:
    btn = QPushButton()
    btn.setIcon(qta.icon(icon_name, color="darkgrey"))
    btn.setIconSize(_BUTTON_ICON_SIZE)
    btn.setMinimumHeight(_BUTTON_ICON_SIZE.height())
    btn.setMinimumWidth(_BUTTON_ICON_SIZE.width())
    btn.setFlat(True)
    return btn


class ProjectsView(QWidget):
    activated = Signal(QModelIndex)
    refreshRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        _refreshButton = _iconButton("mdi6.refresh")

        _title = QLabel("Projects")
        _title.setObjectName("viewTitle")

        header = QHBoxLayout()
        header.addWidget(_title)
        header.addStretch()
        header.addWidget(_refreshButton)

        self._listView = QListView()
        self._listView.setObjectName("projectsList")
        self._listView.setIconSize(QSize(_HEADER_ICON_SIZE, _HEADER_ICON_SIZE))
        self._listView.setUniformItemSizes(True)
        self._listView.setSelectionMode(self._listView.SelectionMode.NoSelection)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(self._listView)

        self._listView.activated.connect(self.activated)
        self._listView.clicked.connect(self.activated)
        _refreshButton.clicked.connect(self.refreshRequested)

    def setModel(self, model):
        self._listView.setModel(model)


class ProgramsView(QWidget):
    activated = Signal(QModelIndex)
    backRequested = Signal()
    refreshRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._iconLabel = QLabel()
        self._iconLabel.hide()
        self._nameLabel = QLabel()
        self._nameLabel.setObjectName("viewTitle")

        _backButton = _iconButton("ph.skip-back-fill")
        _refreshButton = _iconButton("mdi6.refresh")

        header = QHBoxLayout()
        header.addWidget(_backButton)
        header.addWidget(self._iconLabel)
        header.addWidget(self._nameLabel)
        header.addStretch()
        header.addWidget(_refreshButton)

        self._listView = QListView()
        self._listView.setObjectName("programsList")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(header)
        layout.addWidget(self._listView)

        self._listView.activated.connect(self.activated)
        _backButton.clicked.connect(self.backRequested)
        _refreshButton.clicked.connect(self.refreshRequested)

    def setModel(self, model):
        self._listView.setModel(model)

    def setLabel(self, text: str):
        self._nameLabel.setText(text)

    def setIcon(self, pixmap: QPixmap | None):
        if pixmap is not None and not pixmap.isNull():
            self._iconLabel.setPixmap(
                pixmap.scaled(
                    _HEADER_ICON_SIZE,
                    _HEADER_ICON_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self._iconLabel.show()
        else:
            self._iconLabel.hide()


class MainView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.projectsView = ProjectsView()
        self.programsView = ProgramsView()

        self._stack = QStackedWidget()
        self._stack.addWidget(self.projectsView)
        self._stack.addWidget(self.programsView)

        layout = QVBoxLayout(self)
        layout.addWidget(self._stack)

        self.showProjectList()

    def showProjectList(self):
        self._stack.setCurrentIndex(0)

    def showProgramList(self):
        self._stack.setCurrentIndex(1)
