#!/usr/bin/env python
# coding: utf-8

import base64
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QSpinBox,
    QDialogButtonBox,
    QPushButton,
)
from PyQt6.QtGui import QIcon, QPixmap
from type.dict import WordTableUnit, WeightDict
from data.icon import ICON


class EditWindow(QDialog):
    """编辑词条窗口"""

    def __init__(
        self, unit: WordTableUnit, weightDict: WeightDict, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._unit = unit
        self._weightDict = weightDict
        self._result = None  # 用于存储结果

        self.setWindowTitle("编辑词条权重")
        iconData = base64.b64decode(ICON)
        pixmap = QPixmap()
        pixmap.loadFromData(iconData)
        self.setWindowIcon(QIcon(pixmap))

        dialogLayout = QVBoxLayout()

        # 表单布局
        formLayout = QFormLayout()
        formLayout.addRow("词条:", QLabel(unit["word"]))
        formLayout.addRow("编码:", QLabel(unit["code"]))
        formLayout.addRow("来源:", QLabel(unit["source"]))
        formLayout.addRow("常用:", QLabel("是" if unit["range"] else "否"))

        # 权重编辑框
        self._weightEdit = QSpinBox()
        self._weightEdit.setFixedWidth(120)
        self._weightEdit.setMaximum(268435455)
        self._weightEdit.setValue(unit["weight"])
        formLayout.addRow("权重:", self._weightEdit)

        dialogLayout.addLayout(formLayout)

        # 按钮组的水平布局
        middleButtonsLayout = QHBoxLayout()
        topButton = QPushButton("置顶")
        topButton.clicked.connect(self._handleTopEvent)
        zeroButton = QPushButton("清零")
        zeroButton.clicked.connect(self._clearWeight)
        maxButton = QPushButton("最大")
        maxButton.clicked.connect(self._handleMaxEvent)
        minButton = QPushButton("最小")
        minButton.clicked.connect(self._handleMinEvent)
        middleButtonsLayout.addWidget(topButton)
        middleButtonsLayout.addWidget(zeroButton)
        middleButtonsLayout.addWidget(maxButton)
        middleButtonsLayout.addWidget(minButton)
        # 添加伸缩器使按钮居中
        middleButtonsLayout.addStretch()
        middleButtonsLayout.addStretch()

        dialogLayout.addLayout(middleButtonsLayout)

        # 底部按钮
        buttons = QDialogButtonBox()
        buttons.setStandardButtons(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        cancelBtn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        if cancelBtn:
            cancelBtn.setText("取消")
        okBtn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if okBtn:
            okBtn.setText("确定")

        # 连接按钮信号到槽函数
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        dialogLayout.addWidget(buttons)
        self.setLayout(dialogLayout)

    def accept(self):
        """实现确定方法"""
        newWeight = self._weightEdit.value()
        if self._unit["weight"] == newWeight:
            self._result = None
        else:
            # * 权重值不一样时才传递
            self._result = self._unit.copy()
            self._result["weight"] = newWeight
        super().accept()  # 关闭对话框

    def reject(self):
        """实现取消方法"""
        self._result = None
        super().reject()  # 关闭对话框

    def getResult(self) -> WordTableUnit | None:
        """获取对话框结果"""
        return self._result

    def _clearWeight(self) -> None:
        """清零权重值"""
        self._weightEdit.setValue(0)

    def _handleTopEvent(self):
        """处理权重值置顶事件"""
        self._weightEdit.setValue(self._weightDict["max"] + 512)

    def _handleMaxEvent(self):
        """处理权重值最大化事件"""
        self._weightEdit.setValue(self._weightDict["max"])

    def _handleMinEvent(self):
        """处理权重值最小化事件"""
        self._weightEdit.setValue(self._weightDict["min"])
