import sys
sys.path.insert(0, '/home/rodo/Documents/GitHub/BitTracker')
import config
import requests

# BTC
# ETH 
# MATIC 
# SOL 
# ADA 4H
# DOGE 
# XRP 4h
# TRX 4h
# url = f"https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_{coin}_USDT/history?"+\
#         "period_id=1HRS&time_end=2022-08-10T00:00:00&"+\
#         f"limit=100000&output_format=csv&apiKey={config.API_COINAPI3}"

# download = requests.get(url)
# decoded_content = download.content.decode('utf-8')
# file = open('sandbox/historical_data/sol_1h_original.csv', 'w')
# file.write(decoded_content)
# file.close()


    # cr = csv.reader(decoded_content.splitlines(), delimiter=',')
    # my_list = list(cr)
    # for row in my_list:
    #     print(row)
# r = requests.get(url)
# data = r.json()
# print(r.data)



def get_and_save(API, coin, savefilename, custom_url=False):
    if custom_url == False:
        # url = f"https://rest.coinapi.io/v1/ohlcv/BITFINEX_SPOT_{coin}_USD/history?"+\
        # url = f"https://rest.coinapi.io/v1/ohlcv/KRAKEN_SPOT_{coin}_USDT/history?"+\
        # url = f"https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_{coin}_USDT/history?" + \
        url = f"https://rest.coinapi.io/v1/ohlcv/BITSTAMP_SPOT_{coin}_USD/history?"+\
            "period_id=1DAY&time_end=2022-10-01T00:00:00&"+\
            f"limit=100000&output_format=csv&apiKey={API}"
        # Timeframe param: HRS, MIN
    else:
        url = custom_url

    download = requests.get(url)
    decoded_content = download.content.decode('utf-8')
    file = open(f"sandbox/historical_data/{savefilename}_original.csv", 'w')
    file.write(decoded_content)
    file.close()
    print('Done: ' + coin )

# get_and_save(config.API_COINAPI1, 'DOGE', 'doge_15m')
# get_and_save(config.API_COINAPI2, 'DOGE', 'doge_1h_2')
# get_and_save(config.API_COINAPI3, 'SOL', 'matic_4h')
# get_and_save(config.API_COINAPI4, 'ETH', 'eth_15m_2')
# get_and_save(config.API_COINAPI5, 'ETH', 'eth_15m_3')
# get_and_save(config.API_COINAPI6, 'ETH', 'eth_1h_bfn')
get_and_save(config.API_COINAPI7, 'BTC', 'btc_1d')
# get_and_save(config.API_COINAPI8, 'XRP', 'xrp_4h')
# get_and_save(config.API_COINAPI9, 'DOGE', 'doge_4h')
# get_and_save(config.API_COINAPI10, 'ETH', 'eth_4h')
# get_and_save(config.API_COINAPI11, 'SOL', 'sol_4h')
# get_and_save(config.API_COINAPI12, 'MATIC', 'matic_4h')
# get_and_save(config.API_COINAPI13, 'ADA', 'ada_4h')


# custom_url = f"https://rest.coinapi.io/v1/ohlcv/BITSTAMP_SPOT_BTC_USD/history?" + \
#         "period_id=15MIN&time_end=2014-01-08T16:15:00&"+ \
#         f"limit=100000&output_format=csv&apiKey={config.API_COINAPI8}"
# get_and_save('', 'BTC', 'btc_15m_3', custom_url)

