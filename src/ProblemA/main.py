# -*- coding: utf-8 -*-
"""
  @author DDullahan
  @date 2019-4-18 09:35
  @version 1.0
"""

from atrader import *
import datetime

# 回测入口
if __name__ == '__main__':
    # 确定回测时间段
    begin = datetime.date(2017, 3, 1).isoformat()
    end = datetime.date(2017, 12, 1).isoformat()

    # 获取hs300的标的
    targets = get_code_list('hs300')
    targets = list(targets['code'])
    # 清除因子含有NaN的标的
    for target in targets:
        data = get_factor_by_code(factor_list=['PE'], target=target, begin_date=begin, end_date=end)
        if data['PE'].isna().any():
            print('出现NaN 删除标的:', target)
            targets.remove(target)
    # 选用不同回测策略 调仓日期月末
    run_backtest(
        strategy_name='SingleFactor',
        file_path='ThreeLines.py',
        target_list=targets,
        frequency='day',
        fre_num=1,
        begin_date=begin,
        end_date=end
    )
