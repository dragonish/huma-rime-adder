#!/usr/bin/env python
# coding: utf-8

import argparse
from type.dict import Config
from .config import loadConfig


def parseArgsWithConfig(parser: argparse.ArgumentParser) -> Config:
    """解析命令行参数，合并配置文件设置"""
    # 首先加载配置文件
    configSettings = loadConfig()

    # 解析命令行参数
    args = parser.parse_args()

    # 处理日志配置（命令行优先级高于配置文件）
    if args.log:
        configSettings["log"] = args.log
    configSettings["log"] = configSettings["log"].upper()

    # 处理工作目录配置（命令行优先级高于配置文件）
    if args.work:
        configSettings["work"] = args.work

    return configSettings
