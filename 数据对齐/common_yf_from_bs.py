# common_yf_from_bs.py
# 完整版：Baostock + 新浪混合数据源，含本地 Parquet 缓存、全局登录、增量更新

import os
import sys
import baostock as bs
import pandas as pd
import requests
import time
import os
import threading
import atexit
import random
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# 1. 获取当前目录和父目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 2. 先插入父目录（此时父目录最优先）
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 3. 再插入当前目录（当前目录会把父目录挤到后面，从而变成“最优先”）
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 4. 此时可以直接导入，无需加任何点（.）或反斜杠（\）
from common_stock_dict import stocks_dict

# =========================================================================
# 1. 全局登录管理（只登录一次，不手动注销，进程退出时自动清理）
# =========================================================================
_BS_READY = False
_BS_LOGIN_LOCK = threading.Lock()

def _ensure_baostock_ready():
    """确保 Baostock 已登录（只执行一次）"""
    global _BS_READY
    if _BS_READY:
        return
    with _BS_LOGIN_LOCK:
        if _BS_READY:
            return
        lg = bs.login()
        if lg.error_code != '0':
            raise ConnectionError(f"Baostock 登录失败: {lg.error_msg}")
        _BS_READY = True
        print("✅ Baostock 全局登录成功 (仅此一次)")

def _logout_baostock():
    """进程退出时自动注销"""
    global _BS_READY
    if _BS_READY:
        bs.logout()
        _BS_READY = False
        print("✅ Baostock 连接已释放")

atexit.register(_logout_baostock)

# =========================================================================
# 2. Baostock 查询函数（带重试和自动重连）
# =========================================================================
def _query_baostock(bs_code: str, start_date: str, end_date: str,
                    frequency: str, adjustflag: str = "2") -> pd.DataFrame:
    """
    封装 Baostock 查询，含自动重试与连接重置。
    frequency: 'd' 日线, '5'/'15'/'30'/'60' 分钟线
    adjustflag: '2' 前复权, '3' 不复权, '1' 后复权
    """
    global _BS_READY
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            _ensure_baostock_ready()
        except Exception as e:
            print(f"⚠️ 登录异常: {e}，重置状态重试 ({attempt+1}/{MAX_RETRIES})")
            _BS_READY = False
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1)
            continue

        if frequency == 'd':
            fields = "date,code,open,high,low,close,volume,amount"
        else:
            fields = "date,time,code,open,high,low,close,volume,amount"

        try:
            rs = bs.query_history_k_data_plus(
                bs_code,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjustflag
            )
        except Exception as e:
            # 捕获所有异常，包括 UnicodeDecodeError
            print(f"⚠️ 查询过程异常 ({type(e).__name__}): {e}，重置连接重试 ({attempt+1}/{MAX_RETRIES})")
            _BS_READY = False
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1)
            continue

        # 检查返回状态（也可能触发编码错误）
        try:
            if rs.error_code != '0':
                # 若错误信息涉及网络，则重置重试
                if "网络" in rs.error_msg or "接收" in rs.error_msg or "连接" in rs.error_msg:
                    print(f"⚠️ 网络错误: {rs.error_msg}，重置重试 ({attempt+1}/{MAX_RETRIES})")
                    _BS_READY = False
                    if attempt == MAX_RETRIES - 1:
                        print(f"❌ 最终失败: {rs.error_msg}")
                        return pd.DataFrame()
                    time.sleep(1)
                    continue
                else:
                    print(f"❌ 查询失败: {rs.error_msg}")
                    return pd.DataFrame()
        except Exception as e:
            # 读取 rs.error_msg 也可能触发编码错误
            print(f"⚠️ 读取错误信息异常: {e}，视为网络错误重试 ({attempt+1}/{MAX_RETRIES})")
            _BS_READY = False
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1)
            continue

        # 获取数据
        data_list = []
        try:
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
        except Exception as e:
            print(f"⚠️ 数据提取异常: {e}，重试 ({attempt+1}/{MAX_RETRIES})")
            _BS_READY = False
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1)
            continue

        if not data_list:
            return pd.DataFrame()

        df = pd.DataFrame(data_list, columns=rs.fields)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount'] if 'amount' in df.columns else ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    return pd.DataFrame()

