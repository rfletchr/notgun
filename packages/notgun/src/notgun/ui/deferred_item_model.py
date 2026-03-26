from __future__ import annotations
import typing

from qtpy import QtCore, QtGui


class DeferredItem(QtGui.QStandardItem):
    """Base class for items that support deferred (lazy) child loading.

    Subclass this and override :meth:`canFetchMore` and :meth:`fetch`
    to implement lazy loading of children.

    Example::

        class MyItem(DeferredItem):
            def __init__(self, node):
                super().__init__(node.name)
                self._node = node
                self._fetched = False

            def canFetchMore(self) -> bool:
                return not self._fetched

            def fetch(self) -> None:
                self._fetched = True
                for child in self._node.children():
                    self.appendRow(MyItem(child))
    """

    def itemHasChildren(self) -> bool:
        """Return True if this item may have children.

        Called by the model's ``hasChildren``. The default returns True when
        :meth:`canFetchMore` is True (children not yet loaded) or when the
        item already has rows (children already loaded). Override if you need
        finer control — for example, to always return False for leaf nodes
        before any fetch has occurred.
        """
        return self.canFetchMore() or self.rowCount() > 0

    def canFetchMore(self) -> bool:
        """Return True if this item has children that have not been loaded yet.

        The model will call :meth:`fetch` when a view requests more data.
        Once all children are loaded this should return False so the model
        stops asking.
        """
        return False

    def fetch(self) -> None:
        """Load and append child items.

        Subclasses should call ``appendRow`` / ``appendRows`` here to add
        children to *self*. This is called by the model whenever a view
        triggers ``fetchMore`` for this item's index.
        """

    def uniqueId(self) -> str:
        raise NotImplementedError

    def hasUniqueId(self) -> bool:
        return False


class DeferredItemModel(QtGui.QStandardItemModel):
    """A QStandardItemModel that delegates lazy loading to its items.

    When items in the model are instances of :class:`DeferredItem`, the model
    forwards ``hasChildren``, ``canFetchMore``, and ``fetchMore`` calls to the
    item itself. Non-:class:`DeferredItem` items behave as normal
    ``QStandardItem`` entries.

    Items that return ``True`` from :meth:`DeferredItem.hasUniqueId` are
    automatically registered in an internal lookup table as they are inserted
    and unregistered when they are removed. Use :meth:`itemById` to retrieve
    them by id.

    Use :meth:`fetchAll` before activating a filter so that proxy models have
    the full tree available to search against.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._id_lookup: dict[str, DeferredItem] = {}
        self.rowsInserted.connect(self._onRowsInserted)
        self.rowsAboutToBeRemoved.connect(self._onRowsAboutToBeRemoved)

    # ------------------------------------------------------------------
    # Unique-id lookup

    def itemById(self, uid: str) -> typing.Union[DeferredItem, None]:
        """Return the :class:`DeferredItem` registered under *uid*, or None."""
        return self._id_lookup.get(uid)

    def _registerItem(self, item: QtGui.QStandardItem) -> None:
        if isinstance(item, DeferredItem) and item.hasUniqueId():
            self._id_lookup[item.uniqueId()] = item

    def _unregisterSubtree(self, item: QtGui.QStandardItem) -> None:
        """Remove *item* and all already-loaded descendants from the lookup."""
        if isinstance(item, DeferredItem) and item.hasUniqueId():
            self._id_lookup.pop(item.uniqueId(), None)
        for row in range(item.rowCount()):
            self._unregisterSubtree(item.child(row))

    def _onRowsInserted(
        self, parent: QtCore.QModelIndex, first: int, last: int
    ) -> None:
        parent_item = self.itemFromIndex(parent) or self.invisibleRootItem()
        for row in range(first, last + 1):
            self._registerItem(parent_item.child(row))

    def _onRowsAboutToBeRemoved(
        self, parent: QtCore.QModelIndex, first: int, last: int
    ) -> None:
        parent_item = self.itemFromIndex(parent) or self.invisibleRootItem()
        for row in range(first, last + 1):
            child = parent_item.child(row)
            if child is not None:
                self._unregisterSubtree(child)

    # ------------------------------------------------------------------

    def hasChildren(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        item = self.itemFromIndex(parent)
        if isinstance(item, DeferredItem):
            return item.itemHasChildren()
        return super().hasChildren(parent)

    def canFetchMore(self, parent: QtCore.QModelIndex) -> bool:
        item = self.itemFromIndex(parent)
        if isinstance(item, DeferredItem):
            return item.canFetchMore()
        return super().canFetchMore(parent)

    def fetchMore(self, parent: QtCore.QModelIndex) -> None:
        item = self.itemFromIndex(parent)
        if isinstance(item, DeferredItem):
            item.fetch()
        else:
            super().fetchMore(parent)

    def fetchAll(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> None:
        """Recursively fetch all deferred children in the tree.

        Call this before activating a filter on a proxy model so that the
        proxy has the full tree available to search against. For large or
        expensive trees, consider calling it only when the user starts typing
        rather than upfront.
        """
        if self.canFetchMore(parent):
            self.fetchMore(parent)

        for row in range(self.rowCount(parent)):
            self.fetchAll(self.index(row, 0, parent))


class DeferredProxyModel(QtCore.QSortFilterProxyModel):
    """A sort/filter proxy that eagerly fetches deferred children when filtering.

    When the filter pattern is non-empty, :meth:`fetchAll` is called on the
    source :class:`DeferredItemModel` so that unloaded children are visible to
    the filter. When the filter is cleared the tree returns to lazy behaviour.

    The source model must be a :class:`DeferredItemModel`.
    """

    def setFilterFixedString(self, pattern: str) -> None:
        self._maybeEagerFetch(pattern)
        super().setFilterFixedString(pattern)

    def setFilterRegularExpression(self, pattern) -> None:
        text = pattern if isinstance(pattern, str) else pattern.pattern()
        self._maybeEagerFetch(text)
        super().setFilterRegularExpression(pattern)

    def setFilterWildcard(self, pattern: str) -> None:
        self._maybeEagerFetch(pattern)
        super().setFilterWildcard(pattern)

    def _maybeEagerFetch(self, pattern: str) -> None:
        if not pattern:
            return
        source = self.sourceModel()
        if isinstance(source, DeferredItemModel):
            source.fetchAll()
