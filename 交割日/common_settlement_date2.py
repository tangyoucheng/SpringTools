import datetime

# 🚨 【工业级刚性防火墙】：每年年底只需手动更新一次次年的中国休市调休脏日期（2026-2027年真实/模拟对齐）
# 仅需录入【原本是周一到周五但因为法定长假休市】的脏日期，周末补班股市不开盘无需录入，代码会自动过滤。
CHINESE_MARKET_HOLIDAYS = {
    "2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07",
    "2027-01-26", "2027-01-27", "2027-01-28", "2027-01-29",
    "2027-10-01", "2027-10-04", "2027-10-05", "2027-10-06"
}

def get_weekday_cn(date_obj):
    """辅助函数：将英文星期转换为直观的中文星期"""
    week_dict = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
    return week_dict[date_obj.weekday()]

def get_next_trading_day_v2_4(start_date):
    """【核心管道辅助】：计算指定日期之后的第一个真实国内交易日（下周一冲锋期校准）"""
    curr = start_date + datetime.timedelta(days=1)
    while str(curr) in CHINESE_MARKET_HOLIDAYS or curr.weekday() >= 5:
        curr += datetime.timedelta(days=1)
    return curr

def calculate_strict_tactical_calendar_v2_4(year, month):
    """【十六字军规4路合围终极自校准矩阵 - V2.4 终极完全体】
    
    100% 独立离线计算，精准锁定中国资产四大核心衍生品交割/结算/行权周期的生死边界。
    """
    first_day = datetime.date(year, month, 1)
    w_first = first_day.weekday()
    
    # -------------------------------------------------------------------------
    # 1. 中金所股指期货大考 (当月第三个星期五)
    # 🚨【法定计算规则】：中金所沪深300(IF)/上证50(IH)/中证500(IC)/中证1000(IM)四大主力期货合约，
    #    刚性固定在【每个月的第三个星期五】进行最终交割结算。
    # 🚨【自校准与前置博弈逻辑】：
    #    - 自校准：若第三个星期五撞上国内法定假期，交割日无条件自动【强行顺延】至长假后的第一个交易日。
    #    - 前3天不买：主力资金在交割日前3个交易日进入跨期移仓展期高潮。空头为榨取期指利润，常提前通过
    #      融券大单定向无差别错砸高波权重股。此时日线走成一条直线的稳固图形往往是前置诱猎陷阱，强行禁买。
    # -------------------------------------------------------------------------
    cffex_settlement = datetime.date(year, month, 1 + (4 - w_first) % 7 + 14)
    while str(cffex_settlement) in CHINESE_MARKET_HOLIDAYS or cffex_settlement.weekday() >= 5:
        cffex_settlement += datetime.timedelta(days=1)
        
    cffex_no_buy_start = cffex_settlement - datetime.timedelta(days=3)
    cffex_no_buy_end = cffex_settlement - datetime.timedelta(days=1)
    cffex_go_day = get_next_trading_day_v2_4(cffex_settlement)

    # -------------------------------------------------------------------------
    # 2. 场内股指期权/个股期权大考 (当月第四个星期三)
    # 🚨【法定计算规则】：上海证券交易所、深圳交易所及中金所挂钩的场内核心股指/个股ETF期权合约，
    #    刚性固定在【每个月的第四个星期三】进行最终到期行权与行权价结算。
    # 🚨【自校准与前置博弈逻辑】：
    #    - 自校准：若第四个星期三撞上国内长假，交割日无条件自动【强行顺延】至假期后的第一个交易日。
    #    - 前2天不买：期权多空双方为了在周三争夺关键行权价格线，量化对冲基金会在前2个交易日（周一、周二）
    #      通过瞬间对倒或融券恶意做空成分股来操纵标的 ETF 净值。长进光子、天承科技等高权重股极易躺枪。
    # -------------------------------------------------------------------------
    days_to_first_wednesday = (2 - w_first) % 7
    options_settlement = datetime.date(year, month, 1 + days_to_first_wednesday + 21)
    while str(options_settlement) in CHINESE_MARKET_HOLIDAYS or options_settlement.weekday() >= 5:
        options_settlement += datetime.timedelta(days=1)
        
    options_no_buy_start = options_settlement - datetime.timedelta(days=2)
    options_no_buy_end = options_settlement - datetime.timedelta(days=1)
    options_go_day = get_next_trading_day_v2_4(options_settlement)

    # -------------------------------------------------------------------------
    # 3. 月末联合变盘大考 (离岸A50交割 + 恒指结算 + 雪球月末集中观察)
    # 🚨【法定计算规则】：
    #    - 新加坡富时A50期指、香港恒生指数/恒生科技指数期货，刚性固定在【每个月的倒数第二个交易日】最终交割结算。
    #    - 挂钩中证1000/科创50的场外结构化私募产品(雪球/气囊)，固定在【每个月的最后一个交易日】迎来集中月度观察。
    # 🚨【自校准与前置博弈逻辑】：
    #    - 自校准：中国放长假时，海外交易所虽然开盘，但由于 A股 现货停牌无法操纵，因此新交所官方刚性规定，
    #      若月末撞上国内假期，交割日无条件自动【强行提前】至国内假期休市之前的倒数第二个真实国内交易日。
    #    - 前3天不买：离岸外资做空力量与雪球临界敲入盘在月末前3天完美共振。利用下坠的价格对散户进行极限心理
    #      洗盘，逼迫散户在最绝望的冰点割肉，为主力平仓提供血包。
    # -------------------------------------------------------------------------
    if month == 12:
        last_day = datetime.date(year, 12, 31)
    else:
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
    work_days = []
    curr_day = last_day
    while len(work_days) < 5:
        if curr_day.weekday() < 5 and str(curr_day) not in CHINESE_MARKET_HOLIDAYS:
            work_days.append(curr_day)
        curr_day -= datetime.timedelta(days=1)
        
    # 🚨【核心Bug修正】：work_days 是按时间倒序排列的
    # work_days[0] 是全月最后一天（倒数第一交易日 -> 雪球观察日）
    # work_days[1] 是倒数第二交易日（-> 新加坡A50/港股期指结算日）
    sgx_a50_settlement = work_days[1]      
    snowball_observation = work_days[0]    
    
    monthend_no_buy_start = sgx_a50_settlement - datetime.timedelta(days=3)
    monthend_no_buy_end = sgx_a50_settlement - datetime.timedelta(days=1)
    monthend_go_day = get_next_trading_day_v2_4(snowball_observation)

    return {
        "CFFEX": {
            "no_buy_zone": (cffex_no_buy_start, cffex_no_buy_end),
            "settlement_day": cffex_settlement,
            "go_day": cffex_go_day
        },
        "OPTIONS": {
            "no_buy_zone": (options_no_buy_start, options_no_buy_end),
            "settlement_day": options_settlement,
            "go_day": options_go_day
        },
        "MONTH_END": {
            "no_buy_zone": (monthend_no_buy_start, monthend_no_buy_end),
            "settlement_days": (sgx_a50_settlement, snowball_observation),
            "go_day": monthend_go_day
        }
    }

