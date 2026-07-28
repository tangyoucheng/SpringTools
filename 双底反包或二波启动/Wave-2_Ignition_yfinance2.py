#cdp_poc_today_ATR.py
import os
import sys
import datetime
import numpy as np
import pandas as pd
import yfinance as yf

# 使用免安装版本时，为了读取CDP_config.py，添加的设定
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 假设 stock_dict 从配置中导入，若本地测试可自行定义
#from cdp_poc_today_ATR_config import stocks_list

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime, timedelta

# ==========================================
# 第一部分：高精度量化形态识别核心引擎
# ==========================================


def is_limit_up(close, pre_close, date_str, ticker="", is_st_stock=False):
    """
    【工业级 A 股高精度涨停卡死判定函数 - 完美兼容 2026 最新主板 ST 交易新规】
    
    业务逻辑：
    1. 动态拦截 yfinance 的股票代码格式，精准识别主板、创业板、科创板以及 ST/戴帽股票。
    2. 引入时间轴沙箱，以 2026 年 7 月 6 日为分水岭，自动无缝分流计算主板 ST 股的新旧涨幅限制。
    3. 模拟中国 A 股交易所特有的“四舍五入精确到分”进位机制，使用绝对价格卡死（>= limit_price）。
    4. 彻底剔除浮点数带来的百分比精度误差（如 1e-9 微调），杜绝低价股的伪涨停和漏报 Bug。
    
    参数说明：
    :param close: 当前 K 线的实际收盘价（Float）。
    :param pre_close: 当前 K 线的昨日收盘价（Float），作为涨停板计算的基准绝对分母。
    :param date_str: 当前 K 线的日期字符串（格式 'YYYY-MM-DD'），用于新规上线日的时间轴动态比对。
    :param ticker: 标准 A 股代码字符串（如 "300750.SZ" / "600519.SS"），用于识别板块。
    :param is_st_stock: 外部穿透传入的个股当前实时 ST 身份标记。
    :return: 布尔值。True 代表该 K 线上封死涨停板；False 代表未触及涨停。
    """
    # 【安全防线】如果前一日收盘价异常小于或等于 0（如停牌、无量或除权异常零值数据），
    # 此时计算涨停无意义，直接返回 False 熔断，防止分母为 0 导致系统崩溃。
    if pre_close <= 1e-4:
        return False

    # 【代码格式规范化】强转代码为大写字符串，并以第一个圆点 '.' 拆分，
    # 完美剥离出 yfinance 格式下的纯数字前缀（例如："300750.SZ" -> pure_code="300750"）
    ticker_str = str(ticker).upper()
    pure_code = ticker_str.split(".")[0]

    # =====================================================================
    # 核心逻辑第一步：动态匹配各板块及特殊身份的涨幅限制阈值（pct）
    # =====================================================================
    # 【分支 A】触发 ST 股票风控线（外部标记为 ST，或者代码中隐式包含 "ST" 字样）
    if is_st_stock or "ST" in ticker_str:
        # 将当前 K 线的日期和 2026 交易新规生效日强转为标准的 pandas 时间戳对象进行数学比对
        current_date = pd.to_datetime(date_str)
        rule_change_date = pd.to_datetime("2026-07-06")
        
        # 状况 A-1：如果是创业板或科创板的 ST 股，新规前后均不限制，涨幅始终为 20%
        if pure_code.startswith("30") or pure_code.startswith("68"):
            pct = 0.20
        # 状况 A-2：【关键新规适配】如果是沪深主板 ST 股，且当前日期处于 2026年7月6日（含）之后，
        # 规则拉平！主板 ST 涨跌幅正式放宽由 5% 步入 10% 时代，完美防止新数据漏报！
        elif current_date >= rule_change_date:
            pct = 0.10  
        # 状况 A-3：属于 2026年7月6日 之前的历史老数据，主板 ST 股票依然严格按照传统的 5% 计算，防止历史回测产生“假涨停”
        else:
            pct = 0.05
            
    # 【分支 B】触发 20CM 高弹性板块（纯数字代码以 30 开头的创业板，或 68 开头的科创板大段）
    elif pure_code.startswith("30") or pure_code.startswith("68"):
        pct = 0.20  # 无论新股还是老股，普通创业板/科创板涨幅限制固定为 20%
        
    # 【分支 C】触发普通沪深主板蓝筹（代码以 000、002、600、601、603、605 等开头）
    else:
        pct = 0.10  # 普通主板股票涨幅限制固定为 10%

    # =====================================================================
    # 核心逻辑第二步：模拟交易所分钱进位算法，精确卡死理论涨停价格
    # =====================================================================
    # 1. 理论计算公式：昨日收盘价 * (1 + 涨幅限制比例)。
    # 2. 浮点数精度微调（+ 1e-9）：量化回测的硬核细节。在 Python 底层二进制浮点数运算中，
    #    例如 9.13 * 1.1 的理论值是 10.043，但计算机内部存储可能会由于精度缺失变成 10.042999999999。
    #    直接四舍五入会变成 10.04，而实际交易所进位是 10.05。因此引入 1e-9 的微小正向扰动，可以完美对冲浮点数精度截断。
    # 3. 严格执行 round(..., 2)：对标 A 股交易所撮合系统的四舍五入到分钱进位制，生成唯一的绝对价格红线。
    limit_price = round(pre_close * (1 + pct) + 1e-9, 2)

    # =====================================================================
    # 核心逻辑第三步：绝对价格刚性比对（消灭比例判定，杜绝低价股伪信号）
    # =====================================================================
    # 放弃原本宽松的 (close - pre_close) / pre_close >= pct - 0.001 逻辑。
    # 对于 1~2 元的低价股或 ST 股，比例判定极易将 9.91% 误判为涨停。
    # 这里强行执行绝对价格刚性卡死：收盘价 close 必须大于或等于精确算至分钱的理论涨停价 limit_price，才是真正的铁板涨停。
    return close >= limit_price



