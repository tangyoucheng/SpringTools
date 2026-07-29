#common_Volume_Profile.py
#筹码分布墙
import pandas as pd
import numpy as np

# 1. 完整注入 2026-07-28 鸣志电器 原始变量数据
stock_info = {
    "股票代码": "603728.SS",
    "股票名称": "鸣志电器",
    "收盘价": 47.01,
    "最高价": 48.15,
    "最低价": 46.8,
    "14日ATR": 3.27074184,
    "5日ATR": 2.525812254,
}

raw_data = {
    "周期类型": ["1天短线历史", "3天短线历史", "5天短线历史", "20日线(月度)", "60日线(季度)", "120日线(半年)", "250日线(年度)"],
    "智能审定真POC": [47.02, 46.81, 47.18, 49.77, 65.62, 62.42, 61.58],
    "中轴(CDP)": [47.34, 46.88, 47.12, 49.05, 58.9, 57.05, 56.05],
    "低吸支撑(NL)": [46.47, 44.16, 43.44, 44.18, 46.75, 43.67, 43.44],
    "高抛阻力(NH)": [47.89, 49.72, 50.7, 51.88, 59.16, 60.39, 59.62],
}

def generate_ultimate_matrix_evolution(stock_info, raw_data):
    df_raw = pd.DataFrame(raw_data)
    close_p = stock_info["收盘价"]
    atr_5d = stock_info["5日ATR"]
    
    # 提取绝对原生事件流
    events = []
    events.append({"price": close_p, "label": f"★当前收盘价[{close_p}]", "weight": 6})
    
    panic_line = round(close_p - atr_5d, 2)
    events.append({"price": panic_line, "label": f"⚠️日内恐慌激活线({panic_line})", "weight": 3})
    
    for _, row in df_raw.iterrows():
        p_type = row["周期类型"]
        events.append({"price": row["智能审定真POC"], "label": f"{p_type}真POC({row['智能审定真POC']})", "weight": 5})
        events.append({"price": row["高抛阻力(NH)"], "label": f"{p_type}高抛阻力NH({row['高抛阻力(NH)']})", "weight": 2})
        events.append({"price": row["低吸支撑(NL)"], "label": f"{p_type}低吸支撑NL({row['低吸支撑(NL)']})", "weight": 2})
        
    df_events = pd.DataFrame(events)
    all_prices = sorted(df_events["price"].unique(), reverse=True)
    
    print(f"================== 📊 {stock_info['股票名称']} ({stock_info['股票代码']}) 终极自演化断层筹码墙 ==================")
    print(f"当前收盘价: {close_p} | 5日ATR: {round(atr_5d, 4)} | 相对波动率: {round(atr_5d/close_p*100, 2)}%")
    print(f"🤖 算法状态：零人工干预。高低价全自适应Tick报价盾牌已对齐...\n")
    print(f"{'绝对价格(元)':<12} {'筹码能量条 (绝对数学重叠)':<30} 触发技术位说明")
    print("-" * 115)
    
    # 全自适应 Tick 共振窗（此中高价标的自主演化对齐为 0.0235元）
    tick_window = max(close_p * 0.0005, 0.015)
    processed_prices = set()
    
    for idx in range(len(all_prices)):
        current_p = all_prices[idx]
        
        if any(abs(current_p - p) <= tick_window for p in processed_prices):
            continue
            
        matched = df_events[abs(df_events["price"] - current_p) <= tick_window]
        
        if not matched.empty:
            processed_prices.add(current_p)
            total_weight = matched["weight"].sum()
            bar_str = "█" * total_weight
            
            labels = matched["label"].unique()
            label_str = " | ".join(labels)
            
            print(f"{current_p:<14} {bar_str:<30} {label_str}")
            
            # 【纯客观上行断层审计】测算与下一个独立骨架点之间的物理旷度
            if idx < len(all_prices) - 1:
                next_p = None
                for n_p in all_prices[idx+1:]:
                    if abs(n_p - current_p) > tick_window:
                        next_p = n_p
                        break
                
                if next_p:
                    gap = current_p - next_p
                    # 上行阻力区断层空间判定：转为收益率断层跨度与ATR波动率比例对比，防范恐慌误报
                    relative_gap_ratio = gap / current_p
                    base_vol_ratio = atr_5d / close_p
                    
                    if current_p > close_p and relative_gap_ratio > base_vol_ratio:
                        atr_spans = round(gap / atr_5d, 1)
                        print(f"  [↓ 绝对断层空间: {round(gap, 2)} 元 | 跨度约 {atr_spans} 个ATR | 🚨 矩阵自演化提示：上方无任何历史筹码防线]")

# 执行全自适应终极算法
generate_ultimate_matrix_evolution(stock_info, raw_data)
