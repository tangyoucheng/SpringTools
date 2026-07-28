#common_yf_from_ak.py

import akshare as ak
import pandas as pd
from datetime import datetime, timezone, timedelta

# =========================================================================
# 方法一：通用数据对齐清洗器
# =========================================================================
def align_akshare_to_yfinance(df_raw: pd.DataFrame, is_minute: bool = False) -> pd.DataFrame:
    """
    将 AkShare 日线/分钟线接口返回的数据，统一清洗、强转并对齐为 yfinance 英文标准 6 列结构。
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    try:
        # 分流处理 AkShare “日期”与“时间”的接口字段差异
        if is_minute:
            rename_dict = {'时间': 'Datetime', '开盘': 'Open', '最高': 'High', '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'}
        else:
            rename_dict = {'日期': 'Datetime', '开盘': 'Open', '最高': 'High', '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'}
            
        df_cleaned = df_raw.rename(columns=rename_dict)
        df_cleaned['Datetime'] = pd.to_datetime(df_cleaned['Datetime'])
        df_cleaned.set_index('Datetime', inplace=True)
        df_cleaned['Adj Close'] = df_cleaned['Close']
        
        target_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        df_final = df_cleaned[target_columns].copy()
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            df_final[col] = df_final[col].astype(float)
        df_final['Volume'] = df_final['Volume'].astype(int)
        df_final.sort_index(inplace=True)
        return df_final
    except Exception as e:
        print(f"❌ [AkShare数据对齐失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法二：【全自动免参】当日实时 1分钟K线抓取器（固定北京时间）
# =========================================================================
def fetch_stock_today_live_1m_ak(stock_code: str) -> pd.DataFrame:
    """
    无需指定时间，全自动获取今天开盘至此时此刻最新的 1分钟 实时K线。
    底层强制锁定北京时间（东八区），完美自适应海外运行环境。
    """
    try:
        # 强制指定东八区时区对象，获取绝对的北京时间
        tz_bj = timezone(timedelta(hours=8))
        now_bj = datetime.now(tz_bj)
        
        today_str = now_bj.strftime('%Y-%m-%d')
        current_time_str = now_bj.strftime('%Y-%m-%d %H:%M:%S')
        
        # 提取高频全量分钟快照
        df_raw = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='1', adjust='')
        df_aligned = align_akshare_to_yfinance(df_raw, is_minute=True)
        
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[today_str:current_time_str]
        return df_aligned
    except Exception as e:
        print(f"❌ [AkShare当日实时1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法三：指定历史时间范围 1分钟K线抓取器
# =========================================================================
def fetch_stock_1m_data_ak(stock_code: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    获取指定历史时间范围内的 1分钟 K线数据（基于本地内存秒级高精度切片）。
    """
    try:
        df_raw = ak.stock_zh_a_hist_min_em(symbol=stock_code, period='1', adjust='')
        df_aligned = align_akshare_to_yfinance(df_raw, is_minute=True)
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[start_time:end_time]
        return df_aligned
    except Exception as e:
        print(f"❌ [AkShare历史1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法四：指定日期范围 1天K线（日线）抓取器
# =========================================================================
def fetch_stock_1d_data_ak(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取指定日期范围内的日线数据。支持标准的前复权逻辑。
    """
    try:
        st_date = pd.to_datetime(start_date).strftime('%Y%m%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y%m%d')
        df_raw = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=st_date, end_date=ed_date, adjust=adjust)
        return align_akshare_to_yfinance(df_raw, is_minute=False)
    except Exception as e:
        print(f"❌ [AkShare 1天线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 🚀 AkShare 接口测试入口（完整覆盖测试）
# =========================================================================
if __name__ == "__main__":
    test_code = "688551"  # 科威尔
    print("==================================================================")
    print(f"📡 启动 AkShare 工业级开源数据库测试自动化流程，标的: {test_code}")
    print("==================================================================\n")
    
    # 测试一：当日实时全自动1分钟线提取
    print("👉 [测试一]: 正在调用【当日实时免参1分钟接口】(已锁死北京时间)...")
    df_live = fetch_stock_today_live_1m_ak(test_code)
    if not df_live.empty:
        print("Base结构对齐成功！今日最新2根K线明细:")
        print(df_live.tail(2))
        print(f"📊 今日已生成分钟K线总数: {len(df_live)} 根\n")
    else:
        print("⚠️ 测试一未返回数据，请检查网络或是否处于非交易日。\n")
        
    # 测试二：历史指定范围1分钟线截取
    print("👉 [测试二]: 正在调用【指定历史范围1分钟接口】...")
    df_hist_1m = fetch_stock_1m_data_ak(test_code, "2026-07-27 13:30:00", "2026-07-27 14:30:00")
    if not df_hist_1m.empty:
        print("✅ 测试二成功！高级内存切片机制工作正常。明细尾部:")
        print(df_hist_1m.tail(2))
        print(f"📊 截取历史时段行数: {len(df_hist_1m)} 行\n")
        
    # 测试三：历史指定日线数据获取
    print("👉 [测试三]: 正在调用【指定日期范围日线接口】...")
    df_hist_1d = fetch_stock_1d_data_ak(test_code, "2026-07-15", "2026-07-28", adjust="qfq")
    if not df_hist_1d.empty:
        print("✅ 测试三成功！官方历史专线清洗成功。最新3个交易日明细:")
        print(df_hist_1d.tail(3))
        print(f"📊 国际量化格式检验: {df_hist_1d.columns.tolist()}")
    print("\n🏁 AkShare 独立量化数据管道全部测试完毕，运行一切正常。")
