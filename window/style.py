#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton, QSizePolicy
from PyQt6.QtGui import QCursor, QDesktopServices
from common.file import openDirectory

WINDOW_WIDTH = 520
WINDOW_HEIGHT = 400

BUTTON_BLUE = """
    QPushButton { background-color: #1668dc; color: #ffffff; }
    QPushButton:hover { background-color: #3c89e8; }
    """

BUTTON_RED = """
    QPushButton { background-color: #dc4446; color: #ffffff; }
    QPushButton:hover { background-color: #e86e6b; }
    """


class CustomWidthInput(QLineEdit):
    """自定义宽度输入框"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class NoFoucsButton(QPushButton):
    """无焦点按钮"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)


class ClickableLabel(QLabel):
    """可点击标签组件，支持打开链接或本地目录"""

    def __init__(self, text: str, url: str = "", directory: str = "", parent=None):
        super().__init__(text, parent=parent)
        self._url = url
        self._directory = directory
        self.setStyleSheet("color: #4fc1ff;")
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def setDirectory(self, directory: str) -> None:
        """设置点击后打开的本地目录"""
        self._directory = directory

    def mousePressEvent(self, ev) -> None:
        if ev and ev.button() == Qt.MouseButton.LeftButton:
            self._link_clicked()
        return super().mousePressEvent(ev)

    def _link_clicked(self):
        if self._directory:
            openDirectory(self._directory)
        elif self._url:
            QDesktopServices.openUrl(QUrl(self._url))
