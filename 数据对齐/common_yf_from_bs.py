# common_yf_from_bs.py
# 使用 Baostock 替代 AkShare，所有接口与原 AkShare 版本完全兼容
# 新增：不复权 + 复权因子自行计算前复权功能

import baostock as bs
import pandas as pd
from datetime import datetime, timezone, timedelta

# =========================================================================
# 方法一：通用数据对齐清洗器（增强时间解析，适配多种 Baostock 格式）
# =========================================================================
def align_baostock_to_yfinance(df_raw: pd.DataFrame, is_minute: bool = False) -> pd.DataFrame:
    """
    将 Baostock 日线/分钟线接口返回的数据，统一清洗为 yfinance 标准 6 列。
    自动识别多种时间格式（如 'HHMMSS'、'YYYYMMDDHHMMSSmmm' 等）。
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    try:
        # ----- 第一步：构造 Datetime 列 -----
        if is_minute:
            # 分钟线：优先使用 date + time 组合
            if 'date' in df_raw.columns and 'time' in df_raw.columns:
                # 检查 time 字段样本格式
                sample = str(df_raw['time'].iloc[0])
                if len(sample) > 6 and sample.isdigit():
                    # time 本身包含日期信息（如 20260727093500000）
                    # 直接解析整个时间戳
                    df_raw['Datetime'] = pd.to_datetime(df_raw['time'], errors='coerce')
                    # 如果解析失败，尝试按格式 '%Y%m%d%H%M%S%f'
                    if df_raw['Datetime'].isnull().all():
                        df_raw['Datetime'] = pd.to_datetime(df_raw['time'], format='%Y%m%d%H%M%S%f', errors='coerce')
                else:
                    # time 为纯时分秒（如 093500），拼接日期
                    # 补足 6 位
                    time_padded = df_raw['time'].astype(str).str.zfill(6)
                    df_raw['Datetime'] = pd.to_datetime(df_raw['date'] + ' ' + time_padded, errors='coerce')
            else:
                # 没有 date/time，尝试索引或其他列
                if 'Datetime' in df_raw.columns:
                    df_raw['Datetime'] = pd.to_datetime(df_raw['Datetime'], errors='coerce')
                else:
                    df_raw['Datetime'] = pd.to_datetime(df_raw.index, errors='coerce')
                    if df_raw['Datetime'].isnull().all():
                        first_col = df_raw.columns[0]
                        df_raw['Datetime'] = pd.to_datetime(df_raw[first_col], errors='coerce')
        else:
            # 日线：直接用 date 列或索引
            if 'date' in df_raw.columns:
                df_raw['Datetime'] = pd.to_datetime(df_raw['date'], errors='coerce')
            else:
                df_raw['Datetime'] = pd.to_datetime(df_raw.index, errors='coerce')
                if df_raw['Datetime'].isnull().all():
                    first_col = df_raw.columns[0]
                    df_raw['Datetime'] = pd.to_datetime(df_raw[first_col], errors='coerce')

        # 丢弃无法解析时间戳的行
        df_raw = df_raw.dropna(subset=['Datetime'])
        if df_raw.empty:
            return pd.DataFrame()

        # ----- 第二步：标准化列名 -----
        rename_map = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'amount': 'Amount'
        }
        df_renamed = df_raw.rename(columns=rename_map)
        # 确保必需列存在
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df_renamed.columns:
                df_renamed[col] = None

        # ----- 第三步：设置索引并构造输出 -----
        df_renamed.set_index('Datetime', inplace=True)
        df_renamed['Adj Close'] = df_renamed['Close']  # 默认填充，后续可能覆盖

        target_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        df_final = df_renamed[target_cols].copy()

        # 类型转换
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        df_final['Volume'] = pd.to_numeric(df_final['Volume'], errors='coerce').fillna(0).astype(int)

        df_final.sort_index(inplace=True)
        return df_final

    except Exception as e:
        print(f"❌ [数据对齐失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 辅助函数：股票代码转 Baostock 格式
# =========================================================================
def _code_to_baostock(stock_code: str) -> str:
    """转换股票代码为 Baostock 所需的 'sh.xxxxxx' 或 'sz.xxxxxx'"""
    if stock_code.startswith('6'):
        return f"sh.{stock_code}"
    else:
        return f"sz.{stock_code}"

# =========================================================================
# 辅助函数：执行 Baostock 查询（自动登录/注销）
# =========================================================================
def _query_baostock(bs_code: str, start_date: str, end_date: str,
                    frequency: str, adjustflag: str = "2") -> pd.DataFrame:
    """
    封装 Baostock 查询，返回包含原始字段的 DataFrame。
    frequency: 'd' 日线, '5'/'15'/'30'/'60' 分钟线
    adjustflag: '2' 前复权, '3' 不复权, '1' 后复权
    """
    lg = bs.login()
    if lg.error_code != '0':
        print(f"❌ Baostock 登录失败: {lg.error_msg}")
        bs.logout()
        return pd.DataFrame()

    # 根据频率选择字段
    if frequency == 'd':
        fields = "date,code,open,high,low,close,volume,amount"
    else:
        fields = "date,time,code,open,high,low,close,volume,amount"

    rs = bs.query_history_k_data_plus(
        bs_code,
        fields,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        adjustflag=adjustflag
    )

    if rs.error_code != '0':
        print(f"❌ Baostock 查询失败: {rs.error_msg}")
        bs.logout()
        return pd.DataFrame()

    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    bs.logout()

    if not data_list:
        return pd.DataFrame()

    df = pd.DataFrame(data_list, columns=rs.fields)
    # 转换数值列（保留字符串时间）
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount'] if 'amount' in df.columns else ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# =========================================================================
# 方法二：【全自动免参】当日实时 K线抓取（实际返回 5分钟线）
# =========================================================================
def fetch_stock_today_live_1m_bs(stock_code: str) -> pd.DataFrame:
    """
    获取今日开盘至现在的 5分钟 K线（Baostock 不支持 1分钟）。
    返回格式与 yfinance 一致。
    """
    try:
        tz_bj = timezone(timedelta(hours=8))
        now_bj = datetime.now(tz_bj)
        today_str = now_bj.strftime('%Y-%m-%d')
        current_time_str = now_bj.strftime('%Y-%m-%d %H:%M:%S')

        bs_code = _code_to_baostock(stock_code)
        df_raw = _query_baostock(bs_code, today_str, today_str, frequency="5", adjustflag="2")
        if df_raw.empty:
            return pd.DataFrame()

        df_aligned = align_baostock_to_yfinance(df_raw, is_minute=True)
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[today_str:current_time_str]
        return df_aligned
    except Exception as e:
        print(f"❌ [当日实时K线抓取失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 方法三：指定历史时间范围 K线抓取（实际返回 5分钟线）
# =========================================================================
def fetch_stock_1m_data_bs(stock_code: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    获取指定历史时间段的 5分钟 K线（Baostock 无 1分钟，自动替换为 5分钟）。
    """
    try:
        start_date = start_time.split(' ')[0]
        end_date = end_time.split(' ')[0]
        bs_code = _code_to_baostock(stock_code)
        df_raw = _query_baostock(bs_code, start_date, end_date, frequency="5", adjustflag="2")
        if df_raw.empty:
            return pd.DataFrame()

        df_aligned = align_baostock_to_yfinance(df_raw, is_minute=True)
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[start_time:end_time]
        return df_aligned
    except Exception as e:
        print(f"❌ [历史1分钟线抓取失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 方法四：指定日期范围日线抓取器（直接使用 Baostock 前复权）
# =========================================================================
def fetch_stock_1d_data_bs(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取指定日期范围的日线数据，支持前复权 (qfq)、后复权 (hfq)、不复权 ("").
    默认前复权，直接使用 Baostock 返回的复权价格。
    """
    try:
        adjust_map = {"qfq": "2", "hfq": "1", "": "3"}
        adj_flag = adjust_map.get(adjust, "2")  # 默认前复权

        st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        bs_code = _code_to_baostock(stock_code)
        df_raw = _query_baostock(bs_code, st_date, ed_date, frequency="d", adjustflag=adj_flag)
        if df_raw.empty:
            return pd.DataFrame()

        return align_baostock_to_yfinance(df_raw, is_minute=False)
    except Exception as e:
        print(f"❌ [日线抓取失败 (Baostock直接复权)]: {e}")
        return pd.DataFrame()

# =========================================================================
# 【新增】方法五：获取不复权日线数据（原始价格）
# =========================================================================
def fetch_stock_1d_raw(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取指定日期范围的原始（不复权）日线数据，返回标准六列（价格未复权）。
    可用于配合复权因子自行计算前复权。
    """
    try:
        st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        bs_code = _code_to_baostock(stock_code)
        df_raw = _query_baostock(bs_code, st_date, ed_date, frequency="d", adjustflag="3")  # 不复权
        if df_raw.empty:
            return pd.DataFrame()
        return align_baostock_to_yfinance(df_raw, is_minute=False)
    except Exception as e:
        print(f"❌ [不复权日线抓取失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 【增强版】方法六：获取复权因子（若无事件则自动补全为 1.0）
# =========================================================================
def fetch_stock_adj_factor(stock_code: str, start_date: str, end_date: str) -> pd.Series:
    """
    获取指定日期范围的复权因子。如果该区间内没有除权事件，
    则自动返回该区间全为 1.0 的因子序列（即不复权）。
    """
    try:
        st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        bs_code = _code_to_baostock(stock_code)

        lg = bs.login()
        if lg.error_code != '0':
            print(f"❌ Baostock 登录失败: {lg.error_msg}")
            bs.logout()
            # 返回全1序列作为兜底
            date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
            return pd.Series(1.0, index=date_range, name='adjust_factor')

        rs = bs.query_adjust_factor(bs_code, start_date=st_date, end_date=ed_date)
        if rs.error_code != '0':
            print(f"❌ 复权因子查询失败: {rs.error_msg}")
            bs.logout()
            date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
            return pd.Series(1.0, index=date_range, name='adjust_factor')

        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        bs.logout()

        # ------------------- 核心修补点 -------------------
        if not data_list:
            # 如果没有查到复权因子，说明区间内无除权，直接返回全 1 序列
            print(f"ℹ️ 提示: {start_date} 至 {end_date} 区间无除权事件，复权因子默认为 1.0")
            date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
            return pd.Series(1.0, index=date_range, name='adjust_factor')
        # ------------------------------------------------

        df = pd.DataFrame(data_list, columns=rs.fields)
        df['adjust_factor'] = pd.to_numeric(df['adjust_factor'], errors='coerce')
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        factor_series = df['adjust_factor'].dropna().sort_index()
        return factor_series
    except Exception as e:
        print(f"❌ [复权因子抓取失败]: {e}")
        # 异常时也返回全1序列
        st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
        return pd.Series(1.0, index=date_range, name='adjust_factor')

# =========================================================================
# 【新增】方法七：根据原始价格和复权因子计算前复权
# =========================================================================
def calc_forward_price(raw_df: pd.DataFrame, factor_series: pd.Series) -> pd.DataFrame:
    """
    根据不复权价格 (raw_df) 和复权因子 (factor_series) 计算前复权价格。
    raw_df: 标准六列 DataFrame (索引为日期)
    factor_series: 日期索引的复权因子
    返回标准六列，价格调整为前复权。
    """
    if raw_df.empty or factor_series.empty:
        return pd.DataFrame()

    # 对齐日期
    common_dates = raw_df.index.intersection(factor_series.index)
    if len(common_dates) == 0:
        print("❌ 日期无交集，无法计算复权")
        return pd.DataFrame()

    raw_df = raw_df.loc[common_dates].copy()
    factor = factor_series.loc[common_dates]

    # 最新因子作为基准（也可用最后一个交易日的因子）
    base_factor = factor.iloc[-1]  # 区间最后一个因子

    # 前复权因子 = base_factor / 当日因子
    fwd_factor = base_factor / factor

    # 应用复权到所有价格列
    for col in ['Open', 'High', 'Low', 'Close']:
        raw_df[col] = raw_df[col] * fwd_factor

    # 更新 Adj Close 为调整后的收盘价
    raw_df['Adj Close'] = raw_df['Close']

    return raw_df

# =========================================================================
# 【新增】方法八：一站式获取自行计算的前复权日线数据
# =========================================================================
def fetch_stock_1d_self_adj(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取指定日期范围的日线数据，使用不复权 + 复权因子自行计算前复权。
    返回标准六列，与 fetch_stock_1d_data_bs 格式一致。
    优势：复权计算独立于平台，可避免不同平台复权差异。
    """
    try:
        # 获取原始不复权价格
        raw_df = fetch_stock_1d_raw(stock_code, start_date, end_date)
        if raw_df.empty:
            return pd.DataFrame()

        # 获取复权因子
        factor_series = fetch_stock_adj_factor(stock_code, start_date, end_date)
        if factor_series.empty:
            return pd.DataFrame()

        # 计算前复权
        adj_df = calc_forward_price(raw_df, factor_series)
        return adj_df
    except Exception as e:
        print(f"❌ [自行复权计算失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 🚀 测试入口（包含新增函数测试）
# =========================================================================
if __name__ == "__main__":
    test_code = "688551"
    start_d = "2026-07-15"
    end_d = "2026-07-28"

    print("=" * 70)
    print(f"📡 测试 Baostock 数据源（含不复权+复权因子功能），标的: {test_code}")
    print("=" * 70 + "\n")

    # ---- 测试原有功能 ----
    print("👉 [测试一] 直接前复权 (Baostock原生):")
    df_orig = fetch_stock_1d_data_bs(test_code, start_d, end_d, adjust="qfq")
    if not df_orig.empty:
        print("✅ 成功，最新3行:")
        print(df_orig.tail(3))
        print(f"   Adj Close 最后值: {df_orig['Adj Close'].iloc[-1]:.2f}\n")
    else:
        print("⚠️ 测试一失败\n")

    # ---- 测试新增：不复权 ----
    print("👉 [测试二] 不复权原始价格:")
    df_raw = fetch_stock_1d_raw(test_code, start_d, end_d)
    if not df_raw.empty:
        print("✅ 成功，最新3行:")
        print(df_raw.tail(3))
        print(f"   Close 最后值: {df_raw['Close'].iloc[-1]:.2f}\n")
    else:
        print("⚠️ 测试二失败\n")

    # ---- 测试新增：复权因子 ----
    print("👉 [测试三] 复权因子序列 (前5个):")
    factor = fetch_stock_adj_factor(test_code, start_d, end_d)
    if not factor.empty:
        print(factor.head())
        print(f"   因子最后值: {factor.iloc[-1]:.4f}\n")
    else:
        print("⚠️ 测试三失败\n")

    # ---- 测试新增：自行计算前复权 ----
    print("👉 [测试四] 自行计算前复权 (基于因子):")
    df_self = fetch_stock_1d_self_adj(test_code, start_d, end_d)
    if not df_self.empty:
        print("✅ 成功，最新3行:")
        print(df_self.tail(3))
        print(f"   Adj Close 最后值: {df_self['Adj Close'].iloc[-1]:.2f}\n")
    else:
        print("⚠️ 测试四失败\n")

    # ---- 对比两种前复权（允许小误差） ----
    if not df_orig.empty and not df_self.empty:
        diff = (df_orig['Adj Close'] - df_self['Adj Close']).abs().max()
        print(f"📊 两种前复权最大差异: {diff:.4f} (若接近0则两者一致)\n")

    print("🏁 全部测试完毕。")