# =========================================================================
# 3. 工具函数：代码转换、数据对齐
# =========================================================================
def _code_to_baostock(stock_code: str) -> str:
    if stock_code.startswith('6'):
        return f"sh.{stock_code}"
    else:
        return f"sz.{stock_code}"

def align_baostock_to_yfinance(df_raw: pd.DataFrame, is_minute: bool = False) -> pd.DataFrame:
    """清洗并标准化为六列格式（Open, High, Low, Close, Adj Close, Volume）"""
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    try:
        if is_minute:
            if 'date' in df_raw.columns and 'time' in df_raw.columns:
                sample = str(df_raw['time'].iloc[0])
                if len(sample) > 6 and sample.isdigit():
                    df_raw['Datetime'] = pd.to_datetime(df_raw['time'], errors='coerce')
                    if df_raw['Datetime'].isnull().all():
                        df_raw['Datetime'] = pd.to_datetime(df_raw['time'], format='%Y%m%d%H%M%S%f', errors='coerce')
                else:
                    time_padded = df_raw['time'].astype(str).str.zfill(6)
                    df_raw['Datetime'] = pd.to_datetime(df_raw['date'] + ' ' + time_padded, errors='coerce')
            else:
                if 'Datetime' in df_raw.columns:
                    df_raw['Datetime'] = pd.to_datetime(df_raw['Datetime'], errors='coerce')
                else:
                    df_raw['Datetime'] = pd.to_datetime(df_raw.index, errors='coerce')
        else:
            if 'date' in df_raw.columns:
                df_raw['Datetime'] = pd.to_datetime(df_raw['date'], errors='coerce')
            else:
                df_raw['Datetime'] = pd.to_datetime(df_raw.index, errors='coerce')

        df_raw = df_raw.dropna(subset=['Datetime'])
        if df_raw.empty:
            return pd.DataFrame()

        rename_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
            'volume': 'Volume', 'amount': 'Amount'
        }
        df_renamed = df_raw.rename(columns=rename_map)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col not in df_renamed.columns:
                df_renamed[col] = None

        df_renamed.set_index('Datetime', inplace=True)
        df_renamed['Adj Close'] = df_renamed['Close']

        target_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        df_final = df_renamed[target_cols].copy()
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        df_final['Volume'] = pd.to_numeric(df_final['Volume'], errors='coerce').fillna(0).astype(int)
        df_final.sort_index(inplace=True)
        return df_final
    except Exception as e:
        print(f"❌ [数据对齐失败]: {e}")
        return pd.DataFrame()

