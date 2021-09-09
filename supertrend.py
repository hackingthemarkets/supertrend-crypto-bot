from logging import error
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
tckers = pd.read_csv("all_ticker_USDT.csv")

tickers = tckers["ticker"]
print(tickers)
DATA_LIST = []
exchange = ccxt.binance({
    "apiKey": config.BINANCE_API_KEY,
    "secret": config.BINANCE_SECRET_KEY
})

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

def check_buy_sell_signals(df,ticker):
    global in_position

    #print("checking for buy and sell signals")
    #print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        #print("changed to uptrend, buy")
        if not in_position:
            

            print("buy")

            side ="/"
            ticker = ticker.replace(side,'')
            datafrem = [{"ticker":ticker}]

            datafrem = pd.DataFrame(datafrem)
            datafrem.to_csv("NEW_COINS.csv")
            DATA = {"ticker":ticker}
            DATA_LIST.append(DATA)
            
            in_position = True
        else:
            print("already in position, nothing to do")
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        if in_position:
            #print("changed to downtrend, sell")
            
            print(" sell")
            in_position = False
        else:
            print("You aren't in position, nothing to sell")






while True:
    for ticker in tickers :
        try:
            AT =ticker[:-4]
            BT =ticker[-4:]
            ticker =AT+"/"+BT 
            print("==========", ticker , "===============")

            bars = exchange.fetch_ohlcv(ticker, timeframe='1d', limit=100)
            df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            supertrend_data = supertrend(df)
            
            check_buy_sell_signals(supertrend_data,ticker)
            
            
            time.sleep(60)
        except:
            print(error)
    dd = pd.DataFrame(DATA_LIST)
    dd.to_csv("coins_in_posation.csv")
