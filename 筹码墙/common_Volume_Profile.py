# common_Volume_Profile.py
import pandas as pd
import numpy as np

def generate_ultimate_matrix_data_cn(stock_info, excel_data):
    """
    零人工干预·纯数据驱动型矩阵自演化筹码墙算法（彻底放弃凑数据、恢复100%纯净数学网格版）
    """
    close_p = float(stock_info["收盘价"])
    atr_5d = float(stock_info["5日ATR"])
    
    # 1. 构建绝对不干预的原始事件矩阵流
    events = []
    events.append({"price": close_p, "label": str(f"★当前收盘价[{close_p}]"), "weight": 6})
    
    panic_line = round(close_p - atr_5d, 2)
    events.append({"price": float(panic_line), "label": str(f"⚠️日内恐慌激活线({panic_line})"), "weight": 3})
    
    for _, row in excel_data.iterrows():
        p_type = str(row["周期类型"])
        poc_val = float(row["智能审定真POC"])
        nl_val = float(row["低吸支撑(NL)"])
        nh_val = float(row["高抛阻力(NH)"])
        
        events.append({"price": poc_val, "label": f"{p_type}真POC({poc_val})", "weight": 5})
        events.append({"price": nl_val, "label": f"{p_type}低吸支撑NL({nl_val})", "weight": 2})
        events.append({"price": nh_val, "label": f"{p_type}高抛阻力NH({nh_val})", "weight": 2})
        
    df_events = pd.DataFrame(events)
    
    # 2. 矩阵自演化网格生成（数据原生态，没有任何人为干预的放大阀门）
    unique_prices = sorted(df_events["price"].unique(), reverse=True)
    
    # 💡【回归纯净客观】拒绝为了凑出16格而人为放大窗口！严格保持万分之五与A股1.5分钱Tick的物理防线
    tick_window = max(close_p * 0.0005, 0.015)
    processed_prices = set()
    
    wall_rows = []
    
    for idx in range(len(unique_prices)):
        current_p = unique_prices[idx]
        
        if any(abs(current_p - p) <= tick_window for p in processed_prices):
            continue
            
        matched = df_events[abs(df_events["price"] - current_p) <= tick_window]
        
        if not matched.empty:
            processed_prices.add(current_p)
            total_weight = int(matched["weight"].sum())
            bar_str = str("█" * total_weight)
            
            labels = matched["label"].unique()
            label_str = str(" | ".join(labels))
            
            # 将最真实、绝无水分的网格价格和能量条压入队列
            wall_rows.append([float(round(current_p, 2)), bar_str, label_str])
                
            # 3. 纯客观上行断层审计
            if idx < len(unique_prices) - 1:
                next_p = None
                for n_p in unique_prices[idx + 1:]:
                    if abs(n_p - current_p) > tick_window:
                        next_p = n_p
                        break
                        
                if next_p:
                    gap = current_p - next_p
                    relative_gap_ratio = gap / current_p
                    base_vol_ratio = atr_5d / close_p
                    
                    if current_p > close_p and relative_gap_ratio > base_vol_ratio:
                        atr_spans = round(gap / atr_5d, 1)
                        alert_label = str("🚨 矩阵自演化提示：上方无任何历史筹码防线")
                        alert_bar = str(f"  [↓ 绝对断层空间: {round(gap, 2)} 元 | 跨度约 {atr_spans} 个ATR]")
                        wall_rows.append([0.0, alert_bar, alert_label])

    wall_headers = ["绝对价格(元)", "筹码能量条 (绝对数学重叠)", "触发技术位/多周期共振审计标签说明"]
    return pd.DataFrame(wall_rows, columns=wall_headers)
