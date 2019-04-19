# -*- coding: utf-8 -*-
from atrader import *


def init(context: 'ContextBackReal'):
	"""用户初始化函数"""
	# TODO 写您的初始化操作
	set_backtest(initial_cash=10000000.000000, stock_cost_fee=30)
	reg_factor(['PB'])
	context.Tlen = len(context.target_list)
	pass


def on_data(context: 'ContextBackReal'):
	"""刷新bar函数"""
	position = context.account().positions['volume_long'].values
	factor1 = get_reg_factor(reg_idx=context.reg_factor[0], target_indices=[], length=1, df=1)
	target = np.array(range(context.Tlen))
	factor = factor1['value'].values
	print(factor)
	buy_signal = np.logical_and(position == 0, factor <1).tolist()
	target_buy = target[buy_signal].tolist()
	sell_signal = np.array(factor >1)
	target_sell = target[sell_signal].tolist()
	cash = context.account(account_idx=0).cash
	# print(get_performance(strategy_id))
	# print(target_sell)
	# print(cash.valid_cash.values)
	for targets in target_buy:
		order_target_value(account_idx=0, target_idx=targets, side=1, target_value=cash.valid_cash.values / len(target_buy),
						   price=0, order_type=2)
	for targets in target_sell:
		order_target_volume(account_idx=0, target_idx=targets, target_volume=0, side=1,
							order_type=2, price=0)

	# TODO 写 bar 逻辑函数
	pass


import datetime as dt

if __name__ == '__main__':
	begin = '2016-01-01'
	end = '2016-12-31'
	run_backtest(strategy_name='PB',
				 file_path='.',
				 frequency='month',
				 fre_num=1,
				 target_list=get_code_list('zz500')['code'],
				 begin_date=begin,
				 end_date=end)
