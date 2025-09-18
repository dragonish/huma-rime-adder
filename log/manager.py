#!/usr/bin/env python
# coding: utf-8

import os
import sys
from loguru import logger
from pathlib import Path
from common.file import isDirectoryWritable, openDirectory


class LogManager:
    """日志管理器，处理不同平台的日志文件存储"""

    _appName: str = "huma-rime-adder"
    _logDir: Path = Path.cwd()

    @classmethod
    def _initialize(cls):
        """初始化"""
        cls._logDir = cls._getLogDirectory()
        cls._logDir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _getLogDirectory(cls) -> Path:
        """获取日志目录（跨平台兼容）"""
        if sys.platform == "darwin":  # macOS
            return cls._getMacosLogDir()
        elif sys.platform == "win32":  # Windows
            return cls._getWindowsLogDir()
        else:  # Linux/Unix
            return cls._getUnixLogDir()

    @classmethod
    def _getMacosLogDir(cls) -> Path:
        """获取 macOS 日志目录"""
        # 优先使用 Library/Logs 目录
        logDir = Path.home() / "Library" / "Logs" / cls._appName

        # 检查目录是否存在或可写
        if isDirectoryWritable(logDir):
            return logDir

        # 降级到 Application Support 目录
        fallbackDir = (
            Path.home() / "Library" / "Application Support" / cls._appName / "logs"
        )
        if isDirectoryWritable(fallbackDir):
            fallbackDir.mkdir(parents=True, exist_ok=True)
            return fallbackDir

        # 最后使用临时目录
        tempDir = Path("/tmp") / cls._appName / "logs"
        tempDir.mkdir(parents=True, exist_ok=True)
        return tempDir

    @classmethod
    def _getWindowsLogDir(cls) -> Path:
        """获取 Windows 日志目录"""
        # 使用 AppData/Local
        localAppData = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        logDir = localAppData / cls._appName / "logs"
        logDir.mkdir(parents=True, exist_ok=True)
        return logDir

    @classmethod
    def _getUnixLogDir(cls) -> Path:
        """获取 Unix/Linux 日志目录"""
        # 使用 ~/.local/share 或 ~/logs
        logDir = Path.home() / ".local" / "share" / cls._appName / "logs"
        logDir.mkdir(parents=True, exist_ok=True)
        return logDir

    @classmethod
    def setupLogging(cls, level: str = "INFO"):
        """设置日志记录器"""
        cls._initialize()
        logFile = cls._logDir / f"{cls._appName}.log"
        logger.add(logFile, level=level, rotation="100 MB")
        print(f"日志文件位置: {logFile}")
        print(f"日志级别: {level}")

    @classmethod
    def getLogFileLocation(cls) -> str:
        """获取日志文件位置"""
        logFile = cls._logDir / f"{cls._appName}.log"
        return str(logFile)

    @classmethod
    def openLogDirectory(cls):
        """打开日志文件位置"""
        if not hasattr(cls, "_logDir") or not cls._logDir:
            print("错误：未设置日志目录")
            return

        logDir = str(cls._logDir)
        openDirectory(logDir)