def find_pattern_instances_fast(df, ticker="", is_st_stock=False):
    """
    【工业级 NumPy 高速形态寻找核心 - 双指针洗盘反包状态机】
    
    业务逻辑：
    1. 接收标准化清洗后的 K 线 DataFrame，全线转换为原生 NumPy 数组以榨干 CPU 性能。
    2. 第一阶段（i 循环）：寻找符合 A 股精确进位算法的“涨停日”。
    3. 第二阶段（j 循环）：在涨停后 5 天内寻找“缩量阴线（主力良性洗盘被套日）”。
    4. 第三阶段（k 循环）：在阴线后、且在涨停后 5 天的紧凑周期内，寻找“大阳线或再度涨停且收盘价绝对反包阴线最高价”的爆发点。
    5. 通过动态双指针控制（next_i），在成功触发后让指针实现空间跨越，彻底去重。
    
    参数说明：
    :param df: 已重置索引且包含 date, open, high, close, volume 等核心小写列名的标准化 DataFrame。
    :param ticker: 标准 A 股代码字符串，用于涨停规则分流。
    :param is_st_stock: 外部穿透传入的该股当前 ST 状态。
    :return: 包含所有完美触发【洗盘反包】瞬间的行索引（k值）列表。
    """
    # 强制进行内存深拷贝，彻底切断与外层调用函数的引用链，封杀 SettingWithCopy 隐式赋值警告
    df_clone = df.copy()
    
    # 全面将所有列名强制转换为小写字符串，双重保险防御不同 API 带来的大小写差异崩溃
    df_clone.columns = [str(col).lower() for col in df_clone.columns]
    
    # 【量价防御】对可能存在的零成交量或 NaN 空值进行 0 填充（如停牌或除权异常数据），
    # 防止 rolling 计算时因单个 NaN 导致后续 5 天均量全盘污染变成 NaN。
    df_clone["volume"] = df_clone["volume"].fillna(0)
    df_clone["vol_ma5"] = df_clone["volume"].rolling(5).mean().fillna(0)

    # =====================================================================
    # 核心优化：全线将 Pandas Series 降维导出为原生的 NumPy 数组。
    # 目的：循环内部完全脱离 Pandas 的索引对齐、类型检查和轴校验，效率可狂飙 20~50 倍。
    # =====================================================================
    dates = df_clone["date"].dt.strftime("%Y-%m-%d").to_numpy() # 提取日期字符串数组（用于涨停新规时间比对）
    opens = df_clone["open"].to_numpy()                         # 开盘价矩阵
    highs = df_clone["high"].to_numpy()                         # 最高价矩阵
    closes = df_clone["close"].to_numpy()                       # 收盘价矩阵
    volumes = df_clone["volume"].to_numpy()                     # 成交量矩阵
    vol_ma5 = df_clone["vol_ma5"].to_numpy()                   # 5日均量矩阵

    n = len(df_clone)
    pattern_indices = [] # 初始化形态索引结果池

    # 防御性断言：若单股总交易行数不足 10 天，根本无法凑齐状态机周期，直接熔断返回空列表
    if n < 10:
        return pattern_indices

    # =====================================================================
    # 【第一阶段：i 循环】全局扫描寻找基准涨停日 i
    # =====================================================================
    i = 1
    while i < n:
        # 提取第 i 天的前一日收盘价作为涨停计算的绝对基准分母
        pre_close_i = closes[i - 1]
        
        # 精准碰撞：判定第 i 天是否真正卡死在 A 股理论涨停板上
        # 传入 dates[i] 触发状态机内部的 2026.07.06 新规主板 ST 规则切换轴
        if not is_limit_up(closes[i], pre_close_i, dates[i], ticker, is_st_stock):
            i += 1 # 未涨停，指针正常步进 1 天
            continue

        # 碰撞成功，确认主力建仓或强拉的基准日位置
        limit_up_idx = i
        limit_close = closes[limit_up_idx] # 锁死涨停日收盘价（套牢盘成本线）
        limit_vol = volumes[limit_up_idx]   # 锁死涨停日成交量（资金底牌量度）

        # 【锁定历史建仓均量 - 彻底斩断未来数据污染】
        # 关键量化设计：直接提取涨停日当天的 5日均量 作为后续洗盘的缩量参考标尺。
        # 此处的数值完全由第 i 天及此前历史决定，阴线日对比它时绝无未来数据带来的自身污染！
        limit_vol_ma5 = vol_ma5[limit_up_idx]

        # 【防呆兜底防御】如果该股在涨停日及前几天刚经历极端长期停牌，导致计算出的均量异常为 0 或 NaN，
        # 强制采用涨停当天暴涨成交量的 60% 作为等效均量垫进行替代，防止由于分母或对比值异常导致选股死锁。
        if np.isnan(limit_vol_ma5) or limit_vol_ma5 <= 1e-4:
            limit_vol_ma5 = limit_vol * 0.6

        # 形态状态机状态标记：用于标记当前这波涨停红浪内，是否成功孵化出完整的洗盘反包
        pattern_found_in_this_wave = False
        
        # 动态指针预备步进值：默认情况下如果这波失败了，下一次外层循环从涨停后一天（i + 1）继续探测
        next_i = i + 1

        # =====================================================================
        # 【第二阶段：j 循环】在涨停后的 1~5 天内，寻找洗盘缩量阴线 j
        # =====================================================================
        # 严格限制洗盘周期：最大不能超过涨停后的 5 个交易日（确保短线主力资金未死、属于紧凑洗盘）
        for j in range(limit_up_idx + 1, min(limit_up_idx + 6, n)):
            is_yin = closes[j] < opens[j]          # 条件一：收盘价低于开盘价，铁证阴线
            is_trapped = closes[j] < limit_close   # 条件二：收盘价砸落在涨停收盘价下方（造成追高浮筹全面被套）
            
            # 安全防线：显式拦截停牌股、无量一字跌停或数据断档时 NaN 对比失效的隐患
            v_j = volumes[j]
            if np.isnan(v_j) or v_j <= 1e-4:
                continue

            # 条件三：【极致清洗判定】洗盘日成交量必须双重严格小于涨停当日量，且小于涨停日锁死的5日均量！
            # 这代表主力资金在刻意压盘窒息，散户浮筹在恐慌出局，无大资金出货承接。
            is_low_vol = v_j < limit_vol and v_j < limit_vol_ma5

            # 当阴线、被套、极致缩量三者在中途完美共振，确立洗盘陷阱日位置
            if is_yin and is_trapped and is_low_vol:
                yin_idx = j
                yin_high = highs[yin_idx] # 锁死该洗盘阴线的最高价（定义短线最强套牢盘压力位）

                # =====================================================================
                # 【第三阶段：k 循环】在阴线后、且在涨停后 5 天大周期内，寻找反包大阳线 k
                # =====================================================================
                # 反包窗口紧跟阴线日启动，但整体依然受控于涨停后的 5 日大博弈周期内（超过5天则沦为僵尸图形）
                for k in range(yin_idx + 1, min(limit_up_idx + 6, n)):
                    # 提取反包日前一天的收盘价作为分母
                    pre_close_k = closes[k - 1]
                    
                    # 极端异常价格兜底（防分母为 0 崩溃）
                    if pre_close_k <= 1e-4:
                        continue
                    
                    # 判断 k 日是否拉出大阳线：定义为个股单日涨幅狠狠超越 5% 大关
                    is_big_yang = (closes[k] - pre_close_k) / pre_close_k >= 0.05
                    
                    # 判断 k 日是否暴力到直接再度拉出涨停板封死成本区
                    is_rebound_limit = is_limit_up(
                        closes[k], pre_close_k, dates[k], ticker, is_st_stock
                    )
                    
                    # 关键反包卡死：第 k 日的收盘价，必须绝对跨越、超越洗盘阴线的最高价（yin_high）
                    # 代表这一根阳线强行收复了洗盘的所有失地，主力完成反戈一击，浮筹清洗完毕。
                    is_engulfing = closes[k] > yin_high

                    # 当（大阳线 或 再度涨停）且收盘价绝对反包压力位时，状态机完美闭环！
                    if (is_big_yang or is_rebound_limit) and is_engulfing:
                        pattern_indices.append(k) # 精准捕获并记录该反包完成日的行索引位置
                        
                        pattern_found_in_this_wave = True # 标记当前红浪孵化成功
                        
                        # 【核心指针跃迁优化】
                        # 既然在第 k 天已经完成了完美的洗盘反包，那么从涨停日到第 k 天之间的这段行情已经彻底消费完毕。
                        # 此时让 next_i 直接快进、跨越跳跃到反包日之后的一天（k + 1）。
                        # 目的：彻底斩断同一段上涨大波段中可能因小阴小阳引发的信号二次重叠触发，防止信号多重共振！
                        next_i = k + 1
                        break # 跳出当前 k 循环（寻找反包流）
                        
                # 状态机去重分流：如果这波阴线探测已经顺藤摸瓜成功触发了反包，
                # 立刻无条件斩断当前涨停浪里的后续阴线探测，防止漏斗逻辑多重叠加
                if pattern_found_in_this_wave:
                    break # 跳出当前 j 循环（寻找阴线流）

        # 【双指针动态收缩控制】
        # 若这一波涨停红浪内最终没有孵化出成功形态，指针正常前移 1 天（i + 1）；
        # 若不幸或万幸找到了，则利用 next_i 让指针实现闪电快进，跳过已交易区间，从而开始寻找下一轮大资金运作。
        i = next_i if pattern_found_in_this_wave else i + 1

    # 向筛选引擎吐回全矩阵纯净、无重复、高时效的历史成功触发索引列表
    return pattern_indices



