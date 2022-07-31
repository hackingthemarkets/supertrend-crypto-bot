import ccxt
import config
import schedule
from datetime import datetime
import time
import pandas as pd
pd.set_option('display.max_rows', None)

# import warnings
# warnings.filterwarnings('ignore')


exchange = ccxt.binance({
    "apiKey": config.API_BINANCE,
    "secret": config.SECRET_BINANCE,
})

def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr


def atr(data, length):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(length).mean()

    return atr


def supertrend(df, length=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, length)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['is_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df.loc[current,'close'] > df.loc[previous,'upperband']:
            df.loc[current,'is_uptrend'] = True
        elif df.loc[current,'close'] < df.loc[previous,'lowerband']:
            df.loc[current,'is_uptrend'] = False
        else:
            df.loc[current,'is_uptrend'] = df.loc[previous,'is_uptrend']

            if df.loc[current,'is_uptrend'] and df.loc[current,'lowerband'] < df.loc[previous,'lowerband']:
                df.loc[current,'lowerband'] = df.loc[previous,'lowerband']

            if not df.loc[current,'is_uptrend'] and df.loc[current,'upperband'] > df.loc[previous,'upperband']:
                df.loc[current,'upperband'] = df.loc[previous,'upperband']
        
    return df


in_position = False

def check_buy_sell_signals(df, coinpair):
    global in_position

    print("Checking for buy and sell signals")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df.loc[previous_row_index,'is_uptrend'] and df.loc[last_row_index,'is_uptrend']:
        if not in_position:
            print("Changed to uptrend, buy")
            order = exchange.create_market_buy_order(coinpair, 0.05)
            # print(order)
            in_position = True
        else:
            print("Already in position, nothing to do")
    
    if df.loc[previous_row_index,'is_uptrend'] and not df.loc[last_row_index,'is_uptrend']:
        if in_position:
            print("changed to downtrend, sell")
            order = exchange.create_market_sell_order(coinpair, 0.05)
            # print(order)
            in_position = False
        else:
            print("You aren't in position, nothing to sell")

def run_bot(coinpair='ETH/USDT', timeframe='1m' ):
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv(coinpair, timeframe, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    # print(supertrend_data)

    check_buy_sell_signals(supertrend_data, coinpair)


schedule.every(1).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)
