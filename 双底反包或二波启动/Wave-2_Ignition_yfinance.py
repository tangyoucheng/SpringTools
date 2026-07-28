#cdp_poc_today_ATR.py
import os
import sys
import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# 使用免安装版本时，为了读取CDP_config.py，添加的设定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 假设 stock_dict 从配置中导入，若本地测试可自行定义
#from cdp_poc_today_ATR_config import stocks_list

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ==========================================
# 第一部分：高精度量化形态识别核心引擎
# ==========================================


def is_limit_up(close, pre_close, ticker=""):
    """
    【高精度 A 股涨停卡死判定函数】
    1. 完美解析 yfinance 格式代码 (如 300750.SZ)
    2. 严格比对分钱价格，杜绝低价股伪涨停 Bug
    """
    if pre_close <= 1e-4:
        return False

    ticker_str = str(ticker).upper()
    pure_code = ticker_str.split(".")[0]

    # 动态匹配涨幅限制（完美包容 688 和 689 科创板大段）
    if "ST" in ticker_str:
        pct = 0.05
    elif pure_code.startswith("30") or pure_code.startswith("68"):
        pct = 0.20  # 创业板、科创板
    else:
        pct = 0.10  # 主板

    # 精确算分钱，离散进位计算
    limit_price = round(pre_close * (1 + pct) + 1e-9, 2)
    return close >= limit_price


def find_pattern_instances_fast(df, ticker=""):
    """
    【NumPy 高速形态寻找核心】
    1. 彻底切断未来函数，阴线缩量严格以涨停当日均量作为唯一参照基准
    2. 全流程零均值/NaN 熔断，保障停牌断层不会引发 False 崩溃
    3. 将所有需要的列提取为 NumPy 数组，彻底摆脱 .iloc 的性能瓶颈
    """
    df_clone = df.copy()

    # 统一列名规范，并在计算均线前用 fillna(0) 填充，防止停牌导致 rolling 全盘 NaN
    df_clone.columns = [str(col).lower() for col in df_clone.columns]
    df_clone["volume"] = df_clone["volume"].fillna(0)
    df_clone["vol_ma5"] = df_clone["volume"].rolling(5).mean().fillna(0)

    # 提取安全底层 NumPy 矩阵
    opens = df_clone["open"].to_numpy()
    highs = df_clone["high"].to_numpy()
    closes = df_clone["close"].to_numpy()
    volumes = df_clone["volume"].to_numpy()
    vol_ma5 = df_clone["vol_ma5"].to_numpy()

    n = len(df_clone)
    pattern_indices = []

    if n < 10:
        return pattern_indices

    i = 1
    while i < n:
        pre_close_i = closes[i - 1]

        # 1. 寻找涨停日 i
        if not is_limit_up(closes[i], pre_close_i, ticker):
            i += 1
            continue

        limit_up_idx = i
        limit_close = closes[limit_up_idx]
        limit_vol = volumes[limit_up_idx]

        # 【锁定基准】锁死涨停当天的5日均量作为标准，拒绝后期洗盘日的自身污染
        limit_vol_ma5 = vol_ma5[limit_up_idx]

        # 如果涨停日异常兜底，采用当天成交量的 60% 代替
        if np.isnan(limit_vol_ma5) or limit_vol_ma5 <= 1e-4:
            limit_vol_ma5 = limit_vol * 0.6

        pattern_found_in_this_wave = False
        next_i = i + 1

        # 2. 寻找涨停后的缩量阴线被套日 j
        for j in range(limit_up_idx + 1, min(limit_up_idx + 6, n)):
            is_yin = closes[j] < opens[j]
            is_trapped = closes[j] < limit_close

            v_j = volumes[j]
            if np.isnan(v_j) or v_j <= 1e-4:
                continue

            is_low_vol = v_j < limit_vol and v_j < limit_vol_ma5

            if is_yin and is_trapped and is_low_vol:
                yin_idx = j
                yin_high = highs[yin_idx]

                # 3. 寻找反包大阳线日 k
                for k in range(yin_idx + 1, min(limit_up_idx + 6, n)):
                    pre_close_k = closes[k - 1]
                    if pre_close_k <= 1e-4:
                        continue

                    is_big_yang = (closes[k] - pre_close_k) / pre_close_k >= 0.05
                    is_rebound_limit = is_limit_up(closes[k], pre_close_k, ticker)
                    is_engulfing = closes[k] > yin_high

                    if (is_big_yang or is_rebound_limit) and is_engulfing:
                        pattern_indices.append(k)  # 捕获反包日 K
                        pattern_found_in_this_wave = True
                        next_i = k + 1
                        break
                if pattern_found_in_this_wave:
                    break

        i = next_i if pattern_found_in_this_wave else i + 1

    return pattern_indices


