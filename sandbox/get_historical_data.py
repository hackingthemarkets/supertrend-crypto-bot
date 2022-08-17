import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')

from collections import namedtuple
import utils
import ccxt
import csv
import config
from datetime import datetime
import time
import pandas as pd
pd.set_option('display.max_rows', None)
import requests

# BTC
# ETH
# MATIC
# SOL
# ADA
# DOGE
# XRP
# TRX
url = "https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_SOL_USDT/history?"+\
        "period_id=1HRS&time_end=2022-08-10T00:00:00&"+\
        f"limit=100000&output_format=csv&apiKey={config.API_COINAPI3}"


download = requests.get(url)
decoded_content = download.content.decode('utf-8')
file = open('sandbox/historical_data/sol_1h_original.csv', 'w')
file.write(decoded_content)
file.close()


    # cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    # my_list = list(cr)
    # for row in my_list:
    #     print(row)
# r = requests.get(url)
# data = r.json()
# print(r.data)
