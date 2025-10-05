#!/usr/bin/env python
# coding: utf-8

import re


def isPureEnglish(text: str) -> bool:
    """判断文本是否为纯英文

    Args:
        text (str): 文本

    Returns:
        bool: 纯英文时为 `True`
    """
    return bool(re.fullmatch(r"[A-Za-z]+", text))


def containsEnglishLetter(text: str) -> bool:
    """
    检测字符串中是否包含英文字母

    参数:
        text (str): 要检测的字符串

    返回:
        bool: 如果包含英文字母返回 `True`，否则返回 `False`
    """
    return bool(re.search("[a-zA-Z]", text))
