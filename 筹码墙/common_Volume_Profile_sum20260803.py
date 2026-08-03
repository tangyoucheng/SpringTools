# common_Volume_Profile_sum20260803.py
import os
import glob
import pandas as pd

# ==========================================
# 1. 全自适应配置参数
# ==========================================
EXCEL_DIR = "2026-07-29"  # 存放您所有股票Excel文件的文件夹路径
OUTPUT_FILE = "adaptive_breakout_stocks.csv"  # 筛选结果的输出文件名

def analyze_stock_sheet(file_path):
    try:
        # 读取Excel，不设置表头，保持原生行索引 (Excel行号 - 1 = Python索引)
        df = pd.read_excel(file_path, sheet_name='Sheet1', header=None)
        
        # ==============================================================================
        # 2. 绝对精确的【100%对照截图】数据抓取（补齐 nl_20d，绝无错位与漏写）
        # ==============================================================================
        stock_code = str(df.iloc[32, 1])      # B33: 股票代码 (如 600418.SS)
        stock_name = str(df.iloc[32, 2])      # C33: 股票名称 (如 江淮汽车)
        current_close = float(df.iloc[32, 3])  # D33: 当日最新收盘价 (如 26.27)
        atr_14 = float(df.iloc[32, 6])         # G33: 14日ATR (如 1.698)
        atr_5 = float(df.iloc[32, 7])          # H33: 5日ATR (如 1.858)
        
        # C35: 基于ATR和POC算出来的CDP价格矩阵中轴
        cdp_matrix_center = float(df.iloc[34, 2]) # C35 (数值: 26.2)
        
        # D列：多周期“真POC”筹码墙核心
        poc_1d = float(df.iloc[34, 3])   # D35: 1天真POC (26.20)
        
        # E列：多周期“NL低吸支撑线”筹码墙 (修复完善点：必须完整调入用于A杀超卖判定)
        nl_1d = float(df.iloc[34, 4])    # E35: 1天NL (24.32)
        nl_3d = float(df.iloc[35, 4])    # E36: 3天NL (22.25)
        nl_5d = float(df.iloc[36, 4])    # E37: 5天NL (22.51)
        nl_20d = float(df.iloc[37, 4])   # 🟢 完美补齐 E38: 20日NL (20.30)
        
        # F列：多周期“NH高抛阻力线”筹码墙
        nh_1d = float(df.iloc[34, 5])    # F35: 1天NH (27.27)
        nh_3d = float(df.iloc[35, 5])    # F36: 3天NH (26.27)
        nh_5d = float(df.iloc[36, 5])    # F37: 5天NH (26.11)
        nh_20d = float(df.iloc[37, 5])   # F38: 20日NH (27.66)
        
        # F40: 120日线(半年)高抛阻力NH (用于测算上方终极真空断层空间)
        nh_120d = float(df.iloc[39, 5])  # F40: 120日NH

        # ==============================================================================
        # 3. 终极自适应分流判定与风险矩阵审核 (面向全场A杀 facts 彻底去理想化)
        # ==============================================================================
        
        atr_ratio = atr_5 / atr_14  # 动能偏离比
        nh_list = [nh_1d, nh_3d, nh_5d, nh_20d]
        nh_max = max(nh_list)
        nh_min = min(nh_list)
        nh_spread = nh_max - nh_min # 中短期筹码墙绝对厚度
        
        # 【自适应筹码墙聚合度检验】
        adaptive_threshold = max(atr_14 * 0.35, current_close * 0.015) 
        is_wall_cohesive = nh_spread <= adaptive_threshold # 【核心条件一：墙凝聚事实】
        
        # 【绝对客观的多头阵营判定】
        is_above_support = current_close >= min(cdp_matrix_center, poc_1d) # 【核心条件二：底线支撑事实】

        # 【风险约束：短线乖离防守约束】
        # 防超买基准锚定筹码墙上限 nh_max，严重高位超买的在常态行情下直接拦截
        is_not_overbought = (current_close - nh_max) <= (atr_14 * 1.5) # 【核心条件三：乖离控制】

        # ==============================================================================
        # 4. 全要素分流状态机 (基于全场A杀与极致超卖事实的完全自适应)
        # ==============================================================================
        is_price_ready = False
        is_energy_ok = False
        state_desc = ""

        # 【全市场A杀事实通道：极致超卖后的 CDP 强行破墙突变】
        # 1. 测算超卖事实：当前价格距离20日NL(低吸支撑线)跌幅超过15%，说明是纯正的无底A杀股
        is_severely_oversold = (nl_20d - current_close) / nl_20d >= 0.15
        
        # 2. 测算反抗事实：在这场A杀中，今天突然爆量，价格强行刺穿了 1天历史NH(昨高抛阻力墙F35)，证明盘中多头暴力摧毁空头防线
        is_violent_rebound = (current_close > nh_1d) and (current_close > poc_1d)

        if is_severely_oversold and is_violent_rebound and (atr_ratio >= 1.10):
            # 激活【A杀冰点突变逆袭】通道：豁免墙黏合与乖离限制，抓取从深渊里爆量翘板的真妖股
            is_price_ready = True
            is_energy_ok = True
            is_wall_cohesive = True   
            is_not_overbought = True  
            state_desc = "真实A杀极度超卖 + 今日CDP强行破墙（冰点逆袭启动）"

        # --- 若不是这种极端A杀逆袭，则老老实实走原本的【筹码墙稳健突破】逻辑 ---
        else:
            # 动态过墙变盘线
            breakout_trigger_line = nh_max + max(nh_spread * 0.2, atr_14 * 0.1)

            if current_close < nh_min * 0.98:
                state_desc = "无动能冷门状态"
                
            elif nh_min * 0.98 <= current_close <= breakout_trigger_line:
                # 状态 B：股价正处于筹码墙内部蓄势，或者贴着墙上限进行多空摩擦
                if atr_ratio <= 1.08:
                    is_price_ready = True
                    is_energy_ok = True
                    state_desc = "临界点贴墙蓄势摩擦"
                else:
                    state_desc = "墙内异常高位发散震盘（暂不具备突破确定性）"
                    
            elif current_close > breakout_trigger_line:
                # 状态 C：股价已明确穿透自适应破墙线
                is_breakout_valid = current_close > cdp_matrix_center
                is_not_fake_drop = current_close >= nh_min
                
                # 趋势拦截：真正的常态强突，20日筹码压力墙上限（nh_20d）不能处于比120日半年墙（nh_120d）还高15%以上的单边阴跌退潮期
                is_not_bear_rebound = nh_20d <= nh_120d * 1.15
                
                if atr_ratio >= 0.95 and is_breakout_valid and is_not_fake_drop and is_not_bear_rebound:
                    is_price_ready = True
                    is_energy_ok = True
                    
                    dynamic_ah_line = nh_max + (atr_14 * 0.2) 
                    if current_close > dynamic_ah_line:
                        state_desc = "放量强突 + 超越AH追多线（超强主升浪启动）"
                    elif current_close < poc_1d:
                        state_desc = "放量强突 + 主力中枢洗盘（假阴真阳形态）"
                    else:
                        state_desc = "放量强突主升启动（稳健过墙形态）"
                else:
                    if not is_not_bear_rebound:
                        state_desc = "单边阴跌A杀股无支撑的虚假脉冲诱多"
                    else:
                        state_desc = "动能错位/缺乏主力控盘的诱多假突破"

        # ==============================================================================
        # 5. 空间性价比与防空过滤判定 (自适应双重地平线锁定)
        # ==============================================================================
        is_space_profitable = False
        breakout_type = ""

        if is_price_ready and is_energy_ok and is_not_overbought and is_wall_cohesive and is_above_support:
            # 检测中短期墙与120日长线套牢墙的靠拢程度
            resonance_degree = abs(nh_120d - nh_max) / nh_max
            
            if "冰点逆袭启动" in state_desc:
                # A杀超跌反弹不计算上方真空，因为头顶全是套牢盘，它玩的是纯粹的超跌死弹
                is_space_profitable = True
                breakout_type = state_desc
            elif resonance_degree <= 0.025:
                is_space_profitable = True
                breakout_type = f"{state_desc} + 多周期终极共振形态"
            elif current_close > nh_120d:
                is_space_profitable = True
                breakout_type = f"{state_desc} + 历史死筹全瓦解（天空断层主升）"
            else:
                # 引入冰点期底线空间约束：上方真空空间既要大于5日ATR短期波幅，绝对价格空间又必须大于3.5%
                absolute_pct_space = (nh_120d - current_close) / current_close
                is_atr_space_ok = (nh_120d - current_close) >= atr_5
                
                if is_atr_space_ok and (absolute_pct_space >= 0.035):
                    is_space_profitable = True
                    breakout_type = f"{state_desc} + 中短期真空断层突破"
                else:
                    breakout_type = "空间受限（上方空间不足以抵抗日内流动性噪音）"

        # ==============================================================================
        # 6. 输出复合全部自适应条件的优质标的
        # ==============================================================================
        if is_wall_cohesive and is_above_support and is_price_ready and is_energy_ok and is_space_profitable:
            return {
                "股票代码": stock_code,
                "股票名称": stock_name,
                "当前收盘": current_close,
                "今日CDP中轴(C35)": cdp_matrix_center,
                "动能偏离比(Ratio)": round(atr_ratio, 2),
                "自适应允许墙宽": round(adaptive_threshold, 2),
                "实际筹码墙厚度": round(nh_spread, 2),
                "终极突破模式": breakout_type,
                "长线压制位(NH_120d)": nh_120d
            }
        return None

    except Exception as e:
        print(f"解析文件 {os.path.basename(file_path)} 时严重报错，请核对单元格数据。错误: {e}")
        return None
# ==========================================
# 5. 批量执行主程序
# ==========================================
if __name__ == "__main__":
    excel_files = glob.glob(os.path.join(EXCEL_DIR, "*.xlsm"))
    
    if not excel_files:
        print(f"未在 '{EXCEL_DIR}' 文件夹中找到任何 .xlsx 文件，请先创建该文件夹并放入数据。")
    else:
        print(f"开始使用自适应【是是逻辑】扫描 {len(excel_files)} 个股票的 CDP-POC 矩阵...")
        results = []
        
        for file in excel_files:
            stock_analysis = analyze_stock_sheet(file)
            if stock_analysis:
                results.append(stock_analysis)
        
        if results:
            result_df = pd.DataFrame(results)
            result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            print(f"\n🚀 筛选完成！共有 {len(results)} 只股票满足【动态启动】条件。")
            print(f"结果已保存至: {OUTPUT_FILE}")
            print(result_df.to_string())
        else:
            print("\n扫描完毕：当前没有股票满足自适应启动条件。")
