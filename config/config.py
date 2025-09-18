#!/usr/bin/env python
# coding: utf-8

import configparser
import os
import sys
from loguru import logger
from type.dict import Config, TigressFiles


def getProgramPath():
    """获取程序所在的原始目录（考虑 PyInstaller 打包情况）"""
    try:
        # PyInstaller 打包后获取程序原始路径
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        else:
            # 开发模式下，返回项目根目录
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    except:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def loadConfig(configFile="config.ini") -> Config:
    """从程序目录下的 config.ini 文件加载配置，优先级低于命令行"""
    files: TigressFiles = {
        "main": "tigress.extended.dict.yaml",
        "characters": "tigress.dict.yaml",
        "phrases": "tigress_ci.dict.yaml",
        "simple": "",
        "english": "easy_english.dict.yaml",
        "charset": "core2022.dict.yaml",
        "pinyin": "PY_c.dict.yaml",
        "pinyintip": "opencc/PYPhrases.txt",
        "emoji": "opencc/emoji.txt",
        "name": "",
        "symbols": "symbols.yaml",
    }
    config: Config = {"log": "INFO", "work": "", "tigress": files}
    programPath = getProgramPath()
    configPath = os.path.join(programPath, configFile)

    if not os.path.exists(configPath):
        return config

    try:
        parser = configparser.ConfigParser()
        parser.read(configPath)

        if "ARGS" in parser:
            # 将配置转换为字典，排除空值
            for key, value in parser["ARGS"].items():
                if value:
                    config[key] = value
        if "TIGRESS" in parser:
            for key, value in parser["TIGRESS"].items():
                if value:
                    config["tigress"][key] = value
    except Exception as e:
        logger.warning(f"警告：读取配置文件失败: {e}", file=sys.stderr)

    return config
