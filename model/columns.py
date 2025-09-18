#!/usr/bin/env python
# coding: utf-8

from typing import cast, Iterable, TypedDict


class Columns(TypedDict):
    text: int
    code: int
    weight: int


class ColumnsModel:
    """码表列解析模型"""

    def __init__(self) -> None:
        self.dict: Columns = {"text": -1, "code": -1, "weight": -1}
        self.str = ""
        self.isCompleted = False
        self._columnsScope = False

    def _parseColumns(self, line: str) -> None:
        """解析列配置

        Args:
            line (str): 行内容
        """
        if line.startswith("- text"):
            self.dict["text"] = max(cast(Iterable[int], self.dict.values())) + 1
        elif line.startswith("- code"):
            self.dict["code"] = max(cast(Iterable[int], self.dict.values())) + 1
        elif line.startswith("- weight"):
            self.dict["weight"] = max(cast(Iterable[int], self.dict.values())) + 1

        self._columnsScope = not (max(cast(Iterable[int], self.dict.values())) == 2)

    def _setFormatStr(self) -> None:
        """获取格式化字符串"""
        if self._isAllColumnsUnset():
            self.dict = {"text": 0, "code": 1, "weight": 2}

        inputList: list[str] = []
        for i in range(3):
            if self.dict["text"] == i:
                inputList.append("{text}")
            elif self.dict["code"] == i:
                inputList.append("{code}")
            elif self.dict["weight"] == i:
                inputList.append("{weight}")
        self.str = "\t".join(inputList)

    def _isAllColumnsUnset(self) -> bool:
        """检测所有列是否都未被设置（值均为 -1）

        Returns:
            bool: 如果所有列都为 -1 返回 True，否则返回 False
        """
        return all(value == -1 for value in self.dict.values())

    def lineHandler(self, line: str) -> None:
        """行处理器

        Args:
            line (str): 行内容
        """
        if line == "...":
            self.isCompleted = True
            self._setFormatStr()
            return

        if line == "columns:":
            self._columnsScope = True
            return

        if self._columnsScope:
            self._parseColumns(line)
