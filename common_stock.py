#common_stock.py

import os
import sys
import datetime
import numba
import numpy as np
import pandas as pd
import yfinance as yf
import exchange_calendars as xcals
import pytz  # 🚨 引入时区库，确保全球服务器运行都能锁定北京时间
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, ROUND_DOWN

# 使用免安装版本时，为了读取CDP_config.py，添加的设定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def detect_stock_board_and_suffix(stock_code: str) -> tuple[str, str]:
    """【资产管理级：全市场多维板块智能审定与自适应分流引擎 - 智能去重防重拼版】

    严格按照中国 A 股最新代码划分标准，实现【后缀拼接】与【板块归属标签】的一体化无损输出。
    集成了智能后缀剥离引擎，若入参已带后缀（如 .SS / .SZ / .ss / .sz），会自动去重，绝不重复拼接。

    入参:
        stock_code (str): 股票代码（支持 '688551'、'688551.SS'、'300750.sz' 等各类格式）

    出参:
        tuple[str, str]: (标准带扩展名的代码, 板块中文标签)
                         例如: ('688551.SS', '科创板')
    """
    # 1. 🚨【核心增补防线：自适应后缀去重与清洗引擎】
    # 强转字符串，转为大写并剔除首尾空格
    code_raw = str(stock_code).upper().strip()

    # 如果代码中包含点号（.），说明自带后缀，直接用左切片斩断，剥离出前 6 位纯数字核心
    if "." in code_raw:
        code_clean = code_raw.split(".")[0].strip()
    else:
        code_clean = code_raw

    # 2. 🚨【核心流控多分支判定引擎】—— 严格划分五大核心板块
    if code_clean.startswith("688"):
        # ==========================================
        # A. 科创板（涨跌幅 20%）
        # ==========================================
        target_stock = f"{code_clean}.SS"
        board_label = "科创板"

    elif code_clean.startswith(("300", "301")):
        # ==========================================
        # B. 创业板（涨跌幅 20%）
        # ==========================================
        target_stock = f"{code_clean}.SZ"
        board_label = "创业板"

    elif code_clean.startswith(("920", "43", "83", "87")):
        # ==========================================
        # C. 北交所/新三板（北交所新股涨跌幅 30%）
        # ==========================================
        target_stock = f"{code_clean}.SS"  # 雅虎财经接口强行归类于 .SS
        board_label = "北交所"

    elif code_clean.startswith("6"):
        # ==========================================
        # D. 沪市主板（涨跌幅 10%）
        # 排除掉 688 之后，其余所有 6 开头的代码（600/601/603/605）皆为沪市主板
        # ==========================================
        target_stock = f"{code_clean}.SS"
        board_label = "沪市主板"

    elif code_clean.startswith(("000", "001", "002", "003")):
        # ==========================================
        # E. 深市主板/原中小板（涨跌幅 10%）
        # ==========================================
        target_stock = f"{code_clean}.SZ"
        board_label = "深市主板"

    else:
        # ==========================================
        # F. 冗余兜底层（如退市整理期、B股或未知新型代码）
        # ==========================================
        if code_clean.startswith("900"):
            target_stock = f"{code_clean}.SS"  # 上海B股
            board_label = "沪市B股"
        elif code_clean.startswith("200"):
            target_stock = f"{code_clean}.SZ"  # 深圳B股
            board_label = "深市B股"
        else:
            # 未知代码默认按数字前缀粗暴切分，防止程序中断
            target_stock = (
                f"{code_clean}.SS"
                if code_clean.startswith(("5", "7", "9"))
                else f"{code_clean}.SZ"
            )
            board_label = "其他未知板块"

    return target_stock, board_label
