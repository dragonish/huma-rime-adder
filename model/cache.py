#!/usr/bin/env python
# coding: utf-8

from type.dict import CacheUnit, WordTableUnit


class CacheList(list[CacheUnit]):
    """缓存列表，不包含重复的词条"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._processList()

    def _processList(self):
        """整理列表的方法"""
        if not self:
            return

        # 创建一个临时字典来存储去重后的元素
        tempDict = {}

        # 反向遍历，保留最后出现的元素(以保留最新权重)
        for i in range(len(self) - 1, -1, -1):
            item = self[i]
            key = (item["word"], item["code"])

            # 如果已存在，则更新权重(保留最新值)
            if key in tempDict:
                tempDict[key]["weight"] = item["weight"]
            else:
                tempDict[key] = item

        # 使用去重后的元素重建列表
        self[:] = [item for _, item in sorted(tempDict.items())]

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

    def findCode(self, code: str) -> CacheUnit | None:
        """查找并删除首个匹配编码的元素

        Args:
            code (str): 待查找编码

        Returns:
            CacheUnit | None: 返回匹配的元素
        """
        for cacheItem in self:
            if cacheItem["code"] == code:
                super().remove(cacheItem)
                return cacheItem
        return None

    def toList(self) -> list[CacheUnit]:
        """转换为普通 list 类型"""
        return list(self)


class DeleteCacheList(list[WordTableUnit]):
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