# =========================================================================
# 4. 智能日线缓存（自动下载并保存为 Parquet）
# =========================================================================
CACHE_DIR = "stocks_data/cache_baostock/daily"
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_stock_1d_data_bs(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    智能日线获取器（自动扩展缓存）：
    1. 若缓存不存在 → 下载 start_date ~ end_date 并保存。
    2. 若缓存存在但范围不足 → 自动下载缺失的前置/后置区间，合并后返回。
    """
    st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
    ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
    cache_file = os.path.join(CACHE_DIR, f"{stock_code}.parquet")
    
    # 如果缓存不存在，直接下载全量
    if not os.path.exists(cache_file):
        print(f"📥 首次下载 {stock_code} {st_date} ~ {ed_date}")
        return _download_and_cache(stock_code, st_date, ed_date, adjust)
    
    # 读取现有缓存
    try:
        df_cached = pd.read_parquet(cache_file)
        if not isinstance(df_cached.index, pd.DatetimeIndex):
            df_cached.index = pd.to_datetime(df_cached.index)
    except Exception as e:
        print(f"⚠️ 缓存损坏，重新下载 {stock_code}")
        return _download_and_cache(stock_code, st_date, ed_date, adjust)
    
    # 检查缓存覆盖范围
    cache_start = df_cached.index.min()
    cache_end = df_cached.index.max()
    need_download = False
    new_start = st_date
    new_end = ed_date
    
    # 如果需要更早的数据（向前扩展）
    if pd.to_datetime(st_date) < cache_start:
        need_download = True
        new_start = st_date
        print(f"🔄 向前扩展 {stock_code}: 补充 {st_date} ~ {cache_start.strftime('%Y-%m-%d')}")
    
    # 如果需要更新的数据（向后扩展）
    if pd.to_datetime(ed_date) > cache_end:
        need_download = True
        new_end = ed_date
        print(f"🔄 向后扩展 {stock_code}: 补充 {cache_end.strftime('%Y-%m-%d')} ~ {ed_date}")
    
    # 如果需要扩展，下载缺失区间并与现有缓存合并
    if need_download:
        # 下载新数据（使用不复权，因为我们要统一存储前复权）
        adjust_map = {"qfq": "2", "hfq": "1", "": "3"}
        adj_flag = adjust_map.get(adjust, "2")
        bs_code = _code_to_baostock(stock_code)
        
        # 注意：只下载缺失的区间，避免重复下载已有数据
        # 如果是向前扩展，下载 new_start ~ (cache_start - 1天)
        # 如果是向后扩展，下载 (cache_end + 1天) ~ new_end
        # 但为了简单，我们可以直接下载 new_start ~ new_end，然后合并去重
        # 因为 Baostock 查询速度很快，重复下载少量数据可以接受
        df_new_raw = _query_baostock(bs_code, new_start, new_end, frequency="d", adjustflag=adj_flag)
        if df_new_raw.empty:
            print(f"⚠️ 扩展区间无数据，可能未上市或停牌")
        else:
            df_new = align_baostock_to_yfinance(df_new_raw, is_minute=False)
            if not df_new.empty:
                # 合并：用新数据覆盖旧数据（去重）
                df_combined = pd.concat([df_cached, df_new]).sort_index()
                df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
                df_combined.to_parquet(cache_file)
                df_cached = df_combined
                print(f"💾 缓存已扩展，当前 {len(df_cached)} 行")
    
    # 返回请求区间内的数据
    return df_cached.loc[st_date:ed_date]

def _download_and_cache(stock_code: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
    """内部函数：下载并缓存"""
    adjust_map = {"qfq": "2", "hfq": "1", "": "3"}
    adj_flag = adjust_map.get(adjust, "2")
    bs_code = _code_to_baostock(stock_code)
    df_raw = _query_baostock(bs_code, start_date, end_date, frequency="d", adjustflag=adj_flag)
    if df_raw.empty:
        return pd.DataFrame()
    df_aligned = align_baostock_to_yfinance(df_raw, is_minute=False)
    if df_aligned.empty:
        return pd.DataFrame()
    # 保存缓存
    cache_file = os.path.join(CACHE_DIR, f"{stock_code}.parquet")
    df_aligned.to_parquet(cache_file)
    print(f"💾 缓存已保存: {cache_file} ({len(df_aligned)} 行)")
    return df_aligned

# =========================================================================
# 5. 复权因子（返回 Series，若无则全1）
# =========================================================================
def fetch_stock_adj_factor(stock_code: str, start_date: str, end_date: str) -> pd.Series:
    st_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
    ed_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
    bs_code = _code_to_baostock(stock_code)

    try:
        _ensure_baostock_ready()
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
        return pd.Series(1.0, index=date_range, name='adjust_factor')

    rs = bs.query_adjust_factor(bs_code, start_date=st_date, end_date=ed_date)
    if rs.error_code != '0':
        print(f"⚠️ 复权因子查询失败: {rs.error_msg}，使用默认 1.0")
        date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
        return pd.Series(1.0, index=date_range, name='adjust_factor')

    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())

    if not data_list or 'adjust_factor' not in rs.fields:
        print(f"ℹ️ 无除权事件或因子字段缺失，复权因子默认为 1.0")
        date_range = pd.date_range(start=st_date, end=ed_date, freq='D')
        return pd.Series(1.0, index=date_range, name='adjust_factor')

    df = pd.DataFrame(data_list, columns=rs.fields)
    df['adjust_factor'] = pd.to_numeric(df['adjust_factor'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df['adjust_factor'].dropna().sort_index()

def calc_forward_price(raw_df: pd.DataFrame, factor_series: pd.Series) -> pd.DataFrame:
    if raw_df.empty or factor_series.empty:
        return pd.DataFrame()
    common = raw_df.index.intersection(factor_series.index)
    if len(common) == 0:
        return pd.DataFrame()
    raw = raw_df.loc[common].copy()
    factor = factor_series.loc[common]
    base_factor = factor.iloc[-1]
    fwd_factor = base_factor / factor
    for col in ['Open', 'High', 'Low', 'Close']:
        raw[col] = raw[col] * fwd_factor
    raw['Adj Close'] = raw['Close']
    return raw

def fetch_stock_1d_self_adj(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """自行计算前复权（不复权 + 因子）"""
    raw_df = fetch_stock_1d_data_bs(stock_code, start_date, end_date, adjust="")
    if raw_df.empty:
        return pd.DataFrame()
    factor = fetch_stock_adj_factor(stock_code, start_date, end_date)
    if factor.empty:
        return pd.DataFrame()
    return calc_forward_price(raw_df, factor)

# =========================================================================
# 6. 新浪 1 分钟线（弥补 Baostock 无 1 分钟）
# =========================================================================
def _fetch_sina_minute(stock_code: str, scale: int = 1, count: int = 300) -> pd.DataFrame:
    if stock_code.startswith('6'):
        sina_symbol = f"sh{stock_code}"
    else:
        sina_symbol = stock_code
    url = (f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
           f"CN_MarketData.getKLineData?symbol={sina_symbol}&scale={scale}&ma=no&datalen={count}")
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://finance.sina.com.cn/'}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df.rename(columns={'day': 'Datetime', 'open': 'Open', 'high': 'High',
                           'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
        for col in ['Open', 'High', 'Low', 'Close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0).astype(int)
        df['Adj Close'] = df['Close']
        df.sort_index(inplace=True)
        return df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
    except Exception as e:
        print(f"❌ 新浪分钟线失败: {e}")
        return pd.DataFrame()

def fetch_stock_today_live_1m_bs(stock_code: str) -> pd.DataFrame:
    """今日实时 1 分钟线（新浪）"""
    df = _fetch_sina_minute(stock_code, scale=1, count=500)
    if df.empty:
        return pd.DataFrame()
    tz_bj = timezone(timedelta(hours=8))
    today_str = datetime.now(tz_bj).strftime('%Y-%m-%d')
    return df.loc[today_str:]

def fetch_stock_1m_data_bs(stock_code: str, start_time: str, end_time: str) -> pd.DataFrame:
    """历史 1 分钟线（新浪）"""
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time)
    minutes_needed = int((end_dt - start_dt).total_seconds() / 60) + 50
    count = min(max(minutes_needed, 100), 2000)
    df = _fetch_sina_minute(stock_code, scale=1, count=count)
    if df.empty:
        return pd.DataFrame()
    return df.loc[start_time:end_time]


# -------------------- 线程安全打印 --------------------
_print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)

# -------------------- 修改 _query_baostock（去登录，纯查询） --------------------
# =========================================================================
# 最终版 _query_baostock（专治解压/编码错误）
# =========================================================================
def _query_baostock(bs_code: str, start_date: str, end_date: str,
                    frequency: str, adjustflag: str = "2") -> pd.DataFrame:
    """
    最终稳定版：支持网络错误、解压错误、编码错误的健壮重试。
    失败次数过多时直接返回空，避免卡死。
    """
    global _BS_READY
    MAX_RETRIES = 3  # 减少重试次数，快速跳过
    for attempt in range(MAX_RETRIES):
        try:
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
        except Exception as e:
            error_msg = str(e)
            # 如果是解压或编码错误，重置连接状态
            if any(key in error_msg for key in ["decompress", "zlib", "distance", "utf-8", "unpack", "codec"]):
                safe_print(f"⚠️ 数据解析错误（{type(e).__name__}），重置连接并重试 {attempt+1}/{MAX_RETRIES}")
                _BS_READY = False  # 强制下次重新登录
            else:
                safe_print(f"⚠️ 查询异常（{type(e).__name__}）: {e}，重试 {attempt+1}/{MAX_RETRIES}")
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1.5 ** (attempt + 1))  # 1.5, 2.25, 3.375 秒
            continue

        # 检查返回状态码
        try:
            if rs.error_code != '0':
                err_msg = rs.error_msg
                if any(key in err_msg for key in ["网络", "接收", "连接", "超时", "解压", "数据"]):
                    safe_print(f"⚠️ 服务器错误: {err_msg}，重试 {attempt+1}/{MAX_RETRIES}")
                    if "解压" in err_msg:
                        _BS_READY = False
                    if attempt == MAX_RETRIES - 1:
                        return pd.DataFrame()
                    time.sleep(1.5 ** (attempt + 1))
                    continue
                else:
                    safe_print(f"❌ 查询失败（业务错误）: {err_msg}")
                    return pd.DataFrame()  # 业务错误直接退出
        except Exception as e:
            safe_print(f"⚠️ 读取错误信息异常: {e}，视为网络错误重试 {attempt+1}/{MAX_RETRIES}")
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1.5 ** (attempt + 1))
            continue

        # 提取数据
        data_list = []
        try:
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
        except Exception as e:
            error_msg = str(e)
            safe_print(f"⚠️ 数据提取异常: {error_msg}，重试 {attempt+1}/{MAX_RETRIES}")
            if any(key in error_msg for key in ["decompress", "zlib", "distance", "utf-8"]):
                _BS_READY = False
            if attempt == MAX_RETRIES - 1:
                return pd.DataFrame()
            time.sleep(1.5 ** (attempt + 1))
            continue

        if not data_list:
            return pd.DataFrame()

        df = pd.DataFrame(data_list, columns=rs.fields)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount'] if 'amount' in df.columns else ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df

    return pd.DataFrame()

# =========================================================================
# 单只股票更新任务（单线程调用，无并发冲突）
# =========================================================================
def _update_single_stock_task(code: str, start_date: str, end_date: str) -> tuple:
    """
    处理单只股票的增量更新或首次下载（单线程安全）。
    """
    stock_num = code.split('.')[1]
    cache_file = os.path.join(CACHE_DIR, f"{stock_num}.parquet")
    status = "skipped"

    try:
        if os.path.exists(cache_file):
            # 增量更新
            df_existing = pd.read_parquet(cache_file)
            if not isinstance(df_existing.index, pd.DatetimeIndex):
                df_existing.index = pd.to_datetime(df_existing.index)

            last_date = df_existing.index.max().strftime('%Y-%m-%d')
            if last_date >= end_date:
                status = "uptodate"
                return (stock_num, status)

            start_inc = (pd.to_datetime(last_date) + timedelta(days=1)).strftime('%Y-%m-%d')
            safe_print(f"🔄 {stock_num}: 补充 {start_inc} ~ {end_date}")

            df_new_raw = _query_baostock(code, start_inc, end_date, frequency="d", adjustflag="2")
            if df_new_raw.empty:
                status = "no_data"
                return (stock_num, status)

            df_new = align_baostock_to_yfinance(df_new_raw, is_minute=False)
            if df_new.empty:
                status = "align_fail"
                return (stock_num, status)

            df_combined = pd.concat([df_existing, df_new]).sort_index()
            df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
            df_combined.to_parquet(cache_file)
            status = "updated"
            safe_print(f"✅ {stock_num} 更新完成，现有 {len(df_combined)} 行")
        else:
            # 首次下载
            safe_print(f"📥 {stock_num}: 首次全量下载 {start_date} ~ {end_date}")
            df = fetch_stock_1d_data_bs(stock_num, start_date, end_date, adjust="qfq")
            status = "downloaded" if not df.empty else "failed"

    except Exception as e:
        safe_print(f"⚠️ {stock_num} 处理异常: {e}")
        status = "error"

    # 单线程模式下，每次请求后固定等待 0.3 秒，有效避免服务器压力
    time.sleep(0.3)
    return (stock_num, status)

# =========================================================================
# 【单线程版】全市场更新（稳定优先，速度次之）
# =========================================================================
def update_all_stocks_incremental(start_date: str = None, end_date: str = None,
                                  stock_list: list = None):
    """
    单线程全市场更新（稳定第一）。
    参数：
        start_date: 首次下载起始日期（默认5年前）
        end_date: 截止日期（默认今天）
        stock_list: 指定股票代码列表（如 ['sh.600000']），若为None则自动获取全市场
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')

    # 1. 主线程登录
    try:
        _ensure_baostock_ready()
    except Exception as e:
        print(f"❌ Baostock 登录失败: {e}")
        return

    # 2. 获取股票列表
    if stock_list is None:
        print("🔄 正在获取全市场股票列表...")
        rs = bs.query_stock_basic()
        if rs.error_code != '0':
            print(f"❌ 获取列表失败: {rs.error_msg}")
            stock_list = ['sh.600000', 'sh.600036', 'sz.000001']
            print(f"⚠️ 使用兜底列表: {stock_list}")
        else:
            stock_list = []
            while (rs.error_code == '0') & rs.next():
                code = rs.get_row_data()[0]
                if code.startswith(('sh.', 'sz.')) and not code.startswith(('sh.000', 'sh.999')):
                    stock_list.append(code)
            print(f"✅ 获取到 {len(stock_list)} 只股票")
    else:
        print(f"📋 使用指定的 {len(stock_list)} 只股票")

    if not stock_list:
        print("❌ 无股票可更新")
        return

    print(f"🔄 开始单线程更新（稳定模式），区间 {start_date} ~ {end_date}")
    total = len(stock_list)
    completed = 0
    failed_stocks = []

    for code in stock_list:
        stock_num, status = _update_single_stock_task(code, start_date, end_date)
        completed += 1
        if status in ["failed", "error", "no_data"]:
            failed_stocks.append(stock_num)
        if completed % 50 == 0:
            print(f"⏳ 进度: {completed}/{total}，失败: {len(failed_stocks)}")

    print(f"🎉 更新完成！总计 {total} 只，失败 {len(failed_stocks)} 只")
    if failed_stocks:
        print(f"❌ 失败列表: {failed_stocks[:10]}{'...' if len(failed_stocks)>10 else ''}")

# =========================================================================
# 7. 全市场初始化/增量更新（支持指定起始日期）
# =========================================================================
def update_all_stocks_incremental_delete(start_date: str = None, end_date: str = None):
    """
    全市场数据初始化/增量更新（修复版：使用 query_stock_basic 获取列表）
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
    
    # ----- 修复点：改用 query_stock_basic 获取全市场股票 -----
    try:
        _ensure_baostock_ready()
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 方法1：使用 query_stock_basic（推荐，更稳定）
    rs = bs.query_stock_basic()
    if rs.error_code != '0':
        print(f"❌ 获取股票列表失败: {rs.error_msg}")
        print("尝试使用备用方法 query_all_stock...")
        # 备用方法：使用 query_all_stock
        rs = bs.query_all_stock(day=end_date)
        if rs.error_code != '0':
            print(f"❌ 备用方法也失败: {rs.error_msg}")
            return
    
    #codes = []
    #while (rs.error_code == '0') & rs.next():
    #    row = rs.get_row_data()
    #    # query_stock_basic 返回的列：code, name, industry, ...
    #    code = row[0]
    #    # 只保留沪深A股（去掉北交所、指数等）
    #    if code.startswith(('sh.', 'sz.')) and not code.startswith(('sh.000', 'sh.999')):
    #        codes.append(code)
    #
    #if not codes:
    #    print("❌ 未获取到任何股票代码，请检查网络和 Baostock 版本")
    #    print("尝试手动指定测试股票...")
    #    codes = ['sh.600000', 'sh.600036', 'sz.000001']  # 兜底
    #    print(f"使用兜底列表: {codes}")
    #
    #print(f"🔄 共 {len(codes)} 只股票，区间 {start_date} ~ {end_date}")

    codes = []
    for stock_code in stocks_dict.keys():
        if stock_code.startswith('6'):
            codes.append(f"sh.{stock_code}")
        else:
            codes.append(f"sz.{stock_code}")
    
    for i, code in enumerate(codes):
        stock_num = code.split('.')[1]
        cache_file = os.path.join(CACHE_DIR, f"{stock_num}.parquet")
        
        if os.path.exists(cache_file):
            # ---- 增量更新 ----
            try:
                df_existing = pd.read_parquet(cache_file)
                if not isinstance(df_existing.index, pd.DatetimeIndex):
                    df_existing.index = pd.to_datetime(df_existing.index)
                last_date = df_existing.index.max().strftime('%Y-%m-%d')
                
                if last_date >= end_date:
                    if (i + 1) % 500 == 0:
                        print(f"⏳ 进度: {i+1}/{len(codes)} (已最新)")
                    continue
                
                start_inc = (pd.to_datetime(last_date) + timedelta(days=1)).strftime('%Y-%m-%d')
                print(f"🔄 {stock_num}: 补充 {start_inc} ~ {end_date}")
                
                bs_code = _code_to_baostock(stock_num)
                df_new_raw = _query_baostock(bs_code, start_inc, end_date, frequency="d", adjustflag="2")
                if df_new_raw.empty:
                    continue
                df_new = align_baostock_to_yfinance(df_new_raw, is_minute=False)
                if df_new.empty:
                    continue
                
                df_combined = pd.concat([df_existing, df_new]).sort_index()
                df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
                df_combined.to_parquet(cache_file)
                print(f"✅ {stock_num} 更新完成，现有 {len(df_combined)} 行")
            except Exception as e:
                print(f"⚠️ {stock_num} 更新异常: {e}")
                continue
        else:
            # ---- 首次下载 ----
            print(f"📥 {stock_num}: 首次全量下载 {start_date} ~ {end_date}")
            fetch_stock_1d_data_bs(stock_num, start_date, end_date, adjust="qfq")
        
        if (i + 1) % 100 == 0:
            print(f"⏳ 进度: {i+1}/{len(codes)}")
    
    print("🎉 全市场更新完成！")

# =========================================================================
# 8. 测试入口
# =========================================================================
if __name__ == "__main__":
    # 指定股票列表（省去全市场扫描）
    #my_stocks = ['sh.600983', 'sh.600984', 'sh.601169']
    my_stocks = []
    for stock_code in stocks_dict.keys():
        if stock_code.startswith('6'):
            my_stocks.append(f"sh.{stock_code}")
        else:
            my_stocks.append(f"sz.{stock_code}")

    # 执行全市场增量更新（第一次会很慢，以后每天只增量）
    print("👉 [初始化] 从 2025-01-01 开始下载全市场数据（仅演示，实际运行需谨慎）")
    #update_all_stocks_incremental(start_date="2025-01-01")  
    update_all_stocks_incremental(start_date="2025-01-01", stock_list=my_stocks)
    #update_all_stocks_incremental() 

    #test_code = "688551"
    #print("="*70)
    #print("📡 混合数据源完整测试（日线缓存+复权因子+新浪分钟线）")
    #print("="*70)
#
    ## 测试日线缓存
    #print("\n👉 [测试1] 日线 (前复权，自动缓存):")
    #df_day = fetch_stock_1d_data_bs(test_code, "2026-07-15", "2026-07-28", adjust="qfq")
    #if not df_day.empty:
    #    print(df_day.tail(3))
    #    print(f"最后收盘价: {df_day['Close'].iloc[-1]:.2f}\n")
#
    ## 测试复权因子
    #print("👉 [测试2] 复权因子:")
    #factor = fetch_stock_adj_factor(test_code, "2025-07-15", "2026-07-28")
    #print(factor.head())
    #print(f"因子最后值: {factor.iloc[-1]:.4f}\n")
#
    ## 测试自行计算前复权
    #print("👉 [测试3] 自行计算前复权:")
    #df_self = fetch_stock_1d_self_adj(test_code, "2026-07-15", "2026-07-28")
    #if not df_self.empty:
    #    print(df_self.tail(3))
    #    print(f"计算后收盘价: {df_self['Close'].iloc[-1]:.2f}\n")
#
    ## 测试新浪分钟线
    #print("👉 [测试4] 新浪今日1分钟线 (前5条):")
    #df_live = fetch_stock_today_live_1m_bs(test_code)
    #if not df_live.empty:
    #    print(df_live.head())
    #    print(f"今日数据条数: {len(df_live)}\n")
#
    ## 测试历史分钟线
    #print("👉 [测试5] 新浪历史1分钟线 (2026-07-27 13:30-14:30):")
    #df_hist = fetch_stock_1m_data_bs(test_code, "2026-07-27 13:30:00", "2026-07-27 14:30:00")
    #if not df_hist.empty:
    #    print(df_hist.tail(2))
    #    print(f"区间行数: {len(df_hist)}\n")
#
    #print("🏁 所有测试完成。")
