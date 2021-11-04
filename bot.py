import configparser
#from configobj import ConfigObj
import ccxt
from os import path
import logging as log
from supertrend import Worker
import time
import logging
import os

class Bot():

    def __init__(self):
        config_parser = configparser.ConfigParser()
        settings_path = path.abspath("settings.conf")
        config_parser.read(settings_path)

        #config_obj = ConfigObj(settings_path)
        #test = config_obj['binance']
        
        #print(test)
        #print(config_obj)

        workers = []

        for config_section in config_parser.sections():

            if not (config_section in ccxt.exchanges):
                continue
            
            config = config_parser[config_section]

            exchange_cls = getattr(ccxt, config_section)

            exchange = exchange_cls({
                'apiKey': config['apikey'],
                'secret': config['apisecret']
            })

            sandbox_mode = config.getboolean('sandboxmode')
            exchange.set_sandbox_mode(sandbox_mode)

            #ticker = exchange.fetch("ETH/EUR")
            #print(ticker)
            #break

            markets = []
            
            for market in exchange.loadMarkets():
                watchlist = config['wachtlist'].split(',')
                currency = market.split('/')[0]
                if(market.endswith('/'+ config['basecurrency']) and currency in watchlist):
                    markets.append(market)

            if len(markets) == 0:
                break

            balance = exchange.fetch_balance()
            free_balance = balance[config['basecurrency']]['free']
            size = (free_balance *  min(1, float(config['percentageatrisk']))) / len(markets)

            polling_interval = config['pollinginterval']
            base_currency = config['basecurrency']
            bars_timeframe = config['barstimeframe']
            console_output = config.getboolean('consoleoutput')
            dataframe_logging = config.getboolean('dataframelogging')
            file_output = config.getboolean('fileoutput')
            take_profit = config['takeprofit']
            minimum_order_size = float(config['minimumordersize'])

            for market in markets:
                bot_id = config_section.lower() + "_" + market.replace("/", "_").lower()
                logger = self.mylogger('supertrend', bot_id)
                workers.append(Worker(minimum_order_size, take_profit, console_output, dataframe_logging, file_output, polling_interval, base_currency, bars_timeframe, logger, bot_id, config_section, exchange, market, size))
        
        self.workers = workers
    
    def mylogger(self, strategy, bot_id):
        logger = logging.getLogger(strategy)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(threadName)s:%(name)s] %(asctime)s %(levelname)s:\t%(message)s')
        file_handler = logging.FileHandler(os.path.join(bot_id + ".log"), 'w')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def run(self):
        for worker in self.workers:
            worker.start()
            time.sleep(5)

Bot().run()