# common_Volume_Profile.py
import pandas as pd
import numpy as np

def generate_ultimate_matrix_data_cn(stock_info, excel_data):
    """
    零人工干预·纯数据驱动型矩阵自演化筹码墙算法（终极净化无隐患完全体版）
    """
    # 在最前置源头强制统一强类型，封死底层浮点数精度漂移
    close_p = float(stock_info["收盘价"])
    atr_5d = float(stock_info["5日ATR"])
    
    # 1. 构建绝对不干预的原始事件矩阵流
    events = []
    events.append({"price": close_p, "label": str(f"★当前收盘价[{close_p}]"), "weight": 6})
    
    panic_line = float(round(close_p - atr_5d, 2))
    events.append({"price": panic_line, "label": str(f"⚠️日内恐慌激活线({panic_line})"), "weight": 3})
    
    for _, row in excel_data.iterrows():
        p_type = str(row["周期类型"])
        poc_val = float(row["智能审定真POC"])
        nl_val = float(row["低吸支撑(NL)"])
        nh_val = float(row["高抛阻力(NH)"])
        
        events.append({"price": poc_val, "label": f"{p_type}真POC({poc_val})", "weight": 5})
        events.append({"price": nl_val, "label": f"{p_type}低吸支撑NL({nl_val})", "weight": 2})
        events.append({"price": nh_val, "label": f"{p_type}高抛阻力NH({nh_val})", "weight": 2})
        
    df_events = pd.DataFrame(events)
    
    # 2. 矩阵自演化非均匀网格轴生成（绝对去重并降序排列）
    unique_prices = sorted(df_events["price"].unique(), reverse=True)
    
    # 严格保持标准对齐窗：高低价全自适应 TickSize 心理窗（1.5分钱保底）
    tick_window = max(close_p * 0.0005, 0.015)
    processed_prices = set()
    
    wall_rows = []
    
    for idx in range(len(unique_prices)):
        current_p = unique_prices[idx]
        
        # 避免近似网格的二次重复处理
        if any(abs(current_p - p) <= tick_window for p in processed_prices):
            continue
            
        matched = df_events[abs(df_events["price"] - current_p) <= tick_window]
        
        if not matched.empty:
            processed_prices.add(current_p)
            total_weight = int(matched["weight"].sum())
            bar_str = str("█" * total_weight)
            
            labels = matched["label"].unique()
            label_str = str(" | ".join(labels))
            
            # 将无水分的原生态网格节点压入队列
            wall_rows.append([float(round(current_p, 2)), bar_str, label_str])
                
            # 3. 【彻底修补：绝对相邻物理断层审计】
            # 拒绝任何越级和主观跳过，只测算排序网格轴中绝对相邻的下一格
            if idx < len(unique_prices) - 1:
                next_p = unique_prices[idx + 1]
                gap = current_p - next_p
                
                # 转化为无量纲收益率断层比例与现货标准相对波动率对比
                relative_gap_ratio = gap / current_p
                base_vol_ratio = atr_5d / close_p
                
                # 💡【修补重力场盲区】只要当前节点或下一个相邻节点处于现价上方，即证明断层横跨反弹阻力真空区
                if (current_p > close_p or next_p > close_p) and relative_gap_ratio > base_vol_ratio:
                    atr_spans = round(gap / atr_5d, 1)
                    alert_label = str("🚨 矩阵自演化提示：上方无任何历史筹码防线")
                    alert_bar = str(f"  [↓ 绝对断层空间: {round(gap, 2)} 元 | 跨度约 {atr_spans} 个ATR]")
                    # 强类型Numeric隔离，写入0.0供Excel模块拦截，彻底根除公式损坏报错
                    wall_rows.append([0.0, alert_bar, alert_label])

    wall_headers = ["绝对价格(元)", "筹码能量条 (绝对数学重叠)", "触发技术位/多周期共振审计标签说明"]
    return pd.DataFrame(wall_rows, columns=wall_headers)
