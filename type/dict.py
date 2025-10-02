#!/usr/bin/env python
# coding: utf-8

from typing import TypedDict


class CodeUnit(TypedDict):
    word: str
    weight: int
    source: str


class CodeTableUnit(CodeUnit):
    range: bool


class EncodeResult(TypedDict):
    cleanWord: str
    isEnglish: bool
    code: str
    weight: int
    range: bool


class CacheUnit(TypedDict):
    word: str
    code: str
    weight: int | str


class SymbolsUnit(TypedDict):
    comment: str
    symbols: list[str]


class TigressFiles(TypedDict):
    main: str
    simple: str
    phrases: str
    characters: str
    charset: str
    pinyin: str
    pinyintip: str
    english: str
    name: str
    emoji: str
    symbols: str


class Config(TypedDict):
    log: str
    work: str
    input: str
    encode: str
    tigress: TigressFiles
