#!/usr/bin/env python
# coding: utf-8

from PyQt6.QtWidgets import QApplication
from typing import Optional


class Application:
    """应用程序管理器"""

    _instance: Optional[QApplication] = None

    @classmethod
    def getInstance(cls) -> QApplication:
        """获取 QApplication 实例"""
        if cls._instance is None:
            raise RuntimeError("QApplication 未初始化，请先调用 initialize()")
        return cls._instance

    @classmethod
    def initialize(cls, *args, **kwargs) -> QApplication:
        """初始化 QApplication"""
        if cls._instance is None:
            cls._instance = QApplication(*args, **kwargs)
        return cls._instance

    @classmethod
    def exit(cls, returnCode: int = 0):
        """退出应用程序"""
        app = cls.getInstance()
        app.exit(returnCode)


def getApp() -> QApplication:
    """获取应用程序实例的便捷函数"""
    return Application.getInstance()


def exitApp(returnCode: int = 0):
    """退出应用程序的便捷函数"""
    Application.exit(returnCode)
