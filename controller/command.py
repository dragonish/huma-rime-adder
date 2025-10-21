#!/usr/bin/env python
# coding: utf-8

from typing import TypeVar, Generic
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal
from model.calc import CalcModel
from common.conversion import getCleanWord
from common.english import isPureEnglish
from type.status import MessageType


T = TypeVar("T", bound="CalcCommand")


class CalcCommand(QObject):
    """抽象命令接口"""

    finished = pyqtSignal(object)

    def __init__(self, model: CalcModel) -> None:
        super().__init__()
        self._model = model

    def execute(self, *args, **kwargs):
        raise NotImplementedError


class CommandRunable(QRunnable, Generic[T]):
    """将命令包装为可运行对象"""

    def __init__(self, command: T, *args, **kwargs) -> None:
        super().__init__()
        self._command = command
        self._args = args
        self._kwargs = kwargs

    def run(self):
        self._command.execute(*self._args, **self._kwargs)


class EncodeCommand(CalcCommand):
    """编码词条命令"""

    def execute(self, word: str):
        result = self._model.encode(word)
        self.finished.emit(result)


class SimpleCommand(CalcCommand):
    """简码命令"""

    def execute(self, word: str):
        result = self._model.simple(word)
        self.finished.emit(result)


class QueryCommand(CalcCommand):
    """查询命令"""

    def execute(self, code: str, word: str):
        isEnglish = isPureEnglish(getCleanWord(word))
        result = (code, self._model.query(code, isEnglish))
        self.finished.emit(result)


class NameQueryCommand(CalcCommand):
    """原名查询命令"""

    def execute(self, name: str):
        result = self._model.nameQuery(name)
        self.finished.emit(result)


class EmojiQueryCommand(CalcCommand):
    """表情查询命令"""

    def execute(self, emojiText: str):
        result = self._model.emojiQuery(emojiText)
        self.finished.emit(result)


class SymbolsQueryCommand(CalcCommand):
    """符号查询命令"""

    def execute(self, symbolsCode: str):
        result = self._model.symbolsQuery(symbolsCode)
        self.finished.emit(result)


class ExtraQueryCommand(CalcCommand):
    """额外查询命令"""

    def execute(self, word: str):
        result = (word, self._model.encode(word))
        self.finished.emit(result)


class CheckThreeCommand(CalcCommand):
    """校验三简词命令"""

    def execute(self):
        result = self._model.checkShortThreeWords()
        self.finished.emit(result)


class TinyPinyinCommand(CalcCommand):
    """整理拼音命令"""

    def execute(self, t: MessageType):
        result = False
        match t:
            case MessageType.TINY_PINYIN_TABLE:
                result = self._model.tinyPinyinTable()
            case MessageType.TINY_PINYIN_TIP:
                result = self._model.tinyOpenCCPinyin()
        self.finished.emit(tuple([t, result]))


class ImportWordsCommand(CalcCommand):
    """导入词库文件命令"""

    def execute(self, filePath: str):
        encodeState = self._model.encodeFile(filePath)
        self.finished.emit(encodeState)
