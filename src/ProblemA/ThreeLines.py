# -*- coding: utf-8 -*-
"""
  @author DDullahan
  @date 2019-4-18 21:17
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
    # 设置参数：
    context.win = 61  # 计算所需总数据长度
    context.short = 5  # 短期均线参数
    context.middle = 20  # 中期均线参数
    context.long = 60  # 长期均线参数
    context.Tlen = len(context.target_list)  # 标的总数


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
    # 获取收盘价数据
    close = data.value.values.reshape(-1, context.win).astype(float)
    # 计算均线值：
    mashort = close[:, -context.short:].mean(axis=1)  # 短期均线
    mamiddle = close[:, -context.middle:].mean(axis=1)  # 中期均线
    malong = close[:, -context.long:].mean(axis=1)  # 长期均线

    if DEBUG:
        print('过去' + str(context.short) + '天因子均值:', mashort)
        print('过去' + str(context.middle) + '天因子均值:', mamiddle)
        print('过去' + str(context.long) + '天因子均值:', malong)

    target = np.array(range(context.Tlen))

    # 计算卖信号并卖出
    positions = context.account().positions['volume_long'].values
    sell_signal = np.logical_and(positions > 0, mashort < malong,
                                 mamiddle < malong)  # 有持仓的情况下，短期和中期均线都小于长期均线，卖出，等价于短期和中期均线上穿长期均线，买入；
    sell_signal = np.logical_not(sell_signal)
    target_sell = target[sell_signal].tolist()
    for targets in target_sell:
        order_target_volume(account_idx=0, target_idx=targets, target_volume=0, side=1,
                            order_type=2, price=0)

    # 计算买信号并均分资产买入
    positions = context.account().positions['volume_long'].values
    cash = context.account().cash['valid_cash'].values
    buy_signal = np.logical_and(cash > 0, mashort > malong,
                                mamiddle > malong)  # 有资金情况下，短期和中期均线都大于长期均线，买入，等价于短期和中期均线上穿长期均线，买入；
    buy_signal = np.logical_not(buy_signal)
    target_buy = target[buy_signal].tolist()
    for targets in target_buy:
        order_target_value(account_idx=0, target_idx=targets, target_value=1e6 / len(target_buy), side=1,
                           order_type=2, price=0)

    if DEBUG:
        print('买信号:', buy_signal)
        print('卖信号:', sell_signal)



