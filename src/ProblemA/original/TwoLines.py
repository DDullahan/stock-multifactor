# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     简单双均线V
   Description :
   Author :       haoyuan.m
   date：          2018/10/26
-------------------------------------------------
   Change Activity:
                   2018/10/26:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'

from atrader import *
import numpy as np


# %%
def init(context):
    set_backtest(initial_cash=1e6)
    reg_kdata('day', 1)
    # reg_userindi(indi_func=gen_signal)
    context.win = 21
    context.long_win = 20
    context.short_win = 5
    context.Tlen = len(context.target_list)


def on_data(context):
    positions = context.account().positions['volume_long'].values
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=context.win, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    close = data.close.values.reshape(-1, context.win).astype(float)
    mashort = close[:, -context.short_win:].mean(axis=1)
    malong = close[:, -context.long_win:].mean(axis=1)
    target = np.array(range(context.Tlen))
    long = np.logical_and(positions == 0, mashort > malong)
    short = np.logical_and(positions > 0, mashort < malong)
    target_long = target[long].tolist()
    target_short = target[short].tolist()
    for targets in target_long:
        order_target_value(account_idx=0, target_idx=targets, target_value=1e6/len(target_long), side=1,
            order_type=2, price=0)
    for targets in target_short:
        order_target_volume(account_idx=0, target_idx=targets, target_volume=0, side=1,
                        order_type=2, price=0)
if __name__ == '__main__':
    run_backtest(strategy_name='SMA', file_path='TwoLines.py', target_list=get_code_list('hs300')['code'],
                 frequency='day', fre_num=1, begin_date='2017-09-01', end_date='2018-03-01', fq=1)


