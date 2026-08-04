import os
import glob
import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.utils import get_column_letter

def analyze_xlsm_stock_precise(file_path):
    # data_only=True 确保读取的是公式计算后的数值，而不是公式本身
    wb = load_workbook(file_path, data_only=True)
    ws = wb.active 
    
    # 1. 严格提取 B33:H33 基础数据
    stock_code = str(ws['B33'].value).strip() if ws['B33'].value else "未知代码"
    stock_name = str(ws['C33'].value).strip() if ws['C33'].value else "未知名称"
    
    try:
        current_price = float(ws['D33'].value)
    except:
        return None # 无法读取当前价则跳过
        
    try:
        atr_14 = float(ws['G33'].value) if ws['G33'].value else 0.0
        atr_5 = float(ws['H33'].value) if ws['H33'].value else 0.0
    except:
        atr_14, atr_5 = 0.0, 0.0

    # 2. 提取多周期 CDP 关键参考位（用于趋势与方向控制）
    cdp_20_cdp = float(ws['D38'].value) if ws['D38'].value else 0.0  # 20日中轴
    cdp_20_nl  = float(ws['F38'].value) if ws['F38'].value else 0.0  # 20日低吸支撑
    cdp_20_al  = float(ws['E38'].value) if ws['E38'].value else 0.0  # 20日止损边界
    
    cdp_60_cdp = float(ws['D39'].value) if ws['D39'].value else 0.0  # 60日中轴
    cdp_60_nl  = float(ws['F39'].value) if ws['F39'].value else 0.0  # 60日低吸支撑

    # 3. 扫描 45 行以后的全表筹码墙数据
    walls_data = []
    for r in range(45, ws.max_row + 1):
        price_val = ws.cell(row=r, column=2).value # B列：绝对价格
        label_val = ws.cell(row=r, column=3).value # C列：筹码标签说明
        
        if price_val is not None:
            try:
                price_num = float(price_val)
                walls_data.append({"价格": price_num, "标签": str(label_val or ""), "行号": r})
            except ValueError:
                continue

    if not walls_data:
        return None

    df_walls = pd.DataFrame(walls_data)
    # 统计黑格子数量
    df_walls['能量强度'] = df_walls['标签'].apply(lambda x: x.count('■'))

    # ==================== 【彻底修复】严格区分“上方阻力”与“下方支撑” ====================
    current_price_rows = df_walls[df_walls['标签'].str.contains('★当前收盘价|当前收盘', na=False)]
    
    if not current_price_rows.empty:
        # 【标准语法修复】：通过 .values[0] 提取纯数值，彻底解决 iloc 报错问题
        current_row_idx = int(current_price_rows['行号'].values[0])
        upper_walls = df_walls[df_walls['行号'] < current_row_idx]
        lower_walls = df_walls[df_walls['行号'] > current_row_idx]
    else:
        upper_walls = df_walls[df_walls['价格'] > current_price]
        lower_walls = df_walls[df_walls['价格'] < current_price]

    # ==================== 【算法完善】：近端优先的阶梯利润空间扫描 ====================
    if not upper_walls.empty:
        # 优先寻找当前价上方 1.5倍 14日ATR 范围内的“第一道套牢墙”
        near_window = current_price + (1.5 * atr_14 if atr_14 > 0 else current_price * 0.05)
        near_upper_walls = upper_walls[upper_walls['价格'] <= near_window]
        
        if not near_upper_walls.empty:
            # 如果眼前就有阻力墙，不管多厚，必须以眼前的墙作为第一目标位（实战防御）
            max_strength = near_upper_walls['能量强度'].max()
            best_resistance = near_upper_walls[near_upper_walls['能量强度'] == max_strength].iloc[0]
        else:
            # 眼前无阻力，属于局部真空，则去寻找上方最厚的那个全局阻力墙
            max_strength = upper_walls['能量强度'].max()
            best_resistance = upper_walls[upper_walls['能量强度'] == max_strength].iloc[0]
            
        target_price = best_resistance['价格']
        resistance_name = best_resistance['标签']
        profit_to_wall = (target_price - current_price) / current_price
    else:
        target_price, resistance_name, profit_to_wall = None, "上方无阻力(筹码真空断层)", 0.0

    # ==================== 【算法完善】：多维空间+动能趋势立体选股算法 ====================
    # 1) 动态安全垫窗口：根据个股自身属性(1.5倍ATR)，动态计算支撑是否属于“近距离贴身保护”
    safe_window_price = current_price - (1.5 * atr_14 if atr_14 > 0 else current_price * 0.03)
    
    # 2) 过滤脚下动态安全垫范围内的大周期硬核筹码墙
    hard_floors = lower_walls[(lower_walls['价格'] >= safe_window_price) & 
                              (lower_walls['标签'].str.contains('20日|60日|半年|年度|核心|真POC', na=False))]
    has_strong_floor = not hard_floors.empty
    floor_max_energy = hard_floors['能量强度'].max() if has_strong_floor else 0

    # 3) 动能变频比
    atr_ratio = atr_5 / atr_14 if atr_14 > 0 else 1.0
    is_amplitude_crushed = atr_ratio <= 0.85   # 波幅深度萎缩
    is_amplitude_expanding = atr_ratio >= 1.20 # 波幅恐慌放大

    # 4) 大大趋势方向滤镜（识别一字跌停、破位主跌浪等无解死局）
    is_bear_market_trend = cdp_20_cdp < cdp_60_cdp and current_price < cdp_60_nl

    # 5) 交叉矩阵推演最终实战状态
    if is_bear_market_trend and is_amplitude_crushed:
        # 特别防御：一字跌停或单边主跌浪中的无量横盘，属于无量阴跌死水，强制打入3级
        bottom_status = "【3级：破位阴跌真空区】大趋势严重走坏，当前缩量属于无量阴跌死水，切勿抄底！"
        
    elif current_price <= cdp_20_nl * 1.02 and is_amplitude_crushed and has_strong_floor and floor_max_energy >= 3 and not is_bear_market_trend:
        # 真正的1级：位置跌透 + 抛压耗尽 + 强筹码守卫 + 大趋势未崩塌
        bottom_status = "【1级：坚实左侧底】空间跌透 + 波幅冰点 + 中长期大筹码护盘。黄金左侧潜伏点！"
        
    elif current_price < cdp_20_al and is_amplitude_expanding and has_strong_floor:
        # 2级：恐慌砸盘砸到历史大铁板上
        bottom_status = "【2级：恐慌暴跌撞墙】击穿月度极限边界，恐慌盘涌出，但正砸在历史强支撑上。适合挂单接飞刀。"
        
    elif current_price < cdp_20_nl or (is_amplitude_crushed and not has_strong_floor):
        # 3级：没有掩体的无量横盘或者破位股
        bottom_status = "【3级：破位阴跌真空区】价格已穿透支撑位，且脚下缺乏核心大筹码防线。严禁建仓！"
        
    elif current_price > cdp_20_cdp * 1.05 and is_amplitude_crushed:
        # 5级：高位滞涨风险
        bottom_status = "【5级：高位悬空滞涨】价格悬空于各中长期支撑上方，高位缩量久盘必跌。随时发生补跌，严禁建仓！"
        
    else:
        # 4级：正常波动区间
        bottom_status = f"【4级：中继常态震荡】多空在中轴【{cdp_20_cdp}】附近正常博弈，空间或时间未换到位，暂不建仓。"
    # ========================================================================

    return {
        "股票代码": stock_code,
        "股票名称": stock_name,
        "当前收盘价": current_price,
        "第一大阻力价": target_price,
        "阻力墙特征": resistance_name,
        "到阻力墙利润空间": profit_to_wall, 
        "5日ATR": atr_5,
        "14日ATR": atr_14,
        "底部状态评估": bottom_status
    }

