#!/usr/bin/env python
# coding: utf-8

import os
import sys
from loguru import logger
from app.application import Application
from common.file import getProgramPath
from config.args import parseArgsWithConfig
from controller.controller import AdderController
from data.version import APP_VERSION
from type.status import ExitCode
from log.manager import LogManager
from model.calc import CalcModel
from window.window import AdderWindow


if __name__ == "__main__":
    # 使用支持配置文件的解析函数
    config = parseArgsWithConfig()

    # ? 去除 Qt 的字体回退警告日志
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts=false"
    LogManager.setupLogging(level=config["log"])

    logger.info(f"猛击虎码加词器(v{APP_VERSION})开始运行...")

    # 设定工作目录
    workDir = getProgramPath()  # 使用程序原始目录作为默认工作目录
    if config["work"]:
        if os.path.exists(config["work"]) and os.path.isdir(config["work"]):
            workDir = config["work"]
        else:
            logger.warning("指定的工作目录不存在: {}", config["work"])

    os.chdir(workDir)
    logger.info("工作目录: {}", workDir)

    model = CalcModel(workDir, config["tigress"])

    errFile = model.fileChecker()
    if len(errFile) > 0:
        logger.error("没有找到码表文件: {}", errFile)
        logger.error("缺失码表文件，程序结束运行，退出代码: {}", ExitCode.ERROR.value)
        sys.exit(ExitCode.ERROR.value)  #! 退出程序

    if config["encode"]:
        encodeState = model.encodeFile(config["encode"])
        exitCode = ExitCode.NOTHING
        if encodeState:
            exitCode = model.writer()
            logger.info("程序结束运行，退出代码: {}", exitCode.value)
        else:
            logger.warning("未编码词库文件，程序结束运行，退出代码: {}", exitCode.value)
        sys.exit(exitCode.value)

    adderApp = Application.initialize(sys.argv)
    adderWindow = AdderWindow()
    controller = AdderController(model=model, view=adderWindow)
    adderWindow.show()

    if config["input"]:
        controller.encodeWord(config["input"])

    sys.exit(adderApp.exec())
