
import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')
sys.path.insert(0, '.')
import pandas, numpy, time
import supertrend_bot
# pandas.set_option('display.max_rows', None)



class ResultRecorder:
    def __init__(self):
        self.profit_and_loss_dict = {'profit': [], 'loss': []}
        # self.columns=['coinpair', 'length_in_days', 'balance', 'config_length', 'config_multiplier', 
        #                     'no_of_orders', 'profit_order', 'average_profit', 'loss_order', 'average_loss']
        self.results = pandas.DataFrame()
        self.order_number = 0
        self.marking_timestamp = int(time.time()%1000)

    def add_profit_loss(self, amount):
        if amount <= 0: self.profit_and_loss_dict['loss'].append(amount)
        if amount > 0:  self.profit_and_loss_dict['profit'].append(amount)
        self.order_number += 1

    def add_new_row(self, row_data):
        self.results = pandas.concat([self.results, pandas.DataFrame([row_data])])

    def save_in_csv(self, name=None):
        if name == None: 
            name = f"sandbox/individual_backtest/backtest_summary_{self.marking_timestamp}.csv"
        self.results.to_csv(name, index=False, index_label=False)

    def get_profit_order_number(self):
        return len(self.profit_and_loss_dict['profit'])
    def get_profit_order(self):
        return self.profit_and_loss_dict['profit']
    def get_average_profit(self):
        return numpy.mean(self.profit_and_loss_dict['profit'])

    def get_loss_order(self):
        return self.profit_and_loss_dict['loss']
    def get_loss_order_number(self):
        return len(self.profit_and_loss_dict['loss'])
    def get_average_loss(self):
        return numpy.average(self.profit_and_loss_dict['loss'])

    def reset(self):
        self.profit_and_loss_dict = {'profit': [], 'loss': []}
        self.order_number = 0


def backtest(length, multiplier, result_recorder, df=None, coin=None, timeframe=None):
    # Define config for bot
    bot = supertrend_bot.SupertrendBot(
                    account='',
                    coinpair='',
                    trade_log_path='log/trade_log_test.txt',
                    length = length, multiplier = multiplier)
    
    # Get dataframe if not passed
    if len(df) == 0:
        df = pandas.read_csv(f"sandbox/historical_data/{coin}_{timeframe}_original.csv")
        df['timestamp'] = df['time_period_start']
        df['open'] = df['price_open']
        df['high'] = df['price_high']
        df['low'] = df['price_low']
        df['close'] = df['price_close']
        df.drop(['time_period_start', 'time_open', 
                'price_open', 'price_high', 'price_low', 
                'price_close', 'volume_traded', 'trades_count'], axis=1)
        df = df.iloc[::-1].reset_index()
        print('length_of_df =', len(df), end=' ')
    
    # Format data with supertrend signals
    supertrend_data = bot.supertrend_format(df)

    is_in_position = False
    position = 0
    lot = 100
    balance = 0
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

                result_recorder.add_profit_loss(pnl - fee*lot)

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

def main():
    trend = '_bear'
    coins = ('btc', 'doge', 'eth', 'matic')
    timeframes = ('1h', '4h');  length_in_days = (1/24, 1/6)
    config_lengths = numpy.arange(4, 28, 1)
    config_multipliers = numpy.arange(5, 30, 0.5)

    trend = ''

    for coin in coins:
        print('='*50)
        backtest(coin, timeframes, length_in_days, config_lengths, config_multipliers, 
                    trend=trend,
                    savefilename=None)

        for timeframe, length_in_day in zip(timeframes, length_in_days):
            print(f'coin = {coin}, timeframe = {timeframe}')
            df = pandas.read_csv(f"sandbox/historical_data/{coin}_{timeframe}_original{trend}.csv")

            # Rename columns and drop some to reduce memory weight
            df['timestamp'] = df['time_period_start']
            df['open'] = df['price_open']
            df['high'] = df['price_high']
            df['low'] = df['price_low']
            df['close'] = df['price_close']
            df.drop(['time_period_start', 'time_open', 
                    'price_open', 'price_high', 'price_low', 
                    'price_close', 'volume_traded', 'trades_count'], axis=1)
            df = df.iloc[::-1].reset_index()
            print('length_of_df =', len(df), end=' ')

            for length in config_lengths:
                for multiplier in config_multipliers:
                    print(f'length = {length}, multiplier = {multiplier}')

                    supertrend_data, balance = backtest(length, multiplier, result_recorder, df=df)
                    
                    result_recorder.add_new_row({
                        'coinpair': coin,
                        'length_in_days': length_in_day*len(supertrend_data), 
                        'balance': balance, 
                        'config_length': length, 
                        'config_multiplier': multiplier, 
                        'no_of_orders': result_recorder.order_number, 
                        'number_of_profit_order': result_recorder.get_profit_order_number(), 
                        'average_profit': result_recorder.get_average_profit(), 
                        'number_of_loss_order': result_recorder.get_loss_order_number(), 
                        'average_loss': result_recorder.get_average_loss(),
                        'avarage_pnl_per_month': balance / (length_in_day*len(supertrend_data)) * 30,
                        'profit_amounts': f"\"{result_recorder.get_profit_order()}\"",
                        'loss_amounts': f"\"{result_recorder.get_loss_order()}\"",
                    })

                    ## Save trade history for each configuration of each coin and timeframe combination
                    result_recorder.save_in_csv()
                    result_recorder.reset()
                print()

# main()