def generate_report(folder_path, output_path, start_row=1, start_col=1):
    xlsm_files = glob.glob(os.path.join(folder_path, "*.xlsm"))
    results = []
    
    print(f"正在精准解析 {len(xlsm_files)} 个股票文件...")
    for file in xlsm_files:
        try:
            stock_data = analyze_xlsm_stock_precise(file)
            if stock_data:
                results.append(stock_data)
        except Exception as e:
            print(f"文件 {os.path.basename(file)} 解析异常: {e}")
            
    if not results:
        print("未提取到任何有效数据。")
        return

    df_report = pd.DataFrame(results)
    # 按利润空间从大到小降序排列
    df_report = df_report.sort_values(by="到阻力墙利润空间", ascending=False)
    df_report['到阻力墙利润空间'] = df_report['到阻力墙利润空间'].apply(lambda x: f"{x:.2%}")

    # 读取或创建总表
    if os.path.exists(output_path):
        wb_out = load_workbook(output_path)
        ws_out = wb_out.active
    else:
        wb_out = Workbook()
        ws_out = wb_out.active
    
    # 彻底擦除老数据矩形，防止新旧混合
    max_exist_row = ws_out.max_row
    max_exist_col = ws_out.max_column
    if max_exist_row >= start_row and max_exist_col >= start_col:
        print("正在清除旧数据残余...")
        for r in range(start_row, max_exist_row + 1):
            for c in range(start_col, max_exist_col + 1):
                ws_out.cell(row=r, column=c).value = None

    # 写入新表头
    headers = list(df_report.columns)
    for c_idx, header in enumerate(headers):
        cell = ws_out.cell(row=start_row, column=start_col + c_idx)
        cell.value = header
        
    # 写入新数据
    for r_idx, row_data in enumerate(df_report.values):
        for c_idx, value in enumerate(row_data):
            cell = ws_out.cell(row=start_row + 1 + r_idx, column=start_col + c_idx)
            cell.value = value
            
    wb_out.save(output_path)
    print(f" 运行成功！已将最精准、最契合实盘逻辑的选股数据干净写入报告。")

# --- 执行区域 ---
if __name__ == "__main__":
    # 1. 你的文件夹路径
    #target_folder = r"C:\price_py\CDP\算反弹阻力用\2026-08-03" # 建议用绝对路径确保万无一失
    #target_folder = "2026-07-30" # 建议用绝对路径确保万无一失
    target_folder = "2026-08-04" # 建议用绝对路径确保万无一失
    
    # 2. 输出的报告文件名
    #output_excel = r"C:\price_py\CDP\算反弹阻力用\总筛选报告.xlsx" 
    output_excel = f"总筛选报告_{target_folder}.xlsx" 
    
    # 3. 在这里【指定开始行和开始列】
    # 1代表A列，2代表B列，3代表C列...
    GEN_START_ROW = 2  
    GEN_START_COL = 2  
    
    generate_report(target_folder, output_excel, start_row=GEN_START_ROW, start_col=GEN_START_COL)
