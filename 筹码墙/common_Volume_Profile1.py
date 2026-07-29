#common_Volume_Profile.py
#筹码分布墙

import pandas as pd
import numpy as np

def generate_ultimate_matrix_evolution_df_cn(stock_info, excel_data):
    """
    零人工干预·纯数据驱动型矩阵自演化筹码墙算法（DataFrame 完全整合中文版）
    """
    close_p = stock_info["收盘价"]
    atr_5d = stock_info["5日ATR"]
    
    # 1. 构建绝对不干预的原始原始事件矩阵流
    events = []
    
    # ★注入当前现价（赋予权重 6：全场最高敏感度标识）
    events.append({"price": close_p, "label": f"★当前收盘价[{close_p}]", "weight": 6})
    
    # ⚠️动态注入日内恐慌激活线（当前价 - 5日ATR）
    panic_line = round(close_p - atr_5d, 2)
    events.append({"price": panic_line, "label": f"⚠️日内恐慌激活线({panic_line})", "weight": 3})
    
    # 2. 从您生成的标准 DataFrame 中动态提取“资金战线”核心技术位
    # ※基于前述审计逻辑：AL（止损边界）和 AH（追多边界）属于外围动能警报线，故不注入现货筹码防线实体中
    for _, row in excel_data.iterrows():
        p_type = row["周期类型"]
        
        # 转换为标准数字浮点型，规避类型冲突风险
        poc_val = float(row["智能审定真POC"])
        nl_val = float(row["低吸支撑(NL)"])
        nh_val = float(row["高抛阻力(NH)"])
        
        # 压入真POC成本主峰
        events.append({"price": poc_val, "label": f"{p_type}真POC({poc_val})", "weight": 5})
        # 压入低吸支撑NL边界
        events.append({"price": nl_val, "label": f"{p_type}低吸支撑NL({nl_val})", "weight": 2})
        # 压入高抛阻力NH边界
        events.append({"price": nh_val, "label": f"{p_type}高抛阻力NH({nh_val})", "weight": 2})
        
    df_events = pd.DataFrame(events)
    
    # 3. 【矩阵自演化核心】完全由数据本身决定网格轴（无视固定步长，执行全样本绝对去重并降序排列）
    unique_prices = sorted(df_events["price"].unique(), reverse=True)
    
    print(f"================== 📊 {stock_info['股票名称']} ({stock_info['股票代码']}) 矩阵自演化断层筹码墙 ==================")
    print(f"当前收盘价: {close_p} | 5日ATR: {round(atr_5d, 4)} | 相对波动率: {round(atr_5d/close_p*100, 2)}%")
    print(f"🤖 算法状态：零人工干预。网格轴由 {len(unique_prices)} 个市场原生技术位矩阵自演化排列。\n")
    print(f"{'绝对价格(元)':<12} {'筹码能量条 (绝对数学重叠)':<30} 触发技术位/多周期共振审计标签说明")
    print("-" * 125)
    
    # 4. 全自适应 Tick 共振窗（取高价股万分之五波幅与低价股最小 Tick Size 1.5分钱的较大者）
    tick_window = max(close_p * 0.0005, 0.015)
    processed_prices = set()
    
    # 5. 遍历非均匀原生数据轴并进行视觉绘制
    for idx in range(len(unique_prices)):
        current_p = unique_prices[idx]
        
        # 避免近似网格的二次重复处理与展示
        if any(abs(current_p - p) <= tick_window for p in processed_prices):
            continue
            
        # 捕获当前 Tick 共振盾牌之内的所有事件流
        matched = df_events[abs(df_events["price"] - current_p) <= tick_window]
        
        if not matched.empty:
            processed_prices.add(current_p)
            
            # 汇总计算密集度加权权重并转化为能量方块
            total_weight = matched["weight"].sum()
            bar_str = "█" * total_weight
            
            # 合并同档发生发生技术位撞击的共振标签
            labels = matched["label"].unique()
            label_str = " | ".join(labels)
            
            # 高亮标出当前价所在的现货肉搏战区行
            if "★" in label_str:
                # 采用标准的终端红色高亮高亮行
                print(f"\033[1;31;45m{current_p:<14} {bar_str:<30} {label_str}\033[0m")
            else:
                print(f"{current_p:<14} {bar_str:<30} {label_str}")
                
            # 6. 【纯客观上行断层审计】测算与下一个独立骨架点之间的物理旷度距离
            if idx < len(unique_prices) - 1:
                next_p = None
                for n_p in unique_prices[idx + 1:]:
                    if abs(n_p - current_p) > tick_window:
                        next_p = n_p
                        break
                        
                if next_p:
                    gap = current_p - next_p
                    
                    # 转化为收益率断层跨度与现货标准相对波动率对比，彻底杜绝恐慌伪警报噪声
                    relative_gap_ratio = gap / current_p
                    base_vol_ratio = atr_5d / close_p
                    
                    if current_p > close_p and relative_gap_ratio > base_vol_ratio:
                        atr_spans = round(gap / atr_5d, 1)
                        print(f"\033[3;33m  [↓ 绝对断层空间: {round(gap, 2)} 元 | 跨度约 {atr_spans} 个ATR | 🚨 矩阵自演化提示：上方无任何历史筹码防线]\033[0m")

# =========================================================================
# 📊 【验证用模拟主程序区域】（直接注入鸣志电器真实数据）
# =========================================================================
if __name__ == "__main__":
    # 模拟您的 stock_info 变量数据
    stock_info = {
        "股票代码": "603728.SS",
        "股票名称": "鸣志电器",
        "收盘价": 47.01,
        "最高价": 48.15,
        "最低价": 46.8,
        "14日ATR": 3.27074184,
        "5日ATR": 2.525812254,
    }
    
    # 模拟您通过循环追加动态生成的二维数据列表
    headers = ["周期类型", "智能审定真POC", "中轴(CDP)", "止损边界(AL)", "低吸支撑(NL)", "高抛阻力(NH)", "追多边界(AH)"]
    table_rows = [
        ["1天短线历史", 47.02, 47.34, 45.92, 46.47, 47.89, 48.76],
        ["3天短线历史", 46.81, 46.88, 41.32, 44.16, 49.72, 52.44],
        ["5天短线历史", 47.18, 47.12, 39.86, 43.44, 50.70, 54.38],
        ["20日线(月度)", 49.77, 49.05, 41.35, 44.18, 51.88, 56.74],
        ["60日线(季度)", 65.62, 58.90, 46.50, 46.75, 59.16, 71.30],
        ["120日线(半年)", 62.42, 57.05, 40.32, 43.67, 60.39, 73.77],
        ["250日线(年度)", 61.58, 56.05, 39.88, 43.44, 59.62, 72.22],
    ]
    
    # 模拟生成您的最终备用 DataFrame
    excel_data = pd.DataFrame(table_rows, columns=headers)
    
    # 执行无缝整合后的终极自演化筹码墙程序
    generate_ultimate_matrix_evolution_df_cn(stock_info, excel_data)
