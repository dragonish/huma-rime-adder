#!/usr/bin/env python
# coding: utf-8

from loguru import logger
from PyQt6.QtCore import QObject
from app.application import exitApp
from model.calc import CalcModel
from window.window import AdderWindow
from common.file import openDirectory
from common.english import isPureEnglish
from type.status import ExitCode, CacheStatus, MessageType
from type.dict import WordTableUnit


class AdderController(QObject):
    """控制器，继承 `QObject` 以便连接信号/槽"""

    def __init__(self, model: CalcModel, view: AdderWindow) -> None:
        super().__init__()
        self._model = model
        self._view = view
        self._tinyState = False

        if not self._model.getNameFileStatus():
            self._view.hideNameTab()

        if not self._model.getEmojiFileStatus():
            self._view.hideEmojiTab()

        if not self._model.getSymbolsFileStatus():
            self._view.hideSymbolsTab()

        self._view.workDirectoryLabel.setText(f"工作目录: {self._model.getWorkDir()}")

        self._view.closeSignal.connect(self._handleCloseEvent)  # 监听关闭信号
        self._view.tinySignal.connect(self._handleTinyPinyinEvent)
        self._view.importSignal.connect(self._handleImportWordsEvent)
        self._view.encodeButton.clicked.connect(self._handleEncodeEvent)
        self._view.addButton.clicked.connect(self._handleAddEvent)
        self._view.queryButton.clicked.connect(self._handleQueryEvent)
        self._view.simpleButton.clicked.connect(self._handleSimpleEvent)
        self._view.indentButton.clicked.connect(self._handleIndentEvent)
        self._view.nameQueryButton.clicked.connect(self._handleNameQueryEvent)
        self._view.nameDoneButton.clicked.connect(self._handleNameDoneEvent)
        self._view.emojiQueryButton.clicked.connect(self._handleEmojiQueryEvent)
        self._view.emojiDoneButton.clicked.connect(self._handleEmojiDoneEvent)
        self._view.symbolsQueryButton.clicked.connect(self._handleSymbolsQueryEvent)
        self._view.symbolsDoneButton.clicked.connect(self._handleSymbolsDoneEvent)
        self._view.openWorkDirectoryButton.clicked.connect(
            self._handleOpenWorkDirectoryEvent
        )
        self._view.wordTableView.rowDeleted.connect(self._handleWordDeleteEvent)
        self._view.wordTableView.editWeight.connect(self._handleWordWeightEditEvent)
        self._view.checkThreeWords.clicked.connect(self._handleCheckThreeWords)

    def _handleCloseEvent(self, forceExit: bool):
        """处理关闭事件"""
        if forceExit:
            exitCode = ExitCode.FORCE_EXIT
        else:
            exitCode = self._model.writer()
            if self._tinyState:
                exitCode = ExitCode.SUCCESS
        logger.info("程序结束运行，退出代码: {}", exitCode.value)
        exitApp(exitCode.value)

    def _handleAddEvent(self):
        """处理添加事件"""
        word = self._view.getWord()
        code = self._view.getCode()
        weight = self._view.getWeight()
        if word and code:
            cacheStatus = self._model.add(word, code, weight)
            match cacheStatus:
                case CacheStatus.MAIN:
                    self._view.showMsg("添加至主码表")
                case CacheStatus.PHRASES:
                    self._view.showMsg("调整词组码表")
                case CacheStatus.CHARACTERS:
                    self._view.showMsg("调整单字码表")
                case CacheStatus.NEW_CHARACTERS:
                    self._view.showMsg("添加至单字码表")
                case CacheStatus.SIMPLE:
                    self._view.showMsg("添加至简词码表")
                case CacheStatus.SIMPLE_EXCEPTION:
                    self._view.showMsg("无简词码表，未添加词条！")
                case CacheStatus.ENGLISH:
                    self._view.showMsg("添加至英文码表")
                case CacheStatus.ENGLISH_EXCEPTION:
                    self._view.showMsg("无英文码表，未添加词条！")
                case CacheStatus.INVALID_CODE:
                    self._view.showMsg("所输入编码的格式有问题！")

            autoEncode = False
            if cacheStatus.isPhrases():
                cleanWord = self._model.getCleanWord(word)
                if len(cleanWord) == 3:
                    autoEncode = True

            if autoEncode:
                info = self._model.simple(word)
                self._view.setEncodeInfo(info)
                results = self._model.query(info["code"], info["isEnglish"])
                self._view.setTableData(info["code"], results)
                self._view.showMsg("添加成功并自动编码三简词")
            elif not cacheStatus.isException():
                self._view.clear()

    def _handleEncodeEvent(self):
        """处理词条编码事件"""
        word = self._view.getWord()
        info = self._model.encode(word)
        self._view.setEncodeInfo(info)
        if info["code"]:
            results = self._model.query(info["code"], info["isEnglish"])
            if not info["isEnglish"] and len(results) > 0 and info["weight"] == 0:
                newWeight = results[-1]["weight"] - 10
                self._view.setWeight(newWeight if newWeight >= 0 else 0)
            self._view.setTableData(info["code"], results)
            self._view.showMsg("编码成功")
        else:
            self._view.showMsg("未编码，请检查输入！")

    def _handleSimpleEvent(self):
        """处理词条简码事件"""
        word = self._view.getWord()
        info = self._model.simple(word)
        self._view.setEncodeInfo(info)
        if info["code"]:
            results = self._model.query(info["code"], info["isEnglish"])
            if not info["isEnglish"] and len(results) > 0 and info["weight"] == 0:
                newWeight = results[-1]["weight"] - 10
                self._view.setWeight(newWeight if newWeight >= 0 else 0)
            self._view.setTableData(info["code"], results)
            self._view.showMsg("简码编码成功")
        else:
            self._view.showMsg("未编码，请检查输入！")

    def _handleQueryEvent(self):
        """处理编码查询事件"""
        code = self._view.getCode()
        word = self._view.getWord()
        isEnglish = isPureEnglish(self._model.getCleanWord(word))
        if code:
            results = self._model.query(code, isEnglish)
            self._view.setTableData(code, results)
            self._view.showMsg("查询完成")
        else:
            self._view.showMsg("没有找到编码，请检查输入！")

    def _handleIndentEvent(self):
        """处理缩进查询事件"""
        code = self._view.getCode()
        indentCode = code[:-1]
        word = self._view.getWord()
        isEnglish = isPureEnglish(self._model.getCleanWord(word))
        if indentCode:
            self._view.setCode(indentCode)
            results = self._model.query(indentCode, isEnglish)
            self._view.setTableData(indentCode, results)
            self._view.showMsg("缩进查询完成")
        else:
            self._view.showMsg("将缩进成空的编码，请检查输入！")

    def _handleWordDeleteEvent(self, deleteItem: WordTableUnit):
        """处理删除词条事件"""
        self._model.delete(deleteItem)
        self._view.showMsg("已删除词条")

    def _handleWordWeightEditEvent(self, item: WordTableUnit):
        """处理词条列表权重值编辑事件"""
        cacheStatus = self._model.edit(item)
        code = item["code"]
        results = self._model.query(code, cacheStatus == CacheStatus.ENGLISH)
        self._view.setTableData(code, results)
        self._view.showMsg("调整词条权重完成")

    def _handleNameQueryEvent(self):
        """处理查询原名事件"""
        name = self._view.getTransName()
        results = self._model.nameQuery(name)
        self._view.setNameTableData(results)
        self._view.showMsg("查询原名完成")

    def _handleNameDoneEvent(self):
        """处理完成原名事件"""
        transName = self._view.getTransName()
        if transName:
            oriNames = self._view.getNameTableData()
            self._model.updateName(transName, oriNames)
            self._view.clearName()
            self._view.showMsg("完成原名更新")
            self._extraQuery(transName)
        else:
            self._view.showMsg("译名为空，请检查输入！")

    def _handleEmojiQueryEvent(self):
        """处理查询表情事件"""
        emojiText = self._view.getEmojiText()
        results = self._model.emojiQuery(emojiText)
        self._view.setEmojiTableData(results)
        self._view.showMsg("查询表情完成")

    def _handleEmojiDoneEvent(self):
        """处理完成表情事件"""
        emojiText = self._view.getEmojiText()
        if emojiText:
            emojiList = self._view.getEmojiTableData()
            self._model.updateEmoji(emojiText, emojiList)
            self._view.clearEmoji()
            self._view.showMsg("完成表情更新")
            self._extraQuery(emojiText)
        else:
            self._view.showMsg("表情文本为空，请检查输入！")

    def _handleSymbolsQueryEvent(self):
        """处理查询符号事件"""
        symbolCode = self._view.getSymbolsCode()
        result = self._model.symbolsQuery(symbolCode)
        self._view.setSymbolsTableData(result["symbols"])
        self._view.setSymbolsComment(result["comment"])
        self._view.showMsg("查询符号完成")

    def _handleSymbolsDoneEvent(self):
        """处理完成符号事件"""
        code = self._view.getSymbolsCode()
        if code:
            symbols = self._view.getSymbolsTableData()
            comment = self._view.getSymbolsComment()
            self._model.updateSymbols(code, comment, symbols)
            self._view.clearSymbols()
            self._view.showMsg("完成符号更新")
        else:
            self._view.showMsg("符号编码为空，请检查输入！")

    def _extraQuery(self, word: str):
        """额外查询处理"""
        info = self._model.encode(word)
        if info["code"]:
            results = self._model.query(info["code"], info["isEnglish"])
            exists = any(item["word"] == word for item in results)
            if not exists:
                self._view.setWord(word)
                self._view.setEncodeInfo(info)
                if not info["isEnglish"] and len(results) > 0 and info["weight"] == 0:
                    newWeight = results[-1]["weight"] - 10
                    self._view.setWeight(newWeight if newWeight >= 0 else 0)
                self._view.setTableData(info["code"], results)
                self._view.switchToTab(0)
                self._view.showMsg("完成事件并为新词条编码")
        else:
            self._view.showMsg("完成事件但额外查询词条存在性异常！")

    def _handleOpenWorkDirectoryEvent(self):
        """处理打开工作目录"""
        workDir = self._model.getWorkDir()
        openDirectory(workDir)

    def _handleCheckThreeWords(self):
        """处理校验三简词事件"""
        result = self._model.checkShortThreeWords()
        conflictCount = len(result["conflictCodes"])
        additionalCount = len(result["additionalEntries"])
        if conflictCount > 0 or additionalCount > 0:
            reply = self._view.showAutoHandleThreeWordsDialog(
                conflictCount, additionalCount
            )
            if reply:
                r = self._model.handleThreeWordsResult(result)
                if r:
                    self._tinyState = True
                    self._view.showMsg("校验完毕并自动处理三简词至操作缓存，详情见日志")
                else:
                    self._view.showMsg("校验完毕但未自动处理三简词，请检查配置文件！")
            else:
                self._view.showMsg("校验三简词完毕，详情见日志")
        else:
            self._view.showMsg("校验三简词完毕，详情见日志")

    def _handleTinyPinyinEvent(self, type: MessageType):
        """处理整理拼音事件"""
        match type:
            case MessageType.TINY_PINYIN_TABLE:
                if self._model.tinyPinyinTable():
                    self._view.showMsg("整理拼音码表文件完毕")
                    self._tinyState = True
                else:
                    self._view.showMsg("未整理拼音码表，请检查配置文件！")
            case MessageType.TINY_PINYIN_TIP:
                if self._model.tinyOpenCCPinyin():
                    self._view.showMsg("整理拼音滤镜文件完毕")
                    self._tinyState = True
                else:
                    self._view.showMsg("未整理拼音滤镜，请检查配置文件！")

    def _handleImportWordsEvent(self, filePath: str):
        """处理导入词库文件事件"""
        encodeState = self._model.encodeFile(filePath)
        if encodeState:
            self._view.showMsg("编码词库文件完毕")
        else:
            self._view.showMsg("未编码文件，请检查输入！")

    def encodeWord(self, word: str):
        """编码词条

        Args:
            word (str): 词条
        """
        self._view.setWord(word)
        self._handleEncodeEvent()
