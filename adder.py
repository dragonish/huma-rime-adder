#!/usr/bin/env python
# coding: utf-8

import os
import io
import sys
import argparse
import threading
import tkinter as tk
from typing import TypedDict, cast, Iterable
from loguru import logger
from pypinyin import lazy_pinyin


class CodeUnit(TypedDict):
    word: str
    weight: int
    source: str


class Columns(TypedDict):
    text: int
    code: int
    weight: int


class CacheUnit(TypedDict):
    word: str
    code: str
    weight: int | str


class App:
    def __init__(
        self,
        master: tk.Tk,
        work_dir: str,
        simp: bool,
    ) -> None:
        """构造器

        Args:
            master (tk.Tk): Tkinter 窗口对象
            work_dir (str): 工作目录
            simp (bool): 自动编码三简词以及允许插入简词表
        """
        self.master = master
        self.work_dir = work_dir
        self.simp = simp
        self.extended_file = os.path.join(self.work_dir, "tigress.extended.dict.yaml")
        self.simp_file = os.path.join(self.work_dir, "tigress_simp_ci.dict.yaml")
        self.pinyin_file = os.path.join(self.work_dir, "PY_c.dict.yaml")
        self.core_file = os.path.join(self.work_dir, "core2022.dict.yaml")
        self.simple_dict: dict[str, str] = {}
        self.code_dict: dict[str, list[CodeUnit]] = {}
        self.core_set: set[str] = set()
        self.delete_chars_table = str.maketrans(
            "",
            "",
            "!@#$%^&*()-=_+,.！？￥、，。“”‘’\"':;<>《》—…：；（）『』「」〖〗~|·",
        )

        self.extended_cached: list[CacheUnit] = []
        self.simp_cached: list[CacheUnit] = []
        self.pinyin_cached: list[CacheUnit] = []
        self.pinyin_set: set[str] = set([])

        master.title("虎码秃版加词器")

        # 主框架
        main_frame = tk.Frame(master)
        main_frame.pack(padx=5, pady=5)

        # 创建标签和输入框
        tk.Label(main_frame, text="新词:").grid(row=0, column=0)
        self.new_word_var = tk.StringVar()
        word_frame = tk.Frame(main_frame)
        word_frame.grid(row=0, column=1)
        new_word_entry = tk.Entry(word_frame, width=15, textvariable=self.new_word_var)
        new_word_entry.grid(row=0, column=1, padx=2)
        new_word_entry.bind("<Return>", self.encode)
        new_word_entry.focus_set()
        tk.Button(word_frame, text="编码", command=self.encode).grid(
            row=0, column=2, padx=2
        )

        # 字集范围状态展示
        self.range_status_var = tk.StringVar()
        tk.Label(main_frame, textvariable=self.range_status_var).grid(row=0, column=2)

        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=0, column=3)
        tk.Button(button_frame, text="仅添加", command=lambda: self.add(False)).grid(
            row=0, column=1, padx=15
        )
        tk.Button(button_frame, text="添加", command=lambda: self.add(True)).grid(
            row=0, column=2, padx=15
        )

        tk.Label(main_frame, text="编码:").grid(row=1, column=0)
        code_frame = tk.Frame(main_frame)
        code_frame.grid(row=1, column=1)
        self.new_code_var = tk.StringVar()
        new_code_entry = tk.Entry(code_frame, width=15, textvariable=self.new_code_var)
        new_code_entry.grid(row=0, column=0, padx=2)
        new_code_entry.bind("<Return>", self.query)
        tk.Button(code_frame, text="查询", command=self.query).grid(
            row=0, column=1, padx=2
        )

        tk.Label(main_frame, text="权重:").grid(row=1, column=2)
        weight_frame = tk.Frame(main_frame)
        weight_frame.grid(row=1, column=3)
        self.new_weight_var = tk.StringVar(value="0")
        tk.Entry(weight_frame, width=10, textvariable=self.new_weight_var).grid(
            row=0, column=0, padx=2
        )
        tk.Button(weight_frame, text="置顶", command=self.set_top_weight).grid(
            row=0, column=1, padx=2
        )
        tk.Button(
            weight_frame, text="清零", command=lambda: self.new_weight_var.set("0")
        ).grid(row=0, column=2, padx=2)

        tk.Label(main_frame, text="拼音:").grid(row=2, column=0)
        self.pinyin_code_var = tk.StringVar()
        tk.Entry(main_frame, textvariable=self.pinyin_code_var).grid(
            row=2, column=1, sticky="ew"
        )

        tk.Label(main_frame, text="权重:").grid(row=2, column=2)
        pinyin_weight_frame = tk.Frame(main_frame)
        pinyin_weight_frame.grid(row=2, column=3)
        self.pinyin_weight_var = tk.StringVar(value="0")
        tk.Entry(
            pinyin_weight_frame, width=10, textvariable=self.pinyin_weight_var
        ).grid(row=0, column=0, padx=2)
        tk.Button(
            pinyin_weight_frame,
            text="置顶",
            command=lambda: self.pinyin_weight_var.set("1000000"),
        ).grid(row=0, column=1, padx=2)
        tk.Button(
            pinyin_weight_frame,
            text="清零",
            command=lambda: self.pinyin_weight_var.set("0"),
        ).grid(row=0, column=2, padx=2)

        tk.Label(main_frame, text="重码:").grid(row=3, column=0)
        self.listbox = tk.Listbox(main_frame)
        self.listbox.grid(row=3, column=1, columnspan=3, sticky="ew")
        self.listbox.bind("<Double-Button-1>", self.copy_to_clipboard)

        # 底部框架
        bottom_frame = tk.Frame(master)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 状态栏
        self.status_var = tk.StringVar(value="解析码表中")
        status_bar = tk.Label(
            bottom_frame,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor="w",
        )
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 使用 after 方法延迟启动解析任务
        master.after(100, self.start_parsing)

    def start_parsing(self):
        """启动解析任务"""
        thread1 = threading.Thread(target=self.parse_huma)
        thread1.start()
        self.check_threads(thread1)

    def check_threads(self, thread1: threading.Thread):
        """检查线程状态

        Args:
            thread1 (threading.Thread): 线程
        """
        if thread1.is_alive():
            # 使用 after 检查线程状态
            self.master.after(100, lambda: self.check_threads(thread1))
        else:
            # 设置状态信息
            self.status_var.set("解析码表完毕，等待操作中")

    def parse_huma(self) -> None:
        """解析虎码码表内容为编码字典"""
        logger.debug("开始解析虎码码表")
        # 读取所导入的其他码表名称
        extended_lines = self.read_file(self.extended_file)
        import_tables: list[str] = []
        in_scope = False
        for line in extended_lines:
            item = line.strip()
            if in_scope:
                if item.startswith("- "):
                    names = item.split(" ")
                    import_tables.append(names[1])
                else:
                    in_scope = False
                    break
            elif item.startswith("import_tables:"):
                in_scope = True

        logger.info(
            "读取到 {size} 个其他码表名称，分别为: {name}",
            size=len(import_tables),
            name=" ".join(import_tables),
        )

        # 解析所导入的其他码表文件
        for table in import_tables:
            table_file = os.path.join(self.work_dir, table + ".dict.yaml")
            if os.path.exists(table_file):
                parse_lines(
                    self.simple_dict, self.code_dict, self.read_file(table_file), table
                )
                logger.info("解析码表文件： {}", table_file)
            else:
                logger.warning("没有找到码表文件: {}", table_file)

        # 解析用户扩展码表文件
        parse_lines(
            self.simple_dict,
            self.code_dict,
            extended_lines,
            "tigress.extended",
        )
        logger.info("解析用户扩展码表文件: {}", self.extended_file)

        logger.info(
            "解析完毕，读取到 {simple} 个单字，读取到 {code} 组编码",
            simple=len(self.simple_dict),
            code=len(self.code_dict),
        )

        # ? 补充字母表，以支持编码包含字母的词条
        letters = "abcdefghijklmnopqrstuvwxyz"
        for ch in letters:
            self.simple_dict[ch] = ch
            self.simple_dict[ch.upper()] = ch

        # 解析字集码表
        self.parse_core()

    def parse_core(self) -> None:
        """解析字集码表内容为字集集合"""
        logger.debug("开始解析字集码表")
        if not os.path.exists(self.core_file):
            logger.warning("没有找到字集码表文件: {}", self.core_file)
            return

        core_lines = self.read_file(self.core_file)
        for line in core_lines:
            item = line.strip()
            fields = item.split("\t")
            if len(fields) != 2:
                continue
            word = fields[0]
            self.core_set.add(word)

        logger.info(
            "解析完毕，读取到 {} 个常用字",
            len(self.core_set),
        )

        # * 补充一些字母与符号
        letters = "abcdefghijklmnopqrstuvwxyz"
        for ch in letters:
            self.core_set.add(ch)
            self.core_set.add(ch.upper())

    def parse_pinyin(self, lines: list[str]) -> None:
        """解析拼音码表内容为拼音集合

        Args:
            lines (list[str]): 拼音码表行内容
        """
        logger.debug("开始解析和处理拼音码表")
        columns_dict: Columns = {"text": -1, "code": -1, "weight": -1}
        in_header = True
        columns_scope = False
        for line in lines:
            item = line.strip()
            if in_header:
                if item == "...":
                    in_header = False
                    continue

                if item == "columns:":
                    columns_scope = True
                    continue

                if columns_scope:
                    if item.count(":") > 0:
                        columns_scope = False
                        continue
                    parse_columns(columns_dict, item)
            else:
                fields = item.split("\t")
                if len(fields) < 2:
                    continue
                word = fields[columns_dict["text"]]

                if len(word) > 1:
                    self.pinyin_set.add(word)

        self.pinyin_cached = [
            item for item in self.pinyin_cached if not item["word"] in self.pinyin_set
        ]

    def encode(self, _event=None) -> None:
        """编码词条

        Args:
            _event (Event[Entry], optional): event. Defaults to None.
        """
        new_word = self.new_word_var.get()
        clean_word = self.get_clean_word(new_word)
        new_word_len = len(clean_word)
        self.range_status_var.set("")
        if new_word_len == 0:
            self.status_var.set("请输入要添加的词条")
            return

        self.pinyin_weight_var.set("0")
        new_code = ""

        if new_word_len == 1:
            # 单字
            new_code = self.get_code(clean_word, 4)

            if new_code:
                self.status_var.set("已编码此单字")
            else:
                self.status_var.set("未收录的单字，请自行输入编码")
        elif new_word_len == 2:
            # 二字词组
            new_code = self.get_code(clean_word[0], 2) + self.get_code(clean_word[1], 2)
            self.new_code_var.set(new_code)
            if new_code:
                self.status_var.set("已编码此二字词组")
            else:
                self.status_var.set("无法编码此二字词组，请自行输入编码")
        elif new_word_len == 3:
            # 三字词组
            new_code = (
                self.get_code(clean_word[0], 1)
                + self.get_code(clean_word[1], 1)
                + self.get_code(clean_word[2], 2)
            )
            self.new_code_var.set(new_code)
            if new_code:
                self.status_var.set("已编码此三字词组")
            else:
                self.status_var.set("无法编码此三字词组，请自行输入编码")
        else:
            # 多字词组
            new_code = (
                self.get_code(clean_word[0], 1)
                + self.get_code(clean_word[1], 1)
                + self.get_code(clean_word[2], 1)
                + self.get_code(clean_word[-1], 1)
            )
            if new_code:
                self.status_var.set("已编码此多字词组")
            else:
                self.status_var.set("无法编码此多字词组，请自行输入编码")

        if new_code and not new_code in self.code_dict:
            self.new_weight_var.set("255")
        else:
            self.new_weight_var.set("0")
        new_pinyin = self.get_pinyin(clean_word)
        range_state = self.get_range(clean_word)
        self.new_code_var.set(new_code)
        self.pinyin_code_var.set(new_pinyin)
        self.set_listbox_by_code(new_code)
        if range_state:
            self.range_status_var.set("常用")
        else:
            self.range_status_var.set("全集")

        logger.debug(
            "新词: {word} | 编码: {code} | 拼音: {pinyin} | 属于常用字集: {range}",
            word=new_word,
            code=new_code,
            pinyin=new_pinyin,
            range=range_state,
        )

    def query(self, _event=None) -> None:
        """查询当前编码的重码情况

        Args:
            _event (Event[Entry], optional): event. Defaults to None.
        """
        code = self.new_code_var.get()
        if len(code) == 0:
            self.status_var.set("请在编码框输入编码")
            return

        if code in self.code_dict:
            self.new_weight_var.set("0")
        else:
            self.new_weight_var.set("255")
        self.set_listbox_by_code(code)

    def copy_to_clipboard(self, event) -> None:
        """复制重码列表的词条

        Args:
            event ([Event[Entry]]): event.
        """
        selected_item = self.listbox.get(self.listbox.curselection())
        items = selected_item.split("    ")
        if len(items) > 1:
            # 清空剪贴板并添加选中项
            self.master.clipboard_clear()
            self.master.clipboard_append(items[0])
            self.status_var.set("已复制词条: " + items[0])

    def get_code(self, simple: str, code_size: int):
        """获取单字的编码

        Args:
            simple (str): 单字
            code_size (int): 取码位数

        Returns:
            str: 编码
        """
        if simple in self.simple_dict:
            return self.simple_dict[simple][0:code_size]
        return ""

    def get_range(self, word: str) -> bool:
        """获取词条所属的字集范围

        Args:
            word (str): 词条

        Returns:
            bool: True 表示属于常用字集范围，否则为全集
        """
        for ch in word:
            if not ch in self.core_set:
                return False
        return True

    def get_pinyin(self, word: str):
        """获取词条拼音

        Args:
            word (str): 词条

        Returns:
            str: 空格分隔的拼音编码
        """
        py_list = lazy_pinyin(word, strict=False)
        return " ".join([p for p in py_list if p.isalpha()]).lower()

    def set_listbox_by_code(self, code: str) -> None:
        """设置重码列表的内容

        Args:
            code (str): 查询的编码
        """
        self.listbox.delete(0, "end")
        if code in self.code_dict:
            # 降序排序
            self.code_dict[code].sort(key=lambda item: item["weight"], reverse=True)
            for item in self.code_dict[code]:
                range_state = self.get_range(self.get_clean_word(item["word"]))
                range_str = "常用"
                if not range_state:
                    range_str = "全集"

                self.listbox.insert(
                    "end",
                    f"{item["word"]}    {item['weight']}    {item['source']}    {range_str}",
                )
        else:
            self.listbox.insert("end", "居然是零耶")

    def set_top_weight(self) -> None:
        """将权重值置顶"""
        code = self.new_code_var.get()
        if code and code in self.code_dict:
            # 降序排序
            self.code_dict[code].sort(key=lambda item: item["weight"], reverse=True)
            top = self.code_dict[code][0]["weight"] + 512
            self.new_weight_var.set(str(top))
        else:
            self.new_weight_var.set("512")

    def add(self, close: bool) -> None:
        """添加新的词条

        Args:
            close (bool): 是否关闭窗口
        """
        exist = False  # 为 True 时说明该词条被用于调频了

        new_word = self.new_word_var.get()
        clean_word = self.get_clean_word(new_word)
        new_code = self.new_code_var.get()
        new_weight = str_to_int(self.new_weight_var.get())
        new_source = "tigress.extended"

        if clean_word and new_code:
            is_simp = False  # 是否为简词
            if self.simp and len(clean_word) > 1 and len(new_code) < 4:
                is_simp = True

            if is_simp and os.path.exists(self.simp_file):
                # 缓存至简词表中
                self.simp_cached.append(
                    {"word": new_word, "code": new_code, "weight": new_weight}
                )
                new_source = "tigress_simp_ci"
            elif os.path.exists(self.extended_file):
                self.extended_cached.append(
                    {"word": new_word, "code": new_code, "weight": new_weight}
                )
            else:
                logger.error("没有找到用户扩展码表文件: {}", self.extended_file)
                self.status_var.set("没有找到用户扩展码表文件")
                return

            if not close:
                if new_code in self.code_dict:
                    for unit in self.code_dict[new_code]:
                        if new_word == unit["word"]:
                            unit["weight"] = new_weight
                            unit["source"] = new_source
                            exist = True
                            break
                    if not exist:
                        self.code_dict[new_code].append(
                            {
                                "word": new_word,
                                "weight": new_weight,
                                "source": new_source,
                            }
                        )
                else:
                    self.code_dict[new_code] = [
                        {
                            "word": new_word,
                            "weight": new_weight,
                            "source": new_source,
                        }
                    ]
        else:
            self.status_var.set("待添加的词条或编码内容为空")
            return

        pinyin_code = self.pinyin_code_var.get()
        if pinyin_code:
            if close:
                # 查询词条是否用于调频
                if new_code in self.code_dict:
                    for unit in self.code_dict[new_code]:
                        if new_word == unit["word"]:
                            exist = True
                            break

            # 调频时不插入拼音
            if exist:
                logger.debug("该词条({})被用于调频，所以不会插入拼音", new_word)
            else:
                if os.path.exists(self.pinyin_file):
                    pinyin_weight = str_to_int(self.pinyin_weight_var.get())
                    self.pinyin_cached.append(
                        {"word": new_word, "code": pinyin_code, "weight": pinyin_weight}
                    )
                else:
                    logger.warning("没有找到拼音码表文件: {}", self.pinyin_file)

        if close:
            self.master.destroy()
        else:
            self.listbox.delete(0, "end")
            self.new_weight_var.set("0")
            # ? 自动编码三简词
            if self.simp and len(clean_word) == 3 and len(new_code) == 4:
                three_code = new_code[:3]
                self.new_code_var.set(three_code)
                if not three_code in self.code_dict:
                    self.new_weight_var.set("255")
                self.set_listbox_by_code(three_code)
                self.status_var.set("已插入新词条并自动编码三简词")
                logger.debug(
                    "三简词: {word} | 编码: {code}", word=new_word, code=three_code
                )
            else:
                self.new_word_var.set("")
                self.new_code_var.set("")
                self.status_var.set("已向码表文件插入新词条")

            self.pinyin_code_var.set("")
            self.pinyin_weight_var.set("0")

    def append_lines_to_file(self, file_path: str, cached: list[CacheUnit]):
        """在指定文件的末尾添加行内容

        Args:
            file_path (str): 文件路径
            cached (list[CacheUnit]): 缓存单元
        Returns:
            bool: 是否执行成功
        """
        try:
            with io.open(file_path, mode="a+") as f:
                input_list: list[str] = []
                f.seek(0)  # ? 因为 "a+" 权限打开时默认在文件末尾
                for line in f:
                    item = line.strip()
                    if item.startswith("- text"):
                        input_list.append("{text}")
                    elif item.startswith("- code"):
                        input_list.append("{code}")
                    elif item.startswith("- weight"):
                        input_list.append("{weight}")
                    elif item == "...":
                        break
                format_str = "\t".join(input_list)

                f.seek(0)
                content = f.read()

                # 移动到文件末尾以准备写入
                f.seek(0, 2)

                # 检查最后一行是否以换行符结束
                if not content.endswith("\n"):
                    f.write("\n")

                for cache in cached:
                    input = format_str.format(
                        text=cache["word"],
                        code=cache["code"],
                        weight=cache["weight"],
                    )
                    f.write(input + "\n")
                    logger.info(
                        "向码表文件 {table} 插入新行: {input}",
                        table=file_path,
                        input=input,
                    )

                return True
        except PermissionError:
            logger.error("没有权限访问该文件: {}", file_path)
        except IOError:
            logger.error("I/O 错误: {}", file_path)
        except ValueError:
            logger.error("值错误: {}", file_path)
        return False

    def read_file(self, path: str) -> list[str]:
        """读取文件至列表，行尾不含换行符，自动过滤掉空行和以 `#` 开头的项

        Args:
            path (str): 文件路径

        Returns:
            list[str]: 行内容列表
        """
        try:
            with io.open(path, mode="r", encoding="utf-8") as f:
                read_list = f.read().splitlines()  # 不读入行尾的换行符
                filtered_list = [
                    item for item in read_list if item and not item.startswith("#")
                ]
                return filtered_list
        except FileExistsError:
            logger.error("尝试处理不存在的文件: {}", path)
        except PermissionError:
            logger.error("没有权限访问该文件: {}", path)
        except IOError:
            logger.error("I/O 错误: {}", path)
        except ValueError:
            logger.error("值错误: {}", path)

        return []

    def get_clean_word(self, word: str) -> str:
        """获取不带符号的字符串

        Args:
            word (str): 源字符串

        Returns:
            str: 不带符号的字符串
        """
        return word.translate(self.delete_chars_table)

    def writer(self) -> bool:
        """写入器

        Returns:
            bool: 是否有实际写入内容
        """
        write_state = False

        if len(self.extended_cached) > 0:
            if self.append_lines_to_file(self.extended_file, self.extended_cached):
                write_state = True
        if len(self.simp_cached) > 0:
            if self.append_lines_to_file(self.simp_file, self.simp_cached):
                write_state = True
        if len(self.pinyin_cached) > 0:
            self.parse_pinyin(self.read_file(self.pinyin_file))
            if len(self.pinyin_cached) > 0:
                if self.append_lines_to_file(self.pinyin_file, self.pinyin_cached):
                    write_state = True

        return write_state


