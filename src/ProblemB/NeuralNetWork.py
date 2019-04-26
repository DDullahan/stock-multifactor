# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from sklearn.neural_network import MLPClassifier
from atrader import *

# 注册多因子 association为1表示正相关 为-1表示负相关
back_test_factors = {
    'PE': {'association': 1},
    'PB': {'association': 1},
    'PS': {'association': 1},
    'NetWorkingCapital': {'association': -1},
    'NetDebt': {'association': -1},
    'NetIntExpense': {'association': -1}
}
# 注册多因子
factors = ['PE', 'PB', 'PS', 'NetWorkingCapital', 'NetDebt', 'NetIntExpense']

# 训练时间段
train_begin = '2016-09-01'
train_end = '2017-07-01'
# 训练数据滑动窗口长度
train_size = 20

# 测试时间段
test_begin = '2017-08-01'
test_end = '2017-12-01'
# 同时持有bucket个标的
bucket = 10
begin = '2016-01-01'
end = '2018-09-30'


def init(context):
    # 注册初始资金1000万
    set_backtest(initial_cash=10000000)
    # 注册因子
    factors_list = list(back_test_factors.keys())
    reg_factor(factor=factors_list)
    # 注册标的
    context.target_list = get_code_list('hs300')[['code']]
    context.target_list = list(context.target_list['code'])
    context.target_List = context.target_list[1:2]
    # 标准化预处理 获取因子最大值与最小值
    context.back_test_factors = back_test_factors
    for factor in context.back_test_factors.keys():
        factors_data = get_factor_by_factor(factor=factor, target_list=context.target_list, begin_date=begin,
                                            end_date=end)
        factors_data = factors_data.iloc[:, 1:].fillna(value=0)
        context.back_test_factors[factor]['min'] = factors_data.min().min()
        context.back_test_factors[factor]['max'] = factors_data.max().max()

    reg_kdata(frequency='month', fre_num=1)
    # 获取训练时间段内train_size长度的因子数据作为向量
    train_begin_date = datetime.strptime(train_begin, '%Y-%m-%d')
    train_end_date = datetime.strptime(train_end, '%Y-%m-%d')
    train_date_right = train_begin_date
    # 对每一个时间切片 将窗口因子的值的均值组成向量作为输入
    x_all = []
    y_all = []
    while train_date_right <= train_end_date:
        train_date_left = train_date_right - timedelta(days=train_size)
        for index in range(len(context.target_List)):
            target = context.target_List[index]
            next_date = train_date_right + timedelta(days=1)
            kdata = get_kdata(target_list=[target], frequency='day', fre_num=1, begin_date=next_date,
                              end_date=next_date, df=True)
            if kdata.size == 0:
                continue
            y_all.append((kdata['open'].values < kdata['close'].values)[0])
            factors_diff = []
            for factor in factors:
                factor_data = get_factor_by_factor(factor=factor, target_list=target,
                                                   begin_date=train_date_left, end_date=train_date_right)
                # 缺省值直接丢弃
                factor_data = factor_data.iloc[:, 1:].dropna()
                factor_data = factor_data.iloc[-1] - factor_data.iloc[0]
                # 单个因子差作为向量的一维
                factors_diff.append(factor_data.values[0])
            print(factors_diff)
            # 向量加入输入
            x_all.append(factors_diff)
        train_date_right = train_date_right + timedelta(days=1)
    print(x_all)
    print(y_all)
    # 训练
    context.clf = MLPClassifier(solver='sgd', activation='relu', alpha=1e-4, hidden_layer_sizes=(50, 50),
                                random_state=1, max_iter=100, verbose=10, learning_rate_init=.1)
    context.clf.fit(x_all, y_all)
    print('训练完成')
    context.price = [0 for index in range(len(context.target_List))]


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
    # 针对每一个标的 获取最近划窗长度的数据 并预测涨跌
    for index in range(len(context.target_List)):
        x = []
        factor_data = get_reg_factor(reg_idx=context.reg_factor[0], length=train_size,
                                     target_indices=index, df=True)
        factor_data = factor_data['value'].dropna().values
        if len(factor_data) <= 1:
            continue
        x.append(factor_data[-1] - factor_data[0])
        kdata = get_reg_kdata(reg_idx=context.reg_kdata[0], target_indices=index, df=True)
        # 对应股持仓 根据当前封盘价判断是否买入卖出
        ticket = context.account().position(target_idx=index)
        close = kdata['close'].values[0]
        if ticket is not None and close / context.price[index] >= 1.3:
            order_target_volume(account_idx=0, target_idx=index, target_volume=0, side=1,
                                order_type=2, price=0)
        cash = context.account().cash['valid_cash'].values
        # 若因子数据为空 跳过预测
        if len(x) != len(factors):
            continue
        else:
            features = np.array(x).reshape(1, -1)
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
    print('开始回测 回测因子:', list(back_test_factors.keys()))
    run_backtest(strategy_name='Multi Factor',
                 file_path='.',
                 target_list=target_list,
                 frequency='month',
                 fre_num=1,
                 begin_date=begin,
                 end_date=end,
                 fq=1)
    print('回测结束')
