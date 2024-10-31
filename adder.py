#!/usr/bin/env python
# coding: utf-8

import os
import io
import sys
import argparse
import threading
import tkinter as tk
from typing import TypedDict
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


class App:
    def __init__(
        self,
        master: tk.Tk,
        work_dir: str,
        extended_file: str,
    ) -> None:
        """构造器

        Args:
            master (tk.Tk): Tkinter 窗口对象
            work_dir (str): 工作目录
            extended_file (str): 用户扩展码表文件路径
        """
        self.master = master
        self.work_dir = work_dir
        self.extended_file = extended_file
        self.pinyin_file = os.path.join(self.work_dir, "PY_c.dict.yaml")
        self.simple_dict: dict[str, str] = {}
        self.code_dict: dict[str, list[CodeUnit]] = {}
        self.mod = False  # 标识是否实际插入过词条

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
        # 读取所导入的其它码表名称
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
            "读取到 {size} 个其它码表名称，分别为: {name}",
            size=len(import_tables),
            name=" ".join(import_tables),
        )

        # 解析所导入的其它码表文件
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

    def encode(self, _event=None) -> None:
        """编码词条

        Args:
            _event (Event[Entry], optional): event. Defaults to None.
        """
        new_word = self.new_word_var.get()
        new_word_len = len(new_word)
        if new_word_len == 0:
            self.status_var.set("请输入要添加的词条")
            return

        self.pinyin_weight_var.set("0")
        new_code = ""

        if new_word_len == 1:
            # 单字
            new_code = self.get_code(new_word, 4)

            if new_code:
                self.status_var.set("已编码此单字")
            else:
                self.status_var.set("未收录的单字，请自行输入编码")
        elif new_word_len == 2:
            # 二字词组
            new_code = self.get_code(new_word[0], 2) + self.get_code(new_word[1], 2)
            self.new_code_var.set(new_code)
            if new_code:
                self.status_var.set("已编码此二字词组")
            else:
                self.status_var.set("无法编码此二字词组，请自行输入编码")
        elif new_word_len == 3:
            # 三字词组
            new_code = (
                self.get_code(new_word[0], 1)
                + self.get_code(new_word[1], 1)
                + self.get_code(new_word[2], 2)
            )
            self.new_code_var.set(new_code)
            if new_code:
                self.status_var.set("已编码此三字词组")
            else:
                self.status_var.set("无法编码此三字词组，请自行输入编码")
        else:
            # 多字词组
            new_code = (
                self.get_code(new_word[0], 1)
                + self.get_code(new_word[1], 1)
                + self.get_code(new_word[2], 1)
                + self.get_code(new_word[-1], 1)
            )
            if new_code:
                self.status_var.set("已编码此多字词组")
            else:
                self.status_var.set("无法编码此多字词组，请自行输入编码")

        if new_code and not new_code in self.code_dict:
            self.new_weight_var.set("10")
        else:
            self.new_weight_var.set("0")
        new_pinyin = self.get_pinyin(new_word)
        self.new_code_var.set(new_code)
        self.pinyin_code_var.set(new_pinyin)
        self.set_listbox_by_code(new_code)
        logger.debug(
            "新词: {word} | 编码: {code} | 拼音: {pinyin}",
            word=new_word,
            code=new_code,
            pinyin=new_pinyin,
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
            self.new_weight_var.set("10")
        self.set_listbox_by_code(code)

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
                self.listbox.insert(
                    "end", f"{item["word"]}    {item['weight']}    {item['source']}"
                )
        else:
            self.listbox.insert("end", "居然是零耶")

    def set_top_weight(self) -> None:
        """将权重值置顶"""
        code = self.new_code_var.get()
        if code and code in self.code_dict:
            # 降序排序
            self.code_dict[code].sort(key=lambda item: item["weight"], reverse=True)
            self.new_weight_var.set(f"1{self.code_dict[code][0]["weight"]}")
        else:
            self.new_weight_var.set("100")

    def add(self, close: bool) -> None:
        """添加新的词条

        Args:
            close (bool): 是否关闭窗口
        """
        exist = False  # 为 True 时说明该词条被用于调频了

        new_word = self.new_word_var.get()
        new_code = self.new_code_var.get()
        if new_word and new_code:
            if os.path.exists(self.extended_file):
                new_weight = str_to_int(self.new_weight_var.get())
                state = self.append_line_to_file(
                    self.extended_file, new_word, new_code, new_weight
                )

                if not state:
                    self.status_var.set("无法将新词条插入码表文件")
                    return
                self.mod = True

                if not close:
                    if new_code in self.code_dict:
                        for unit in self.code_dict[new_code]:
                            if new_word == unit["word"]:
                                unit["weight"] = new_weight
                                unit["source"] = "tigress.extended"
                                exist = True
                                break
                        if not exist:
                            self.code_dict[new_code].append(
                                {
                                    "word": new_word,
                                    "weight": new_weight,
                                    "source": "tigress.extended",
                                }
                            )
                    else:
                        self.code_dict[new_code] = [
                            {
                                "word": new_word,
                                "weight": new_weight,
                                "source": "tigress.extended",
                            }
                        ]
            else:
                logger.error("没有找到用户扩展码表文件: {}", self.extended_file)
                self.status_var.set("没有找到用户扩展码表文件")
                return
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
                    self.append_line_to_file(
                        self.pinyin_file, new_word, pinyin_code, pinyin_weight
                    )
                else:
                    logger.warning("没有找到拼音码表文件: {}", self.pinyin_file)

        if close:
            self.master.destroy()
        else:
            self.new_word_var.set("")
            self.new_code_var.set("")
            self.new_weight_var.set("0")
            self.pinyin_code_var.set("")
            self.pinyin_weight_var.set("0")
            self.listbox.delete(0, "end")
            self.status_var.set("已向码表文件插入新词条")

    def append_line_to_file(self, file_path: str, word: str, code: str, weight: int):
        """在指定文件的末尾添加行内容

        Args:
            file_path (str): 文件路径
            word (str): 词条内容
            code (str): 编码内容
            weight (int): 权重值

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
                        input_list.append(word)
                    elif item.startswith("- code"):
                        input_list.append(code)
                    elif item.startswith("- weight"):
                        input_list.append(str(weight))
                    elif item == "...":
                        break

                    if len(input_list) == 3:
                        break
                input = "\t".join(input_list)

                f.seek(0)
                content = f.read()

                # 移动到文件末尾以准备写入
                f.seek(0, 2)

                # 检查最后一行是否以换行符结束
                if content.endswith("\n"):
                    f.write(input)
                else:
                    f.write("\n" + input)

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
        except OSError:
            logger.error("操作系统错误: {}", file_path)
        except ValueError:
            logger.error("值错误: {}", file_path)
        return False

    def read_file(self, path: str) -> list[str]:
        """读取文件至列表，行尾不含换行符，自动过滤掉空行和以 `#` 开头的项。

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
        except OSError:
            logger.error("操作系统错误: {}", path)
        except ValueError:
            logger.error("值错误: {}", path)

        return []

    def mod_state(self):
        """获取执行状态

        Returns:
            bool: `Ture` 表示有实际插入词条
        """
        return self.mod


def str_to_int(input: str):
    """将字符串转换为整数，若无法转换则返回 `0`。

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
        columns["text"] = len(columns)
    elif line.startswith("- code"):
        columns["code"] = len(columns)
    elif line.startswith("- weight"):
        columns["weight"] = len(columns)


@logger.catch
def parse_lines(
    simple_dict: dict[str, str],
    code_dict: dict[str, list[CodeUnit]],
    lines: list[str],
    table_name: str,
) -> None:
    """解析行内容列表为码表字典。

    Args:
        simple_dict (dict[str, str]): 单字字典
        code_dict (dict[str, CodeUnit]): 编码字典
        lines (list[str]): 行内容列表
        table_name (str): 码表名称
    """
    columns_dict: Columns = {}
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
                parse_columns(columns_dict, item)
                if len(columns_dict) == 3:
                    columns_scope = False
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

    logger.info("显示程序窗口")
    # 创建主窗口
    root = tk.Tk()
    app = App(root, work_dir, tigress_extended_dict_yaml)

    # 运行主循环
    root.mainloop()
    exit_code = 3
    if app.mod_state():
        exit_code = 0
    logger.info("程序结束运行，退出代码: {}", exit_code)
    sys.exit(exit_code)