def str_to_int(input: str):
    """将字符串转换为整数，若无法转换则返回 `0`

    Args:
        input (str): 待转换字符串

    Returns:
        int: 转换后的整数
    """
    if input.isdigit():
        return int(input)
    return 0


def parse_columns(columns: Columns, line: str) -> None:
    """解析列配置

    Args:
        columns (Columns): 列配置字典
        line (str): 行内容
    """
    if line.startswith("- text"):
        columns["text"] = max(cast(Iterable[int], columns.values())) + 1
    elif line.startswith("- code"):
        columns["code"] = max(cast(Iterable[int], columns.values())) + 1
    elif line.startswith("- weight"):
        columns["weight"] = max(cast(Iterable[int], columns.values())) + 1


@logger.catch
def parse_lines(
    simple_dict: dict[str, str],
    code_dict: dict[str, list[CodeUnit]],
    lines: list[str],
    table_name: str,
) -> None:
    """解析行内容列表为码表字典

    Args:
        simple_dict (dict[str, str]): 单字字典
        code_dict (dict[str, CodeUnit]): 编码字典
        lines (list[str]): 行内容列表
        table_name (str): 码表名称
    """
    columns_dict: Columns = {"text": -1, "code": -1, "weight": -1}
    in_header = True
    columns_scope = False
    for line in lines:
        item = line.strip()
        if in_header:
            if item == "...":
                in_header = False
                continue

            if item == "columns:":
                columns_scope = True
                continue

            if columns_scope:
                if item.count(":") > 0:
                    columns_scope = False
                    continue
                parse_columns(columns_dict, item)
        else:
            fields = item.split("\t")
            if len(fields) < 3:
                continue
            word = fields[columns_dict["text"]]
            code = fields[columns_dict["code"]]
            weight = str_to_int(fields[columns_dict["weight"]])

            # 处理单字字典
            if len(word) == 1:
                # 取全码
                if word in simple_dict:
                    if len(simple_dict[word]) < len(code):
                        simple_dict[word] = code
                else:
                    simple_dict[word] = code

            # 处理编码字典
            if code in code_dict:
                exist = False
                for c in code_dict[code]:
                    if c["word"] == word:
                        # 覆盖同编码同词条项的权重
                        c["weight"] = weight
                        c["source"] = table_name
                        exist = True
                        break
                if not exist:
                    code_dict[code].append(
                        {"word": word, "weight": weight, "source": table_name}
                    )
            else:
                code_dict[code] = [
                    {"word": word, "weight": weight, "source": table_name}
                ]


