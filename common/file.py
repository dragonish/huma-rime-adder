#!/usr/bin/env python
# coding: utf-8

import io
import os
import re
import sys
from loguru import logger
from pathlib import Path
from datetime import datetime


def getTableSource(filename: str) -> str:
    """获取码表对应的源名称

    Args:
        filename (str): 码表名称

    Returns:
        str: 源名称
    """
    tableNameList = re.findall(r"([^/\\]+)\.dict\.yaml$", filename)
    return tableNameList[0] if len(tableNameList) > 0 else filename


@logger.catch
def readFile(path: str, filterComment=True) -> list[str]:
    """读取文件至列表，行尾不含换行符

    Args:
        path (str): 文件路径
        filterComment (bool): 是否过滤掉空行和以 `#` 开头的项

    Returns:
        list[str]: 行内容列表
    """
    try:
        with io.open(path, mode="r", encoding="utf-8") as f:
            readList = f.read().splitlines()  # 不读入行尾的换行符
            if filterComment:
                readList = [
                    item for item in readList if item and not item.startswith("#")
                ]

            return readList
    except FileExistsError:
        logger.error("尝试处理不存在的文件: {}", path)
    except PermissionError:
        logger.error("没有权限访问该文件: {}", path)
    except IOError:
        logger.error("I/O 错误: {}", path)
    except ValueError:
        logger.error("值错误: {}", path)
    return []


def getProgramPath():
    """获取程序所在的原始目录（考虑 PyInstaller 打包情况）"""
    try:
        # PyInstaller 打包后获取程序原始路径
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.abspath(__file__))
    except:
        return os.path.dirname(os.path.abspath(__file__))


def isDirectoryWritable(directory: Path) -> bool:
    """检查目录是否可写"""
    try:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

        # 创建测试文件验证写入权限
        testFile = directory / f".test_write_{datetime.now().timestamp()}"
        with open(testFile, "w") as f:
            f.write("test")
        testFile.unlink()  # 删除测试文件
        return True
    except (PermissionError, OSError):
        return False


def openDirectory(directory: str):
    """打开目录"""
    try:
        import subprocess
        import platform

        system = platform.system().lower()

        logger.debug(f"正在打开目录: {directory}")

        if system == "darwin":
            # macOS
            subprocess.run(["open", directory])
        elif system == "windows":
            # Windows
            subprocess.run(["explorer", directory], shell=True)
        elif system == "linux":
            # Linux
            subprocess.run(["xdg-open", directory])
        else:
            logger.warning(f"不支持的操作系统: {system}")

        logger.debug("目录打开成功")

    except Exception as e:
        logger.error(f"打开目录失败: {e}")
        logger.info(f"请手动打开: {directory}")