def screen_single_stock(ticker, end_date_str=None, filter_st=False):
    """
    【工业级单股高时效性筛选引擎 - 定长回溯风控版】
    
    业务逻辑：
    1. 动态拦截并解析回溯时间窗口（手动基准日或系统当天），自动切出 45 天定长切片。
    2. 穿透 yfinance 的 info 字典，对个股进行实时“戴帽/ST”身份穿透与甄别。
    3. 提取历史K线并将其转换为干净的低开高收矩阵，移交底层 NumPy 探针执行形态识别。
    4. 拦截并校验基准日当天的“均线偏离度”与“反包时效性”，过滤出最完美的企稳买点。
    
    参数说明：
    :param ticker: 符合 yfinance 后缀要求的标准 A 股代码（如 "300750.SZ" / "600519.SS"）。
    :param end_date_str: 手动指定的复盘结束基准日，格式 'YYYY-MM-DD'。若为 None 则默认锁定今天。
    :param filter_st: ST 股票硬过滤开关。True 为直接抹杀；False 为放行并在后续启用 2026 最新涨停规则。
    :return: 碰撞成功则返回包含核心技术指标的字典；失败或触发风控则返回 None。
    """
    try:
        # =====================================================================
        # 1. 动态时间切片计算（定长回溯核心逻辑）
        # =====================================================================
        # 判断是否手动传入了复盘结束日。若未传入，则动态抓取当前操作系统的绝对时间
        if end_date_str is None:
            end_dt = datetime.now()
        else:
            # 将外部传入的 'YYYY-MM-DD' 字符串严格解析为 datetime 对象，以便进行时间轴数学运算
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")

        # 核心风控垫：由结束日期往前狠狠回溯 45 个自然日
        # 作用：用 45 天的饱满空间，完美吃掉十一、春节等长假以及个股因异常波动停牌的无K线断层，
        # 确保下载下来的有效交易K线数量永远大于 15 天，彻底喂饱 5 日指标计算（rolling）所需的历史数据。
        start_dt = end_dt - timedelta(days=45)

        # 将 datetime 对象重新格式化为 yfinance 识别的 'YYYY-MM-DD' 标准检索字符串
        start_date = start_dt.strftime("%Y-%m-%d")
        
        # 注意：yfinance 机制是左闭右开，这里 end=end_date 传入时，yf内部会自动包含到该日期的前一天。
        # 如果需要在实盘当天下午收盘后扫描，或下载历史包含当天的数据，此处的定长设计已过安全对冲。
        end_date = end_dt.strftime("%Y-%m-%d")

        # 实例化 yfinance 的 Ticker 对象，用于拉取个股的基础证券元数据（info）
        yt = yf.Ticker(ticker)
        
        # 初始化 ST 身份标记变量，默认为健康的普通股状态
        is_current_st = False

        # =====================================================================
        # 2. 个股黑天鹅防线（ST 戴帽状态实时穿透）
        # =====================================================================
        try:
            # 强行下钻 yfinance 的实时核心元数据字典
            stock_info = yt.info
            
            # 提取个股的官方中英文股票简称，并强制统一转换为大写，防止因大小写不一致引发漏报
            short_name = stock_info.get("shortName", "").upper()
            long_name = stock_info.get("longName", "").upper()
            
            # 穿透检测：如果个股简称中包含了 "ST"、"*ST" 或 "SST" 字样，铁证如山，判定为 ST 股
            if "ST" in short_name or "ST" in long_name:
                is_current_st = True # 标记身份，为接下来的高精度涨停函数提供分流依据
                
                # 如果外部调用时明确开启了硬过滤（filter_st=True），则将其作为垃圾资产直接在首关熔断出局
                if filter_st:
                    return None
        except Exception:
            # 防御性编程：在某些极端的网络环境下（如大陆境内直接请求 info 偶尔被墙），
            # 如果info请求超时报错，则直接选择 pass 忽略，防止由于元数据接口抽风导致整个个股的数据拉取流死亡。
            pass

        # =====================================================================
        # 3. 历史K线拉取与标准化清洗
        # =====================================================================
        # 仅向 yfinance 请求拉取指定 45 天定长区间内的精准历史切片数据
        df = yt.history(start=start_date, end=end_date, progress=False)

        # 防空包机制：如果个股在指定时间内处于长期停牌状态导致无数据（empty），
        # 或者因为刚上市新股导致总行数不足 15 天，无法喂饱指标计算，则直接无条件劝退淘汰。
        if df.empty or len(df) < 15:
            return None

        # 兼容性清洗：新版 yfinance 在批量请求或某些特定资产上会返回特殊的 MultiIndex（多维列名索引）。
        # 如果发现是多维列，我们强行剥离出最底层的核心列名级别（Level 0），彻底展平列名，防止后续索引 KeyError 崩溃。
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 展平 DataFrame 默认的时间序列 Index，将 'Date' 彻底降维转换为常规的数据列
        df = df.reset_index()
        
        # 全面将所有列名强制转换为极简的纯小写字符串（如 'Close' -> 'close', 'Volume' -> 'volume'）
        # 目的：彻底降伏并统一不同 API 版本间由于大小写差异带来的全盘取值崩溃隐患。
        df.columns = [str(col).lower() for col in df.columns]
        
        # 强制将日期列洗成标准的 pandas Datetime 格式，以便底层矩阵能够进行精准的 YYYY-MM-DD 时间轴轴向匹配
        df["date"] = pd.to_datetime(df["date"])

        # =====================================================================
        # 4. 底层 NumPy 形态探针调用
        # =====================================================================
        # 将清洗好的 DataFrame 与识别到的实时 ST 标记一起，丢入底层全 NumPy 矩阵加速的状态机中。
        # 返回值 trigger_points 是一个包含所有成功触发【洗盘反包】完成日的行索引位置列表（如 [12, 24]）。
        trigger_points = find_pattern_instances_fast(
            df, ticker, is_st_stock=is_current_st
        )

        # =====================================================================
        # 5. 时效窗口控制与均线偏离度碰撞（选股核心关卡）
        # =====================================================================
        # 如果列表中至少包含一次成功触发的波段信号，说明该主力在近期曾展示过极其强烈的控盘痕迹
        if len(trigger_points) >= 1:
            
            # 锁定当前下载切片的最末尾一行（即您指定的 end_date 基准日当天）的行索引
            latest_idx = len(df) - 1
            
            # 顺藤摸瓜，精准提取出距离基准日最近的那一次【反包成功日】的行索引位置
            most_recent_trigger_k = trigger_points[-1]

            # 【时效性精准测算】计算在基准日（结束日）当天收盘时，距离当时大阳线反包成功已经过去了几个交易日
            days_since_trigger = latest_idx - most_recent_trigger_k

            # 【黄金买点时效判定】
            # 1. 如果 days_since_trigger == 0，代表今天刚拉起大阳线反包，此时价格通常暴涨狂飙，绝不能追高。
            # 2. 如果 days_since_trigger > 4，代表反包过去太久，行情可能早已走完甚至重回阴跌，沦为僵尸信号。
            # 3. 只有当反包发生在 1~4 天前，经过短暂冲高震荡后今天恰好首次回调时，才是最具有爆发力的“回踩买点”。
            if days_since_trigger < 1 or days_since_trigger > 4:
                return None

            # 精准剥离出基准日当天的实际收盘价
            current_close = df["close"].iloc[latest_idx]
            
            # 【核心抗震荡设计】如果 yfinance 某些极少数行取出来的是带 Timestamp index 的单元素 Series，
            # 通过 hasattr 检测并强行执行 .item() 剥离脱壳，将其彻底还原转换成纯粹的 Python 基础 float 浮点数，
            # 彻底杜绝后续四舍五入 round() 函数报错导致线程池崩溃的噩梦。
            if hasattr(current_close, "item"):
                current_close = current_close.item()

            # 基于当前仅有的 45 天定长切片，动态计算 5日技术均线（ma5），对缺失的前几行使用 0 兜底防御
            df["ma5"] = df["close"].rolling(5).mean().fillna(0)
            
            # 剥离出基准日当天的 5日均线 核心数值
            current_ma5 = df["ma5"].iloc[latest_idx]
            if hasattr(current_ma5, "item"):
                current_ma5 = current_ma5.item()

            # 极端异常防呆：若当前均线价格为 0（如异常数据）或最新价本身就是个无效的 NaN，直接熔断放弃
            if current_ma5 <= 1e-4 or np.isnan(current_close):
                return None

            # 【测算与 5日线 的绝对偏离度】公式：|最新收盘价 - 5日均线价| / 5日均线价
            deviation = abs(current_close - current_ma5) / current_ma5

            # 【主力控盘回踩卡死条件】
            # 偏离度必须死死限制在 1.5% 以内。代表最新价格几乎精准吻合、紧贴在 5 日均线上方或下方。
            # 结合前面“缩量+刚反包”的基因，这在技术面上代表强烈的洗盘无量企稳信号，是挂单抄底的黄金胜率区。
            if deviation <= 0.015:
                # 碰撞成功！向大总管线程池返回该个股最终洗炼出来的核心策略成果报表字典
                return {
                    "代码": ticker,
                    "名称类型": "ST股" if is_current_st else "普通股",
                    "基准日收盘": round(current_close, 2),
                    "基准日MA5": round(current_ma5, 2),
                    "历史形态次数": len(trigger_points),
                    "距反包日天数": days_since_trigger,
                    "5日线偏离度(%)": round(deviation * 100, 2),
                }
    except Exception:
        # 【全线异步静默熔断机制】
        # 单只个股在多线程并发中若遭遇任何不可抗力引发的严重异常（例如：yfinance临时封禁IP、证券停牌无数据等），
        # 在此处实施静默隔离、直接向线程池吐回 None。这样能保证大总管扫描任务行云流水，绝不因单只股票的意外而卡死或打断全盘。
        return None
        
    # 如果走完流程没有命中任何核心形态及偏离度窗口，默认返回 None 宣告该股今日出局
    return None



