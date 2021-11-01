import ccxt
import config
import schedule
import pandas as pd

pd.set_option('display.max_rows', None)

import warnings
warnings.filterwarnings('ignore')

import numpy as np
from datetime import datetime
import time

exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY
})

def show_balance(wallets):

    balance = exchange.fetch_balance()

    for wallet in wallets:
        print(f"{wallet} Free Balance: { balance[wallet]['free']}")


def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)):
        previous = current - 1

        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
        
    return df


in_position = False

def check_buy_sell_signals(df):
    global in_position

    print("Checking for buy and sell signals...")

    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("==> changed to uptrend, BUY!")
        if not in_position:
            order = exchange.create_market_buy_order(config.TRADING_PAIR, config.POSITION_SIZE)
            print(order)
            in_position = True
        else:
            print("!==> already in position, nothing to buy")
    else:
        print("<==> no buy signal found")

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            print("==> changed to downtrend, SELL!")
            order = exchange.create_market_sell_order(config.TRADING_PAIR, config.POSITION_SIZE)
            print(order)
            in_position = False
        else:
            print("!<== not in position, nothing to sell")
    else:
        print("<==> no sell signal found")

    print(df.tail(5))

def run_bot():
    show_balance(['BTC', 'ETH', 'USDT', 'EUR'])
    bars = exchange.fetch_ohlcv(config.TRADING_PAIR, timeframe=config.TIMEFRAME, limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend(df)
    
    check_buy_sell_signals(supertrend_data)


schedule.every(60).seconds.do(run_bot)


while True:
    schedule.run_pending()
    time.sleep(1)
