from collections import namedtuple
import utils
import ccxt
import config
from datetime import datetime
import time
import pandas as pd
pd.set_option('display.max_rows', None)

# import warnings
# warnings.filterwarnings('ignore')


account = ccxt.binance({
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


def supertrend_format(df, length=7, atr_multiplier=3):
    '''
    Return the dataframe with '''
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


def check_buy_sell_signals(df, coinpair):
    global is_in_position, position

    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    # # Uncomment this to execute order immediately
    # df.loc[last_row_index,'is_uptrend'] = True
    # df.loc[previous_row_index,'is_uptrend'] = False

    if not df.loc[previous_row_index,'is_uptrend'] and df.loc[last_row_index,'is_uptrend']:
        if not is_in_position:
            position = lot / df.loc[last_row_index,'close'] 
            account.create_market_buy_order(coinpair, position)
            is_in_position = True
            utils.trade_log(f"Uptrend,Buy,{is_in_position},{position},")
        else:
            utils.trade_log(f"Already in position,-,{is_in_position},{position},")

    elif df.loc[previous_row_index,'is_uptrend'] and not df.loc[last_row_index,'is_uptrend']:
        if is_in_position:
            account.create_market_sell_order(coinpair, position)
            position = 0
            is_in_position = False
            utils.trade_log(f"Downtrend,Sell,{is_in_position},{position},")
        else:
            utils.trade_log(f"No position,-,{is_in_position},{position},")
    
    else:
        utils.trade_log('No signal,,,,')

def run_bot(coinpair, timeframe):
    utils.trade_log(f"\n{datetime.now()},")

    bars = account.fetch_ohlcv(coinpair, timeframe, limit=200)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend_format(df, length=supertrend_config.length, atr_multiplier=supertrend_config.multipler)
    # print(supertrend_data.tail(50))
    check_buy_sell_signals(supertrend_data, coinpair)

    utils.trade_log(f"{datetime.now()}")



#========================#

######### Config #########
is_in_position = False
position = 0
lot = 50    # USDT
coinpair = 'SOL/USDT'
timeframe_in_minutes = 15
timeframe='15m'
supertrend_config = namedtuple('Supertrend_config', ['length', 'multipler'])._make([14, 2.5])

######### Log #########
utils.trade_log(f"""\n"Start config: is_in_position={is_in_position}, \
position={position}, \
lot={lot}, \
coinpair={coinpair}, \
timeframe_in_minutes={timeframe_in_minutes}, \
timeframe={timeframe}, \
{supertrend_config}" """)

######### Run until it's terminated #########
while True:
    little_delay = 0.1      # second, to make sure we have a new complete candle
    # time.sleep(60*timeframe_in_minutes - time.time() % 60*timeframe_in_minutes + little_delay)
    time.sleep(2)         # for testing
    run_bot(coinpair=coinpair, timeframe=timeframe)
