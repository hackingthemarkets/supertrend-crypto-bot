import configparser
import datetime
import logging
import pytz
import os
import time
from os import path

import ccxt

from supertrend import Worker


class Formatter(logging.Formatter):
    """override logging.Formatter to use an aware datetime object"""

    def converter(self, timestamp):
        dt = datetime.datetime.utcfromtimestamp(timestamp)
        tzinfo = pytz.timezone('UTC')
        return tzinfo.localize(dt)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            try:
                s = dt.isoformat(timespec='milliseconds')
            except TypeError:
                s = dt.isoformat()
        return s


class Bot:

    def __init__(self):
        config_parser = configparser.ConfigParser()
        settings_path = path.abspath("exchanges.conf")
        config_parser.read(settings_path)

        now = Bot.timestamp_now_utc()

        main_logger = self.build_logger(now)

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
                print(
                    f"Provided watchlist is empty or specified cryptos are not available under the {base_currency} market on {config_section} exchange")
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

            Bot.log_info(main_logger, f"Selected based currency: {base_currency}", file_output, console_output)
            Bot.log_info(main_logger, f"Initial available capital: {free_balance}", file_output, console_output)
            Bot.log_info(main_logger, f"Number of selected markets: {num_markets}", file_output, console_output)
            Bot.log_info(main_logger, f"Percentage of capital unlock: {unlocked_capital}", file_output, console_output)
            Bot.log_info(main_logger, f"Allocated capital per market: {allocation_per_market}", file_output,
                         console_output)

            if minimum_order_size > allocation_per_market:
                # log proper message
                Bot.log_info(main_logger, "Capital allocated per market is insufficient!", file_output,
                             console_output)
                Bot.log_info(main_logger, f"Minimum capital allocation: {minimum_order_size}", file_output,
                             console_output)
                Bot.log_info(main_logger, f"Actual allocated capital: {allocation_per_market}", file_output,
                             console_output)
                break

            for market in markets:
                bot_id = Bot.get_bot_id(config_section, market, sandbox_mode, now)
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
    def get_bot_id(exchange_name: str, market: str, is_sandbox: bool, now: str):

        return exchange_name.lower() + \
               "_" + market.replace("/", "_").lower() + \
               ("_sandbox" if is_sandbox else "_live_") + \
               now

    @staticmethod
    def log_info(logger, message, file_output, console_output):
        if file_output:
            logger.info(message)
        if console_output:
            print(message)

    @staticmethod
    def build_logger(bot_id):
        logger = logging.getLogger(bot_id)
        logger.setLevel(logging.INFO)
        format = Formatter('[%(threadName)s] %(asctime)s %(levelname)s:\t%(message)s')  #:%(name)s
        file_handler = logging.FileHandler(os.path.join(bot_id + ".log"), 'w')
        file_handler.setFormatter(format)
        logger.addHandler(file_handler)
        return logger

    @staticmethod
    def timestamp_now_utc():
        return str(datetime.datetime.now(tz=pytz.UTC)) \
            .replace(' ', '') \
            .replace('-', '') \
            .replace(':', '') \
            .replace('.', '') \
            .replace('+', '')

    def run(self):
        for worker in self.workers:
            worker.start()
            time.sleep(5)


Bot().run()
