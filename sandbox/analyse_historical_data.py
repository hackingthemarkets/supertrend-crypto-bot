from distutils.command.install_egg_info import safe_name
import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')
import pandas
import supertrend_bot
pandas.set_option('display.max_rows', None)

bot_matic = supertrend_bot.SupertrendBot(
                account='account',
                coinpair='MATIC/USDT',
                trade_log_path='log/trade_log_bot_matic.txt',
                length = 7, multiplier = 4.5,
                is_in_position=False, 
                position=0, 
                lot=50,
                timeframe='15m',
                timeframe_in_minutes=15)

df = pandas.read_csv("sandbox/historical_data/matic_15m.csv")
df = df.iloc[:1000:-1].reset_index()

supertrend_data = bot_matic.supertrend_format(df)
print(supertrend_data.head(10))



# BACKTEST
is_in_position = False
position = 0
lot = 100
balance = 1000
fee = 0.005

# for i in range(1,500): 
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
            supertrend_data.loc[current,'order'] = 'sell'
            supertrend_data.loc[current,'position'] = position
            supertrend_data.loc[current,'price'] = sell_price
            supertrend_data.loc[current,'pnl'] = pnl
            supertrend_data.loc[current,'balance'] = balance
            position = 0
        else:
            supertrend_data.loc[current,'order'] = 'sell_but_not_in_position'
    # NO SIGNAL
    else:
        supertrend_data.loc[current,'order'] = 'na'


supertrend_data.to_csv('sandbox/backtest_result/matic_15m.csv', index=False, index_label=False)