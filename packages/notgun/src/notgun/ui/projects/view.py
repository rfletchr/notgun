import qtawesome as qta
from qtpy import QtGui, QtCore, QtWidgets

import notgun.ui.projects.model


DEFAULT_SIZE = 128


class ProjectsView(QtWidgets.QWidget):
    activated = QtCore.Signal(QtCore.QModelIndex)
    clicked = QtCore.Signal(QtCore.QModelIndex)
    previewSizeChanged = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.item_delegate = ProjectsDelegate(DEFAULT_SIZE)

        self.view = QtWidgets.QListView()
        # self.view.setResizeMode(QtWidgets.QListView.ResizeMode.Fixed)
        self.view.setUniformItemSizes(True)
        self.view.setItemDelegate(self.item_delegate)

        self.view.activated.connect(self.activated)
        self.view.clicked.connect(self.onViewClicked)

        self.size_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.size_slider.setRange(64, 512)
        self.size_slider.setValue(DEFAULT_SIZE)
        self.size_slider.setSingleStep(64)
        self.size_slider.setTickInterval(64)
        self.size_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)

        # enable snapping to ticks
        self.size_slider.setPageStep(64)

        self.size_slider.valueChanged.connect(self.onSizeSliderChanged)
        self.size_slider.sliderReleased.connect(self.onSizeSliderReleased)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(self.size_slider)

    def onViewClicked(self, index: QtCore.QModelIndex):
        if not index.isValid():
            return

        self.clicked.emit(index)

    def setModel(self, model: QtCore.QAbstractItemModel):
        self.view.setModel(model)

    def onSizeSliderChanged(self, value: int):
        self.item_delegate.setDesiredHeight(value)
        self.view.reset()

    def onSizeSliderReleased(self):
        self.previewSizeChanged.emit(self.size_slider.value())


class ProjectsDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate for rendering project items in the ProjectsView.

    The image is given a square aspect ratio based on the desired height, and the text is rendered to the right in the remaining space.
    """

    def __init__(self, desired_height: int, parent=None):
        super().__init__(parent)
        self._desired_height = desired_height
        self._error_icon = qta.icon("ei.error", color="red")
        self._lock_icon = qta.icon("fa6s.lock", color="darkgray")

    def setDesiredHeight(self, height: int):
        self._desired_height = height

    def sizeHint(
        self,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ) -> QtCore.QSize:

        return QtCore.QSize(self._desired_height, self._desired_height)

    def paint(
        self,
        painter: QtGui.QPainter,
        option: QtWidgets.QStyleOptionViewItem,
        index: QtCore.QModelIndex,
    ):
        project: notgun.ui.projects.model.ProjectItem = index.data(
            QtCore.Qt.ItemDataRole.UserRole
        )

        if project is None:
            return super().paint(painter, option, index)

        # use a dark bg color
        base_bg = option.palette.color(QtGui.QPalette.ColorRole.Dark)

        # modulate the base bg color to give us an alternate color for even/odd rows
        if index.row() % 2 == 0:
            bg = base_bg
        else:
            # make the alternate color a bit lighter
            bg = QtGui.QColor(base_bg)
            bg.setAlpha(200)

        # if we're selected pick a pen using the Highlight color
        if option.state & QtWidgets.QStyle.StateFlag.State_Selected:
            color = option.palette.color(QtGui.QPalette.ColorRole.Highlight)
            color.setAlpha(128)
            pen = QtGui.QPen(color)
            pen.setWidth(2)
        else:
            pen = QtGui.QPen(QtCore.Qt.PenStyle.NoPen)

        # shrink the rect to add some padding
        rect = option.rect.adjusted(4, 4, -4, -4)

        # fill the background with a rounded rect
        painter.save()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setBrush(QtGui.QBrush(bg))
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 8, 8)
        painter.restore()

        # adjust the rect into a square for the image and add a little padding
        image_rect = QtCore.QRect(rect)
        image_rect.setWidth(image_rect.height())
        image_rect.adjust(4, 4, -4, -4)

        # if we have an image, draw it making sure to maintain the aspect ratio and center it in the image rect
        pixmap = index.data(QtCore.Qt.ItemDataRole.DecorationRole)
        if pixmap is not None:
            pixmap = pixmap.scaled(
                image_rect.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            pixmap_rect = QtCore.QRect(image_rect)
            pixmap_rect.setSize(pixmap.size())
            pixmap_rect.moveCenter(image_rect.center())

            # make a clip path based on the images actual size to give it rounded corners
            path = QtGui.QPainterPath()
            path.addRoundedRect(pixmap_rect, 8, 8)

            painter.save()
            painter.setClipPath(path)
            painter.drawPixmap(pixmap_rect, pixmap)
            painter.restore()
        else:
            # if we don't have an image, draw a placeholder rect
            painter.save()
            # use the shadow color for the placeholder
            colour = option.palette.color(QtGui.QPalette.ColorRole.Shadow)
            painter.setBrush(QtGui.QBrush(colour))
            painter.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
            painter.drawRoundedRect(image_rect, 8, 8)

            if project.status == notgun.ui.projects.model.ProjectStatus.LOCKED:
                icon = self._lock_icon
            elif project.status == notgun.ui.projects.model.ProjectStatus.ERROR:
                icon = self._error_icon
            else:
                icon = None

            if icon is not None:
                pixmap = icon.pixmap(image_rect.size() * 0.75)
                pixmap_rect = QtCore.QRect(image_rect)
                pixmap_rect.setSize(pixmap.size())
                pixmap_rect.moveCenter(image_rect.center())
                painter.drawPixmap(pixmap_rect, pixmap)

            painter.restore()

        # draw the text in the remaining space to the right of the image
        text_rect = QtCore.QRect(rect)
        text_rect.setLeft(image_rect.right() + 8)

        text = index.data(QtCore.Qt.ItemDataRole.DisplayRole)
        if text is not None:
            painter.save()
            painter.setPen(
                QtGui.QPen(option.palette.color(QtGui.QPalette.ColorRole.Text))
            )
            painter.drawText(
                text_rect,
                QtCore.Qt.AlignmentFlag.AlignVCenter
                | QtCore.Qt.AlignmentFlag.AlignLeft,
                text,
            )
            painter.restore()
