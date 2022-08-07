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


def supertrend_format(df, length, atr_multiplier):
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


def check_buy_sell_signals(supertrend_data, coinpair):
    global is_in_position, position

    last_row_index = len(supertrend_data.index) - 1
    previous_row_index = last_row_index - 1

    # # Uncomment this to execute order immediately
    # df.loc[last_row_index,'is_uptrend'] = True
    # df.loc[previous_row_index,'is_uptrend'] = False

    if not supertrend_data.loc[previous_row_index,'is_uptrend'] and supertrend_data.loc[last_row_index,'is_uptrend']:
        if not is_in_position:
            position = lot / supertrend_data.loc[last_row_index,'close'] 
            order = account.create_market_buy_order(coinpair, position)
            position = order['filled']
            is_in_position = True
            utils.trade_log(f"Uptrend,Buy,{is_in_position},{position},", 'log/trade_log_2.txt')
        else:
            utils.trade_log(f"Already in position,-,{is_in_position},{position},", 'log/trade_log_2.txt')

    elif supertrend_data.loc[previous_row_index,'is_uptrend'] and not supertrend_data.loc[last_row_index,'is_uptrend']:
        if is_in_position:
            order = account.create_market_sell_order(coinpair, position)
            position = position - order['filled']
            is_in_position = False
            utils.trade_log(f"Downtrend,Sell,{is_in_position},{position},", 'log/trade_log_2.txt')
        else:
            utils.trade_log(f"No position,-,{is_in_position},{position},", 'log/trade_log_2.txt')
    
    else:
        utils.trade_log('No signal,,,,', 'log/trade_log_2.txt')

def run_bot(coinpair, timeframe):
    utils.trade_log(f"\n{datetime.now()},", 'log/trade_log_2.txt')

    bars = account.fetch_ohlcv(coinpair, timeframe, limit=200)
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    supertrend_data = supertrend_format(df, length=supertrend_config.length, atr_multiplier=supertrend_config.multipler)
    supertrend_data.drop(columns=['previous_close', 'high-low', 'high-pc', 'low-pc', 'tr', 'atr'], axis=0, inplace=True)
    print('\n', supertrend_data.tail(4), '\n')
    check_buy_sell_signals(supertrend_data, coinpair)

    utils.trade_log(f"{datetime.now()}", 'log/trade_log_2.txt')



#========================#

######### Config #########
is_in_position = False
position = 0
lot = 50    # USDT
coinpair = 'MATIC/USDT'
timeframe_in_minutes = 15
timeframe='15m'
supertrend_config = namedtuple('Supertrend_config', ['length', 'multipler'])._make([7, 4.5])
little_delay = 5      # second, to make sure the exchange adds a new candle

######### Log #########
utils.trade_log(f"""\n"Start config: is_in_position={is_in_position}, \
position={position}, \
lot={lot}, \
coinpair={coinpair}, \
timeframe_in_minutes={timeframe_in_minutes}, \
timeframe={timeframe}, \
{supertrend_config}" """, 'log/trade_log_2.txt')

######### Run until it's terminated #########
while True:
    try:
        run_bot(coinpair=coinpair, timeframe=timeframe)
    except Exception as e:
        print(e)
        time.sleep(5)
        continue


    # time.sleep(2)         # for testing
    time.sleep(60*timeframe_in_minutes - time.time() % (60*timeframe_in_minutes) + little_delay)
