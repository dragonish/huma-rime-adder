#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from type.dict import CodeTableUnit


class WordTableModel(QAbstractTableModel):
    """重码词条的表格模型"""

    def __init__(self) -> None:
        super().__init__()
        self._data: list[CodeTableUnit] = []

    def _getColKey(self, index: QModelIndex):
        colKey = "word"
        match index.column():
            case 0:
                colKey = "word"
            case 1:
                colKey = "weight"
            case 2:
                colKey = "source"
            case 3:
                colKey = "range"
        return colKey

    def rowCount(self, parent=None) -> int:
        return len(self._data)

    def columnCount(self, parent=None) -> int:
        return 4

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        value = self._data[index.row()][self._getColKey(index)]
        if isinstance(value, bool):
            return "是" if value else "否"
        return str(value)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            # 设置列标题
            match section:
                case 0:
                    return "词条"
                case 1:
                    return "权重"
                case 2:
                    return "来源"
                case 3:
                    return "常用"
        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][self._getColKey(index)] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def updateData(self, newData: list[CodeTableUnit]) -> None:
        """更新数据

        Args:
            new_data (list[CodeTableUnit]): 新数据
        """
        self.beginResetModel()
        self._data = newData
        self.endResetModel()

    def clearData(self) -> None:
        """清空数据"""
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def getFirstRowWeight(self) -> int:
        """获取第一行的 `weight` 列值，没有时返回 `0`

        Returns:
            int: 第一行的 `weight` 值，如果没有数据则返回 `0`
        """
        if not self._data:
            return 0

        try:
            weight = self._data[0].get("weight")
            return int(weight) if weight is not None else 0
        except (ValueError, TypeError):
            return 0

    def getLastRowWeight(self) -> int:
        """获取最后一行的 `weight` 列值，没有时返回 `0`

        Returns:
            int: 最后一行的 `weight` 值，如果没有数据则返回 `0`
        """
        if not self._data:
            return 0

        try:
            weight = self._data[-1].get("weight")
            return int(weight) if weight is not None else 0
        except (ValueError, TypeError):
            return 0
