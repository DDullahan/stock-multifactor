# -*- coding: utf-8 -*-
"""
  @author DDullahan
  @date 2019-4-18 09:35
  @version 1.0
"""

from atrader import *
import numpy as np

DEBUG = True


def init(context):
    # 注册初始资金1000万,股票手续费千分之3
    set_backtest(initial_cash=10000000, stock_cost_fee=30)
    # 注册因子
    reg_factor(factor=['PE'])
    # 设置参数
    context.win = 41  # 计算所需数据总长度
    context.long_win = 40  # 长周期窗口长度
    context.short_win = 10  # 短周期窗口长度
    context.Tlen = len(context.target_list)  # 标的长度


def on_data(context):
    # 获取win窗口长度因子数据
    data = get_reg_factor(reg_idx=context.reg_factor[0], length=context.win, df=True)

    if DEBUG:
        print('过去' + str(context.win) + '天因子数据:')
        print(data)

    # 如果因子结果出现NaN 结束预测
    if data['value'].isna().any():
        if DEBUG:
            print('数据存在NaN')
        return
    close = data.value.values.reshape(-1, context.win).astype(float)

    # 获取过去因子均值
    mashort = close[:, -context.short_win:].mean(axis=1)
    malong = close[:, -context.long_win:].mean(axis=1)

    if DEBUG:
        print('过去' + str(context.short_win) + '天因子均值:', mashort)
        print('过去' + str(context.long_win) + '天因子均值:', malong)

    # 根据均值获取买卖信号
    target = np.array(range(context.Tlen))

    # 计算卖信号并卖出
    positions = context.account().positions['volume_long'].values
    sell_signal = np.logical_and(positions > 0, mashort < malong)  # 有持仓 短期均值小于长期均值卖出
    target_sell = target[sell_signal].tolist()
    for targets in target_sell:
        order_target_volume(account_idx=0, target_idx=targets, target_volume=0, side=1,
                            order_type=2, price=0)

    # 计算买信号并均分资产买入
    positions = context.account().positions['volume_long'].values
    cash = context.account().cash['valid_cash'].values
    buy_signal = np.logical_and(cash > 0, mashort > malong)  # 有余款 短期均值大于长期均值则买入
    target_buy = target[buy_signal].tolist()
    for targets in target_buy:
        order_target_value(account_idx=0, target_idx=targets, target_value=cash / len(target_buy), side=1,
                           order_type=2, price=0)

    if DEBUG:
        print('买信号:', buy_signal)
        print('卖信号:', sell_signal)
