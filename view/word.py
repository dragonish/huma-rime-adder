#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMenu, QTableView
from model.word import WordTableModel


class WordTableView(QTableView):
    """重码的表格视图"""

    rowDeleted = pyqtSignal(dict)
    passWeight = pyqtSignal(int)

    def __init__(self, model: WordTableModel) -> None:
        super().__init__()
        self._model = model

        self.setModel(model)
        self._custom()

    def _custom(self) -> None:
        """自定义视图显示"""
        self.setColumnWidth(0, 145)
        self.setColumnWidth(2, 120)
        self.setColumnWidth(3, 40)

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
            weightAction = menu.addAction("传递权重")
            deleteAction = menu.addAction("删除词条")

            row = index.row()
            action = menu.exec(viewport.mapToGlobal(pos))

            if action == weightAction:
                weight = self._model.getWeight(row)
                self.passWeight.emit(weight)
            elif action == deleteAction:
                removedData = self._model.removeRow(row)
                self.rowDeleted.emit(removedData)
