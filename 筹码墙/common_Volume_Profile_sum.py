# audit_near_rebound_radar.py
import os
import sys
import pandas as pd
from pathlib import Path

# 使用免安装版本时，为了读取CDP_config.py，添加的设定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 💡【无缝对齐】导入第二个独立脚本中的 Excel 导出函数
from export_profit_margin_wave1_excel import export_profit_pool_to_excel

def scan_highest_near_rebound_profit(end_date):
    """
    自动遍历独立Excel文件，精准测算当前最新价到头顶第一堵实质性重力墙（厚度>=4格）之间的最大套利利润期望。
    """
    target_dir = Path(end_date)
    if not target_dir.exists():
        print(f"🚨 错误：未找到指定日期 [{end_date}] 的文件夹，请先确保数据已导出完成。")
        return

    excel_files = list(target_dir.glob("*.xlsm"))
    if not excel_files:
        print(f"🚨 警告：在 [{end_date}] 文件夹内未检测到任何导出的 .xlsm 文件。")
        return

    audit_results = []

    print(f"🤖 正在启动 [近端第一浪反弹雷达]，正在对全网 {len(excel_files)} 只错砸个股进行贴身重力墙审计...\n")

    for file_path in excel_files:
        try:
            # 1. 严格相对位移读取：由于您用最新完备版 openpyxl 导出，结构完全对齐
            # 股票基础数据在第33行（对应 skiprows=31, nrows=2）
            df_stock = pd.read_excel(file_path, sheet_name="Sheet1", skiprows=31, nrows=2, header=None)
            stock_code = str(df_stock.iloc[1, 1])  # B33 股票代码
            stock_name = str(df_stock.iloc[1, 2])  # C33 股票名称
            close_price = float(df_stock.iloc[1, 3]) # D33 最新收盘价
            atr_5d = float(df_stock.iloc[1, 7])      # H33 5日ATR

            # 读取下方的动态自演化筹码墙区域
            df_wall = pd.read_excel(
                file_path, 
                sheet_name="Sheet1", 
                skiprows=44,       # 顺延一行，精准跳过筹码墙中文标题，咬合指标行
                usecols=[1, 2, 3], # 💡【锁死列空间】只精准提取B、C、D三列，根除崩溃隐患
                header=None
            )
            df_wall.columns = ["绝对价格(元)", "筹码能量条", "审计标签说明"]
            
            # 剔除断层警报占位行，只留真实的筹码价格节点
            df_wall = df_wall.dropna(subset=["绝对价格(元)"])
            df_wall = df_wall[df_wall["绝对价格(元)"] != "-"]
            df_wall["绝对价格(元)"] = df_wall["绝对价格(元)"].astype(float)

            first_gravity_price = 0.0
            first_gravity_labels = ""
            wall_thickness = 0
            
            # 筹码墙升序排列，自下而上寻找阻碍物
            df_wall_asc = df_wall.sort_values(by="绝对价格(元)", ascending=True)
            
            for _, row in df_wall_asc.iterrows():
                p_node = float(row["绝对价格(元)"])
                bar_str = str(row["筹码能量条"])
                label_str = str(row["审计标签说明"])
                
                # 过滤条件：严格处于当前收盘价上方，且墙体厚度（能量条格子数）必须大于等于 4格
                if p_node > close_price and len(bar_str) >= 4:
                    first_gravity_price = p_node
                    first_gravity_labels = label_str
                    wall_thickness = len(bar_str)
                    break 

            if first_gravity_price > 0:
                rebound_profit_pct = ((first_gravity_price - close_price) / close_price) * 100
                atr_distance = (first_gravity_price - close_price) / atr_5d
                
                audit_results.append({
                    "股票代码": stock_code,
                    "股票名称": stock_name,
                    "当前收盘价": close_price,
                    "5日ATR": atr_5d,
                    "首道重力墙(元)": first_gravity_price,
                    "墙体装甲厚度": f"{wall_thickness}格",
                    "触网净空间(元)": round(first_gravity_price - close_price, 2),
                    "ATR波动跨度": round(atr_distance, 1),
                    "★第一浪利润期望": round(rebound_profit_pct, 2),
                    "首墙性质标签": first_gravity_labels
                })

        except Exception:
            continue

    # 生成雷达总表并执行降序排列
    df_report = pd.DataFrame(audit_results)
    if df_report.empty:
        print("🚨 全网审计结束：未检测到任何现价上方有实质性重力墙拦截的个股。")
        return

    df_report = df_report.sort_values(by="★第一浪利润期望", ascending=False).reset_index(drop=True)

    # # 6. 纯中文控制台原生态无水分高亮输出（完整保留原有展示机制）
    print(f"@@@@@@@@@@@@@@@@@@ 🏆 {end_date} 衍生品错砸·近端第一浪反弹套利龙虎榜 @@@@@@@@@@@@@@@@@@")
    print(f"🤖 审计状态：零主观粉饰。利润排序完全由 [当前价 ➡️ 头顶首道实质重力墙] 之间的净空旷率自演化决定。")
    print("-" * 155)
    print(f"{'排名':<4} {'代码':<10} {'股票名称':<10} {'当前价':<8} {'5日ATR':<8} {'首道实质重力墙':<14} {'装甲厚度':<10} {'净空间(元)':<12} {'ATR跨度':<10} {'★第一浪利润期望'}")
    print("-" * 155)
    
    for idx, row in df_report.iterrows():
        if idx < 3:
            print(f"\033[1;31;45m{idx+1:<6} {row['股票代码']:<11} {row['股票名称']:<11} {row['当前收盘价']:<11} {row['5日ATR']:<11} {row['首道重力墙(元)']:<18} {row['墙体装甲厚度']:<12} {row['触网净空间(元)']:<16} {row['ATR波动跨度']:<12} {row['★第一浪利润期望']}%  🔥\033[0m")
        else:
            print(f"{idx+1:<6} {row['股票代码']:<11} {row['股票名称']:<11} {row['当前收盘价']:<11} {row['5日ATR']:<11} {row['首道重力墙(元)']:<18} {row['墙体装甲厚度']:<12} {row['触网净空间(元)']:<16} {row['ATR波动跨度']:<12} {row['★第一浪利润期望']}%")
    print("-" * 155)
    print(f"💡 实战看盘指引：‘★第一浪利润期望’最大的个股，代表其在跌穿近端大资金本营后，距离上方首个真正的套牢压力盘盘口最远，反弹阻力最小。刚到重力墙区间，永远不用担心卖飞。\n")

    # =========================================================================
    # 🚀【全新数据并轨追加区】将计算排序后的龙虎榜结果转化为列表，分流打入Excel导出引擎
    # =========================================================================
    profit_pool_list = []
    for _, row in df_report.iterrows():
        profit_pool_list.append({
            "股票代码": str(row["股票代码"]),
            "股票名称": str(row["股票名称"]),
            "当前收盘价": float(row["当前收盘价"]),
            "5日ATR": float(row["5日ATR"]),
            "首道重力墙(元)": float(row["首道重力墙(元)"]),
            "墙体装甲厚度": str(row["墙体装甲厚度"]),
            "触网净空间(元)": float(row["触网净空间(元)"]),
            "ATR波动跨度": float(row["ATR波动跨度"]),
            "★第一浪利润期望": float(row["★第一浪利润期望"]),
            "首墙性质标签": str(row["首墙性质标签"])
        })
        
    # 一键调用 Excel 模块，安全落表保存
    export_profit_pool_to_excel(profit_pool_list, end_date)

if __name__ == "__main__":
    #scan_highest_near_rebound_profit("2026-07-28")
    scan_highest_near_rebound_profit("2026-07-29")
