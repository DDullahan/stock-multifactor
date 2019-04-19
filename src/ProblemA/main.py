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
    target = ['SSE.600000']
    begin = datetime.date(2017, 1, 1).isoformat()
    end = datetime.date(2018, 12, 1).isoformat()

    # 选用不同回测策略 调仓日期月末
    run_backtest(
        strategy_name='SingleFactor',
        file_path='ThreeLines.py',
        target_list=target,
        frequency='month',
        fre_num=1,
        begin_date=begin,
        end_date=end
    )
