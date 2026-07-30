#common_yfinance.py

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

def clean_and_standardize_sh_sz_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """【A股交易所级 K线流 - V4.0 资管无痕隐形清洗器】

    🔥 彻底尊重原表习惯：
    1. 绝不改变原表的物理索引（保留 Date 索引，绝不重置为 0, 1, 2）。
    2. 绝不增加任何新列（不产生 date_str 列），保持原汁原味的列数。
    3. 绝不打破原有的数据顺序。
    4. 仅原地剥离 Price 复合外壳，并将 Volume 刚性对齐为 A股标准的“手”。
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    # 深拷贝，确保不污染外部原始内存
    df_cleaned = df_raw.copy()

    try:
        # 1. 🚨【原地剥壳】：剥离 Price 多重索引大帽子，还原单层列名
        if isinstance(df_cleaned.columns, pd.MultiIndex):
            df_cleaned.columns = df_cleaned.columns.get_level_values(-1)

        # 彻底剔除列名中可能隐藏的空白符
        df_cleaned.columns = [str(col).strip() for col in df_cleaned.columns]

        # 2. 🚨【A股手单位原地对齐】：把成交量从“股”缩放为国内标准的“手”
        if "Volume" in df_cleaned.columns:
            df_cleaned["Volume"] = (
                df_cleaned["Volume"].fillna(0.0).astype(float) / 100.0
            )

        # 3. 🚨【类型刚性约束】：确保所有价格列全部是干净的 float
        for col in ["Open", "High", "Low", "Close"]:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].astype(float)

        # 💯 完美的无痕返回：原表的 Index、顺序、列结构完全一模一样！
        return df_cleaned

    except Exception as e:
        print(f"⚠️ [无痕清洗提示]: 遇到微观阻碍，已启动安全原样返回: {e}")
        return df_raw
