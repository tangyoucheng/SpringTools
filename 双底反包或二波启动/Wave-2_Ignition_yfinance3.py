import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import logging
import numpy as np
import pandas as pd
from tqdm import tqdm
import yfinance as yf

logging.getLogger("yfinance").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")


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
    if pre_close <= 1e-4:
        return False
    ticker_str = str(ticker).upper()
    pure_code = ticker_str.split(".")[0]

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
    df_clone = df.copy()
    df_clone.columns = [str(col).lower() for col in df_clone.columns]
    df_clone["volume"] = df_clone["volume"].fillna(0)
    df_clone["vol_ma5"] = df_clone["volume"].rolling(5).mean().fillna(0)

    dates = df_clone["date"].dt.strftime("%Y-%m-%d").to_numpy()
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
            is_yin = closes[j] < opens[j]
            is_trapped = closes[j] < limit_close
            v_j = volumes[j]
            if np.isnan(v_j) or v_j <= 1e-4:
                continue

            is_low_vol = v_j < limit_vol and v_j < limit_vol_ma5

            if is_yin and is_trapped and is_low_vol:
                yin_idx = j
                yin_high = highs[yin_idx]

                for k in range(yin_idx + 1, min(limit_up_idx + 6, n)):
                    pre_close_k = closes[k - 1]
                    if pre_close_k <= 1e-4:
                        continue
                    is_big_yang = (closes[k] - pre_close_k) / pre_close_k >= 0.05
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


def screen_single_stock(ticker, end_date_str=None, filter_st=False):
    try:
        if end_date_str is None:
            end_dt = datetime.now()
        else:
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")

        start_dt = end_dt - timedelta(days=45)
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = end_dt.strftime("%Y-%m-%d")

        yt = yf.Ticker(ticker)
        is_current_st = False

        try:
            stock_info = yt.info
            short_name = stock_info.get("shortName", "").upper()
            long_name = stock_info.get("longName", "").upper()
            if "ST" in short_name or "ST" in long_name:
                is_current_st = True
                if filter_st:
                    return None
        except Exception:
            pass

        df = yt.history(start=start_date, end=end_date, progress=False)

        if df.empty or len(df) < 15:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        df.columns = [str(col).lower() for col in df.columns]
        df["date"] = pd.to_datetime(df["date"])

        trigger_points = find_pattern_instances_fast(
            df, ticker, is_st_stock=is_current_st
        )

        if len(trigger_points) >= 1:
            latest_idx = len(df) - 1
            most_recent_trigger_k = trigger_points[-1]
            days_since_trigger = latest_idx - most_recent_trigger_k

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
                    "名称类型": "ST股" if is_current_st else "普通股",
                    "基准日收盘": round(current_close, 2),
                    "基准日MA5": round(current_ma5, 2),
                    "距反包日天数": days_since_trigger,
                    "5日线偏离度(%)": round(deviation * 100, 2),
                }
    except Exception:
        return None
    return None


def generate_all_a_share_tickers():
    tickers = []

    #for i in range(1, 1350):
    #    tickers.append(f"000{i:03d}.SZ" if i < 1000 else f"00{i:03d}.SZ")
    #for i in range(2001, 3050):
    #    tickers.append(f"00{i:03d}.SZ")
    #for i in range(1, 1000):
    #    tickers.append(f"300{i:03d}.SZ")
    #for i in range(1001, 1600):
    #    tickers.append(f"301{i:03d}.SZ")

    #for i in range(0, 1000):
    #    tickers.append(f"600{i:03d}.SS")
    #for i in range(1000, 2000):
    #    tickers.append(f"601{i:03d}.SS")
    #for i in range(3001, 4000):
    #    tickers.append(f"603{i:03d}.SS")
    #for i in range(5001, 5500):
    #    tickers.append(f"605{i:03d}.SS")
    #for i in range(1, 820):
    #    tickers.append(f"688{i:03d}.SS")
    #tickers.append("689009.SS")

    return list(set(tickers))


def start_market_scan(max_workers=30, end_date=None, filter_st=False):
    target_date_str = (
        end_date if end_date else datetime.now().strftime("%Y-%m-%d")
    )
    print("==================================================")
    print(f"🎯 启动定长回溯选股，指定结束基准日: {target_date_str}")
    print("==================================================")

    all_tickers = generate_all_a_share_tickers()
    total_count = len(all_tickers)
    hit_results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(
                screen_single_stock, ticker, target_date_str, filter_st
            ): ticker
            for ticker in all_tickers
        }

        for future in tqdm(
            as_completed(future_to_ticker), total=total_count, desc="扫描全市场进度"
        ):
            try:
                data = future.result()
                if data is not None:
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
        print(f"\n👀 扫描完成，在 [{target_date_str}] 当天未发现符合形态的标的。")
        return None


if __name__ == "__main__":
    start_market_scan(max_workers=30, end_date=None, filter_st=False)
    #start_market_scan(max_workers=30, end_date="2025-10-10", filter_st=False)
