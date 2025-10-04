#!/usr/bin/env python
# coding: utf-8

from enum import Enum, auto


class ExitCode(Enum):
    SUCCESS = 0  # 正常退出
    ERROR = 1  # 异常退出
    NOTHING = 3  # 正常退出但无实际操作
    FORCE_EXIT = 4  # 强制退出


class CacheStatus(Enum):
    UNKNOWN = auto()
    MAIN = auto()
    PHRASES = auto()
    CHARACTERS = auto()
    NEW_CHARACTERS = auto()
    SIMPLE = auto()
    SIMPLE_EXCEPTION = auto()
    ENGLISH = auto()
    ENGLISH_EXCEPTION = auto()

    def isPhrases(self) -> bool:
        return self in (CacheStatus.MAIN, CacheStatus.PHRASES)

    def isException(self) -> bool:
        return self in (CacheStatus.SIMPLE_EXCEPTION, CacheStatus.ENGLISH_EXCEPTION)


class MessageType(Enum):
    TINY_PINYIN_TABLE = auto()  # 整理拼音码表
    TINY_PINYIN_TIP = auto()  # 整理拼音滤镜
