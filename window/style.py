#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLineEdit, QPushButton, QSizePolicy

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