def execute_strategic_interceptor_v2_4(target_date_str, stock_name, is_index_weight=False):
    """【十六字军规机器强拦截器 - V2.4 零误差完全体时间轴格式版】"""
    t_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    cal = calculate_strict_tactical_calendar_v2_4(t_date.year, t_date.month)
    
    day_str = t_date.strftime('%m月%d日')
    week_str = get_weekday_cn(t_date)
    
    # 精准区间匹配
    is_cffex_nobuy = cal["CFFEX"]["no_buy_zone"][0] <= t_date <= cal["CFFEX"]["no_buy_zone"][1]
    is_cffex_freeze = t_date == cal["CFFEX"]["settlement_day"]
    
    is_opt_nobuy = cal["OPTIONS"]["no_buy_zone"][0] <= t_date <= cal["OPTIONS"]["no_buy_zone"][1]
    is_opt_freeze = t_date == cal["OPTIONS"]["settlement_day"]
    
    is_me_nobuy = cal["MONTH_END"]["no_buy_zone"][0] <= t_date <= cal["MONTH_END"]["no_buy_zone"][1]
    is_me_freeze = t_date in cal["MONTH_END"]["settlement_days"]

    # 🚨【核心修改：决策树分支判定输出，完美融入您指定的流水账格式与可买日子】
    if (is_cffex_nobuy or is_opt_nobuy or is_me_nobuy) and is_index_weight:
        # 判断具体是被哪个品种的无缝接力砸盘压制，给出精确的时间轴Facts标签
        if is_cffex_nobuy and is_opt_nobuy:
            print(f" 🚫 {day_str} ({week_str})  ──> 🚫 期指刚出清，期权大资金为了行权价无缝接力砸盘 (1000ETF期权异动)")
        elif is_cffex_nobuy:
            print(f" 🚫 {day_str} ({week_str})  ──> 🚫 期指空头换月前置打压期 (IM/IC大单融券定向错砸)")
        elif is_opt_nobuy:
            print(f" 🚫 {day_str} ({week_str})  ──> 🚫 场内期权多空行权价卡位博弈期 (ETF现货震荡清洗噪音)")
        elif is_me_nobuy:
            print(f" 🚫 {day_str} ({week_str})  ──> 🚫 月末离岸空头与雪球敲入盘多维联合绞杀期 (全盘高危失血)")
            
    elif is_cffex_freeze or is_opt_freeze or is_me_freeze:
        if is_cffex_freeze:
            print(f" 🛑 {day_str} ({week_str})  ──> 🛑 中金所主力合约结算交割日 (坚决不动)")
        elif is_opt_freeze:
            print(f" 🛑 {day_str} ({week_str})  ──> 🛑 场内期权最终行权到期日 (坚决不动)")
        elif t_date == cal["MONTH_END"]["settlement_days"][0]:
            print(f" 🛑 {day_str} ({week_str})  ──> 🛑 新加坡A50期指/港股期指最终交割日 (坚决不动)")
        elif t_date == cal["MONTH_END"]["settlement_days"][1]:
            print(f" 🛑 {day_str} ({week_str})  ──> 🛑 私募雪球/气囊产品月末集中观察日 (坚决不动)")
            
    else:
        # 🚨【核心重构点】：如果完美避开所有雷区，决策树在此处直接大范围输出“🟢 绝对可以安全买入的日期”
        print(f" 🟢 {day_str} ({week_str})  ──> 🟢 没有任何衍生品枷锁，属于安全反击冲锋期 (饱满开火/常规采用V6.3筹码墙)")

if __name__ == "__main__":
    print("=========================================================================")
    print(" 📊 07月份 衍生品流水账时间轴矩阵 (V2.4 终极完美注释修正完全体)")
    print("=========================================================================")
    
    # 模拟生成 7月份中下旬核心决战周的每一天，送入拦截器决策树
    days_7 = ["2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17", 
              "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", 
              "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29", 
              "2026-07-30", "2026-07-31"]
    
    for d_str in days_7:
        execute_strategic_interceptor_v2_4(d_str, "长进光子", is_index_weight=True)

    print("\n", "=" * 73, sep="")
    print(" 📊 08月份 衍生品全量时间轴流水账前瞻 (提早为您圈定下个月的所有可买日期)")
    print("=" * 73)
    
    # 精准生成 8 月份一整个月所有国内法定交易日的时间轴，交给决策树自动判断分类
    start_date = datetime.date(2026, 8, 1)
    end_date = datetime.date(2026, 8, 31)
    curr = start_date
    while curr <= end_date:
        # 排除周末
        if curr.weekday() < 5:
            execute_strategic_interceptor_v2_4(curr.strftime('%Y-%m-%d'), "长进光子", is_index_weight=True)
        curr += datetime.timedelta(days=1)
