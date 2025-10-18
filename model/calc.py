#!/usr/bin/env python
# coding: utf-8

import copy
import io
import os
import re
from typing import cast
from loguru import logger
from type.dict import (
    CacheUnit,
    CodeTableUnit,
    WordTableUnit,
    CodeUnit,
    EncodeResult,
    SymbolsUnit,
    TigressFiles,
)
from type.status import ExitCode, CacheStatus
from model.columns import ColumnsModel
from model.cache import CacheList, DeleteCacheList
from common.file import getTableSource, readFile
from common.conversion import safeGet, strToInt
from common.pinyin import getPinyin, getTonePinyin
from common.english import isPureEnglish


class CalcModel:
    """计算模型"""

    def __init__(
        self,
        workDir: str,
        tigressFiles: TigressFiles,
    ) -> None:
        """构造器

        Args:
            workDir (str): 工作目录
            tigressFiles(TigressFiles): 码表文件路径对象
        """
        self._workDir = workDir

        self._mainSourceName = getTableSource(tigressFiles["main"])  # 主码表源名称
        self._simpleSourceName = getTableSource(tigressFiles["simple"])  # 简词表源名称
        self._phrasesSourceName = getTableSource(
            tigressFiles["phrases"]
        )  # 词组表源名称
        self._charactersSourceName = getTableSource(
            tigressFiles["characters"]
        )  # 单字表源名称
        self._englishSourceName = getTableSource(
            tigressFiles["english"]
        )  # 英文表源名称

        self._tigressFiles = cast(
            TigressFiles,
            {
                key: os.path.join(self._workDir, str(value))
                for key, value in tigressFiles.items()
            },
        )

        self._characterDict: dict[str, str] = {}  # 单字字典
        self._codeDict: dict[str, list[CodeUnit]] = {}  # 编码字典
        self._englishDict: dict[str, list[CodeUnit]] = {}  # 英文字典
        self._charset: set[str] = set()  # 字集集合
        self._nameDict: dict[str, list[str]] = {}  # 原名字典
        self._emojiDict: dict[str, list[str]] = {}  # 表情字典
        self._symbolsDict: dict[str, SymbolsUnit] = {}  # 符号字典

        self._isParseTigress = False  # 是否已解析虎码码表
        self._isParseEnglish = False  # 是否已解析英文码表
        self._isParseName = False  # 是否已解析原名码表
        self._isParseEmoji = False  # 是否已解析表情码表
        self._isParseSymbols = False  # 是否已解析符号码表

        self._tigressCached: list[CacheUnit] = []  # 虎码词条缓存
        self._tigressDeleteCached: list[WordTableUnit] = []  # 虎码词条删除缓存
        self._simpleCached: list[CacheUnit] = []  # 简码缓存
        self._simpleDeleteCached: list[WordTableUnit] = []  # 简码删除缓存
        self._phrasesCached: list[CacheUnit] = []  # 词组缓存
        self._phrasesDeleteCached: list[WordTableUnit] = []  # 词组删除缓存
        self._charactersCached: list[CacheUnit] = []  # 单字缓存
        self._charactersDeleteCached: list[WordTableUnit] = []  # 单字删除缓存
        self._englishCached: list[CacheUnit] = []  # 英文缓存
        self._englishDeleteCached: list[WordTableUnit] = []  # 英文删除缓存
        self._charsetCached: set[str] = set()  # 字集缓存
        self._nameCached: dict[str, list[str]] = {}  # 原名缓存
        self._emojiCached: dict[str, list[str]] = {}  # 表情缓存
        self._symbolsCached: dict[str, SymbolsUnit] = {}  # 符号缓存

        self._deleteCharsTable = str.maketrans(
            "",
            "",
            "!@#$%^&*()-=_+,.！？￥、，。“”‘’\"':;<>《》—…：；（）『』「」〖〗~|· ",
        )

        self._simpleFileStatus = False
        if tigressFiles["simple"] and os.path.exists(self._tigressFiles["simple"]):
            self._simpleFileStatus = True

        self._englishFileStatus = False
        if tigressFiles["english"] and os.path.exists(self._tigressFiles["english"]):
            self._englishFileStatus = True

        self._pinyinFileStatus = False
        if tigressFiles["pinyin"] and os.path.exists(self._tigressFiles["pinyin"]):
            self._pinyinFileStatus = True

        self._pinyinTipFileStatus = False
        if tigressFiles["pinyintip"] and os.path.exists(
            self._tigressFiles["pinyintip"]
        ):
            self._pinyinTipFileStatus = True

        self._nameFileStatus = False
        if tigressFiles["name"] and os.path.exists(self._tigressFiles["name"]):
            self._nameFileStatus = True

        self._emojiFileStatus = False
        if tigressFiles["emoji"] and os.path.exists(self._tigressFiles["emoji"]):
            self._emojiFileStatus = True

        self._symbolsFileStatus = False
        if tigressFiles["symbols"] and os.path.exists(self._tigressFiles["symbols"]):
            self._symbolsFileStatus = True

    def _parseMain(self) -> None:
        """解析虎码主码表内容"""
        if self._isParseTigress:
            return
        self._isParseTigress = True

        mainTableFile = self._tigressFiles["main"]
        logger.info("开始读取主码表: {}", mainTableFile)

        # 读取所导入的其他码表名称
        readLines = readFile(mainTableFile)
        importTables: list[str] = []
        inScope = False
        for line in readLines:
            item = line.strip()
            if inScope:
                if item.startswith("- "):
                    names = item.split(" ")
                    importTables.append(names[1])
                else:
                    inScope = False
                    break
            elif item.startswith("import_tables:"):
                inScope = True

        logger.info(
            "读取到 {size} 个其他码表名称，分别为: {name}",
            size=len(importTables),
            name=" ".join(importTables),
        )

        # 解析所导入的其他码表文件
        for tableName in importTables:
            tableFile = os.path.join(self._workDir, tableName + ".dict.yaml")
            if os.path.exists(tableFile):
                logger.info("解析码表文件： {}", tableFile)
                self._parseTigress(readFile(tableFile), tableName)
            else:
                logger.warning("没有找到码表文件: {}", tableFile)

        # 解析主码表文件
        self._parseTigress(readLines, self._mainSourceName)
        logger.info("解析主码表文件: {}", mainTableFile)

        logger.info(
            "解析完毕，读取到 {character} 个单字，读取到 {code} 组编码",
            character=len(self._characterDict),
            code=len(self._codeDict),
        )

        # ? 补充字母表，以支持编码包含字母的词条
        letters = "abcdefghijklmnopqrstuvwxyz"
        for ch in letters:
            self._characterDict[ch] = ch
            self._characterDict[ch.upper()] = ch

        # 解析字集码表
        self._parseCharset()

    def _parseTigress(
        self,
        lines: list[str],
        tableName: str,
    ) -> None:
        """解析行内容列表为码表字典

        Args:
            lines (list[str]): 行内容列表
            tableName (str): 码表名称
        """
        columns = ColumnsModel()
        for line in lines:
            item = line.strip()
            if not columns.isCompleted:
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = strToInt(safeGet(fields, columns.dict["weight"]))

            # 处理单字字典
            if len(word) == 1:
                # 取全码
                if word in self._characterDict:
                    if len(self._characterDict[word]) < len(code):
                        self._characterDict[word] = code
                else:
                    self._characterDict[word] = code

            # 处理编码字典
            if code in self._codeDict:
                # 收录所有词条项
                self._codeDict[code].append(
                    {"word": word, "weight": weight, "source": tableName}
                )
            elif code:
                self._codeDict[code] = [
                    {"word": word, "weight": weight, "source": tableName}
                ]

    def _parseCharset(self) -> None:
        """解析字集码表内容为字集集合"""
        charsetFile = self._tigressFiles["charset"]
        logger.info("开始解析字集码表: {}", charsetFile)

        lines = readFile(charsetFile)
        for line in lines:
            item = line.strip()
            fields = item.split("\t")
            if len(fields) != 2:
                continue
            word = fields[0]
            self._charset.add(word)

        logger.info(
            "解析完毕，读取到 {} 个常用字",
            len(self._charset),
        )

        # * 补充一些字母
        letters = "abcdefghijklmnopqrstuvwxyz"
        for ch in letters:
            self._charset.add(ch)
            self._charset.add(ch.upper())

    def _parseName(self) -> None:
        """解析原名码表文件"""
        if self._isParseName:
            return
        self._isParseName = True

        nameFile = self._tigressFiles["name"]
        logger.info("开始解析原名码表: {}", nameFile)

        lines = readFile(nameFile)
        for line in lines:
            item = line.strip()
            fields = item.split("\t")
            if len(fields) != 2:
                continue
            word = fields[0]
            units = fields[1].split(" ")
            if len(units) == 1:
                continue
            self._nameDict[word] = units[1:]

        logger.info(
            "解析完毕，读取到 {} 条原名",
            len(self._nameDict),
        )

    def _parseEmoji(self) -> None:
        """解析表情码表文件"""
        if self._isParseEmoji:
            return
        self._isParseEmoji = True

        emojiFile = self._tigressFiles["emoji"]
        logger.info("开始解析表情码表: {}", emojiFile)

        lines = readFile(emojiFile)
        for line in lines:
            item = line.strip()
            fields = item.split("\t")
            if len(fields) != 2:
                continue
            word = fields[0]
            units = fields[1].split(" ")
            if len(units) == 1:
                continue
            self._emojiDict[word] = units[1:]

        logger.info("解析完毕，读取到 {} 条表情", len(self._emojiDict))

    def _parseSymbols(self) -> None:
        """解析符号码表文件"""
        if self._isParseSymbols:
            return
        self._isParseSymbols = True

        symbolsFile = self._tigressFiles["symbols"]
        logger.info("开始解析符号码表: {}", symbolsFile)

        lines = readFile(symbolsFile, False)
        inShape = True
        lastComment = ""
        for line in lines:
            item = line.strip()
            if inShape:
                if item == "symbols:":
                    inShape = False
                    continue
            else:
                if item.startswith("#"):
                    lastComment = item[1:]
                    continue
                fields = item.split(": ")
                if len(fields) != 2:
                    lastComment = ""
                    continue
                wordList = re.findall(r"'/([a-zA-Z0-9]+)'", fields[0])
                if len(wordList) == 0:
                    lastComment = ""
                    continue
                word = wordList[0]
                units = [ele.strip() for ele in fields[1].strip(" []").split(",")]
                self._symbolsDict[word] = {
                    "comment": lastComment,
                    "symbols": units,
                }
                lastComment = ""

        logger.info("解析完毕，读取到 {} 条符号", len(self._symbolsDict))

    def _parseEnglish(self) -> None:
        """解析英文码表内容为英文字典"""
        if self._isParseEnglish:
            return
        self._isParseEnglish = True

        columns = ColumnsModel()
        englishFile = self._tigressFiles["english"]
        logger.info("开始解析英文码表: {}", englishFile)

        lines = readFile(englishFile)
        for line in lines:
            item = line.strip()
            if not columns.isCompleted:
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 2:
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = strToInt(safeGet(fields, columns.dict["weight"]))

            if code in self._englishDict:
                self._englishDict[code].append(
                    {"word": word, "weight": weight, "source": self._englishSourceName}
                )
            elif code:
                self._englishDict[code] = [
                    {"word": word, "weight": weight, "source": self._englishSourceName}
                ]

        logger.info(
            "解析完毕，读取到 {} 个英文",
            len(self._englishDict),
        )

    def _getCode(self, char: str, codeSize: int) -> str:
        """获取单字的编码

        Args:
            char (str): 单字
            codeSize (int): 取码位数

        Returns:
            str: 编码
        """
        if char in self._characterDict:
            return self._characterDict[char][0:codeSize]
        return ""

    def _getRange(self, word: str) -> bool:
        """获取词条所属的字集范围

        Args:
            word (str): 词条

        Returns:
            bool: `True` 表示属于常用字集范围，否则为全集
        """
        for ch in word:
            if not ch in self._charset:
                return False
        return True

    def _isSimple(self, word: str, code: str) -> bool:
        """是否为简词

        Args:
            word (str): 文本
            code (str): 编码

        Returns:
            bool: `True` 表示为简词
        """
        wordLen = len(word)
        codeLen = len(code)
        if codeLen == 0 or codeLen > 3:
            return False

        if wordLen <= 1:
            return False
        elif wordLen == 2:
            return codeLen <= 2
        elif wordLen == 3:
            return codeLen <= 3
        else:
            return codeLen == 1

    def _writeEnglish(self):
        """重写英文码表文件"""
        englishFile = self._tigressFiles["english"]
        logger.info("开始重写英文码表: {}", englishFile)

        writeContent: list[str] = []
        cacheList = CacheList()
        deleteCacheList = DeleteCacheList(self._englishDeleteCached.copy())
        columns = ColumnsModel()

        for item in self._englishCached:
            word = item["word"]
            tempCode = item["code"]
            while True:
                cacheList.push(
                    {"word": word, "code": tempCode, "weight": item["weight"]}
                )
                newCode = tempCode[0] + tempCode[1:].lower()
                if newCode == tempCode:
                    newCode = tempCode.lower()
                    if newCode == tempCode:
                        break

                tempCode = newCode

        lines = readFile(englishFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 2:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = safeGet(fields, columns.dict["weight"], "0")

            cacheItem = cacheList.find(word, code)
            if cacheItem:
                if deleteCacheList.find(word, code, cacheItem["weight"]):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word, code=code, weight=cacheItem["weight"]
                )
                writeContent.append(input)
                logger.info(
                    "将 {word}({code}) 的词频由 {old} 替换为 {new}",
                    word=word,
                    code=code,
                    old=weight,
                    new=cacheItem["weight"],
                )
            else:
                if deleteCacheList.find(word, code, weight):
                    logger.info(
                        "删除英文: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    continue
                writeContent.append(line)

        for item in cacheList:
            word = item["word"]
            code = item["code"]
            weight = item["weight"]
            if deleteCacheList.find(word, code, weight):
                # * 若存在于删除缓存中，则跳过处理
                continue
            input = columns.str.format(text=word, code=code, weight=weight)
            writeContent.append(input)
            logger.info(
                "新增英文词条: {word}({code}) - {weight}",
                word=word,
                code=code,
                weight=weight,
            )

        with io.open(englishFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")

        logger.info("重写英文单词码表完成")

    def _writeCharset(self):
        """重写字集码表文件"""
        charsetFile = self._tigressFiles["charset"]
        logger.info("开始重写字集码表: {}", charsetFile)
        with io.open(charsetFile, mode="a+", newline="\n", encoding="utf-8") as f:
            f.seek(0)  # ? 因为 "a+" 权限打开时默认在文件末尾
            content = f.read()

            # 移动到文件末尾以准备写入
            f.seek(0, 2)

            # 检查最后一行是否以换行符结束
            if not content.endswith("\n"):
                f.write("\n")

            for cache in self._charsetCached:
                input = cache + "\tt"
                f.write(input + "\n")
                logger.info("新增常用字: {word}", word=cache)
        logger.info("处理字集码表完成")

    def _writeCharacters(self):
        """重写单字码表文件"""
        charactersFile = self._tigressFiles["characters"]
        logger.info("开始重写单字码表: {}", charactersFile)

        writeContent: list[str] = []
        cacheList = CacheList(self._charactersCached.copy())
        deleteCacheList = DeleteCacheList(self._charactersDeleteCached.copy())
        columns = ColumnsModel()

        lines = readFile(charactersFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = safeGet(fields, columns.dict["weight"], "0")

            cacheItem = cacheList.find(word, code)
            if cacheItem:
                if deleteCacheList.find(word, code, cacheItem["weight"]):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word, code=code, weight=cacheItem["weight"]
                )
                if len(fields) == 4:
                    # ? 补全造词码部分
                    input += "\t" + fields[3]
                writeContent.append(input)
                logger.info(
                    "将 {word}({code}) 的字频由 {old} 替换为 {new}",
                    word=word,
                    code=code,
                    old=weight,
                    new=cacheItem["weight"],
                )
            else:
                if deleteCacheList.find(word, code, weight):
                    logger.info(
                        "删除单字: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    continue
                writeContent.append(line)

        for item in cacheList:
            word = item["word"]
            code = item["code"]
            weight = item["weight"]
            if deleteCacheList.find(word, code, weight):
                # * 若存在于删除缓存中，则跳过处理
                continue
            input = columns.str.format(
                text=word,
                code=code,
                weight=weight,
            )
            writeContent.append(input)
            logger.info(
                "新增单字: {word}({code}) - {weight}",
                word=word,
                code=code,
                weight=weight,
            )

        with io.open(charactersFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")
        logger.info("重写单字码表完成")

    def _writePhrases(self):
        """重写词组码表文件"""
        phrasesFile = self._tigressFiles["phrases"]
        logger.info("开始重写词组码表: {}", phrasesFile)

        writeContent: list[str] = []
        cacheList = CacheList(self._phrasesCached.copy())
        deleteCacheList = DeleteCacheList(self._phrasesDeleteCached.copy())
        columns = ColumnsModel()

        lines = readFile(phrasesFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = safeGet(fields, columns.dict["weight"], "0")

            cacheItem = cacheList.find(word, code)
            if cacheItem:
                if deleteCacheList.find(word, code, cacheItem["weight"]):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word,
                    code=code,
                    weight=cacheItem["weight"],
                )
                writeContent.append(input)
                logger.info(
                    "将 {word}({code}) 的词频由 {old} 替换为 {new}",
                    word=word,
                    code=code,
                    old=weight,
                    new=cacheItem["weight"],
                )
            else:
                if deleteCacheList.find(word, code, weight):
                    logger.info(
                        "删除词组: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    continue
                writeContent.append(line)

        for item in cacheList:
            if deleteCacheList.find(item["word"], item["code"], item["weight"]):
                # * 若存在于删除缓存中，则跳过处理
                continue
            self._tigressCached.append(item)

        with io.open(phrasesFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")
        logger.info("重写词组码表完成")

    def _writeSimple(self):
        """重写简词码表文件"""
        simpleFile = self._tigressFiles["simple"]
        logger.info("开始重写简词码表: {}", simpleFile)

        writeContent: list[str] = []
        deleteSet: set[str] = set()
        cacheList = CacheList(self._simpleCached.copy())
        deleteCacheList = DeleteCacheList(self._simpleDeleteCached.copy())
        columns = ColumnsModel()

        for charsetCache in self._charsetCached:
            deleteSet.add(self._getCode(charsetCache, 3))

        lines = readFile(simpleFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = safeGet(fields, columns.dict["weight"])

            if code in deleteSet:
                logger.info(
                    "简词码 {word}({code}) 与新增的常用字冲突，故删除",
                    word=word,
                    code=code,
                )
                continue

            item = cacheList.find(word, code)
            if item:
                if deleteCacheList.find(word, code, item["weight"]):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word,
                    code=code,
                    weight=item["weight"],
                )
                writeContent.append(input)
                logger.info(
                    "将 {word}({code}) 的词频由 {old} 替换为 {new}",
                    word=word,
                    code=code,
                    old=weight,
                    new=item["weight"],
                )
            else:
                if deleteCacheList.find(word, code, weight):
                    logger.info(
                        "删除简词: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    continue
                writeContent.append(line)

        for item in cacheList:
            word = item["word"]
            code = item["code"]
            weight = item["weight"]
            if code in deleteSet:
                logger.info("简词码 {code} 与新增常用字冲突，故跳过处理")
                continue
            elif deleteCacheList.find(word, code, weight):
                # * 若存在于删除缓存中，则跳过处理
                continue
            else:
                input = columns.str.format(
                    text=word,
                    code=code,
                    weight=weight,
                )
                writeContent.append(input)
                logger.info(
                    "新增简词: {word}({code}) - {weight}",
                    word=word,
                    code=code,
                    weight=weight,
                )

        with io.open(simpleFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")
        logger.info("重写简词码表完成")

    def _writeMain(self):
        """重写主码表文件和拼音滤镜文件"""
        mainFile = self._tigressFiles["main"]
        logger.info("开始重写主码表: {}", mainFile)

        pinyinFile = self._tigressFiles["pinyin"]
        pinyinOpenccFile = self._tigressFiles["pinyintip"]
        writeContent: list[str] = []
        cacheList = CacheList(self._tigressCached.copy())
        deleteCacheList = DeleteCacheList(self._tigressDeleteCached.copy())
        columns = ColumnsModel()

        lines = readFile(mainFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])
            weight = safeGet(fields, columns.dict["weight"], "0")

            cacheItem = cacheList.find(word, code)
            if cacheItem:
                if deleteCacheList.find(word, code, cacheItem["weight"]):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word,
                    code=code,
                    weight=cacheItem["weight"],
                )
                writeContent.append(input)
                logger.info(
                    "将 {word}({code}) 的词频由 {old} 替换为 {new}",
                    word=word,
                    code=code,
                    old=weight,
                    new=cacheItem["weight"],
                )
            else:
                if deleteCacheList.find(word, code, weight):
                    logger.info(
                        "删除词条: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    continue
                writeContent.append(line)

        if len(cacheList) > 0:
            pinyinCacheSet: set[str] = set()

            for item in cacheList:
                word = item["word"]
                code = item["code"]
                weight = item["weight"]
                if deleteCacheList.find(word, code, weight):
                    # * 若存在于删除缓存中，则跳过处理
                    continue
                input = columns.str.format(
                    text=word,
                    code=code,
                    weight=weight,
                )
                writeContent.append(input)
                pinyinCacheSet.add(word)
                logger.info(
                    "新增词条: {word}({code}) - {weight}",
                    word=word,
                    code=code,
                    weight=weight,
                )

            if self._pinyinFileStatus and len(pinyinCacheSet) > 0:
                logger.info("开始处理拼音码表文件: {}", pinyinFile)
                with io.open(
                    pinyinFile, mode="a+", newline="\n", encoding="utf-8"
                ) as f:
                    pinyinColmuns = ColumnsModel()
                    f.seek(0)  # ? 因为 "a+" 权限打开时默认在文件末尾
                    for line in f:
                        if pinyinColmuns.isCompleted:
                            break
                        item = line.strip()
                        pinyinColmuns.lineHandler(item)

                    f.seek(0)
                    content = f.read()

                    # 移动到文件末尾以准备写入
                    f.seek(0, 2)

                    # 检查最后一行是否以换行符结束
                    if not content.endswith("\n"):
                        f.write("\n")

                    for word in pinyinCacheSet:
                        code = getPinyin(self.getCleanWord(word))
                        input = pinyinColmuns.str.format(text=word, code=code, weight=0)
                        f.write(input + "\n")
                        logger.info(
                            "新增拼音词条: {word}({code})", word=word, code=code
                        )
                    logger.info("处理拼音码表文件完成")

            if self._pinyinTipFileStatus and len(pinyinCacheSet) > 0:
                logger.info("开始处理拼音滤镜文件: {}", pinyinOpenccFile)
                with io.open(
                    pinyinOpenccFile, mode="a+", newline="\n", encoding="utf-8"
                ) as f:
                    for word in pinyinCacheSet:
                        code = getTonePinyin(self.getCleanWord(word))
                        input = word + "\t〔" + code + "〕\n"
                        f.write(input)
                        logger.info(
                            "新增拼音滤镜词条: {word}({code})", word=word, code=code
                        )
                    logger.info("处理拼音滤镜文件完成")

        with io.open(mainFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")
        logger.info("重写主码表完成")

    def _writeName(self):
        """重写原名码表文件"""
        nameFile = self._tigressFiles["name"]
        writeList: list[str] = []

        logger.info("开始重写原名码表: {}", nameFile)
        lines = readFile(nameFile)
        for line in lines:
            line = line.strip()
            fields = line.split("\t")
            if len(fields) != 2:
                continue

            word = fields[0]
            tempUnits = fields[1].split(" ")
            units = tempUnits[1:]

            for cacheKey in list(self._nameCached.keys()):
                if cacheKey == word:
                    units = [
                        re.sub(" ", "&nbsp;", x) for x in self._nameCached[cacheKey]
                    ]
                    del self._nameCached[cacheKey]
                    logger.info("重写原名: {word} -> {units}", word=word, units=units)

            if len(units) != 0:
                # ? 忽略空列表，即表示删除此行
                writeList.append(f"{word}\t{word} {' '.join(units)}")

        for cacheKey in self._nameCached:
            if len(self._nameCached[cacheKey]) != 0:
                units = [re.sub(" ", "&nbsp;", x) for x in self._nameCached[cacheKey]]
                writeList.append(f"{cacheKey}\t{cacheKey} {' '.join(units)}")
                logger.info("新增原名: {word} -> {units}", word=cacheKey, units=units)

        with io.open(nameFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeList:
                f.write(line + "\n")
        logger.info("重写原名码表完成")

    def _writeEmoji(self):
        """重写表情码表文件"""
        emojiFile = self._tigressFiles["emoji"]
        writeList: list[str] = []

        logger.info("开始重写表情码表: {}", emojiFile)
        lines = readFile(emojiFile)
        for line in lines:
            line = line.strip()
            fields = line.split("\t")
            if len(fields) != 2:
                continue

            word = fields[0]
            tempUnits = fields[1].split(" ")
            units = tempUnits[1:]

            for cacheKey in list(self._emojiCached.keys()):
                if cacheKey == word:
                    units = self._emojiCached[cacheKey]
                    del self._emojiCached[cacheKey]
                    logger.info("重写表情: {word} -> {units}", word=word, units=units)

            if len(units) != 0:
                # ? 忽略空列表，即表示删除此行
                writeList.append(f"{word}\t{word} {' '.join(units)}")

        for cacheKey in self._emojiCached:
            units = self._emojiCached[cacheKey]
            if len(units) != 0:
                writeList.append(f"{cacheKey}\t{cacheKey} {' '.join(units)}")
                logger.info("新增表情: {word} -> {units}", word=cacheKey, units=units)

        with io.open(emojiFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeList:
                f.write(line + "\n")
        logger.info("重写表情码表完成")

    def _writeSymbols(self):
        """重写符号码表文件"""
        symbolsFile = self._tigressFiles["symbols"]
        writeList: list[str] = []

        logger.info("开始重写符号码表: {}", symbolsFile)
        lines = readFile(symbolsFile, False)
        inShape = True
        lastComment = ""
        lastLine = ""
        for line in lines:
            item = line.strip()
            if inShape:
                writeList.append(line)
                if item == "symbols:":
                    inShape = False
                    lastLine = line
                    continue
            elif item.startswith("#"):
                if lastComment:
                    writeList.append(lastLine)
                lastComment = item[1:]
                lastLine = line
                continue
            else:
                fields = item.split(": ")
                if len(fields) != 2:
                    writeList.append(line)
                    lastComment = ""
                    lastLine = ""
                    continue
                wordList = re.findall(r"'/([a-zA-Z0-9]+)'", fields[0])
                if len(wordList) == 0:
                    writeList.append(line)
                    lastComment = ""
                    lastLine = ""
                    continue
                word = wordList[0]
                units = [ele.strip() for ele in fields[1].strip(" []").split(",")]

                state = False
                for cacheKey in list(self._symbolsCached.keys()):
                    if cacheKey == word:
                        units = self._symbolsCached[cacheKey].get("symbols")
                        lastComment = self._symbolsCached[cacheKey].get("comment")
                        del self._symbolsCached[cacheKey]
                        if len(units) == 0:
                            logger.info("删除符号: {word}", word=word)
                        else:
                            logComment = lastComment
                            if lastComment:
                                writeList.append(f"#{lastComment}")
                                lastComment = ""

                            writeList.append(f"    '/{word}': [ {', '.join(units)} ]")

                            logger.info(
                                "重写符号: {word} -> {units} | 注释: {comment}",
                                word=word,
                                units=units,
                                comment=logComment,
                            )
                        state = True
                        break

                if not state:
                    if lastComment:
                        writeList.append(lastLine)
                        lastComment = ""
                        lastLine = ""
                    writeList.append(line)

        for cacheKey in self._symbolsCached:
            units = self._symbolsCached[cacheKey].get("symbols")
            if len(units) != 0:
                lastComment = self._symbolsCached[cacheKey].get("comment")
                if lastComment:
                    writeList.append(f"#{lastComment}")
                writeList.append(f"    '/{cacheKey}': [ {', '.join(units)} ]")
                logger.info(
                    "新增符号: {word} -> {units} | 注释: {comment}",
                    word=cacheKey,
                    units=units,
                    comment=lastComment,
                )

        with io.open(symbolsFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeList:
                f.write(line + "\n")
        logger.info("重写符号码表完成")

    def getCleanWord(self, word: str) -> str:
        """获取不带符号的字符串

        Args:
            word (str): 源字符串

        Returns:
            str: 不带符号的字符串
        """
        return word.translate(self._deleteCharsTable)

    def tinyPinyinTable(self) -> bool:
        """整理拼音码表文件"""
        if not self._pinyinFileStatus:
            logger.warning("未找到拼音码表文件，跳过整理")
            return False

        pinyinFile = self._tigressFiles["pinyin"]
        writeContent: list[str] = []
        cacheDict: dict[str, list[str]] = {}
        columns = ColumnsModel()

        logger.info("开始整理拼音码表文件: {}", pinyinFile)

        lines = readFile(pinyinFile, False)
        for line in lines:
            item = line.strip()
            if item.startswith("#"):
                writeContent.append(line)
                continue

            if not columns.isCompleted:
                writeContent.append(line)
                columns.lineHandler(item)
                continue

            fields = item.split("\t")
            if len(fields) < 3:
                writeContent.append(line)
                continue
            word = safeGet(fields, columns.dict["text"])
            code = safeGet(fields, columns.dict["code"])

            if word in cacheDict:
                if not code in cacheDict[word]:
                    cacheDict[word].append(code)
                    writeContent.append(line)
            else:
                cacheDict[word] = [code]
                writeContent.append(line)

        with io.open(pinyinFile, mode="w", newline="\n", encoding="utf-8") as f:
            for line in writeContent:
                f.write(line + "\n")
        logger.info("整理拼音码表文件完毕")
        return True

    def tinyOpenCCPinyin(self) -> bool:
        """整理拼音滤镜文件"""
        if not self._pinyinTipFileStatus:
            logger.warning("未找到拼音滤镜文件，跳过整理")
            return False

        pinyinOpenccFile = self._tigressFiles["pinyintip"]
        wordSet: set[str] = set()

        logger.info("开始整理拼音滤镜文件: {}", pinyinOpenccFile)
        self._parseMain()

        logger.info("解析用户码表...")
        for code in self._codeDict:
            for item in self._codeDict[code]:
                word = item["word"]
                if len(word) > 1:
                    wordSet.add(word)
        logger.info("解析完毕，读取到 {} 个词组", len(wordSet))
        logger.info("重写拼音滤镜文件...")
        with io.open(pinyinOpenccFile, mode="w", newline="\n", encoding="utf-8") as f:
            for unit in wordSet:
                tonePinyin = getTonePinyin(self.getCleanWord(unit))
                input = unit + "\t〔" + tonePinyin + "〕\n"
                f.write(input)
        logger.info("整理拼音滤镜文件完毕")
        return True

    def checkShortThreeWords(self):
        """校验三简词"""
        logger.info("开始校验三简词...")
        self._parseMain()

        for code in self._codeDict:
            if len(code) == 3:
                record: list[str] = []
                hadWords = 0
                hadOther = False
                for c in self._codeDict[code]:
                    cw = c["word"]
                    w = self.getCleanWord(cw)
                    if len(w) == 3:
                        hadWords += 1
                        record.append(cw)
                    elif self._getRange(w):
                        hadOther = True
                        record.append(cw)

                if (hadWords > 1) or (hadOther and hadWords > 0):
                    logger.warning(
                        "编码 {code} 存在冲突的词条: {list}", code=code, list=record
                    )
            elif len(code) == 4:
                threeWords: list[str] = []
                for c in self._codeDict[code]:
                    w = self.getCleanWord(c["word"])
                    if len(w) == 3:
                        threeWords.append(c["word"])
                if len(threeWords) == 0:
                    continue

                tc = code[:3]
                hadSimple = False
                if tc in self._codeDict:
                    for sc in self._codeDict[tc]:
                        sw = self.getCleanWord(sc["word"])
                        if len(sw) == 3 or self._getRange(sw):
                            hadSimple = True
                            break

                if not hadSimple:
                    logger.info("以下词条可编码成三简词: {}", threeWords)
        logger.info("校验三简词完成")

    def fileChecker(self) -> str:
        """文件存在性检查器

        Returns:
            str: 所不存在的文件路径
        """
        for key in ["main", "phrases", "characters", "charset"]:
            filepath = self._tigressFiles[key]
            if not os.path.exists(filepath):
                return filepath
        return ""

    def encode(self, word: str) -> EncodeResult:
        """编码词条

        Args:
            word (str): 词条内容

        Returns:
            str: 编码结果
        """
        cleanWord = self.getCleanWord(word)
        newWordLen = len(cleanWord)

        if newWordLen == 0:
            return {
                "cleanWord": "",
                "isEnglish": False,
                "code": "",
                "weight": 0,
                "range": False,
            }

        isEnglish = isPureEnglish(cleanWord)  # 是否为英文单词
        if isEnglish:
            self._parseEnglish()
        else:
            self._parseMain()

        newCode = ""
        weight = 0
        if isEnglish:
            # 英文单词
            newCode = cleanWord
        elif newWordLen == 1:
            # 单字
            newCode = self._getCode(cleanWord, 4)
        elif newWordLen == 2:
            # 二字词组
            newCode = self._getCode(cleanWord[0], 2) + self._getCode(cleanWord[1], 2)
        elif newWordLen == 3:
            # 三字词组
            newCode = (
                self._getCode(cleanWord[0], 1)
                + self._getCode(cleanWord[1], 1)
                + self._getCode(cleanWord[2], 2)
            )
        else:
            # 多字词组
            newCode = (
                self._getCode(cleanWord[0], 1)
                + self._getCode(cleanWord[1], 1)
                + self._getCode(cleanWord[2], 1)
                + self._getCode(cleanWord[-1], 1)
            )

        if not isEnglish and newCode and not newCode in self._codeDict:
            weight = 255

        if isEnglish:
            logger.debug("编码英文单词: {word} | 编码: {code}", word=word, code=newCode)
        else:
            logger.debug(
                "编码词条: {word}({code})",
                word=word,
                code=newCode,
            )

        return {
            "cleanWord": cleanWord,
            "isEnglish": isEnglish,
            "code": newCode,
            "weight": weight,
            "range": self._getRange(cleanWord),
        }

    def simple(self, word: str) -> EncodeResult:
        """简码编码词条

        Args:
            word (str): 词条内容

        Returns:
            EncodeResult: 编码结果
        """
        cleanWord = self.getCleanWord(word)
        newWordLen = len(cleanWord)

        if newWordLen == 0:
            return {
                "cleanWord": "",
                "isEnglish": False,
                "code": "",
                "weight": 0,
                "range": False,
            }

        isEnglish = isPureEnglish(cleanWord)  # 是否为英文单词
        if isEnglish:
            self._parseEnglish()
        else:
            self._parseMain()

        newCode = ""
        weight = 0

        if isEnglish:
            # 英文单词
            newCode = cleanWord.lower()  # 小写化
        elif newWordLen == 1:
            # 单字
            newCode = self._getCode(cleanWord, 1)  # 只取首码
        elif newWordLen == 2:
            # 二字词组
            newCode = self._getCode(cleanWord[0], 1) + self._getCode(cleanWord[1], 1)
        elif newWordLen == 3:
            # 三字词组
            newCode = (
                self._getCode(cleanWord[0], 1)
                + self._getCode(cleanWord[1], 1)
                + self._getCode(cleanWord[2], 1)
            )
        else:
            # 多字词组
            newCode = (
                self._getCode(cleanWord[0], 1)
                + self._getCode(cleanWord[1], 1)
                + self._getCode(cleanWord[2], 1)
                + self._getCode(cleanWord[-1], 1)
            )

        if not isEnglish and newCode and not newCode in self._codeDict:
            weight = 255

        if isEnglish:
            logger.debug("英文单词简码: {word} | 编码: {code}", word=word, code=newCode)
        else:
            logger.debug(
                "简码词条: {word}({code})",
                word=word,
                code=newCode,
            )

        return {
            "cleanWord": cleanWord,
            "isEnglish": isEnglish,
            "code": newCode,
            "weight": weight,
            "range": self._getRange(cleanWord),
        }

    def query(self, code: str, isEnglish: bool) -> list[CodeTableUnit]:
        """查询输入编码的重码详情

        Args:
            code (str): 输入编码
            isEnglish (bool): 是否为英文

        Returns:
            list[CodeTableUnit]: 重码详情
        """
        if len(code) == 0:
            return []

        results: list[CodeTableUnit] = []
        if isEnglish:
            if code in self._englishDict:
                for item in self._englishDict[code]:
                    results.append(
                        {
                            **item,
                            "range": True,
                        }
                    )
        else:
            self._parseMain()
            if code in self._codeDict:
                # 降序排序
                self._codeDict[code].sort(key=lambda item: item["weight"], reverse=True)
                for item in self._codeDict[code]:
                    rangeState = self._getRange(self.getCleanWord(item["word"]))
                    results.append(
                        {
                            **item,
                            "range": rangeState,
                        }
                    )

        return results

    def nameQuery(self, name: str) -> list[str]:
        """查询原名

        Args:
            name (str): 译名

        Returns:
            list[str]: 原名列表
        """
        self._parseName()
        if name in self._nameDict:
            return copy.deepcopy(self._nameDict[name])
        return []

    def emojiQuery(self, name: str) -> list[str]:
        """查询表情

        Args:
            name (str): 表情名称

        Returns:
            list[str]: 表情列表
        """
        self._parseEmoji()
        if name in self._emojiDict:
            return copy.deepcopy(self._emojiDict[name])
        return []

    def symbolsQuery(self, name: str) -> SymbolsUnit:
        """查询符号

        Args:
            name (str): 符号编码

        Returns:
            SymbolsUnit: 符号信息
        """
        self._parseSymbols()
        if name in self._symbolsDict:
            return copy.deepcopy(self._symbolsDict[name])
        return {"comment": "", "symbols": []}

    def updateName(self, transName: str, oriNames: list[str]):
        """更新名称列表

        Args:
            transName (str): 译名
            oriNames (list[str]): 原名列表
        """
        self._nameCached[transName] = oriNames
        self._nameDict[transName] = oriNames
        logger.debug("更新原名缓存: {trans} -> {ori}", trans=transName, ori=oriNames)

    def updateEmoji(self, emojiName: str, emojiList: list[str]):
        """更新表情列表

        Args:
            emojiName (str): 表情名称
            emojiList (list[str]): 表情列表
        """
        self._emojiCached[emojiName] = emojiList
        self._emojiDict[emojiName] = emojiList
        logger.debug("更新表情缓存: {name} -> {list}", name=emojiName, list=emojiList)

    def updateSymbols(self, code: str, comment: str, symbols: list[str]):
        """更新符号列表

        Args:
            code (str): 符号编码
            symbols (list[str]): 符号列表
        """
        symbol: SymbolsUnit = {"comment": comment, "symbols": symbols}
        self._symbolsCached[code] = symbol
        self._symbolsDict[code] = symbol
        logger.debug(
            "更新符号缓存: {code} -> {list} | 注释: {comment}",
            code=code,
            list=symbols,
            comment=comment,
        )

    def add(self, word: str, code: str, weight: int) -> CacheStatus:
        """添加词条

        Args:
            word (str): 词条内容
            code (str): 编码
            weight (int): 权重

        Returns:
            WordCacheStatus: 词条添加状态
        """
        cacheStatus: CacheStatus = CacheStatus.UNKNOWN
        cleanWord = self.getCleanWord(word)
        isEnglish = isPureEnglish(cleanWord)  # 是否为英文单词

        if isEnglish:
            if self._englishFileStatus:
                # 缓存至英文表中
                self._englishCached.append(
                    {"word": word, "code": code, "weight": weight}
                )

                cacheStatus = CacheStatus.ENGLISH
                logger.debug(
                    "缓存至英文码表: {word}({code}) - {weight}",
                    word=word,
                    code=code,
                    weight=weight,
                )

                # 更新当前英文字典
                if code in self._englishDict:
                    exist = False
                    for unit in self._englishDict[code]:
                        if word == unit["word"]:
                            unit["weight"] = weight
                            exist = True
                            break
                    if not exist:
                        self._englishDict[code].append(
                            {
                                "word": word,
                                "weight": weight,
                                "source": self._englishSourceName,
                            }
                        )
                else:
                    self._englishDict[code] = [
                        {
                            "word": word,
                            "weight": weight,
                            "source": self._englishSourceName,
                        }
                    ]
            else:
                cacheStatus = CacheStatus.ENGLISH_EXCEPTION
                logger.warning(
                    "不存在英文码表文件，未缓存: {word}({code})", word=word, code=code
                )
        elif cleanWord and code:
            source = self._mainSourceName
            isSimp = self._isSimple(cleanWord, code)  # 是否为简词

            if isSimp:
                if self._simpleFileStatus:
                    # 缓存至简词表中
                    self._simpleCached.append(
                        {"word": word, "code": code, "weight": weight}
                    )
                    cacheStatus = CacheStatus.SIMPLE
                    logger.debug(
                        "缓存至简词码表: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                    source = self._simpleSourceName
                else:
                    cacheStatus = CacheStatus.SIMPLE_EXCEPTION
                    logger.warning(
                        "不存在简词码表文件，未缓存: {word}({code})",
                        word=word,
                        code=code,
                    )
            else:
                isHandle = False
                if code in self._codeDict:
                    for unit in self._codeDict[code]:
                        if word == unit["word"]:
                            if unit["source"] == self._phrasesSourceName:
                                self._phrasesCached.append(
                                    {
                                        "word": word,
                                        "code": code,
                                        "weight": weight,
                                    }
                                )
                                cacheStatus = CacheStatus.PHRASES
                                logger.debug(
                                    "缓存至词组码表: {word}({code}) - {weight}",
                                    word=word,
                                    code=code,
                                    weight=weight,
                                )
                                source = self._phrasesSourceName
                                isHandle = True
                            elif unit["source"] == self._charactersSourceName:
                                self._charactersCached.append(
                                    {
                                        "word": word,
                                        "code": code,
                                        "weight": weight,
                                    }
                                )
                                cacheStatus = CacheStatus.CHARACTERS
                                logger.debug(
                                    "缓存至单字码表: {word}({code}) - {weight}",
                                    word=word,
                                    code=code,
                                    weight=weight,
                                )
                                source = self._charactersSourceName
                                isHandle = True
                            break

                if not isHandle:
                    if len(word) == 1:
                        self._charactersCached.append(
                            {
                                "word": word,
                                "code": code,
                                "weight": weight,
                            }
                        )
                        cacheStatus = CacheStatus.NEW_CHARACTERS
                        logger.debug(
                            "缓存至单字码表: {word}({code}) - {weight}",
                            word=word,
                            code=code,
                            weight=weight,
                        )
                        source = self._charactersSourceName
                    else:
                        self._tigressCached.append(
                            {
                                "word": word,
                                "code": code,
                                "weight": weight,
                            }
                        )
                        cacheStatus = CacheStatus.MAIN
                        logger.debug(
                            "缓存至主码表: {word}({code}) - {weight}",
                            word=word,
                            code=code,
                            weight=weight,
                        )
                        source = self._mainSourceName

            # 更新当前字典
            if code in self._codeDict:
                exist = False
                for unit in self._codeDict[code]:
                    if word == unit["word"] and source == unit["source"]:
                        unit["weight"] = weight
                        exist = True
                        break
                if not exist:
                    self._codeDict[code].append(
                        {
                            "word": word,
                            "weight": weight,
                            "source": source,
                        }
                    )
            else:
                self._codeDict[code] = [
                    {
                        "word": word,
                        "weight": weight,
                        "source": source,
                    }
                ]

            for ch in cleanWord:
                if not self._getRange(ch):
                    self._charsetCached.add(ch)
                    self._charset.add(ch)
                    logger.debug("缓存至字集码表: {word}", word=ch)

        return cacheStatus

    def delete(self, item: WordTableUnit):
        """删除词条

        Args:
            item (DeleteUnit): 待删除的词条
        """
        source = item["source"]
        code = item["code"]
        word = item["word"]
        weight = item["weight"]
        isEnglish = source == self._englishSourceName

        if isEnglish:
            if code in self._englishDict:
                for unit in self._englishDict[code]:
                    if word == unit["word"] and weight == unit["weight"]:
                        self._englishDict[code].remove(unit)
                        self._englishDeleteCached.append(item)
                        logger.debug(
                            "待删除英文: {word}({code}) - {weight}",
                            word=word,
                            code=code,
                            weight=weight,
                        )
                        break
        else:
            if code in self._codeDict:
                for unit in self._codeDict[code]:
                    if (
                        word == unit["word"]
                        and weight == unit["weight"]
                        and source == unit["source"]
                    ):
                        self._codeDict[code].remove(unit)
                        label = ""

                        match source:
                            case self._mainSourceName:
                                self._tigressDeleteCached.append(item)
                                label = "待删除词条"
                            case self._simpleSourceName:
                                self._simpleDeleteCached.append(item)
                                label = "待删除简码"
                            case self._phrasesSourceName:
                                self._phrasesDeleteCached.append(item)
                                label = "待删除词组"
                            case self._charactersSourceName:
                                self._charactersDeleteCached.append(item)
                                label = "待删除单字"
                            case _:
                                label = "无法删除"

                        logger.debug(
                            "{label}: {word}({code}) - {weight}",
                            label=label,
                            word=word,
                            code=code,
                            weight=weight,
                        )
                        break

    def edit(self, item: WordTableUnit) -> CacheStatus:
        """编辑已有词条的权重"""
        cacheStatus: CacheStatus = CacheStatus.UNKNOWN
        word = item["word"]
        code = item["code"]
        weight = item["weight"]
        source = item["source"]
        isEnglish = source == self._englishSourceName
        if isEnglish:
            # 缓存至英文表中
            self._englishCached.append({"word": word, "code": code, "weight": weight})

            cacheStatus = CacheStatus.ENGLISH
            logger.debug(
                "缓存至英文码表: {word}({code}) - {weight}",
                word=word,
                code=code,
                weight=weight,
            )

            # 更新当前英文字典
            for unit in self._englishDict[code]:
                if word == unit["word"]:
                    unit["weight"] = weight
                    break
        else:
            match source:
                case self._simpleSourceName:
                    # 缓存至简词表中
                    self._simpleCached.append(
                        {"word": word, "code": code, "weight": weight}
                    )
                    cacheStatus = CacheStatus.SIMPLE
                    logger.debug(
                        "缓存至简词码表: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                case self._phrasesSourceName:
                    self._phrasesCached.append(
                        {
                            "word": word,
                            "code": code,
                            "weight": weight,
                        }
                    )
                    cacheStatus = CacheStatus.PHRASES
                    logger.debug(
                        "缓存至词组码表: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                case self._charactersSourceName:
                    self._charactersCached.append(
                        {
                            "word": word,
                            "code": code,
                            "weight": weight,
                        }
                    )
                    cacheStatus = CacheStatus.CHARACTERS
                    logger.debug(
                        "缓存至单字码表: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )
                case self._mainSourceName:
                    self._tigressCached.append(
                        {
                            "word": word,
                            "code": code,
                            "weight": weight,
                        }
                    )
                    cacheStatus = CacheStatus.MAIN
                    logger.debug(
                        "缓存至主码表: {word}({code}) - {weight}",
                        word=word,
                        code=code,
                        weight=weight,
                    )

            # 更新当前字典
            for unit in self._codeDict[code]:
                if word == unit["word"] and source == unit["source"]:
                    unit["weight"] = weight
                    break

            # ? 此处不应添加字集条目
        return cacheStatus

    def getWorkDir(self) -> str:
        """获取工作目录"""
        return self._workDir

    def getNameFileStatus(self) -> bool:
        """获取原名文件状态"""
        return self._nameFileStatus

    def getEmojiFileStatus(self) -> bool:
        """获取表情文件状态"""
        return self._emojiFileStatus

    def getSymbolsFileStatus(self) -> bool:
        """获取符号文件状态"""
        return self._symbolsFileStatus

    def writer(self) -> ExitCode:
        """码表文件写入器

        Returns:
            int: 状态码，`0` 表示有常规写入；`3` 表示无实际写入操作
        """
        writeState = False

        if len(self._englishCached) > 0 or len(self._englishDeleteCached) > 0:
            self._writeEnglish()
            writeState = True
        if len(self._charsetCached) > 0:
            self._writeCharset()
            writeState = True
        if len(self._charactersCached) > 0 or len(self._charactersDeleteCached) > 0:
            self._writeCharacters()
            writeState = True
        if len(self._phrasesCached) > 0 or len(self._phrasesDeleteCached) > 0:
            self._writePhrases()
            writeState = True
        if (
            len(self._simpleCached) > 0
            or len(self._simpleDeleteCached) > 0
            or len(self._charsetCached) > 0
        ):
            self._writeSimple()
            writeState = True
        if len(self._tigressCached) > 0 or len(self._tigressDeleteCached) > 0:
            self._writeMain()
            writeState = True
        if len(self._nameCached) > 0:
            self._writeName()
            writeState = True
        if len(self._emojiCached) > 0:
            self._writeEmoji()
            writeState = True
        if len(self._symbolsCached) > 0:
            self._writeSymbols()
            writeState = True

        return ExitCode.SUCCESS if writeState else ExitCode.NOTHING

    def encodeFile(self, file: str) -> ExitCode:
        """编码词条文件

        Args:
            file (str): 词条输入文件

        Returns:
            ExitCode: 退出状态
        """
        if not os.path.exists(file):
            logger.error("词条输入文件不存在")
            return ExitCode.ERROR

        inputSet = set(readFile(file))
        if len(inputSet) == 0:
            logger.warning("词条输入文件内容为空")
            return ExitCode.NOTHING

        logger.info("共读取到 {} 个输入词条", len(inputSet))

        for line in inputSet:
            item = line.strip()
            if len(item) <= 1:
                continue

            res = self.encode(item)
            dup = self.query(res["code"], res["isEnglish"])
            exists = any(ele["word"] == item for ele in dup)
            if exists:
                continue

            if res["isEnglish"] and self._englishFileStatus:
                self._englishCached.append(
                    {"word": item, "code": res["code"], "weight": 0}
                )
            else:
                self._tigressCached.append(
                    {"word": item, "code": res["code"], "weight": 0}
                )

        writeState = False
        if len(self._englishCached) > 0:
            self._writeEnglish()
            writeState = True
        if len(self._tigressCached) > 0:
            self._writeMain()
            writeState = True
        logger.info(
            "共批量写入 {} 个词条", len(self._englishCached) + len(self._tigressCached)
        )

        return ExitCode.SUCCESS if writeState else ExitCode.NOTHING