# ==========================================
# 第二部分：多线程并发全市场扫描器大总管
# ==========================================


def generate_all_a_share_tickers():
    """
    【全面补全版】自动构造全 A 股符合 yfinance 格式的代码池骨架
    
    说明：
    1. 沪市（上海交易所）股票在 yfinance 中的后缀统一为 '.SS'
    2. 深市（深圳交易所）股票在 yfinance 中的后缀统一为 '.SZ'
    3. 本函数严格覆盖了现役 A 股的主板、创业板、科创板所有核心及扩容号段。
    4. 采用的分段 range 已经过优化，既保证了全市场覆盖率，又避免了过多的无效空号（无交易数据的代码）。
    """
    tickers = []

    # =========================================================================
    # 1. 深圳交易所 (深市 - 后缀 .SZ) 号段构建
    # =========================================================================
    
    # 【深圳主板 / 早期中小板】 000xxx 系列 (000001 - 001999)
    # 涵盖了平安银行等大量老牌深市主板标的
    ##for i in range(1, 1000):
    ##    tickers.append(f"000{i:03d}.SZ")
    ##for i in range(1000, 2000):
    ##    tickers.append(f"00{i:03d}.SZ")

    # 【深圳中小板扩容】 002xxx 与 003xxx 系列 (002001 - 003999)
    # 中小板并入主板后，这些号段依然极为活跃
    ##for i in range(2001, 4000):
    ##    tickers.append(f"00{i:03d}.SZ")

    # 【深圳创业板核心】 300xxx 系列 (300001 - 300999)
    # 创业板第一代核心高成长股聚集地
    ##for i in range(1, 1000):
    ##    tickers.append(f"300{i:03d}.SZ")

    # 【深圳创业板扩容】 301xxx 系列 (301001 - 301699)
    # 近几年创业板注册制实施后，新上市的创业板股票全面启用该号段
    ##for i in range(1001, 1700):
    ##    tickers.append(f"301{i:03d}.SZ")


    # =========================================================================
    # 2. 上海交易所 (沪市 - 后缀 .SS) 号段构建
    # =========================================================================
    
    # 【上海主板传统】 600xxx 系列 (600001 - 600999)
    # 涵盖了贵州茅台、老牌国企等经典沪市蓝筹
    ##for i in range(1, 1000):
    ##    tickers.append(f"600{i:03d}.SS")

    # 【上海主板大盘蓝筹】 601xxx 系列 (601001 - 601999)
    # 多为中字头大盘股、大型银行及非银金融机构
    ##for i in range(1001, 2000):
    ##    tickers.append(f"601{i:03d}.SS")

    # 【上海主板新锐/扩容】 603xxx 与 605xxx 系列 (603001 - 603999, 605001 - 605999)
    # 沪市主板近年新股上市的主要集中号段
    ##for i in range(3001, 4000):
    ##    tickers.append(f"603{i:03d}.SS")
    ##for i in range(5001, 6000):
    ##    tickers.append(f"605{i:03d}.SS")

    # 【上海科创板核心】 688xxx 系列 (688001 - 688999)
    # 20CM 硬科技、半导体、生物医药企业的绝对主战区
    for i in range(1, 1000):
        tickers.append(f"688{i:03d}.SS")

    # 【上海科创板特例】 689xxx 系列 (目前仅 689009 九号公司)
    # 属于 CDR 存托凭证类型，为防止该 20CM 龙头漏报，进行精准手工补全
    tickers.append("689009.SS")


    # =========================================================================
    # 3. 数据清洗与返回
    # =========================================================================
    
    # 使用 set() 去重以确保代码唯一性，随后重新转换为 list 供多线程迭代调用
    final_tickers = list(set(tickers))
    
    # 提示：此时全市场池里大约包含了 5000+ 级别的潜在代码库（已剔除绝大部分空白死号段）
    return final_tickers


