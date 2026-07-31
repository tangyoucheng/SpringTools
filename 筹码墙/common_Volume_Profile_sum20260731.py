import os
import sys
import re
import pandas as pd
from pathlib import Path


# 1. 获取当前目录和父目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 2. 先插入父目录（此时父目录最优先）
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 3. 再插入当前目录（当前目录会把父目录挤到后面，从而变成“最优先”）
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# 💡【无缝对齐】导入第二个独立脚本中的 Excel 导出函数
from export_profit_margin_wave1_excel import export_profit_pool_to_excel
from common_stock import detect_stock_board_and_suffix

def scan_highest_near_rebound_profit_v15(end_date):
    """
    【V15化繁为简决策版】废除一切复杂的套利速度得分公式，回归纯粹的数据直展现。
    强索Excel原始物理列，输出使用的5日ATR，完全按短线第一浪利润期望降序排列。
    """
    target_dir = Path(end_date)
    if not target_dir.exists():
        print(f"🚨 错误：未找到指定日期 [{end_date}] 的文件夹。")
        return

    excel_files = list(target_dir.glob("*.xlsm")) + list(target_dir.glob("*.xlsx"))
    if not excel_files:
        print(f"🚨 警告：在 [{end_date}] 文件夹内未检测到任何有效 Excel 文件。")
        return

    audit_results = []
    vacuum_pattern = r"绝对断层空间:\s*([\d\.]+)\s*元.*跨度约\s*([\d\.]+)\s*个ATR"

    print(f"🤖 正在启动 [V15直展现版·短线雷达]，正在全网清洗 {len(excel_files)} 只个股数据...\n")

    for file_path in excel_files:
        try:
            xl = pd.ExcelFile(file_path)
            active_sheet = xl.sheet_names[0]
            
            # 严格读取基础信息（对齐33行，第1列代码、第2列名称、第3列价格、第7列5日ATR）
            df_stock = pd.read_excel(file_path, sheet_name=active_sheet, skiprows=31, nrows=2, header=None)
            
            stock_code = str(df_stock.iloc[1, 1]).strip()   # B33
            stock_name = str(df_stock.iloc[1, 2]).strip()   # C33
            close_price = float(df_stock.iloc[1, 3])        # D33
            atr_5d = float(df_stock.iloc[1, 7])             # H33            

            if "NaN" in stock_code or stock_code == "" or "股票代码" in stock_code:
                continue

            try:
                target_stock, board_name = detect_stock_board_and_suffix(stock_code)
            except:
                board_name = "沪市主板" if stock_code.startswith(('60', '68')) else "深市主板"
                
            if board_name not in ("沪市主板", "深市主板"):
                continue

            # 读取44行下方的自演化筹码墙
            df_wall = pd.read_excel(file_path, sheet_name=active_sheet, skiprows=44, header=None)
            
            # 自下而上顺序爬坡分析（将筹码墙翻转）
            df_wall_scan = df_wall.iloc[::-1].reset_index(drop=True)
            is_above_current = False
            
            short_term_target_price = 0.0
            short_term_target_label = ""
            wall_thickness = 0
            
            near_vacuum_yuan = 0.0
            near_vacuum_atrs = 0.0
            near_friction_bars = 0
            
            for idx, row in df_wall_scan.iterrows():
                if len(row) < 4:
                    continue
                p_origin = str(row[1]).strip()
                bar_str = str(row[2]).strip()
                p_label = str(row[3]).strip()
                
                # 短线状态机原点精准咬合
                if "★当前收盘价" in p_label or "★当前收盘价" in bar_str:
                    is_above_current = True
                    continue
                    
                if not is_above_current:
                    continue
                
                # 生吞断层文本特征，如实记录沿途路况
                combined_row_text = p_label + " | " + bar_str + " | " + p_origin
                if "绝对断层空间" in combined_row_text:
                    match = re.search(vacuum_pattern, combined_row_text)
                    if match:
                        near_vacuum_yuan += float(match.group(1))
                        near_vacuum_atrs += float(match.group(2))
                    continue
                
                # 正常价格网格审计
                try:
                    p_real = float(p_origin)
                except ValueError:
                    continue
                    
                if p_real > close_price:
                    # 严格判定：厚度 >= 4格，锁定第一浪的实质短线物理边界
                    if "█" in bar_str and len(bar_str) >= 4:
                        short_term_target_price = p_real
                        short_term_target_label = p_label if pd.notna(row[3]) and str(row[3]) != "nan" else bar_str
                        wall_thickness = len(bar_str)
                        break # 触墙立刻截断，死死锁住短线第一浪空间
                    else:
                        # 严格在独立的第二列（能量条列）计数零碎阻力
                        near_friction_bars += bar_str.count("█")

            # 5. 纯客观组装最直接的数据指标
            if short_term_target_price > 0:
                short_profit_pct = ((short_term_target_price - close_price) / close_price) * 100
                atr_distance = (short_term_target_price - close_price) / atr_5d
                
                # 基于数据的客观结构状态划分
                if short_profit_pct <= 2.5:
                    status = "⚠️ 空间狭窄（空间受限）"
                elif near_vacuum_atrs >= 1.5 and near_friction_bars <= 3:
                    status = "🚀 高能真空（黄金连板通道）"
                elif near_friction_bars > 8:
                    status = "⏳ 泥潭粘滞（震荡爬坡慢股）"
                else:
                    status = "💎 标准反弹结构"

                audit_results.append({
                    "股票代码": stock_code,
                    "股票名称": stock_name,
                    "当前收盘价": close_price,
                    "5日ATR": round(atr_5d, 4), # 🎯 【输出使用的ATR】
                    "首道实质拦截墙": short_term_target_price,
                    "墙厚": f"{wall_thickness}格",
                    "★短线第一浪利润期望": round(short_profit_pct, 2), # 🎯 【核心排序字段】
                    "ATR跨度(理论天数)": round(atr_distance, 2),       # 🎯 【通过ATR跨度简单判断时间】
                    "沿途碎石": f"{near_friction_bars}格",
                    "探明真空(元)": round(near_vacuum_yuan, 2),
                    "客观重力状态": status
                })
        except Exception:
            continue

    # 6. 生成汇总大表
    df_report = pd.DataFrame(audit_results)
    if df_report.empty:
        print("🚨 纯净审计结束：未检测到任何有效数据。")
        return
        
    # ⭐️ 核心对齐您的最核心需求：完全按照“★短线第一浪利润期望”进行降序排列！谁空间大谁在最前面！
    df_report = df_report.sort_values(by="★短线第一浪利润期望", ascending=False).reset_index(drop=True)

    # 7. 控制台客观高亮输出
    print(f"\n@@@@@@@@@@@@@@@@@@ 🏆 {end_date} 筹码矩阵·第一浪空间利润降序选股龙虎榜 @@@@@@@@@@@@@@@@@@")
    print("-" * 195)
    print(f"{'排名':<4} {'代码':<12} {'股票名称':<10} {'当前价':<8} {'5日ATR':<10} {'首道实质拦截墙':<14} {'墙厚':<6} {'★短线利润期望 ⬇️' :<18} {'ATR跨度(天数)':<16} {'沿途碎石':<10} {'客观重力状态'}")
    print("-" * 195)
    
    for idx, row in df_report.iterrows():
        detail = f"{idx+1:<6} {row['股票代码']:<13} {row['股票名称']:<10} {row['当前收盘价']:<11} {row['5日ATR']:<11} {row['首道实质拦截墙']:<16} {row['墙厚']:<8} {row['★短线第一浪利润期望']}%{'' :<14} {row['ATR跨度(理论天数)']:<16} {row['沿途碎石']:<12} {row['客观重力状态']}"
        if idx < 3:
            print(f"\033[1;31;45m{detail}  🔥\033[0m")
        else:
            print(detail)
    print("-" * 195)
    
    # 自动将干净的总表数据落地存盘
    output_excel = target_dir / f"筹码墙短线空间降序汇总表_{end_date}.xlsx"
    df_report.to_excel(output_excel, index=False)
    print(f"🎉 物理网格直展现清洗完毕！报表已无水分生成至：\n[ {output_excel} ]\n")
    
if __name__ == "__main__":
    #scan_highest_near_rebound_profit_v15("2026-07-28")
    scan_highest_near_rebound_profit_v15("2026-07-29")
