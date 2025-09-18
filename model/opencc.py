#!/usr/bin/env python
# coding: utf-8

import copy
import re
from PyQt6.QtCore import QAbstractTableModel, QByteArray, QMimeData, QModelIndex, Qt


class OpenCCTableModel(QAbstractTableModel):
    """OpenCC 配置的表格模式"""

    def __init__(self, colName: str, replaceSpace=False) -> None:
        super().__init__()
        self._data: list[str] = []
        self._colName = colName
        self._replaceSpace = replaceSpace

    def rowCount(self, parent=None) -> int:
        return len(self._data)

    def columnCount(self, parent=None) -> int:
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        value = self._data[index.row()]
        if self._replaceSpace:
            return re.sub(r"&nbsp;", " ", value)
        return value

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            # 设置列标题
            match section:
                case 0:
                    return self._colName
        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def insertRows(self, row, count, parent=QModelIndex()):
        if row < 0 or row > self.rowCount() or count < 1:
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        for i in range(count):
            self._data.insert(row, "")
        self.endInsertRows()
        return True

    def flags(self, index):
        defaultFlags = super().flags(index)
        if index.isValid():
            return (
                defaultFlags
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
            )
        return defaultFlags | Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def canDropMimeData(self, data, action, row, column, parent):
        return True

    def mimeTypes(self):
        return ["application/x-myapp-row"]

    def mimeData(self, indexes):
        mimeData = QMimeData()
        encodedData = QByteArray()
        rows = sorted(set(index.row() for index in indexes))
        # 传输被拖动行的行号
        encodedData.append(",".join(str(r) for r in rows).encode())
        mimeData.setData("application/x-myapp-row", encodedData)
        return mimeData

    def dropMimeData(self, mimeData, action, row, column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return False
        if not mimeData.hasFormat("application/x-myapp-row"):
            return False

        if row == -1:
            if parent.isValid():
                row = parent.row()  # 拖动至行条目内部时，视为移动至其上方
            else:
                return False

        encodedData = mimeData.data("application/x-myapp-row")
        rowsStr = bytes(encodedData).decode()
        rows = list(map(int, rowsStr.split(",")))

        # 取所有源行的数据
        movingRws = [self._data[r] for r in rows]

        # 删除旧行，从后往前
        for r in sorted(rows, reverse=True):
            self.beginRemoveRows(QModelIndex(), r, r)
            del self._data[r]
            self.endRemoveRows()

        # 计算插入位置，如果移除行在目标行前，需相应调整目标行索引
        offset = sum(1 for r in rows if r < row)
        insertRow = row - offset
        if insertRow < 0:
            insertRow = 0

        # 插入新行
        for i, row_data in enumerate(movingRws):
            self.beginInsertRows(QModelIndex(), insertRow + i, insertRow + i)
            self._data.insert(insertRow + i, row_data)
            self.endInsertRows()
        return True

    def updateData(self, newData: list[str]) -> None:
        """更新数据

        Args:
            new_data (list[str]): 新数据
        """
        self.beginResetModel()
        self._data = newData
        self.endResetModel()

    def clearData(self) -> None:
        """清空数据"""
        self.beginResetModel()
        self._data = []
        self.endResetModel()

    def appendRow(self, strData: str):
        """在末尾插入数据"""
        row = self.rowCount()
        if not self.insertRows(row, 1):
            return False
        self._data[row] = strData
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        return True

    def removeRow(self, row, parent=QModelIndex()):
        """删除行数据"""
        self.beginRemoveRows(parent, row, row)
        del self._data[row]
        self.endRemoveRows()
        return True

    def getData(self):
        """获取数据"""
        return copy.deepcopy(self._data)
