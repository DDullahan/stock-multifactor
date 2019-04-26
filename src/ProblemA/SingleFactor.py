# -*- coding: utf-8 -*-
from time import sleep

from atrader import *
import numpy as np
import pandas as pd
import datetime as dt

factor = 'PE'
neg = 1


def init(context):
    # 注册初始资金1000万
    set_backtest(initial_cash=10000000)
    # 注册因子
    reg_factor(factor=factor)
    # 基准权重
    context.ratio = 0.8
    context.cons_date = '2016-12-31'
    context.hs300 = get_code_list('hs300', context.cons_date)[['code', 'weight']]
    context.hs300 = context.hs300[context.hs300.weight > 0.35]
    context.sum_weight = context.hs300.weight.sum()
    context.neg = neg
    # print('选择的成分股权重总和为: ', context.sum_weight, '%')


def on_data(context):
    # 获取持仓状况
    positions = context.account().positions['volume_long']
    # 获取最近6天的因子数据
    data = get_reg_factor(reg_idx=context.reg_factor[0], length=6, df=True)
    # 存在NaN则略过此次调仓
    if data['value'].isna().all() or data['date'].isna().any():
        # print('数据全部NaN或无对应日期的因子数据,跳过')
        return
    data = data.dropna()
    # 获取标的的索引集合
    datalist = [data[data['target_idx'] == x] for x in pd.unique(data.target_idx)]
    for target in datalist:
        # 枚举某一标的
        target_idx = target.target_idx.iloc[0]
        position = positions.iloc[target_idx]

        if position == 0:
            # 若目前对应标的无持股，买入
            buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * context.ratio
            order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                                 order_type=2, price=0)
            # print(context.now, context.target_list[target_idx], '以市价单开多仓至仓位:', buy_percent * 100, '%')
        else:
            # 获取过去5天的价格数据,若连续上涨则为强势股,权重+0.2;若连续下跌则为弱势股,权重-0.2
            recent_data = target['value'].tolist()
            if all(np.diff(recent_data) > 0):
                buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * (
                        context.ratio + context.neg * 0.2)
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                                     order_type=2, price=0)
                # print('强势股', context.target_list[target_idx], '以市价单调多仓至仓位:', buy_percent * 100, '%')
            elif all(np.diff(recent_data) < 0):
                buy_percent = context.hs300.iloc[target_idx]['weight'] / context.sum_weight * (
                        context.ratio - context.neg * 0.2)
                order_target_percent(account_idx=0, target_idx=target_idx, target_percent=buy_percent, side=1,
                                     order_type=2, price=0)
                # print('弱势股',  context.target_list[target_idx], '以市价单调空仓至仓位:', buy_percent * 100, '%')


def start_backtest(begin, end, added):
    # 获取成分大于0.35的股份代码
    cons_date = dt.datetime.strptime(begin, '%Y-%m-%d') - dt.timedelta(days=1)
    hs300 = get_code_list('hs300', cons_date)[['code', 'weight']]
    target_list = list(hs300[hs300.weight > 0.35]['code'])
    # 开始回测
    run_backtest(strategy_name=factor + '-' + added,
                 file_path='.',
                 target_list=target_list,
                 frequency='day',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)


if __name__ == '__main__':
    # 确定回测时间段
    begin = '2017-01-01'
    end = '2017-12-01'
    # 读取因子名，对其进行单因子回测
    start_backtest(begin, end, '正')
    # 获取回测报告数据

    print('所有因子回测结束')
