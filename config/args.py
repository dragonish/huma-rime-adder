#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import sys
from type.dict import Config
from data.version import APP_VERSION
from .config import loadConfig


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


def parseArgsWithConfig() -> Config:
    # 启动参数
    parser = argparse.ArgumentParser(description=f"猛击虎码加词器(v{APP_VERSION})")
    parser.add_argument("-c", "--config", required=False, help="自定义配置文件")
    parser.add_argument("-l", "--log", required=False, help="日志记录级别")
    parser.add_argument("-w", "--work", required=False, help="自定义工作目录")
    parser.add_argument("-i", "--input", required=False, help="直接编码的词条")

    """解析命令行参数，合并配置文件设置"""
    # 解析命令行参数
    args = parser.parse_args()

    # 加载配置文件
    if args.config:
        configPath = args.config
    else:
        # 默认从程序目录下的 config.ini 文件加载配置
        programPath = getProgramPath()
        configPath = os.path.join(programPath, "config.ini")
    configFile = None
    if os.path.exists(configPath):
        configFile = configPath
        print(f"使用配置文件: {configFile}")
    configSettings = loadConfig(configFile)

    # 处理日志配置（命令行优先级高于配置文件）
    if args.log:
        configSettings["log"] = args.log
    configSettings["log"] = configSettings["log"].upper()

    # 处理工作目录配置（命令行优先级高于配置文件）
    if args.work:
        configSettings["work"] = args.work

    if args.input:
        configSettings["input"] = args.input

    return configSettings
