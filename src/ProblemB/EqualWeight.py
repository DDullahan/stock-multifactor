# -*- coding: utf-8 -*-
"""
  @author DDullahan
  @date 2019-4-21 20:31
  @version 1.0
"""
from atrader import *

# 注册多因子 association为1表示正相关 为-1表示负相关
back_test_factors = {
    'PE': {'association': 1},
    'PB': {'association': 1}
}

# 同时持有bucket个标的
bucket = 10
begin = '2017-01-01'
end = '2018-12-01'


def init(context):
    # 注册初始资金1000万
    set_backtest(initial_cash=10000000)
    # 注册因子
    factors_list = list(back_test_factors.keys())
    reg_factor(factor=factors_list)
    # 注册标的
    context.target_list = get_code_list('hs300')[['code']]
    context.target_list = list(context.target_list['code'])
    # 标准化预处理 获取因子最大值与最小值
    context.back_test_factors = back_test_factors
    for factor in context.back_test_factors.keys():
        factors_data = get_factor_by_factor(factor=factor, target_list=context.target_list, begin_date=begin,
                                            end_date=end)
        factors_data = factors_data.iloc[:, 1:].fillna(value=0)
        context.back_test_factors[factor]['min'] = factors_data.min().min()
        context.back_test_factors[factor]['max'] = factors_data.max().max()


def on_data(context):
    # 初始化权重数组
    weight = [{'value': 0, 'target_idx': i} for i in range(len(context.target_list))]
    factors_data = get_reg_factor(reg_idx=context.reg_factor[0], df=True).fillna(value=0)
    # 计算各标的的权重和
    for index in range(len(factors_data)):
        target_idx = factors_data.iloc[index]['target_idx']
        factor = factors_data.iloc[index]['factor']
        value = factors_data.iloc[index]['value']
        min = context.back_test_factors[factor]['min']
        max = context.back_test_factors[factor]['max']
        association = context.back_test_factors[factor]['association']
        weight[target_idx]['value'] = weight[target_idx]['value'] + association * (value - min) / (max - min)
    # 对权重排序
    weight.sort(key=lambda obj: obj['value'], reverse=True)
    # 取出前bucket个标的号
    stock = []
    for index in range(bucket):
        stock.append(weight[index]['target_idx'])
    cash = context.account().cash['valid_cash'].values
    for target in range(len(context.target_list)):
        # 不在目标股时 直接卖出
        if context.account().position(target_idx=target) is not None and target not in stock:
            order_target_volume(account_idx=0, target_idx=target, target_volume=0, side=1,
                                order_type=2, price=0)
        # 在目标股直接买入
        if target in stock:
            order_target_value(account_idx=0, target_idx=target, target_value=cash / bucket, side=1,
                               order_type=2, price=0)


if __name__ == '__main__':
    target_list = get_code_list('hs300')[['code']]
    target_list = list(target_list['code'])
    print('开始回测 回测因子:', list(back_test_factors.keys()))
    run_backtest(strategy_name='EqualWeight',
                 file_path='.',
                 target_list=target_list,
                 frequency='month',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)
    print('回测结束')
