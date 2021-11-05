import configparser
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

        workers = []

        for config_section in config_parser.sections():

            if not (config_section in ccxt.exchanges):
                continue
            
            config = config_parser[config_section]

            exchange_cls = getattr(ccxt, config_section)

            sandbox_mode = config.getboolean('sandboxmode')

            api_key = ''
            api_secret = ''

            if not sandbox_mode:
                api_key = config['apikey']
                api_secret = config['apisecret']
            else:
                api_key = config['apikeysandbox']
                api_secret = config['apisecretsandbox']

            exchange = exchange_cls({
                'apiKey': api_key,
                'secret': api_secret
            })

            exchange.set_sandbox_mode(sandbox_mode)

            markets = []
            
            for market in exchange.loadMarkets():
                watchlist = config['wachtlist'].split(',')
                currency = market.split('/')[0]
                if(market.endswith('/'+ config['basecurrency']) and currency in watchlist):
                    markets.append(market)

            if len(markets) == 0:
                # log proper message
                break

            polling_interval = config['pollinginterval']
            base_currency = config['basecurrency']
            bars_timeframe = config['barstimeframe']
            console_output = config.getboolean('consoleoutput')
            dataframe_logging = config.getboolean('dataframelogging')
            file_output = config.getboolean('fileoutput')
            take_profit = float(config['takeprofit'])
            minimum_order_size = float(config['minimumordersize'])

            balance = exchange.fetch_balance()
            free_balance = balance[config['basecurrency']]['free']
            size = (free_balance *  min(1, float(config['percentageatrisk']))) / float(len(markets))

            if minimum_order_size > size:
                # log proper message
                print(f"too small minimal position size - minimum: {minimum_order_size} current: {size}")
                break

            for market in markets:
                bot_id = config_section.lower() + "_" + market.replace("/", "_").lower()
                logger = self.mylogger('supertrend', bot_id)
                workers.append(Worker(sandbox_mode, minimum_order_size, take_profit, console_output, dataframe_logging, file_output, polling_interval, base_currency, bars_timeframe, logger, bot_id, config_section, exchange, market, size))
        
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