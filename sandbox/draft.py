import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')

from collections import namedtuple
import utils
import ccxt
import config
from datetime import datetime
import time
import pandas as pd
pd.set_option('display.max_rows', None)
import requests

################################

# url = f"https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_BTC_USDT/history?period_id=15MIN&time_start=2021-06-01T00:00:00&limit=100&output_format=csv"
# headers = {'X-CoinAPI-Key' : config.API_COINAPI2}
# r = requests.get(url, headers=headers)
# data = r.json()

# # print(r.data)
# print(data)





################################
# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# url = f"https://www.alphavantage.co/query?function=CRYPTO_INTRADAY&symbol=SOL&market=USD&interval=5min&datatype=csv&apikey={config.API_VANTAGE}"
# r = requests.get(url)
# data = r.json()

# # print(r.data)
# print(data)


################################
import warnings
warnings.filterwarnings('ignore')

account = ccxt.binance({
    "apiKey": config.API_TEST,
    "secret": config.SECRET_TEST,
})
account.set_sandbox_mode(True)


account = ccxt.binance({
    "apiKey": config.API_BINANCE,
    "secret": config.SECRET_BINANCE,
})

order = account.create_market_buy_order('BUSD/USDT',50)
print(order)
#################################