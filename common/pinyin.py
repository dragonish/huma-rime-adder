#!/usr/bin/env python
# coding: utf-8

from pypinyin import lazy_pinyin, Style


def getPinyin(word: str) -> str:
    """获取词条拼音

    Args:
        word (str): 词条

    Returns:
        str: 空格分隔的拼音编码
    """
    pyList = lazy_pinyin(word, strict=False)
    return " ".join([p for p in pyList if p.isalpha()]).lower()


def getTonePinyin(word: str) -> str:
    """获取词条的音调拼音

    Args:
        word (str): 词条

    Returns:
        str: `·` 分隔的音调拼音编码
    """
    pyList = lazy_pinyin(word, v_to_u=True, style=Style.TONE)
    return "·".join([p for p in pyList if p.isalpha()]).lower()