def screen_single_stock(ticker, start_date="2025-01-01", end_date="2026-07-28"):
    """
    【单股高时效性筛选引擎】
    """
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty or len(df) < 20:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [str(col).lower() for col in df.columns]
        df = df.reset_index(drop=True)

        trigger_points = find_pattern_instances_fast(df, ticker)

        if len(trigger_points) >= 1:
            latest_idx = len(df) - 1
            most_recent_trigger_k = trigger_points[-1]
            days_since_trigger = latest_idx - most_recent_trigger_k

            # 【时效性黄金跨度】反包大阳线发生在 1~4 天前，今天处于均线回踩期
            if days_since_trigger < 1 or days_since_trigger > 4:
                return None

            current_close = df["close"].iloc[latest_idx]
            if hasattr(current_close, "item"):
                current_close = current_close.item()

            df["ma5"] = df["close"].rolling(5).mean().fillna(0)
            current_ma5 = df["ma5"].iloc[latest_idx]
            if hasattr(current_ma5, "item"):
                current_ma5 = current_ma5.item()

            if current_ma5 <= 1e-4 or np.isnan(current_close):
                return None

            deviation = abs(current_close - current_ma5) / current_ma5

            if deviation <= 0.015:
                return {
                    "代码": ticker,
                    "当前收盘": round(current_close, 2),
                    "5日均线": round(current_ma5, 2),
                    "历史形态次数": len(trigger_points),
                    "距反包日天数": days_since_trigger,
                    "5日线偏离度(%)": round(deviation * 100, 2),
                }
    except Exception:
        # 单只股票网络超时或停牌异常，进行静默隔离，防止打断全市场扫描
        return None
    return None


# ==========================================
# 第二部分：多线程异步全市场扫描器骨架
# ==========================================


def generate_all_a_share_tickers():
    """
    【自动构造 A 股后缀代码】
    工业生产中推荐使用 akshare (ak.stock_info_a_code_name) 或 tushare 获取实时代码。
    此骨架函数采用高效的内置规则，覆盖主板、创业板、科创板常见号段，生成符合 yfinance 要求的后缀。
    """
    tickers = []

    # 1. 创业板 (300xxx, 301xxx) -> 深交所 .SZ
    #for i in range(1, 150):
    #    tickers.append(f"300{i:03d}.SZ")
    #    tickers.append(f"301{i:03d}.SZ")

    # 2. 科创板 (688xxx, 689xxx) -> 上交所 .SS
    #for i in range(1, 150):
    #    tickers.append(f"688{i:03d}.SS")
    #tickers.append("689009.SS")  # 经典存托凭证特例

    # 3. 上海主板 (600xxx, 601xxx, 603xxx) -> 上交所 .SS
    #for i in range(1, 200):
    #    tickers.append(f"600{i:03d}.SS")
    #    tickers.append(f"601{i:03d}.SS")
    #    tickers.append(f"603{i:03d}.SS")

    # 4. 深圳主板 (000xxx, 001xxx) & 中小板 (002xxx) -> 深交所 .SZ
    #for i in range(1, 200):
    #    tickers.append(f"000{i:03d}.SZ")
    #    tickers.append(f"002{i:03d}.SZ")

    return list(set(tickers))  # 去重


def start_market_scan(max_workers=20, start_date="2025-01-01", end_date="2026-07-28"):
    """
    全市场高并发扫描器
    由于核心计算部分已经被转换为 NumPy，瓶颈纯粹在网络 I/O。
    采用多线程异步线程池（ThreadPoolExecutor）可以极大加快下载速度，且比多进程更省内存、防网络断流。
    """
    print("==================================================")
    print("🚀 正在启动【洗盘反包+均线回踩】工业级全市场扫描器...")
    print("==================================================")

    all_tickers = generate_all_a_share_tickers()
    total_count = len(all_tickers)
    print(
        f"📊 已自动构建全 A 股池：包含 {total_count} 只目标股票。并发下载线程数：{max_workers}"
    )

    hit_results = []

    # 建立多线程异步线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交异步任务，建立 Future -> Ticker 的映射
        future_to_ticker = {
            executor.submit(
                screen_single_stock, ticker, start_date, end_date
            ): ticker
            for ticker in all_tickers
        }

        # 使用 tqdm 渲染好看的终端动态进度条
        for future in tqdm(
            as_completed(future_to_ticker), total=total_count, desc="扫描全市场进度"
        ):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                if data is not None:
                    hit_results.append(data)
            except Exception as e:
                # 终极防御：任何未预料的底层错误（如SSL连接断开）都绝不扩散，保证大盘扫描完成
                print(f"\n⚠️ 股票 {ticker} 发生未捕获的严重运行时异常: {e}")

    # ==========================================
    # 第三部分：数据清洗与漂亮输出
    # ==========================================
    print("\n==================================================")
    print("🎯 全市场扫描完毕！开始导出最终策略池...")
    print("==================================================")

    if hit_results:
        result_df = pd.DataFrame(hit_results)
        # 策略优先：按照与5日线的偏离度从小到大排序，越贴近5日均线，买点越完美
        result_df = result_df.sort_values(by="5日线偏离度(%)", ascending=True)

        print(f"\n🔥 今日成功捕捉到 {len(result_df)} 只符合形态的短线黑马股：\n")
        # 展平输出，防止 DataFrame 列被省略号截断
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        print(result_df.to_string(index=False))
        return result_df
    else:
        print("\n👀 扫描完成。今日全市场未发现符合洗盘反包回踩形态的标的。")
        return None


# ==========================================
# 入口函数
# ==========================================
if __name__ == "__main__":
    # 执行全市场扫描（默认开启 20 个线程并发下载，可根据你的网速调整 max_workers）
    # 日期范围可根据回测或实盘需要动态修改
    final_black_horse_pool = start_market_scan(
        max_workers=20, start_date="2025-01-01", end_date="2026-07-28"
    )
