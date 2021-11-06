import configparser
import logging
import os
import time
from os import path

import ccxt

from supertrend import Worker


class Bot:

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
            watchlist = config['watchlist'].split(',')
            markets = []

            try:
                all_markets = exchange.loadMarkets()
            except Exception as e:
                print(e)
                raise

            for market in all_markets:
                currency = market.split('/')[0]
                if market.endswith('/' + config['basecurrency']) and currency in watchlist:
                    markets.append(market)

            base_currency = config['basecurrency']

            if len(markets) == 0:
                # log proper message
                print(f"Provided watchlist is empty or specified cryptos are not available under the {base_currency} market on {config_section} exchange")
                break

            polling_interval = config['pollinginterval']
            bars_timeframe = config['barstimeframe']
            console_output = config.getboolean('consoleoutput')
            dataframe_logging = config.getboolean('dataframelogging')
            file_output = config.getboolean('fileoutput')
            take_profit = float(config['takeprofit'])
            minimum_order_size = float(config['minimumordersize'])
            num_markets = len(markets)
            unlocked_capital = float(config['unlockedcapital'])

            try:
                balance = exchange.fetch_balance()
            except Exception as e:
                print(e)
                raise

            free_balance = balance[base_currency]['free']

            allocation_per_market = Bot.position_sizing(free_balance, num_markets, unlocked_capital)

            print(f"Selected based currency: {base_currency}")
            print(f"Initial available capital: {free_balance}")
            print(f"Number of selected markets: {num_markets}")
            print(f"Percentage of capital unlock: {unlocked_capital}")
            print(f"Allocated capital per market: {allocation_per_market}")

            if minimum_order_size > allocation_per_market:
                # log proper message
                print("Capital allocated per market is insufficient!")
                print(f"Minimum capital allocation: {minimum_order_size}")
                print(f"Actual allocated capital: {allocation_per_market}")
                break

            for market in markets:
                bot_id = Bot.get_bot_id(config_section, market, sandbox_mode)
                logger = self.build_logger(bot_id)
                workers.append(
                    Worker(sandbox_mode, minimum_order_size, take_profit, console_output, dataframe_logging,
                           file_output, polling_interval, base_currency, bars_timeframe, logger, bot_id, config_section,
                           exchange, market, allocation_per_market))

        self.workers = workers

    @staticmethod
    def position_sizing(free_balance, num_markets, unlocked_capital):
        return (free_balance * min(1, unlocked_capital)) / float(num_markets)

    @staticmethod
    def get_bot_id(exchange_name: str, market: str, is_sandbox: bool): 
        return exchange_name.lower() + "_" + market.replace("/", "_").lower() + ("_sandbox" if is_sandbox else "_live")

    @staticmethod
    def build_logger(bot_id):
        logger = logging.getLogger(bot_id)
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

