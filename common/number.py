#!/usr/bin/env python
# coding: utf-8


def isPureNumericStr(s: str) -> bool:
    """是否为纯数字组成的字符串"""
    if not isinstance(s, str):
        return False
    if s == "":
        return False
    for char in s:
        if not char.isdigit():
            return False
    return True
