#!/usr/bin/env python
# coding: utf-8

from typing import Sequence


def strToInt(input: str):
    """将字符串转换为整数，若无法转换则返回 `0`

    Args:
        input (str): 待转换字符串

    Returns:
        int: 转换后的整数
    """
    if input.isdigit():
        return int(input)
    return 0


def safeGet(lst: Sequence[str], index: int, default: str = ""):
    """安全获取字符串列表元素，索引超出范围时返回默认值"""
    try:
        return lst[index]
    except IndexError:
        return default


def getCleanWord(word: str) -> str:
    """获取不带符号的字符串

    Args:
        word (str): 源字符串

    Returns:
        str: 不带符号的字符串
    """
    deleteCharsTable = str.maketrans(
        "",
        "",
        "!@#$%^&*()-=_+,.！？￥、，。“”‘’\"':;<>《》—…：；（）『』「」〖〗~|· ",
    )
    return word.translate(deleteCharsTable)
