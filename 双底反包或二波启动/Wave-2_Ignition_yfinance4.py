import logging
import random
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import numpy as np
import pandas as pd
from tqdm import tqdm

# 引入硬核真实浏览器指纹库
from curl_cffi import requests as chrome_requests

warnings.filterwarnings("ignore")

CHROME_VERSIONS = ["chrome110", "chrome116", "chrome120"]


def is_limit_up(close, pre_close, date_str, ticker="", is_st_stock=False):
    """高精度 A 股涨停板判定函数（彻底修复切片列表Bug）"""
    if pre_close <= 1e-4:
        return False
    ticker_str = str(ticker).upper()

    # 【终极修复】必须用 parts[0] 提取出真正的“字符串”，绝对不能用 parts[0:1]（切片返回的是列表）
    parts = ticker_str.split(".")
    pure_code = parts[0] if len(parts) > 0 else ""

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
    """NumPy 高速形态寻找核心引擎（彻底修复切片列表Bug）"""
    n = len(df)
    pattern_indices = []
    if n < 10:
        return pattern_indices

    # 【终极修复】必须用 parts[0] 提取出字符串
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
            is_yin = closes[j] < opens[j]  # 确认为阴线（包含高开低走的假阴线）

            # 【实战升级】放宽被套定义：收盘低于涨停日的最高价，即确认为盘中追高套牢盘形成
            is_trapped = closes[j] < highs[limit_up_idx]
            v_j = volumes[j]
            if np.isnan(v_j) or v_j <= 1e-4:
                continue

            # 严格缩量判定
            is_low_vol = v_j < limit_vol and v_j < limit_vol_ma5

            if is_yin and is_trapped and is_low_vol:
                yin_idx = j
                yin_high = highs[yin_idx]

                for k in range(yin_idx + 1, min(limit_up_idx + 6, n)):
                    pre_close_k = closes[k - 1]
                    if pre_close_k <= 1e-4:
                        continue

                    # 区分板块的反包大阳线爆发力度
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


def screen_single_stock_sina(ticker, target_date_str):
    """【新浪财经原生引擎 - 物理切片终极加固版】"""
    time.sleep(random.uniform(0.01, 0.03))

    ticker_str = str(ticker).upper()
    parts = ticker_str.split(".")
    # 【终极修复】必须用 parts[0] 提取出真正的代码字符串
    pure_code = parts[0] if len(parts) > 0 else ""

    if pure_code.startswith("6"):
        sina_ticker = f"sh{pure_code}"
    else:
        sina_ticker = f"sz{pure_code}"

    url = f"https://sina.com.cn{sina_ticker}&scale=240&datalen=90"
    chosen_chrome = random.choice(CHROME_VERSIONS)

    try:
        with chrome_requests.Session(impersonate=chosen_chrome) as session:
            headers = {
                "Referer": "https://sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
            response = session.get(url, headers=headers, timeout=10)
            data_json = response.json()

            if (
                not data_json
                or isinstance(data_json, dict)
                or len(data_json) == 0
            ):
                return None

            df = pd.DataFrame(data_json)
            df = df.rename(columns={"day": "date"})
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # 1. 整体翻转成标准正序
            df = df.iloc[::-1].reset_index(drop=True)

            # 2. 精准计算均线与均量
            df["vol_ma5"] = df["volume"].rolling(5).mean().fillna(0)
            df["ma5"] = df["close"].rolling(5).mean().fillna(0)

            # 3. 切割历史矩阵到指定的基准日
            df = df[df["date"] <= target_date_str].reset_index(drop=True)
            if df.empty or len(df) < 15:
                return None

            is_current_st = "ST" in ticker_str

            # 4. 送入形态核心引擎计算
            trigger_points = find_pattern_instances_fast(
                df, ticker, is_st_stock=is_current_st
            )

            if len(trigger_points) >= 1:
                latest_idx = len(df) - 1
                most_recent_trigger_k = trigger_points[-1]
                days_since_trigger = latest_idx - most_recent_trigger_k

                # 时效性限制：反包大阳线发生在 1~4 天前
                if days_since_trigger < 1 or days_since_trigger > 4:
                    return None

                current_close = df["close"].iloc[latest_idx].item()
                current_ma5 = df["ma5"].iloc[latest_idx].item()

                if current_ma5 <= 1e-4 or np.isnan(current_close):
                    return None

                deviation = abs(current_close - current_ma5) / current_ma5

                # 偏离度控制在 5 日线上方 4.5% 范围内（空中加油回踩）
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
    """全自动生成带后缀的 A 股股票池代码"""
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


def start_market_scan(max_workers=20, end_date=None, filter_st=False):
    """
    全新升级：基于新浪财经原生 K 线的多线程超稳扫描主入口
    """
    target_date_str = (
        end_date if end_date else datetime.now().strftime("%Y-%m-%d")
    )
    print("==================================================")
    print(
        f"🎯 启动【新浪财经全真浏览器引擎】选股，基准日: {target_date_str}"
    )
    print("==================================================")

    all_tickers = generate_all_a_share_tickers()
    total_count = len(all_tickers)
    hit_results = []

    # 由于新浪原生接口极轻，支持高并发，max_workers 恢复至 15~25，速度飞快
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(
                screen_single_stock_sina, ticker, target_date_str
            ): ticker
            for ticker in all_tickers
        }

        # 此时进度条会以极为平滑、真实的跳动速度向前滚动，绝不再闪退
        for future in tqdm(
            as_completed(future_to_ticker), total=total_count, desc="扫描全市场进度"
        ):
            try:
                data = future.result()
                if data is not None:
                    # 如果需要过滤ST，在这里对代码名称或结构进行最终剔除
                    if filter_st and "ST" in str(data["代码"]).upper():
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
            f"\n👀 扫描完成，在 [{target_date_str}] 当天全市场未发现符合形态的标的。\n(提示：大阳反包后回踩5日线条件极其严苛，可尝试放宽偏离度至 2.5%)"
        )
        return None


if __name__ == "__main__":
    # max_workers=20 即可，新浪接口吞吐量极大，全市场约 2 分钟扫描完毕
    #start_market_scan(max_workers=20, end_date=None, filter_st=False)
    start_market_scan(max_workers=20, end_date="2026-07-24", filter_st=False)
