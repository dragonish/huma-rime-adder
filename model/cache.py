#!/usr/bin/env python
# coding: utf-8

from type.dict import CacheUnit


class CacheList(list[CacheUnit]):
    """缓存列表，不包含重复的词条"""

    def push(self, val: CacheUnit) -> None:
        """添加缓存元素（如果已存在则更新权重，否则添加新元素）"""

        for item in self:
            if item["word"] == val["word"] and item["code"] == val["code"]:
                item["weight"] = val["weight"]
                return

        # 如果没找到，添加新元素
        super().append(val)

    def toList(self) -> list[CacheUnit]:
        """转换为普通 list 类型"""
        return list(self)