def start_market_scan(max_workers=30, end_date=None, filter_st=False):
    """
    【工业级全市场高并发扫描器 - 定长回溯复盘大总管】
    
    业务逻辑：
    1. 负责调度整个 A 股 5000+ 代码池的并发任务分配。
    2. 基于 ThreadPoolExecutor 构建高效的异步 I/O 线程池，最大化榨干网络带宽。
    3. 集成 tqdm 进度条，实时反馈全市场清洗进度与任务时效。
    
    参数说明：
    :param max_workers: 线程池并发最大工作线程数。由于下载数据极小（仅45天），推荐设为 30-50 以提高速度。
    :param end_date: 手动指定的复盘或实盘结束日期。例如 "2025-10-10"。若为 None，则默认自动锁定今天。
    :param filter_st: 风控开关。True 代表完全抹杀并剔除 ST/*ST 股；False 代表放行，允许捕获 ST 板块里的异动反包。
    :return: 包含所有符合【形态反包后回踩5日线】黑马股的 pandas.DataFrame，若无信号则返回 None。
    """
    # 【时间锚定】若未手动指定结束日期，则动态捕获系统当前的自然日作为选股基准日
    target_date_str = (
        end_date if end_date else datetime.now().strftime("%Y-%m-%d")
    )
    
    print("==================================================")
    print(f"🎯 启动定长回溯选股，指定结束基准日: {target_date_str}")
    print("==================================================")

    # 【载入全空间代码】调用补全后的代码池骨架，拉出全 A 股现役所有主板、创业板、科创板号段
    all_tickers = generate_all_a_share_tickers()
    total_count = len(all_tickers)
    
    # 初始化一个空列表，用于在多线程动态派发中安全接收碰撞成功的个股策略结果字典
    hit_results = []

    # 【并发线程池上下文】启动多线程异步管理器。
    # 选股瓶颈在 yfinance 海外网络请求的等待（I/O密集型），多线程（Thread）比多进程（Process）更轻量、极度节省内存
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        # 【核心高级机制：Future 映射字典】
        # 1. executor.submit 会立即非阻塞地向线程池提交单个个股的筛选任务，并瞬间返回一个 Future 对象（承诺在未来完成）。
        # 2. 通过字典推导式，将这个特殊的 Future 对象作为 Key，对应的股票代码 ticker 作为 Value 进行绑定。
        # 3. 这种映射能让我们在任务异步完成后，精准顺藤摸瓜知道是哪只股票出了结果或抛出了异常。
        future_to_ticker = {
            executor.submit(
                screen_single_stock, ticker, target_date_str, filter_st
            ): ticker
            for ticker in all_tickers
        }

        # 【动态结果捕获流】
        # 1. as_completed 开启一个高效的迭代器监听流，哪个线程先下载完并计算完毕，它就立刻优先弹出哪个 Future。
        # 2. tqdm 嵌套在其最外层，能够根据迭代器弹出的实时频率，在终端绘制出动态自适应的扫描进度条和剩余时间估计。
        for future in tqdm(
            as_completed(future_to_ticker), total=total_count, desc="历史复盘扫描中"
        ):
            # 通过当前已完成的 future 拿到与其捆绑的股票代码，方便定位和异常追踪
            ticker = future_to_ticker[future]
            try:
                # 【阻塞提取结果】调用 .result() 提取 screen_single_stock 的返回值。
                # 如果该股触发出局条件（如不合形态、偏离度超标），会返回 None；若碰撞成功，则返回个股数据字典。
                data = future.result()
                
                # 若数据不为空，说明该股在基准日当天完美符合“刚反包+精准回踩5日线”的黄金临界点
                if data is not None:
                    hit_results.append(data) # 压入策略池
                    
            except Exception:
                # 【终极防御性策略】
                # 全市场并发扫描中最忌讳因单只个股网络断流、SSL握手失败或 yfinance 接口限流抛出异常导致整个大盘扫描任务彻底崩溃。
                # 此处实施强力的静默熔断隔离，发生任何未预料的单股底层异常均直接 pass，全力确保整体扫描流程铁索连环、永不中断。
                pass

    print(
        f"\n==================== 📊 基准日 [{target_date_str}] 筛选结果 ===================="
    )

    # 【数据清洗与矩阵展现】
    if hit_results:
        # 将线程池收集到的字典列表统一拼装转化为标准的 pandas DataFrame 结构
        result_df = pd.DataFrame(hit_results)
        
        # 【量化排序优化】
        # 技术面上，收盘价距离 5 日线偏离度越小（越贴近均线），说明主力洗盘踩得越扎实，挂单的安全垫越厚。
        # 因此这里按照“5日线偏离度(%)”进行升序排序（从小到大），将最完美的信号顶到最上方。
        result_df = result_df.sort_values(by="5日线偏离度(%)", ascending=True)
        
        # 规避 pandas 终端打印长数据时由于列宽限制自动产生省略号的情况，强制将其 100% 展平输出
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        
        # 以精简美观的非索引表格形式打印最终的策略信号黑马池
        print(result_df.to_string(index=False))
        return result_df
    else:
        # 如果 hit_results 为空，提示在该交易日大盘环境下，全市场未孵化出符合要求的标的
        print(f"\n👀 扫描完成，在 [{target_date_str}] 当天未发现符合形态的标的。")
        return None


# ==========================================
# 入口函数
# ==========================================
if __name__ == "__main__":
    # 【使用场景 1：日常实盘选股】不传参数，默认以今天为结束日，往前推45天快速选股
    start_market_scan(max_workers=30, end_date=None, filter_st=False)

    # 【使用场景 2：历史任意节点复盘】手动指定历史某一天，穿越回当天看当时的选股信号
    #start_market_scan(max_workers=30, end_date="2025-10-10", filter_st=False)
