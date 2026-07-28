import logging
import random
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from tqdm import tqdm
import yfinance as yf

# 屏蔽海外访问时 yfinance 产生的繁杂底层调试日志
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")


# 过滤掉雅虎财经常见的 404 僵尸股报错，保持终端纯净
class YahooErrorFilter:

    def __init__(self, stderr):
        self.stderr = stderr

    def write(self, message):
        if "HTTP Error 404" not in message and "quoteSummary" not in message:
            self.stderr.write(message)

    def flush(self):
        self.stderr.flush()


sys.stderr = YahooErrorFilter(sys.stderr)


def is_limit_up(close, pre_close, date_str, ticker="", is_st_stock=False):
    """高精度 A 股涨停板判定函数（已彻底修复切片 Bug）"""
    if pre_close <= 1e-4:
        return False
    ticker_str = str(ticker).upper()
    parts = ticker_str.split(".")
    pure_code = parts[0] if len(parts) > 0 else ""

    # 动态适配 A 股主板、双创以及 ST 板块的涨停幅度
    if is_st_stock or "ST" in ticker_str:
        current_date = pd.to_datetime(date_str)
        rule_change_date = pd.to_datetime("2026-07-06")
        if pure_code.startswith("30") or pure_code.startswith("68"):
            pct = 0.20
        elif current_date >= rule_change_date:
            pct = 0.10
        else:
            pct = 0.05
    elif pure_code.startswith("30") or pure_code.startswith("68"):
        pct = 0.20
    else:
        pct = 0.10

    limit_price = round(pre_close * (1 + pct) + 1e-9, 2)
    return close >= limit_price


def find_pattern_instances_fast(df, ticker="", is_st_stock=False):
    """NumPy 高速形态寻找核心引擎（完美切断未来函数）"""
    n = len(df)
    pattern_indices = []
    if n < 10:
        return pattern_indices

    ticker_str = str(ticker).upper()
    parts = ticker_str.split(".")
    pure_code_str = parts[0] if len(parts) > 0 else ""

    dates = df["date"].to_numpy()
    opens = df["open"].to_numpy()
    highs = df["high"].to_numpy()
    closes = df["close"].to_numpy()
    volumes = df["volume"].to_numpy()
    vol_ma5 = df["vol_ma5"].to_numpy()

    i = 1
    while i < n:
        pre_close_i = closes[i - 1]
        if not is_limit_up(
            closes[i], pre_close_i, dates[i], ticker, is_st_stock
        ):
            i += 1
            continue

        limit_up_idx = i
        limit_close = closes[limit_up_idx]
        limit_vol = volumes[limit_up_idx]
        limit_vol_ma5 = vol_ma5[limit_up_idx]

        if np.isnan(limit_vol_ma5) or limit_vol_ma5 <= 1e-4:
            limit_vol_ma5 = limit_vol * 0.6

        pattern_found_in_this_wave = False
        next_i = i + 1

        for j in range(limit_up_idx + 1, min(limit_up_idx + 6, n)):
            is_yin = closes[j] < opens[j]  # 假阴线或真阴线洗盘
            is_trapped = closes[j] < highs[limit_up_idx]  # 存在追高套牢盘
            v_j = volumes[j]
            if np.isnan(v_j) or v_j <= 1e-4:
                continue

            # 严格对比启动日均量参照物
            is_low_vol = v_j < limit_vol and v_j < limit_vol_ma5

            if is_yin and is_trapped and is_low_vol:
                yin_idx = j
                yin_high = highs[yin_idx]

                for k in range(yin_idx + 1, min(limit_up_idx + 6, n)):
                    pre_close_k = closes[k - 1]
                    if pre_close_k <= 1e-4:
                        continue

                    # 区分板块的反包阳线幅判定
                    if pure_code_str.startswith(
                        "30"
                    ) or pure_code_str.startswith("68"):
                        is_big_yang = (
                            closes[k] - pre_close_k
                        ) / pre_close_k >= 0.08
                    else:
                        is_big_yang = (
                            closes[k] - pre_close_k
                        ) / pre_close_k >= 0.095

                    is_rebound_limit = is_limit_up(
                        closes[k], pre_close_k, dates[k], ticker, is_st_stock
                    )
                    is_engulfing = closes[k] > yin_high

                    if (is_big_yang or is_rebound_limit) and is_engulfing:
                        pattern_indices.append(k)
                        pattern_found_in_this_wave = True
                        next_i = k + 1
                        break
                if pattern_found_in_this_wave:
                    break
        i = next_i if pattern_found_in_this_wave else i + 1

    return pattern_indices


