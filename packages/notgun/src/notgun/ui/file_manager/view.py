from qtpy import QtCore, QtGui, QtWidgets

import notgun.ui.file_manager.model
import notgun.workareas


class WorkareaIconDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._overlay_icon = QtGui.QIcon.fromTheme("document-edit")  # type: ignore

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ):
        super().paint(painter, option, index)

        data = index.data(notgun.ui.file_manager.model.ModelRole.Data)
        if not isinstance(data, notgun.workareas.WorkArea):
            return

        if not data.schema.workfiles:
            return

        styled_option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(styled_option, index)
        style = (
            styled_option.widget.style()
            if styled_option.widget is not None
            else QtWidgets.QApplication.style()
        )
        rect = style.subElementRect(
            QtWidgets.QStyle.SubElement.SE_ItemViewItemDecoration,
            styled_option,
            styled_option.widget,
        )
        if not rect.isValid() or rect.isEmpty():
            return

        icon_rect = QtCore.QRect(0, 0, rect.width() // 2, rect.height() // 2)
        icon_rect.moveCenter(rect.center())
        self._overlay_icon.paint(painter, icon_rect)


class FileManagerView(QtWidgets.QWidget):
    """
    This view presesents the project browser UI like a traditional file manager.
    """

    projectItemClicked = QtCore.Signal(QtCore.QModelIndex)  # type: ignore
    workareaItemClicked = QtCore.Signal(QtCore.QModelIndex)  # type: ignore
    workareaItemActivated = QtCore.Signal(QtCore.QModelIndex)  # type: ignore
    workareaItemRightClicked = QtCore.Signal(QtCore.QModelIndex, QtCore.QPoint)  # type: ignore
    pathItemClicked = QtCore.Signal(QtCore.QModelIndex)  # type: ignore
    searchChanged = QtCore.Signal(str)  # type: ignore

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("file_manager_view")

        self.path_view = QtWidgets.QListView()
        self.path_view.setObjectName("path_view")
        self.path_view.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.path_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.path_view.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.path_view.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.path_view.setWrapping(False)
        self.path_view.setAlternatingRowColors(True)
        self.path_view.setFixedHeight(self.path_view.fontMetrics().height() + 14)
        self.path_view.clicked.connect(self.pathItemClicked)

        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setObjectName("search_bar")
        self.search_bar.textChanged.connect(self.searchChanged)

        self.projects_view = QtWidgets.QListView()
        self.projects_view.setObjectName("project_items_view")
        self.projects_view.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
        self.projects_view.clicked.connect(self.projectItemClicked)

        self.workarea_icons_view = QtWidgets.QListView()
        self.workarea_icons_view.setObjectName("workarea_icons_view")
        self.workarea_icons_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.workarea_icons_view.setIconSize(QtCore.QSize(64, 64))
        self.workarea_icons_view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.workarea_icons_view.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.workarea_icon_delegate = WorkareaIconDelegate()
        self.workarea_icons_view.setItemDelegate(self.workarea_icon_delegate)
        self.workarea_icons_view.clicked.connect(self.workareaItemClicked)
        self.workarea_icons_view.activated.connect(self.workareaItemActivated)

        self.workarea_icons_view.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.workarea_icons_view.customContextMenuRequested.connect(
            self.onWorkareaItemRightClicked
        )

        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.size_slider.setObjectName("size_slider")
        self.size_slider.setRange(32, 512)
        self.size_slider.setSingleStep(32)
        self.size_slider.setValue(64)
        self.size_slider.valueChanged.connect(self.onIconSizeChanged)

        grid_layout = QtWidgets.QGridLayout()  #
        grid_layout.addWidget(self.path_view, 0, 1)
        grid_layout.addWidget(self.search_bar, 0, 2)
        grid_layout.addWidget(self.projects_view, 1, 0)
        grid_layout.addWidget(self.workarea_icons_view, 1, 1, 1, 2)
        grid_layout.addWidget(self.size_slider, 2, 2)

        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 5)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setRowStretch(0, 0)
        grid_layout.setRowStretch(1, 1)

        self.setLayout(grid_layout)

    def enableListMode(self):
        self.workarea_icons_view.setFlow(QtWidgets.QListView.Flow.TopToBottom)
        self.workarea_icons_view.setViewMode(QtWidgets.QListView.ViewMode.ListMode)

    def enableIconMode(self):
        self.workarea_icons_view.setFlow(QtWidgets.QListView.Flow.LeftToRight)
        self.workarea_icons_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)

    def setPathModel(self, model):
        self.path_view.setModel(model)

    def setWorkareaModel(self, model):
        self.workarea_icons_view.setModel(model)

    def setWorkareaRootIndex(self, index):
        self.workarea_icons_view.setRootIndex(index)

    def setProjectsModel(self, model):
        self.projects_view.setModel(model)

    def onIconSizeChanged(self, value):
        self.workarea_icons_view.setIconSize(QtCore.QSize(value, value))

    def onWorkareaItemRightClicked(self, pos):
        index = self.workarea_icons_view.indexAt(pos)
        # NOTE: don't reject invalid index, as it can be used to show context menu for white space.
        global_pos = self.workarea_icons_view.viewport().mapToGlobal(pos)
        self.workareaItemRightClicked.emit(index, global_pos)
