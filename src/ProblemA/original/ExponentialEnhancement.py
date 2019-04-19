# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     指数增强
   Description :
   Author :       haoyuan.m
   date：          2018/10/11
-------------------------------------------------
   Change Activity:
                   2018/10/11:
-------------------------------------------------
"""
__author__ = 'haoyuan.m'

from atrader import *
import numpy as np
import pandas as pd
import datetime as dt

'''
本策略以0.8为初始权重跟踪指数标的沪深300中权重大于0.35%的成份股.
个股所占的百分比为(0.8*成份股权重/所选股票占沪深300的总权重)*100%.然后根据个股是否
连续上涨5天;连续下跌5天
来判定个股是否为强势股/弱势股,并对其把权重由0.8调至1.0或0.6
回测数据为:HS300中权重大于0.35%的成份股
回测时间为:
'''


def init(context):
    set_backtest(initial_cash=10000000)
    reg_kdata('day', 1)
    context.ratio = 0.8
    context.cons_date = '2016-12-31'
    context.hs300 = get_code_list('hs300', context.cons_date)[['code', 'weight']]
    context.hs300 = context.hs300[context.hs300.weight > 0.35]
    context.sum_weight = context.hs300.weight.sum()
    print('选择的成分股权重总和为: ', context.sum_weight, '%')


def on_data(context):
    positions = context.account().positions['volume_long']
    #total_asset = context.account().cash['total_asset'].iloc[0]
    data = get_reg_kdata(reg_idx=context.reg_kdata[0], length=6, fill_up=True, df=True)
    if data['close'].isna().any():
        return
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        target_idx = target.target_idx.iloc[0]
        position = positions.iloc[target_idx]
        if position == 0:
            buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * context.ratio
            order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                               order_type=2, price=0)
            # print(context.now, context.target_list[target_idx], '以市价单开多仓至仓位:', buy_percent * 100, '%')
        else:
            # 获取过去5天的价格数据,若连续上涨则为强势股,权重+0.2;若连续下跌则为弱势股,权重-0.2
            recent_data = target['close'].tolist()
            if all(np.diff(recent_data) > 0):
                buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * (context.ratio + 0.2)
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                                     order_type=2, price=0)
                # print('强势股', context.target_list[target_idx], '以市价单调多仓至仓位:', buy_percent * 100, '%')
            elif all(np.diff(recent_data) < 0):
                buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * (context.ratio - 0.2)
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                                     order_type=2, price=0)
                # print('弱势股',  context.target_list[target_idx], '以市价单调空仓至仓位:', buy_percent * 100, '%')


if __name__ == '__main__':
    begin = '2017-01-01'
    end = '2018-01-01'
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    hs300 = get_code_list('hs300', cons_date)[['code', 'weight']]
    targetlist = hs300[hs300.weight > 0.35]['code']
    run_backtest(strategy_name='指数增强',
                 file_path='ExponentialEnhancement.py',
                 target_list=targetlist,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)
