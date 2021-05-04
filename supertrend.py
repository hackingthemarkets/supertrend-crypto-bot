import os
import ccxt
import config
import schedule
import numpy as np
import pandas as pd
import warnings
import pprint
import json
import time
from datetime import datetime, date

pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')
start_st = datetime.fromtimestamp(time.time()).strftime('%Y%m%d-%H%M%S')


# Set your global variables
symbol = 'ETH/USDT'
timeframe = '30m'
limit = 100
in_position = False
quantity_buy_sell = 0.1


exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': config.BINANCE_API_KEY,
    'secret': config.BINANCE_SECRET_KEY,
    'timeout': 50000,
    'enableRateLimit': True,
})


def log_write(msg, start_st=start_st, df=False, json=False, print_it=True):
    st = datetime.fromtimestamp(time.time()).strftime('%Y%m%d-%H%M%S')
    path = os.path.dirname(os.path.realpath(__file__))
    log = open('{}/supertrend-{}.log'.format(path, start_st), 'a')

    if not df and not json:
        entry = f'{st}: {msg}\n'
    elif df:
        entry = f'{st}\n{msg}\n'
    elif json:
    	entry = '{}\n{}\n'.format(st, pprint.pprint(json.loads(msg)))

    log.write(entry)

    if print_it:
    	print(entry.strip())


def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high_minus_low'] = abs(df['high'] - df['low'])
    df['high_minus_pc'] = abs(df['high'] - df['previous_close'])
    df['low_minus_pc'] = abs(df['low'] - df['previous_close'])
    tr = df[['high_minus_low', 'high_minus_pc', 'low_minus_pc']].max(axis=1)
    return tr


def atr(df, period):
    df['tr'] = tr(df)
    atr = df['tr'].rolling(period).mean()
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


def check_buy_sell_signals(df):
    global in_position, symbol, quantity_buy_sell, log

    log_write('Checking for buy and sell signals')

    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        if not in_position:
            log_write('Changed to uptrend, buy')
            order = exchange.create_market_buy_order(symbol, quantity_buy_sell)
            log_write(order)
            in_position = True

            print(df.tail(5))
            log_write(df.tail(5), df=True)

        else:
            log_write('Already in position, nothing to do')

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            log_write('Changed to downtrend, sell')
            order = exchange.create_market_sell_order(symbol, quantity_buy_sell)
            print(order)
            log_write(order)
            in_position = False

            print(df.tail(5))
            log_write(df.tail(5), df=True)

        else:
            log_write('You aren\'t in position, nothing to sell')


def run_bot():
    global symbol, timeframe, limit, log

    msg = f'symbol: {symbol}, timeframe: {timeframe}, limit: {limit}, in_position: {in_position}, quantity_buy_sell: {quantity_buy_sell}'
    log_write(msg)

    log_write('Fetching new bars')

    df = None
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    except:
        pass

    if df is None:
        log_write('Error fetching ohlcv-data from exchange')
    else:
        supertrend_data = supertrend(df)
        check_buy_sell_signals(supertrend_data)


schedule.every(10).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
