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
