#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtWidgets import QGridLayout, QWidget


class InfoGridLayout:
    """信息布局类"""

    def __init__(self, parent=None) -> None:
        self._layout = QGridLayout(parent)
        self._row = 0
        self._col = 0

    def addRowWidget(self, widget: QWidget | None):
        self._layout.addWidget(widget, self._row, 0)
        self._row += 1
        self._col = 0

    def addColWidget(self, widget: QWidget | None):
        self._col += 1
        self._layout.addWidget(widget, self._row, self._col)

    def getLayout(self):
        return self._layout
