#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtWidgets import QMessageBox


class ConfirmDialog:
    """确认操作的弹窗"""

    def __init__(self, msg: str, parent=None):
        self._parent = parent
        self._msg = msg

    def exec(self) -> bool:
        msgBox = QMessageBox(
            QMessageBox.Icon.Question,
            "确认操作",
            self._msg,
            QMessageBox.StandardButton.NoButton,
            self._parent,
        )

        yesButton = msgBox.addButton(QMessageBox.StandardButton.Yes)
        if yesButton:
            yesButton.setText("是")
        noButton = msgBox.addButton(QMessageBox.StandardButton.No)
        if noButton:
            noButton.setText("否")
        msgBox.setDefaultButton(noButton)
        msgBox.setEscapeButton(noButton)

        reply = msgBox.exec()
        return reply == QMessageBox.StandardButton.Yes