def screen_single_stock_yahoo(ticker, target_date_str):
    """
    【雅虎海外专属数据引擎】
    适合在日本等海外网络无阻碍下载 A 股历史 K 线矩阵
    """
    # 适当引入随机防微小封锁，海外 IP 访问雅虎速度极快
    time.sleep(random.uniform(0.002, 0.01))

    end_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    # 往前多拉一点时间（60天），确保历史复权数据健全
    start_dt = end_dt - timedelta(days=60)

    # 雅虎接收结束日期是开区间，为了包含 target_date_str 当天，需要将 end 设为明日前天
    yahoo_end_dt = end_dt + timedelta(days=1)

    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = yahoo_end_dt.strftime("%Y-%m-%d")

    try:
        # 在海外直接使用 yf.download 单股拉取，绝不发生断流和重置
        df = yf.download(
            ticker, start=start_date, end=end_date, progress=False, timeout=12
        )

        if df.empty or len(df) < 15:
            return None

        # 展平多资产可能带来的 MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df.columns = [str(col).lower() for col in df.columns]

        # 转换为标准时间格式
        df["date"] = pd.to_datetime(df["date"])

        # 雅虎返回的是标准的【正序】（历史在上，今天在下），不需要反转
        # 在正序矩阵上计算指标
        df["vol_ma5"] = df["volume"].rolling(5).mean().fillna(0)
        df["ma5"] = df["close"].rolling(5).mean().fillna(0)

        # 二次安全裁剪，确保数据精准停留在 target_date_str 基准日
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        df = df[df["date_str"] <= target_date_str].reset_index(drop=True)

        if df.empty or len(df) < 15:
            return None

        is_current_st = "ST" in str(ticker).upper()

        # 送入 NumPy 形态核心引擎计算
        trigger_points = find_pattern_instances_fast(
            df, ticker, is_st_stock=is_current_st
        )

        if len(trigger_points) >= 1:
            latest_idx = len(df) - 1
            most_recent_trigger_k = trigger_points[-1]
            days_since_trigger = latest_idx - most_recent_trigger_k

            # 时效性限制：反包大阳线发生在 1~4 天前，今天正在走缩量回踩
            if days_since_trigger < 1 or days_since_trigger > 4:
                return None

            current_close = df["close"].iloc[latest_idx].item()
            current_ma5 = df["ma5"].iloc[latest_idx].item()

            if current_ma5 <= 1e-4 or np.isnan(current_close):
                return None

            deviation = abs(current_close - current_ma5) / current_ma5

            # 偏离度控制在 5 日线上方 4.5% 范围内（空中加油形态）
            if deviation <= 0.045:
                return {
                    "代码": ticker,
                    "类型": "ST股" if is_current_st else "普通股",
                    "基准日收盘": round(current_close, 2),
                    "基准日MA5": round(current_ma5, 2),
                    "距反包日天数": int(days_since_trigger),
                    "5日线偏离度(%)": round(deviation * 100, 2),
                }
    except Exception:
        return None
    return None


def generate_all_a_share_tickers():
    """生成带 .SS 和 .SZ 后缀的雅虎格式 A 股股票池代码"""
    tickers = []
    for i in range(1, 1350):
        tickers.append(f"000{i:03d}.SZ" if i < 1000 else f"00{i:03d}.SZ")
    for i in range(2001, 3050):
        tickers.append(f"00{i:03d}.SZ")
    for i in range(1, 1000):
        tickers.append(f"300{i:03d}.SZ")
    for i in range(1001, 1600):
        tickers.append(f"301{i:03d}.SZ")
    for i in range(0, 1000):
        tickers.append(f"600{i:03d}.SS")
    for i in range(1000, 2000):
        tickers.append(f"601{i:03d}.SS")
    for i in range(3001, 4000):
        tickers.append(f"603{i:03d}.SS")
    for i in range(5001, 5500):
        tickers.append(f"605{i:03d}.SS")
    for i in range(1, 820):
        tickers.append(f"688{i:03d}.SS")
    tickers.append("689009.SS")
    return list(set(tickers))


def start_market_scan(max_workers=10, end_date=None, filter_st=False):
    """【海外定制】雅虎多线程全市场扫描主入口"""
    target_date_str = (
        end_date if end_date else datetime.now().strftime("%Y-%m-%d")
    )
    print("==================================================")
    print(f"🌍 启动海外专属雅虎引擎选股，基准日: {target_date_str}")
    print("==================================================")

    all_tickers = generate_all_a_share_tickers()
    total_count = len(all_tickers)
    hit_results = []

    # 在国外请求雅虎接口，max_workers 保持在 8~12 最佳，速度稳定且极其顺畅
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(
                screen_single_stock_yahoo, ticker, target_date_str
            ): ticker
            for ticker in all_tickers
        }

        # 此时进度条将展现出真实的、稳步推进的国外请求状态
        for future in tqdm(
            as_completed(future_to_ticker),
            total=total_count,
            desc="安全扫描全市场进度",
        ):
            try:
                data = future.result()
                if data is not None:
                    if filter_st and data["类型"] == "ST股":
                        continue
                    hit_results.append(data)
            except Exception:
                pass

    print(
        f"\n==================== 📊 基准日 [{target_date_str}] 筛选结果 ===================="
    )

    if hit_results:
        result_df = pd.DataFrame(hit_results)
        result_df = result_df.sort_values(by="5日线偏离度(%)", ascending=True)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        print(result_df.to_string(index=False))
        return result_df
    else:
        print(
            f"\n👀 扫描完成，在 [{target_date_str}] 当天全市场未发现同时符合【洗盘反包+回踩5日线】的标的。"
        )
        return None


if __name__ == "__main__":
    # max_workers=20 即可，新浪接口吞吐量极大，全市场约 2 分钟扫描完毕
    #start_market_scan(max_workers=20, end_date=None, filter_st=False)
    start_market_scan(max_workers=20, end_date="2026-07-24", filter_st=False)
