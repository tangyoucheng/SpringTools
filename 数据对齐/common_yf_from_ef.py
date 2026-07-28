#common_yf_from_ef.py

import efinance as ef
import pandas as pd
from datetime import datetime

# ==========================================
# 核心方法一：通用数据对齐清洗器（保持保留）
# ==========================================
def align_efinance_to_yfinance(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    通用对齐清洗器：将东财接口返回的中文字段强转并对齐为 yfinance 经典英文 6 列结构。
    支持 1分钟线、日线等东财所有历史 K 线输出。
    """
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()
        
    try:
        # 1. 建立中英文精密映射字典
        rename_dict = {
            '开盘': 'Open',
            '最高': 'High',
            '最低': 'Low',
            '收盘': 'Close',
            '成交量': 'Volume'
        }
        df_cleaned = df_raw.rename(columns=rename_dict)
        
        # 2. 建立标准的 DatetimeIndex 索引
        df_cleaned['Datetime'] = pd.to_datetime(df_cleaned['时间'])
        df_cleaned.set_index('Datetime', inplace=True)
        
        # 3. 补齐国际标准的后复权/前复权收盘价 'Adj Close'
        df_cleaned['Adj Close'] = df_cleaned['Close']
        
        # 4. 强转数据类型并严格保留 yfinance 经典 6 列
        target_columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        df_final = df_cleaned[target_columns].copy()
        
        for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
            df_final[col] = df_final[col].astype(float)
        df_final['Volume'] = df_final['Volume'].astype(int)
        
        return df_final

    except Exception as e:
        print(f"❌ [数据对齐失败]: {e}")
        return pd.DataFrame()


# ==========================================
# ⭐ 追加方法：当日实时 1分钟K线全自动抓取器（免传时间参数）
# ==========================================
def fetch_stock_today_live_1m_ef(stock_code: str) -> pd.DataFrame:
    """
    【无需指定时间】基于东财接口，全自动获取今天开盘至此时此刻的最新 1分钟 实时K线数据。
    自动利用系统时钟掐准“今天”与“现在这一秒”的时间切片。
    """
    try:
        # 1. 自动利用系统时钟锁定今天的日期边界
        today_str = datetime.today().strftime('%Y-%m-%d')
        
        # 2. 自动获取此时此刻的系统精确时间，作为盘中最高截取边界
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 3. 提取天级日期作为东财接口的网络请求参数（东财传参只需到天）
        st_date = datetime.today().strftime('%Y%m%d')
        
        # 4. 抓取东财 1分钟(klt=1) 原始数据
        df_raw = ef.stock.get_quote_history(
            stock_code, 
            klt=1, 
            start_date=st_date, 
            end_date=st_date
        )
        
        # 5. 调用独立对齐清洗方法
        df_aligned = align_efinance_to_yfinance(df_raw)
        
        # 6. 执行盘中高精度切片：从今天 00:00:00 一直切到当前说话的这一秒
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[today_str:current_time_str]
            
        return df_aligned

    except Exception as e:
        print(f"❌ [东财当日实时1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# ==========================================
# 核心方法三：历史指定时间范围 1分钟K线抓取器（保持保留）
# ==========================================
def fetch_stock_1m_data_ef(stock_code: str, start_time: str, end_time: str) -> pd.DataFrame:
    """
    获取指定历史时间范围内的 1分钟 K 线数据（完美对齐 yfinance 结构）。
    """
    try:
        st_date = pd.to_datetime(start_time).strftime('%Y%m%d')
        ed_date = pd.to_datetime(end_time).strftime('%Y%m%d')
        
        df_raw = ef.stock.get_quote_history(
            stock_code, 
            klt=1, 
            start_date=st_date, 
            end_date=ed_date
        )
        
        df_aligned = align_efinance_to_yfinance(df_raw)
        
        if not df_aligned.empty:
            df_aligned = df_aligned.loc[start_time:end_time]
            
        return df_aligned

    except Exception as e:
        print(f"❌ [历史1分钟线抓取失败]: {e}")
        return pd.DataFrame()


# ==========================================
# 核心方法四：1天 K 线（日线）独立抓取器（保持保留）
# ==========================================
def fetch_stock_1d_data_ef(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """
    获取指定日期范围内的 1天 K 线（日线）数据（完美对齐 yfinance 结构）。
    """
    try:
        st_date = pd.to_datetime(start_date).strftime('%Y%m%d')
        ed_date = pd.to_datetime(end_date).strftime('%Y%m%d')
        
        fqt_map = {"qfq": 1, "hfq": 2, "": 0}
        fqt_val = fqt_map.get(adjust, 1)
        
        df_raw = ef.stock.get_quote_history(
            stock_code, 
            klt=101, 
            start_date=st_date, 
            end_date=ed_date,
            fqt=fqt_val
        )
        return align_efinance_to_yfinance(df_raw)

    except Exception as e:
        print(f"❌ [东财1天线抓取失败]: {e}")
        return pd.DataFrame()


# ==========================================
# 🚀 盘后实战及东财全自动当日实时调用演示
# ==========================================
if __name__ == "__main__":
    code = "688551"  # 科威尔
    
    print("====== 🌟 演示：调用东财追加的【当日实时1分钟免参数】方法 ======")
    # 盘中或盘后运行，自动提取今日分时
    df_live_today = fetch_stock_today_live_1m_ef(code)
    
    if not df_live_today.empty:
        print("📊 成功全自动获取今日数据！东财今日最早3根K线明细：")
        print(df_live_today.head(3))
        print("\n📊 东财今日最新成交的3根K线明细：")
        print(df_live_today.tail(3))
        print(f"💡 今日截至目前已自动生成 {len(df_live_today)} 根 1m K线。")
    else:
        print("⚠️ 未能自动获取到今日数据，可能处于非交易时段或服务器清算延迟。")
        
    print("\n====== 📦 演示：东财原有的历史指定周期方法依旧完美保留 ======")
    # 验证历史范围分钟线依然可用
    df_hist_1m = fetch_stock_1m_data_ef(code, "2026-07-27 14:00:00", "2026-07-27 15:00:00")
    print(f"历史指定分钟线留存成功，行数: {len(df_hist_1m)}")
    
    # 验证历史日线依然可用
    df_hist_1d = fetch_stock_1d_data_ef(code, "2026-07-20", "2026-07-28")
    print(f"历史指定日线留存成功，行数: {len(df_hist_1d)}")
