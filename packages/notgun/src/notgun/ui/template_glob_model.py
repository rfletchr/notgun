"""
This model uses a template to scan for all workarea directories in a project and lays them out in a tree structure based on a list of grouping fields.
e.g. (sequence, shot, task, app)

This model does not deal with files

The model has 2 types of items:
- Group: represents a parent item that groups other items based on a field value. e.g. sequence "seq01"
- Workarea: represents a leaf item that corresponds to an actual workarea on disk.


"""

import os
import enum

import qtpy.QtGui

import notgun.templates


class ItemTypes(enum.Enum):
    Group = 1
    Workarea = 2


class ModelRoles(enum.IntEnum):
    ItemTypeRole = qtpy.QtCore.Qt.ItemDataRole.UserRole + 1
    ItemDataRole = qtpy.QtCore.Qt.ItemDataRole.UserRole + 2


class ModelItem(qtpy.QtGui.QStandardItem):
    def __init__(self, item_type: ItemTypes, name: str, data=None):
        super().__init__(name)
        self.setData(item_type, ModelRoles.ItemTypeRole)
        self.setData(data, ModelRoles.ItemDataRole)


def scan(
    root: qtpy.QtGui.QStandardItem,
    template: notgun.templates.PathTemplate,
    fields: dict[str, str],
    identity_field: str,
    grouping_fields: list[str],
) -> None:
    """
    Scans for workareas based on the provided template and fields, and organizes them into a tree structure based on the grouping fields.

    Args:
        root: The root item to populate with the scanned workareas.
        template: The path template to scan with.
        fields: The fields to use for scanning the template.
        grouping_fields: The fields to group the results by in the tree structure.
    """

    potential_workareas = template.glob(fields)

    item_cache: dict[tuple[str, str], ModelItem] = {}

    for workarea_path in potential_workareas:
        if not os.path.isdir(workarea_path):
            continue

        workarea_fields = template.fullmatch(workarea_path)
        if not workarea_fields:
            continue

        current_item = root

        for grouping_field in grouping_fields:
            grouping_value = workarea_fields[grouping_field]
            cache_key = (grouping_field, grouping_value)
            if cache_key in item_cache:
                current_item = item_cache[cache_key]
            else:
                new_item = ModelItem(ItemTypes.Group, grouping_value)
                current_item.appendRow(new_item)
                item_cache[cache_key] = new_item
                current_item = new_item

        workarea_item = ModelItem(
            ItemTypes.Workarea,
            workarea_fields[identity_field],
            data=workarea_path,
        )

        current_item.appendRow(workarea_item)


class WorkareaModel(qtpy.QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["Name"])

    def scan(
        self,
        template: notgun.templates.PathTemplate,
        fields: dict[str, str],
        identity_field: str,
        grouping_fields: list[str],
    ) -> None:
        self.clear()
        self.setHorizontalHeaderLabels(["Name"])
        scan(
            self.invisibleRootItem(),
            template,
            fields,
            identity_field,
            grouping_fields,
        )