if __name__ == "__main__":
    # 启动参数
    ap = argparse.ArgumentParser(description="虎码秃版加词器")
    ap.add_argument("-l", "--log", action="store_true", help="记录日志")
    ap.add_argument("-w", "--work", required=False, help="自定义工作目录")
    ap.add_argument(
        "-s",
        "--simp",
        action="store_true",
        help="在添加三字词后自动尝试编码三简词，并允许将简词插入至简词表",
    )

    args = vars(ap.parse_args())
    if args["log"]:
        logger.add("logs/adder.log", level="TRACE", rotation="100 MB")

    logger.info("程序开始运行")

    # 设定工作目录
    work_dir = os.path.dirname(__file__)
    if args["work"]:
        if os.path.exists(args["work"]) and os.path.isdir(args["work"]):
            work_dir = args["work"]
        else:
            logger.warning("指定的工作目录不存在: {}", args["work"])

    os.chdir(work_dir)
    logger.info("工作目录: {}", work_dir)

    tigress_extended_dict_yaml = os.path.join(work_dir, "tigress.extended.dict.yaml")
    if not os.path.exists(tigress_extended_dict_yaml):
        logger.error("没有找到用户扩展码表文件: {}", tigress_extended_dict_yaml)
        logger.warning("缺失必要文件，程序结束运行，退出代码: {}", 1)
        sys.exit(1)  #! 退出程序

    if args["simp"]:
        logger.info("已启用自动编码三简词及允许将简词插入至简词表")

    logger.info("显示程序窗口")
    # 创建主窗口
    root = tk.Tk()
    app = App(root, work_dir, args["simp"])

    # 运行主循环
    root.mainloop()
    exit_code = 3
    if app.writer():
        exit_code = 0
    logger.info("程序结束运行，退出代码: {}", exit_code)
    sys.exit(exit_code)
