#!/bin/bash

pyinstaller -i icon.ico -y -n huma-rime-adder main.py
cp config.ini.template dist/huma-rime-adder/
