# -*- coding: utf-8 -*-
"""
  @author DDullahan
  @date 2019-4-23 14:18
  @version 1.0
"""
from atrader import *
from sklearn import svm
from datetime import datetime, timedelta

# 注册多因子
factors = ['PE', 'PB']

# 训练时间段
train_begin = '2017-01-01'
train_end = '2017-12-01'
# 训练数据滑动窗口长度
train_size = 20

# 测试时间段
test_begin = '2018-01-01'
test_end = '2018-12-01'
# 持仓数量
bucket = 10


def init(context):
    # 初始资金1000万
    set_backtest(initial_cash=10000000)
    # 注册因子
    reg_factor(factor=factors)
    # 注册标的
    context.target_list = get_code_list('hs300')[['code']]
    context.target_list = list(context.target_list['code'])

    context.target_list = context.target_list[1:3]
    reg_kdata(frequency='month', fre_num=1)
    # 获取训练时间段内train_size长度的因子数据作为向量
    train_begin_date = datetime.strptime(train_begin, '%Y-%m-%d')
    train_end_date = datetime.strptime(train_end, '%Y-%m-%d')
    train_date_right = train_begin_date
    # 对每一个时间切片 将窗口因子的值的均值组成向量作为SVM的输入
    x_all = []
    y_all = []
    while train_date_right <= train_end_date:
        train_date_left = train_date_right - timedelta(days=train_size)
        for index in range(len(context.target_list)):
            target = context.target_list[index]
            kdata = get_kdata(target_list=[target], frequency='day', fre_num=1, begin_date=train_date_right,
                              end_date=train_date_right, df=True)
            if kdata.size == 0:
                # print('K线数据空 跳过')
                continue
            y_all.append((kdata['open'].values < kdata['close'].values)[0])
            factors_mean = []
            for factor in factors:
                factor_data = get_factor_by_factor(factor=factor, target_list=target,
                                                   begin_date=train_date_left, end_date=train_date_right)
                # 缺省值直接丢弃
                factor_data = factor_data.iloc[:, 1:].dropna()
                # 单个因子均值作为向量的一维
                factor_data = factor_data.mean().mean()
                factors_mean.append(factor_data)
            # print(factors_mean)
            # 向量加入输入
            x_all.append(factors_mean)
        train_date_right = train_date_right + timedelta(days=1)
    print(x_all)
    print(y_all)
    # 训练SVM
    context.clf = svm.SVC(C=1.0, kernel='rbf', degree=3, gamma='auto', coef0=0.0, shrinking=True, probability=False,
                          tol=0.001, cache_size=400, verbose=False, max_iter=-1,
                          decision_function_shape='ovr', random_state=None)
    context.clf.fit(x_all, y_all)
    print('训练完成')
    context.price = [0 for index in range(len(context.target_list))]


def on_data(context):
    print('回测日期', context.now)
    # 针对每一个标的 获取最近划窗长度的数据 并通过SVM预测涨跌
    for index in range(len(context.target_list)):
        factor_data = get_reg_factor(reg_idx=context.reg_factor[0], target_indices=index, df=True)
        factor_data = factor_data['value']
        kdata = get_reg_kdata(reg_idx=context.reg_kdata[0], target_indices=index, df=True)
        # 对应股持仓 根据当前封盘价判断是否买入卖出
        ticket = context.account().position(target_idx=index)
        close = kdata['close'].values
        close = close[0]
        if ticket is not None and (close / context.price[index] >= 1.3):
            print('卖出')
            order_target_volume(account_idx=0, target_idx=index, target_volume=0, side=1,
                                order_type=2, price=0)
        target = context.target_list[index]
        cash = context.account().cash['valid_cash'].values
        # 若因子数据为空 跳过预测
        if factor_data.isna().any() or factor_data.isnull().any():
            print('因子数据为空 取消预测')
            continue
        else:
            factor_data = factor_data.values
            features = np.array(factor_data).reshape(1, -1)
            prediction = context.clf.predict(features)[0]
            print('预测结果', prediction)
            # 预测上涨则买入
            if prediction:
                order_target_value(account_idx=0, target_idx=index, target_value=cash / bucket, side=1,
                                   order_type=2, price=0)
                context.price[index] = close


if __name__ == '__main__':
    target_list = get_code_list('hs300')[['code']]
    target_list = list(target_list['code'])
    run_backtest(strategy_name='SVM',
                 file_path='.',
                 target_list=target_list,
                 frequency='day',
                 fre_num=1,
                 begin_date=test_begin,
                 end_date=test_end,
                 fq=1)
