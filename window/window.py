#!/usr/bin/env python
# coding: utf-8

import base64
from loguru import logger
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCloseEvent, QIcon, QPixmap, QShowEvent, QCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSpacerItem,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QWidget,
)
from data.version import APP_VERSION
from data.icon import ICON
from type.dict import CodeTableUnit, EncodeResult
from type.status import MessageType
from model.word import WordTableModel
from model.opencc import OpenCCTableModel
from view.word import WordTableView
from view.opencc import OpenCCTableView
from log.manager import LogManager
from .style import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BUTTON_BLUE,
    BUTTON_RED,
    CustomWidthInput,
    NoFoucsButton,
    ClickableLabel,
)
from .dialog import ConfirmDialog


class AdderWindow(QMainWindow):
    """加词器主窗口"""

    closeSignal = pyqtSignal(bool)  # 关闭信号，参数表示是否强制退出
    importSignal = pyqtSignal(str)  # 导入词库文件信号
    tinySignal = pyqtSignal(MessageType)  # 整理拼音滤镜信号

    def __init__(self) -> None:
        super().__init__()

        self._forceExitState = False

        self.setWindowTitle(f"猛击虎码加词器")
        iconData = base64.b64decode(ICON)
        pixmap = QPixmap()
        pixmap.loadFromData(iconData)
        self.setWindowIcon(QIcon(pixmap))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._tabWidget = QTabWidget(self)
        self.setCentralWidget(self._tabWidget)
        self._createWordTab()
        self._createNameTab()
        self._createEmojiTab()
        self._createSymbolsTab()
        self._createOtherTab()
        self._createStatusBar()

    def _createWordTab(self):
        """创建词条标签页"""
        wordWindow = QWidget(self)
        wordLayout = QGridLayout()

        wordLayout.addWidget(QLabel("新词:"), 0, 0)
        self._wordInput = CustomWidthInput()
        wordLayout.addWidget(self._wordInput, 0, 1)
        self._rangeLabel = QLabel("")
        wordLayout.addWidget(self._rangeLabel, 0, 2)
        self.encodeButton = NoFoucsButton("编码")
        self._wordInput.returnPressed.connect(self.encodeButton.click)
        wordLayout.addWidget(self.encodeButton, 0, 3)
        self.addButton = NoFoucsButton("添加")
        self.addButton.setStyleSheet(BUTTON_BLUE)
        wordLayout.addWidget(self.addButton, 0, 4)
        clearButton = NoFoucsButton("清空")
        clearButton.setStyleSheet(BUTTON_RED)
        clearButton.clicked.connect(self.clear)
        wordLayout.addWidget(clearButton, 0, 5)

        wordLayout.addWidget(QLabel("编码:"), 1, 0)
        self._codeInput = CustomWidthInput()
        wordLayout.addWidget(self._codeInput, 1, 1)
        self.queryButton = NoFoucsButton("查询")
        self._codeInput.returnPressed.connect(self.queryButton.click)
        wordLayout.addWidget(self.queryButton, 1, 2)
        self.simpleButton = NoFoucsButton("简码")
        wordLayout.addWidget(self.simpleButton, 1, 3)
        self.indentButton = NoFoucsButton("缩进")
        wordLayout.addWidget(self.indentButton, 1, 4)

        wordLayout.addWidget(QLabel("权重:"), 2, 0)
        self._weightInput = QSpinBox()
        self._weightInput.setMaximum(268435455)
        wordLayout.addWidget(self._weightInput, 2, 1)
        topButton = NoFoucsButton("置顶")
        topButton.clicked.connect(self._handleTopEvent)
        wordLayout.addWidget(topButton, 2, 2)
        zeroButton = NoFoucsButton("清零")
        zeroButton.clicked.connect(self._clearWeight)
        wordLayout.addWidget(zeroButton, 2, 3)
        maxButton = NoFoucsButton("最大")
        maxButton.clicked.connect(self._handleMaxEvent)
        wordLayout.addWidget(maxButton, 2, 4)
        minButton = NoFoucsButton("最小")
        minButton.clicked.connect(self._handleMinEvent)
        wordLayout.addWidget(minButton, 2, 5)

        self._duplicateLabel = QLabel("重码:")
        self._duplicateLabel.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self._duplicateLabel.setToolTip("编码: 空")
        wordLayout.addWidget(self._duplicateLabel, 3, 0)
        self._wordTableModel = WordTableModel()
        self.wordTableView = WordTableView(self._wordTableModel)
        self.wordTableView.passWeight.connect(self.setWeight)
        wordLayout.addWidget(self.wordTableView, 3, 1, 1, 6)

        wordWindow.setLayout(wordLayout)
        self._tabWidget.addTab(wordWindow, "词条")

    def _createNameTab(self):
        """创建原名标签页"""
        nameWindow = QWidget(self)
        nameLayout = QGridLayout()

        nameLayout.addWidget(QLabel("译名:"), 0, 0)
        self._transNameInput = CustomWidthInput()
        nameLayout.addWidget(self._transNameInput, 0, 1)
        self.nameQueryButton = NoFoucsButton("查询")
        self._transNameInput.returnPressed.connect(self.nameQueryButton.click)
        nameLayout.addWidget(self.nameQueryButton, 0, 2)
        clearTransNameButton = NoFoucsButton("清除")
        clearTransNameButton.clicked.connect(self._clearTransName)
        nameLayout.addWidget(clearTransNameButton, 0, 3)
        self.nameDoneButton = NoFoucsButton("完成")
        self.nameDoneButton.setStyleSheet(BUTTON_BLUE)
        nameLayout.addWidget(self.nameDoneButton, 0, 4)
        nameClearButton = NoFoucsButton("清空")
        nameClearButton.setStyleSheet(BUTTON_RED)
        nameClearButton.clicked.connect(self.clearName)
        nameLayout.addWidget(nameClearButton, 0, 5)

        nameLayout.addWidget(QLabel("名称:"), 1, 0)
        self._oriNameInput = CustomWidthInput()
        nameLayout.addWidget(self._oriNameInput, 1, 1)
        insertNameButton = NoFoucsButton("插入")
        self._oriNameInput.returnPressed.connect(insertNameButton.click)
        insertNameButton.clicked.connect(self._insertName)
        nameLayout.addWidget(insertNameButton, 1, 2)
        clearOriNameButton = NoFoucsButton("清除")
        clearOriNameButton.clicked.connect(self._clearOriName)
        nameLayout.addWidget(clearOriNameButton, 1, 3)

        nameLayout.addWidget(QLabel("原名:"), 2, 0)
        self._nameTableModel = OpenCCTableModel("原名", True)
        nameTableView = OpenCCTableView(self._nameTableModel)
        nameLayout.addWidget(nameTableView, 2, 1, 1, 6)

        nameWindow.setLayout(nameLayout)
        self._tabWidget.addTab(nameWindow, "原名")

    def _createEmojiTab(self):
        """创建表情标签页"""
        emojiWindow = QWidget(self)
        emojiLayout = QGridLayout()

        emojiLayout.addWidget(QLabel("文本:"), 0, 0)
        self._emojiTextInput = CustomWidthInput()
        emojiLayout.addWidget(self._emojiTextInput, 0, 1)
        self.emojiQueryButton = NoFoucsButton("查询")
        self._emojiTextInput.returnPressed.connect(self.emojiQueryButton.click)
        emojiLayout.addWidget(self.emojiQueryButton, 0, 2)
        clearEmojiTextButton = NoFoucsButton("清除")
        clearEmojiTextButton.clicked.connect(self._clearEmojiText)
        emojiLayout.addWidget(clearEmojiTextButton, 0, 3)
        self.emojiDoneButton = NoFoucsButton("完成")
        self.emojiDoneButton.setStyleSheet(BUTTON_BLUE)
        emojiLayout.addWidget(self.emojiDoneButton, 0, 4)
        emojiClearButton = NoFoucsButton("清空")
        emojiClearButton.setStyleSheet(BUTTON_RED)
        emojiClearButton.clicked.connect(self.clearEmoji)
        emojiLayout.addWidget(emojiClearButton, 0, 5)

        emojiLayout.addWidget(QLabel("表情:"), 1, 0)
        self._emojiInput = CustomWidthInput()
        emojiLayout.addWidget(self._emojiInput, 1, 1)
        insertEmojiButton = NoFoucsButton("插入")
        self._emojiInput.returnPressed.connect(insertEmojiButton.click)
        insertEmojiButton.clicked.connect(self._insertEmoji)
        emojiLayout.addWidget(insertEmojiButton, 1, 2)
        clearEmojiButton = NoFoucsButton("清除")
        clearEmojiButton.clicked.connect(self._clearEmoji)
        emojiLayout.addWidget(clearEmojiButton, 1, 3)

        emojiLayout.addWidget(QLabel("列表:"), 2, 0)
        self._emojiTableModel = OpenCCTableModel("表情")
        emojiTableView = OpenCCTableView(self._emojiTableModel)
        emojiLayout.addWidget(emojiTableView, 2, 1, 1, 6)

        emojiWindow.setLayout(emojiLayout)
        self._tabWidget.addTab(emojiWindow, "表情")

    def _createSymbolsTab(self):
        """创建符号标签页"""
        symbolsWindow = QWidget(self)
        symbolsLayout = QGridLayout()

        symbolsLayout.addWidget(QLabel("编码:"), 0, 0)
        self._symbolsCodeInput = CustomWidthInput()
        symbolsLayout.addWidget(self._symbolsCodeInput, 0, 1)
        self.symbolsQueryButton = NoFoucsButton("查询")
        self._symbolsCodeInput.returnPressed.connect(self.symbolsQueryButton.click)
        symbolsLayout.addWidget(self.symbolsQueryButton, 0, 2)
        clearSymbolsCodeButton = NoFoucsButton("清除")
        clearSymbolsCodeButton.clicked.connect(self._clearSymbolsCode)
        symbolsLayout.addWidget(clearSymbolsCodeButton, 0, 3)
        self.symbolsDoneButton = NoFoucsButton("完成")
        self.symbolsDoneButton.setStyleSheet(BUTTON_BLUE)
        symbolsLayout.addWidget(self.symbolsDoneButton, 0, 4)
        symbolsClearButton = NoFoucsButton("清空")
        symbolsClearButton.setStyleSheet(BUTTON_RED)
        symbolsClearButton.clicked.connect(self.clearSymbols)
        symbolsLayout.addWidget(symbolsClearButton, 0, 5)

        symbolsLayout.addWidget(QLabel("符号:"), 1, 0)
        self._symbolsUnitInput = CustomWidthInput()
        symbolsLayout.addWidget(self._symbolsUnitInput, 1, 1)
        insertSymbolsButton = NoFoucsButton("插入")
        self._symbolsUnitInput.returnPressed.connect(insertSymbolsButton.click)
        insertSymbolsButton.clicked.connect(self._insertSymbols)
        symbolsLayout.addWidget(insertSymbolsButton, 1, 2)
        clearSymbolsUnitButton = NoFoucsButton("清除")
        clearSymbolsUnitButton.clicked.connect(self._clearSymbolsUnit)
        symbolsLayout.addWidget(clearSymbolsUnitButton, 1, 3)

        symbolsLayout.addWidget(QLabel("注释:"), 2, 0)
        self._symbolsCommentInput = CustomWidthInput()
        symbolsLayout.addWidget(self._symbolsCommentInput, 2, 1)
        clearSymbolsCommentButton = NoFoucsButton("清除")
        clearSymbolsCommentButton.clicked.connect(self._clearSymbolsComment)
        symbolsLayout.addWidget(clearSymbolsCommentButton, 2, 2)

        symbolsLayout.addWidget(QLabel("列表:"), 3, 0)
        self._symbolsTableModel = OpenCCTableModel("符号")
        symbolsTableView = OpenCCTableView(self._symbolsTableModel)
        symbolsLayout.addWidget(symbolsTableView, 3, 1, 1, 6)

        symbolsWindow.setLayout(symbolsLayout)
        self._tabWidget.addTab(symbolsWindow, "符号")

    def _createOtherTab(self):
        """创建其他标签页"""
        otherWindow = QWidget(self)
        otherLayout = QGridLayout()

        otherLayout.addWidget(QLabel(f"程序版本: {APP_VERSION}"), 0, 0)

        sourceWidget = QWidget()
        sourceLayout = QHBoxLayout()
        sourceLayout.setSpacing(5)
        sourceLayout.setContentsMargins(0, 0, 0, 0)
        sourceLabel = QLabel("项目地址:")
        sourceLayout.addWidget(sourceLabel)
        clickableLabel = ClickableLabel(
            "dragonish/huma-rime-adder",
            "https://github.com/dragonish/huma-rime-adder",
        )
        sourceLayout.addWidget(clickableLabel)

        # 添加一个弹性 spacer，但设置其最小尺寸为 0
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        sourceLayout.addItem(spacer)
        sourceWidget.setLayout(sourceLayout)
        otherLayout.addWidget(sourceWidget, 1, 0)

        self.workDirectoryLabel = QLabel("")
        otherLayout.addWidget(self.workDirectoryLabel, 2, 0)

        otherLayout.addWidget(
            QLabel(f"日志文件: {LogManager.getLogFileLocation()}"), 3, 0
        )

        importWordsButton = NoFoucsButton("导入词库文件")
        importWordsButton.clicked.connect(self._openFileDialog)
        otherLayout.addWidget(importWordsButton, 4, 0)

        self.checkThreeWords = NoFoucsButton("校验三简词")
        otherLayout.addWidget(self.checkThreeWords, 5, 0)

        tinyPinyinButton = NoFoucsButton("整理拼音码表")
        tinyPinyinButton.clicked.connect(
            lambda: self._showTinyConfirmationDialog(MessageType.TINY_PINYIN_TABLE)
        )
        otherLayout.addWidget(tinyPinyinButton, 6, 0)

        tinyPinyinTipButton = NoFoucsButton("整理拼音滤镜")
        tinyPinyinTipButton.clicked.connect(
            lambda: self._showTinyConfirmationDialog(MessageType.TINY_PINYIN_TIP)
        )
        otherLayout.addWidget(tinyPinyinTipButton, 7, 0)

        self.openWorkDirectoryButton = NoFoucsButton("打开工作目录")
        otherLayout.addWidget(self.openWorkDirectoryButton, 8, 0)

        openLogDirectoryButton = NoFoucsButton("打开日志目录")
        openLogDirectoryButton.clicked.connect(LogManager.openLogDirectory)
        otherLayout.addWidget(openLogDirectoryButton, 9, 0)

        forceExitButton = NoFoucsButton("强制退出")
        forceExitButton.setStyleSheet(BUTTON_RED)
        forceExitButton.clicked.connect(self._forceExit)
        otherLayout.addWidget(forceExitButton, 10, 0)

        otherWindow.setLayout(otherLayout)
        self._tabWidget.addTab(otherWindow, "其他")

    def _createStatusBar(self):
        self._status = QStatusBar()
        self._status.setSizeGripEnabled(False)
        self._status.showMessage("等待操作中...")
        self.setStatusBar(self._status)

    def _showTinyConfirmationDialog(self, t: MessageType):
        msg = ""
        match t:
            case MessageType.TINY_PINYIN_TABLE:
                msg = "您确定要执行整理拼音码表操作吗？这将移除拼音码表中重复的编码词条，然后重写拼音码表文件！"
            case MessageType.TINY_PINYIN_TIP:
                msg = "您确定要执行整理拼音滤镜操作吗？这将根据码表中的词组重新生成对应拼音提示，然后覆盖及重写拼音滤镜文件！"

        msgBox = ConfirmDialog(msg, self)
        reply = msgBox.exec()
        if reply:
            self.tinySignal.emit(t)

    def showEvent(self, event: QShowEvent):
        """重写窗口显示事件"""
        super().showEvent(event)
        # 使输入框在窗口显示后获得焦点
        self._wordInput.setFocus()

    def closeEvent(self, event: QCloseEvent):
        """重写窗口关闭事件，以处理文件写入和退出状态码

        Args:
            event (QCloseEvent): 事件
        """
        super().closeEvent(event)
        try:
            logger.debug("发出关闭信号")
            self.closeSignal.emit(self._forceExitState)  # 触发关闭信号
        except Exception as e:
            logger.error("发出关闭信号出错: {}", str(e))

    def showAutoHandleThreeWordsDialog(
        self, conflictCount: int, additionalCount: int
    ) -> bool:
        """自动处理三简词弹窗"""
        msg = f"校验完毕，您确定要继续执行自动处理三简词操作吗？这将移除冲突的 {conflictCount} 组三简词以及补全缺失的 {additionalCount} 组三简词！"
        msgBox = ConfirmDialog(msg, self)
        reply = msgBox.exec()
        return reply

    def hideNameTab(self) -> None:
        """隐藏原名标签页"""
        self._tabWidget.setTabVisible(1, False)

    def hideEmojiTab(self) -> None:
        """隐藏表情标签页"""
        self._tabWidget.setTabVisible(2, False)

    def hideSymbolsTab(self) -> None:
        """隐藏符号标签页"""
        self._tabWidget.setTabVisible(3, False)

    def _forceExit(self) -> None:
        """强制退出"""
        self._forceExitState = True
        logger.debug("强制退出程序")
        self.close()

    def _clearWeight(self) -> None:
        """清零权重值"""
        self._weightInput.setValue(0)

    def _clearTransName(self) -> None:
        """清除译名"""
        self._transNameInput.clear()

    def _insertName(self) -> None:
        """插入原名"""
        name = self._oriNameInput.text().strip()
        if name:
            self._nameTableModel.appendRow(name)
            self._oriNameInput.clear()
            self.showMsg("已插入原名")
        else:
            self.showMsg("原名为空，请检查输入！")

    def _insertEmoji(self) -> None:
        """插入表情"""
        emoji = self._emojiInput.text().strip()
        if emoji:
            self._emojiTableModel.appendRow(emoji)
            self._emojiInput.clear()
            self.showMsg("已插入表情")
        else:
            self.showMsg("表情为空，请检查输入！")

    def _insertSymbols(self) -> None:
        """插入符号"""
        symbol = self._symbolsUnitInput.text().strip()
        if symbol:
            self._symbolsTableModel.appendRow(symbol)
            self._symbolsUnitInput.clear()
            self.showMsg("已插入符号")
        else:
            self.showMsg("符号为空，请检查输入！")

    def _clearEmoji(self) -> None:
        """清除表情输入框"""
        self._emojiInput.clear()

    def _clearOriName(self) -> None:
        """清除原名输入框"""
        self._oriNameInput.clear()

    def _clearEmojiText(self) -> None:
        """清除表情文本框内容"""
        self._emojiTextInput.clear()

    def _clearSymbolsCode(self) -> None:
        """清除符号编码输入框"""
        self._symbolsCodeInput.clear()

    def _clearSymbolsUnit(self) -> None:
        """清除符号单元输入框"""
        self._symbolsUnitInput.clear()

    def _clearSymbolsComment(self) -> None:
        """清除符号注释输入框"""
        self._symbolsCommentInput.clear()

    def showMsg(self, msg: str) -> None:
        """设置状态栏内容"""
        self._status.showMessage(msg)

    def clear(self) -> None:
        """清空所有输入"""
        self._wordInput.clear()
        self._codeInput.clear()
        self._weightInput.setValue(0)
        self._wordTableModel.clearData()
        self._rangeLabel.setText("")
        self._duplicateLabel.setToolTip("编码: 空")

    def clearName(self) -> None:
        """清空所有名称输入"""
        self._transNameInput.clear()
        self._oriNameInput.clear()
        self._nameTableModel.clearData()

    def clearEmoji(self) -> None:
        """清空所有表情输入"""
        self._emojiTextInput.clear()
        self._emojiInput.clear()
        self._emojiTableModel.clearData()

    def clearSymbols(self) -> None:
        """清空所有符号输入"""
        self._symbolsCodeInput.clear()
        self._symbolsUnitInput.clear()
        self._symbolsCommentInput.clear()
        self._symbolsTableModel.clearData()

    def getWord(self) -> str:
        """获取词条"""
        return self._wordInput.text().strip()

    def setWord(self, word: str) -> None:
        """设置词条"""
        self._wordInput.setText(word)

    def getCode(self) -> str:
        """获取编码"""
        return self._codeInput.text().strip()

    def setCode(self, code: str) -> None:
        """设置编码"""
        self._codeInput.setText(code)

    def getWeight(self) -> int:
        """获取权重"""
        return self._weightInput.value()

    def setWeight(self, weight: int) -> None:
        """设置权重值"""
        return self._weightInput.setValue(weight)

    def setEncodeInfo(self, info: EncodeResult) -> None:
        """设置编码信息"""
        self._codeInput.setText(info["code"])
        self._weightInput.setValue(info["weight"])
        if info["isEnglish"]:
            self._rangeLabel.setText("英文")
        else:
            if info["range"]:
                self._rangeLabel.setText("常用")
            else:
                self._rangeLabel.setText("全集")

    def setTableData(self, code: str, data: list[CodeTableUnit]) -> None:
        """设置重码列表数据"""
        self._wordTableModel.updateData(code, data)
        self._duplicateLabel.setToolTip(f"编码: {code}")

    def getTransName(self) -> str:
        """获取译名"""
        return self._transNameInput.text().strip()

    def setNameTableData(self, data: list[str]) -> None:
        """设置原名列表数据"""
        self._nameTableModel.updateData(data)

    def getNameTableData(self) -> list[str]:
        """获取原名列表数据"""
        return self._nameTableModel.getData()

    def getEmojiText(self) -> str:
        """获取表情文本"""
        return self._emojiTextInput.text().strip()

    def setEmojiTableData(self, data: list[str]) -> None:
        """设置表情列表数据"""
        self._emojiTableModel.updateData(data)

    def getEmojiTableData(self) -> list[str]:
        """获取表情列表数据"""
        return self._emojiTableModel.getData()

    def getSymbolsCode(self) -> str:
        """获取符号编码"""
        return self._symbolsCodeInput.text().strip()

    def setSymbolsTableData(self, data: list[str]):
        """设置符号列表数据"""
        self._symbolsTableModel.updateData(data)

    def setSymbolsComment(self, comment: str):
        """设置符号的注释"""
        self._symbolsCommentInput.setText(comment)

    def getSymbolsTableData(self) -> list[str]:
        """获取符号列表数据"""
        return self._symbolsTableModel.getData()

    def getSymbolsComment(self) -> str:
        """获取符号的注释"""
        return self._symbolsCommentInput.text().strip()

    def switchToTab(self, index: int) -> None:
        """切换至指定标签页"""
        self._tabWidget.setCurrentIndex(index)

    def _findMaxWeight(self) -> int:
        """获取重码列表的最大权重值

        Returns:
            int: 权重值，未找到时为 `0`
        """
        return self._wordTableModel.getFirstRowWeight()

    def _findMinWeight(self) -> int:
        """获取编码的最小权重值

        Returns:
            int: 权重值，未找到时为 `0`
        """
        return self._wordTableModel.getLastRowWeight()

    def _handleTopEvent(self):
        """处理权重值置顶事件"""
        code = self.getCode()
        if code:
            weight = self._findMaxWeight() + 512
            self.setWeight(weight)
            self.showMsg("已置顶词条")
        else:
            self.showMsg("没有找到编码，请检查输入！")

    def _handleMaxEvent(self):
        """处理权重值最大化事件"""
        code = self.getCode()
        if code:
            weight = self._findMaxWeight()
            self.setWeight(weight)
            self.showMsg("已最大化权重值")
        else:
            self.showMsg("没有找到编码，请检查输入！")

    def _handleMinEvent(self):
        """处理权重值最小化事件"""
        code = self.getCode()
        if code:
            weight = self._findMinWeight()
            self.setWeight(weight)
            self.showMsg("已最小化权重值")
        else:
            self.showMsg("没有找到编码，请检查输入！")

    def _openFileDialog(self):
        """打开文件选择对话框"""
        filePath, _ = QFileDialog.getOpenFileName(
            self, "选择词库文件", "", "文本文件 (*.txt);;所有文件 (*)"
        )
        if filePath:
            self.importSignal.emit(filePath)
