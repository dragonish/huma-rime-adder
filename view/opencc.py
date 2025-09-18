#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QMenu, QTableView
from model.opencc import OpenCCTableModel


class OpenCCTableView(QTableView):
    """OpenCC 配置的表格视图"""

    def __init__(self, model: OpenCCTableModel) -> None:
        super().__init__()
        self._model = model

        self.setModel(model)
        self._custom()

    def _custom(self) -> None:
        """自定义视图显示和实现元素拖动"""
        self.setColumnWidth(0, 400)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove
        )  # 允许内部移动
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # 设置视图支持右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._openMenu)

    def _openMenu(self, pos):
        """右键菜单"""
        index = self.indexAt(pos)
        if not index.isValid():
            return

        viewport = self.viewport()
        if viewport:
            menu = QMenu()
            deleteAction = menu.addAction("删除行")

            row = index.row()
            action = menu.exec(viewport.mapToGlobal(pos))

            match action:
                case deleteAction:
                    self._model.removeRow(row)
