#!/usr/bin/env python
# coding: utf-8

import configparser
import sys
from type.dict import Config, TigressFiles


def loadConfig(configFile: str | None) -> Config:
    """从配置文件加载配置，优先级低于命令行"""
    files: TigressFiles = {
        "main": "tigress.extended.dict.yaml",
        "characters": "tigress.dict.yaml",
        "phrases": "tigress_ci.dict.yaml",
        "simple": "tigress_simp_ci.dict.yaml",
        "english": "easy_english.dict.yaml",
        "charset": "core2022.dict.yaml",
        "pinyin": "PY_c.dict.yaml",
        "pinyintip": "opencc/PYPhrases.txt",
        "emoji": "opencc/emoji.txt",
        "name": "",
        "symbols": "symbols.yaml",
    }
    config: Config = {
        "log": "INFO",
        "work": "",
        "input": "",
        "encode": "",
        "tinyPinyinTable": False,
        "tinyPinyinTip": False,
        "tigress": files,
    }

    if configFile:
        try:
            parser = configparser.ConfigParser()
            parser.read(configFile)

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
            print(f"警告：读取配置文件失败: {e}", file=sys.stderr)

    return config
