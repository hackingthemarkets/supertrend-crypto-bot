from threading import Thread
import logging
import pandas as pd
import schedule
import warnings
import time

pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')
logging.basicConfig(filename="supertrend.log",  level=logging.INFO, format='[%(processName)s %(threadName)s] %(asctime)s %(message)s', datefmt='[%d.%m.%Y %H:%M:%S] -')


class Supertrend(Thread):

    def __init__(self, exchange_name, config, exchange, market, size):
        Thread.__init__(self, name=(exchange_name + "_" + market.replace("/", "_")).lower())
        self.in_position = False
        self.config = config
        self.exchange = exchange
        self.exchange_name = exchange_name
        self.market = market
        self.size = size # position size: total amount to trade by this worker
 

    def work(self):
     
        bars = self.exchange.fetch_ohlcv(self.market, self.config['timeframe'], limit=100)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        supertrend_data = Worker.supertrend(df)

        self.check_buy_sell_signals(supertrend_data)


    @staticmethod
    def supertrend(df, period=7, atr_multiplier=3):
        hl2 = (df['high'] + df['low']) / 2
        df['atr'] = Supertrend.atr(df, period)
        df['upperband'] = hl2 + (atr_multiplier * df['atr'])
        df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
        df['in_uptrend'] = True

        for current in range(1, len(df.index)):
            previous = current - 1

            if df['close'][current] > df['upperband'][previous]:
                df['in_uptrend'][current] = True
            elif df['close'][current] < df['lowerband'][previous]:
                df['in_uptrend'][current] = False
            else:
                df['in_uptrend'][current] = df['in_uptrend'][previous]

                if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                    df['lowerband'][current] = df['lowerband'][previous]

                if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                    df['upperband'][current] = df['upperband'][previous]
            
        return df


    def check_buy_sell_signals(self, df):

        
        #logging.info(df.tail(3))
        #print(df.tail(3))

        last_row_index = len(df.index) - 1
        previous_row_index = last_row_index - 1

        if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
            logging.info("==> Uptrend detected")
            print("==> Uptrend detected")
            if not self.in_position:
                ticker = self.exchange.fetch_ticker(self.market)
                last_price = ticker['info']['lastPrice']
                position_size = self.buy_position_size(last_price)
                #log.info(f":::::::::> Buying {position_size} {self.market} at market price of {last_price}")
                print(f":::::::::> Buying {position_size} {self.market} at market price of {last_price}")
                order = self.exchange.create_market_buy_order(self.market, position_size)
                #log.info(order)
                print(order)
                self.in_position = True
            else:
                #logging.info(":::::::::> Holding already a position in the market, nothing to buy")
                print(":::::::::> Holding already a position in the market, nothing to buy")

        if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
            logging.info("==> Downtrend detected")
            print("==> Downtrend detected")
            if self.in_position:
                balance = self.exchange.fetch_balance()
                position_size = balance[self.market]['free']
                #log.info(f":::::::::> Selling {position_size} {self.market} at market price")
                print(f":::::::::> Selling {position_size} {self.market} at market price")
                order = self.exchange.create_market_sell_order(self.market, position_size)
                #log.info(order)
                print(order)
                self.in_position = False
            else:
                #logging.info(":::::::::> Do not hold a position in the market, nothing to sell")
                print(":::::::::> Do not hold a position in the market, nothing to sell")


    @staticmethod
    def atr(data, period):
        data['tr'] = Supertrend.tr(data)
        atr = data['tr'].rolling(period).mean()

        return atr

    @staticmethod
    def tr(data):
        data['previous_close'] = data['close'].shift(1)
        data['high-low'] = abs(data['high'] - data['low'])
        data['high-pc'] = abs(data['high'] - data['previous_close'])
        data['low-pc'] = abs(data['low'] - data['previous_close'])

        tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

        return tr

    def buy_position_size(self, last_price):
        return self.size / float(last_price)

    def run(self):
        logging.info("####################################################################")
        logging.info("#                                                                  #")
        logging.info("#                    SUPERTREND TRADING BOT                        #")
        logging.info("#                                                                  #")
        logging.info("####################################################################")
        logging.info("#                                                                  #")
        logging.info(f"Bot ID: {self.exchange_name + '_' + self.market.replace('/', '_').lower()}")
        logging.info(f"Currency: {self.config['currency']}")
        logging.info(f"Market: {self.market}")
        logging.info(f"Exchange: {self.exchange}")
        logging.info(f"Position Size: {self.size}")
        print("####################################################################")
        print("#                                                                  #")
        print("#                    SUPERTREND TRADING BOT                        #")
        print("#                                                                  #")
        print("####################################################################")
        print("#                                                                  #")
        print(f"Bot ID: {self.exchange_name + '_' + self.market.replace('/', '_').lower()}")        
        print((f"Currency: {self.config['currency']}"))
        print(f"Market: {self.market}")
        print(f"Exchange: {self.exchange}")
        print(f"Position Size: {self.size}")

        schedule.every(int(self.config['scheduleevery'])).seconds.do(self.work)
        while True:
            schedule.run_pending()
            time.sleep(1)

    
