
import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')
import pandas, numpy
import supertrend_bot
# pandas.set_option('display.max_rows', None)





# BACKTEST
class ResultRecorder:
    def __init__(self):
        self.profit_and_loss_dict = {'profit': [], 'loss': []}
        # self.columns=['coinpair', 'length_in_days', 'balance', 'config_length', 'config_multiplier', 
        #                     'no_of_orders', 'profit_order', 'average_profit', 'loss_order', 'average_loss']
        self.results = pandas.DataFrame()

    def add_profit_loss(self, amount):
        if amount <= 0: self.profit_and_loss_dict['loss'].append(amount)
        if amount > 0:  self.profit_and_loss_dict['profit'].append(amount)

    def add_new_row(self, row_data):
        self.results = pandas.concat([self.results, pandas.DataFrame([row_data])])

    def save_in_csv(self, name='results_summary'):
        self.results.to_csv(f"sandbox/backtest_result/{name}.csv", index=False, index_label=False)


def run_back_test(coin, length, multiplier):
    # Define config for bot
    bot = supertrend_bot.SupertrendBot(
                    account='',
                    coinpair='',
                    trade_log_path='log/trade_log_test.txt',
                    length = length, multiplier = multiplier)
    print('\n'+'='*50)
    # Format data with supertrend signals
    df = pandas.read_csv(f"sandbox/historical_data/{coin}_{timeframe}_original.csv")
    
    df['timestamp'] = df['time_period_start']
    df['open'] = df['price_open']
    df['high'] = df['price_high']
    df['low'] = df['price_low']
    df['close'] = df['price_close']
    df.drop(['time_period_start', 'time_open', 
            'price_open', 'price_high', 'price_low', 
            'price_close', 'volume_traded', 'trades_count'], axis=1)
    df = df.iloc[:1000:-1].reset_index()
    supertrend_data = bot.supertrend_format(df)


    is_in_position = False
    position = 0
    lot = 100
    balance = 1000
    fee = 0.005

    for i in range(1,len(df.index)):
        current, previous = i, i-1
        
        # BUY
        if not supertrend_data.loc[previous,'is_uptrend'] and supertrend_data.loc[current,'is_uptrend']:
            if not is_in_position:
                position = lot / supertrend_data.loc[current,'close']
                is_in_position = True
                buy_price = supertrend_data.loc[current,'close']
                supertrend_data.loc[current,'order'] = 'buy'
                supertrend_data.loc[current,'position'] = position
                supertrend_data.loc[current,'price'] = buy_price
            else:
                supertrend_data.loc[current,'order'] = 'buy_but_already_in_position'
                supertrend_data.loc[current,'position'] = ''
        # SELL
        elif supertrend_data.loc[previous,'is_uptrend'] and not supertrend_data.loc[current,'is_uptrend']:
            if is_in_position:
                is_in_position = False
                sell_price = supertrend_data.loc[current,'close']
                pnl = (sell_price - buy_price) * position
                balance = balance + pnl - fee*lot

                result_recorder.add_profit_loss(pnl)

                supertrend_data.loc[current,'order'] = 'sell'
                supertrend_data.loc[current,'position'] = position
                supertrend_data.loc[current,'price'] = sell_price
                supertrend_data.loc[current,'pnl'] = pnl
                supertrend_data.loc[current,'balance'] = balance
                position = 0
            else:
                supertrend_data.loc[current,'order'] = 'sell_but_not_in_position'
        # NO SIGNAL
        # else:
        #     supertrend_data.loc[current,'order'] = ''
    return supertrend_data, balance



result_recorder = ResultRecorder()
coins = ('matic',)
timeframes = ('15m', '1h', '4h');  length_in_days = (1/24/4, 1/24, 1/6)
config_lengths = numpy.arange(2, 19, 1)  # [i for i in range(2, 15.25, 0.25)]
config_multipliers = numpy.arange(1, 10.25, 0.25)  # [i for i in range(1, 10.25, 0.25)]

for coin in coins:
    print('coin =', coin)
    for length in config_lengths:
        print('length =', length, end='  ')
        for multiplier in config_multipliers:
            print('multiplier =', multiplier, end=' ')
            for timeframe, length_in_day in zip(timeframes, length_in_days):

                supertrend_data, balance = run_back_test(coin, length, multiplier)
                
                result_recorder.add_new_row({
                    'coinpair': coin,
                    'length_in_days': length_in_day*len(supertrend_data), 
                    'balance': balance, 
                    'config_length': length, 
                    'config_multiplier': multiplier, 
                    'no_of_orders': 0, 
                    'profit_order': 0, 
                    'average_profit': 0, 
                    'loss_order': 0, 
                    'average_loss': 0
                })
                result_recorder.save_in_csv()
                # supertrend_data.to_csv(f"sandbox/backtest_result/{coin}_{timeframe}.csv", index=False, index_label=False)

# TODO
# trade_log function: log or not
# list config with greatest profit from top down











