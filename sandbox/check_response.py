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
import warnings
warnings.filterwarnings('ignore')



account = ccxt.binance({
    "apiKey": config.API_TEST,
    "secret": config.SECRET_TEST,
})
account.set_sandbox_mode(True)


# account = ccxt.binance({
#     "apiKey": config.API_BINANCE,
#     "secret": config.SECRET_BINANCE,
# })

order = account.create_market_sell_order('BUSD/USDT',50)
print(order['average'])