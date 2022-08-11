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
df = df.iloc[:1000:-1]

supertrend_df = bot_matic.supertrend_format(df)
supertrend_df.drop(columns=['previous_close', 'high-low', 'high-pc', 'low-pc', 'tr', 'atr'], axis=0, inplace=True)

print(supertrend_df.head(10))