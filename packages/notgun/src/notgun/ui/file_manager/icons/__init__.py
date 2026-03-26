def get_icon(name: str) -> "QtGui.QIcon":
    from qtpy import QtGui
    import importlib.resources

    with importlib.resources.open_binary("notgun.ui.file_manager.icons", name) as f:
        data = f.read()
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(data)
    return QtGui.QIcon(pixmap)
