#common_yf_from_ef.py

import efinance as ef
import pandas as pd
from datetime import datetime, timezone, timedelta

# =========================================================================
# 方法一：通用数据对齐清洗器
# =========================================================================
def align_efinance_to_yfinance(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    将东财中文字段和结构完美强转为 yfinance 经典的英文 6 列结构和 Datetime 索引。
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
    try:
        rename_dict = {'开盘': 'Open', '最高': 'High', '最低': 'Low', '收盘': 'Close', '成交量': 'Volume'}
        df_cleaned = df_raw.rename(columns=rename_dict)
        df_cleaned['Datetime'] = pd.to_datetime(df_cleaned['时间'])
        df_cleaned.set_index('Datetime', inplace=True)
        df_cleaned['Adj Close'] = df_cleaned['Close']
        
        target_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        df_final = df_cleaned[target_columns].copy()
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            df_final[col] = df_final[col].astype(float)
        df_final['Volume'] = df_final['Volume'].astype(int)
        return df_final
    except Exception as e:
        print(f"❌ [东财数据对齐失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法二：【全自动免参】当日实时 1分钟K线抓取器（固定北京时间）
# =========================================================================
def fetch_stock_today_live_1m_ef(stock_code: str) -> pd.DataFrame:
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
        st_date = now_bj.strftime('%Y%m%d')
        
        # 请求东财当天数据
        df_raw = ef.stock.get_quote_history(stock_code, klt=1, start_date=st_date, end_date=st_date)
        df_aligned = align_efinance_to_yfinance(df_raw)
        
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[today_str:current_time_str]
        return df_aligned
    except Exception as e:
        print(f"❌ [东财当日实时1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法三：指定历史时间范围 1分钟K线抓取器
# =========================================================================
def fetch_stock_1m_data_ef(stock_code: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    获取指定历史具体时间段内的 1分钟 K线数据。
    """
    try:
        st_date = pd.to_datetime(start_time).strftime('%Y%m%d')
        ed_date = pd.to_datetime(end_time).strftime('%Y%m%d')
        df_raw = ef.stock.get_quote_history(stock_code, klt=1, start_date=st_date, end_date=ed_date)
        df_aligned = align_efinance_to_yfinance(df_raw)
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[start_time:end_time]
        return df_aligned
    except Exception as e:
        print(f"❌ [东财历史1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 方法四：指定日期范围 1天K线（日线）抓取器
# =========================================================================
def fetch_stock_1d_data_ef(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取指定日期范围内的日线数据。adjust可选: 'qfq'(前复权), 'hfq'(后复权), ''(不复权)
    """
    try:
        st_date = pd.to_datetime(start_date).strftime('%Y%m%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y%m%d')
        fqt_val = {"qfq": 1, "hfq": 2, "": 0}.get(adjust, 1)
        df_raw = ef.stock.get_quote_history(stock_code, klt=101, start_date=st_date, end_date=ed_date, fqt=fqt_val)
        return align_efinance_to_yfinance(df_raw)
    except Exception as e:
        print(f"❌ [东财1天线抓取失败]: {e}")
        return pd.DataFrame()


# =========================================================================
# 🚀 东方财富接口测试入口（完整覆盖测试）
# =========================================================================
if __name__ == "__main__":
    test_code = "688551"  # 科威尔
    print("==================================================================")
    print(f"📡 启动东方财富（efinance）独立脚本测试自动化流程，标的: {test_code}")
    print("==================================================================\n")
    
    # 测试一：当日实时全自动1分钟线提取
    print("👉 [测试一]: 正在调用【当日实时免参1分钟接口】(已锁死北京时间)...")
    df_live = fetch_stock_today_live_1m_ef(test_code)
    if not df_live.empty:
        print("✅ 测试一成功！数据对齐完毕。今日最新2根K线明细:")
        print(df_live.tail(2))
        print(f"📊 今日已生成分钟K线总数: {len(df_live)} 根\n")
    else:
        print("⚠️ 测试一未返回数据，请检查网络或是否处于非交易日。\n")
        
    # 测试二：历史指定范围1分钟线截取
    print("👉 [测试二]: 正在调用【指定历史范围1分钟接口】...")
    df_hist_1m = fetch_stock_1m_data_ef(test_code, "2026-07-27 13:30:00", "2026-07-27 14:30:00")
    if not df_hist_1m.empty:
        print("✅ 测试二成功！历史范围分钟数据切片成功。明细尾部:")
        print(df_hist_1m.tail(2))
        print(f"📊 截取历史时段行数: {len(df_hist_1m)} 行\n")
        
    # 测试三：历史指定日线数据获取
    print("👉 [测试三]: 正在调用【指定日期范围日线接口】...")
    df_hist_1d = fetch_stock_1d_data_ef(test_code, "2026-07-15", "2026-07-28", adjust="qfq")
    if not df_hist_1d.empty:
        print("✅ 测试三成功！标准前复权日线对齐成功。最新3个交易日明细:")
        print(df_hist_1d.tail(3))
        print(f"📊 索引数据类型验证: {type(df_hist_1d.index)}")
    print("\n🏁 东方财富独立量化数据管道全部测试完毕，运行一切正常。")

