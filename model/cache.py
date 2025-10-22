#!/usr/bin/env python
# coding: utf-8

from type.dict import CacheUnit, CacheTableUnit


class CacheList(list[CacheUnit]):
    """缓存列表，不包含重复的词条"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processList()

    def _processList(self):
        """整理列表的方法"""
        if not self:
            return

        # 创建一个字典来存储最后出现的元素
        tempDict = {}

        # 正向遍历，记录每个键最后一次出现的索引
        for i, item in enumerate(self):
            key = (item["word"], item["code"])
            tempDict[key] = (i, item)

        # 按照原始顺序重新构建列表
        self[:] = [item for _, item in sorted(tempDict.values(), key=lambda x: x[0])]

    def push(self, val: CacheUnit) -> None:
        """添加缓存元素（如果已存在则更新权重，否则添加新元素）"""

        for item in self:
            if item["word"] == val["word"] and item["code"] == val["code"]:
                item["weight"] = val["weight"]
                return

        # 如果没找到，添加新元素
        super().append(val)

    def find(self, word: str, code: str) -> CacheUnit | None:
        """查找并删除首个匹配元素

        Args:
            word (str): 待查找文本
            code (str): 待查找编码

        Returns:
            bool: 返回匹配的元素
        """
        for cacheItem in self:
            if cacheItem["word"] == word and cacheItem["code"] == code:
                super().remove(cacheItem)
                return cacheItem
        return None

    def toList(self) -> list[CacheUnit]:
        """转换为普通 list 类型"""
        return list(self)


class DeleteCacheList(list[CacheTableUnit]):
    """删除缓存列表"""

    def find(self, word: str, code: str, weight: int | str) -> bool:
        """查找并删除首个匹配元素

        Args:
            word (str): 待查找文本
            code (str): 待查找编码
            weight (int): 待查找权重

        Returns:
            bool: 若匹配则返回 `True`
        """
        for cacheItem in self:
            if (
                cacheItem["word"] == word
                and cacheItem["code"] == code
                and str(cacheItem["weight"]) == str(weight)
            ):
                super().remove(cacheItem)
                return True
        return False
