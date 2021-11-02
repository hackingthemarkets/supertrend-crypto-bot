from threading import Thread
import pandas as pd
import schedule
import warnings
import time

pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')

class Worker(Thread):

    def __init__(self, coutput, dflogging, foutput, interval, currency, timeframe, logger, bot_id, ex_name, exchange, market, size):
        Thread.__init__(self, name = 'thread-' + bot_id.replace('_', '-'))
        self.logger = logger
        self.in_position = False
        self.polling_interval = interval
        self.base_currency = currency
        self.bars_timeframe = timeframe
        self.exchange = exchange
        self.exchange_name = ex_name
        self.market = market
        self.size = size # position size: total amount to trade by this worker
        self.console_output = coutput
        self.dataframe_logging = dflogging
        self.file_output = foutput

    def work(self):
        bars = self.exchange.fetch_ohlcv(self.market, self.bars_timeframe, limit=100)
        df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        supertrend_data = Worker.supertrend(df)
        self.check_buy_sell_signals(supertrend_data)


    @staticmethod
    def supertrend(df, period=7, atr_multiplier=3):
        hl2 = (df['high'] + df['low']) / 2
        df['atr'] = Worker.atr(df, period)
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

        if self.dataframe_logging:
            if self.file_output:
                self.logger.info(df.tail(3))
            if self.console_output:
                print(df.tail(3))

        last_row_index = len(df.index) - 1
        previous_row_index = last_row_index - 1

        if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
            if self.file_output:
                self.logger.info("==> Uptrend detected")
            if self.console_output:
                print("==> Uptrend detected")
            if not self.in_position:
                ticker = self.exchange.fetch_ticker(self.market)
                last_price = ticker['info']['lastPrice']
                position_size = self.buy_position_size(last_price)
                if self.file_output:
                    self.logger.info(f":::::::::> Buying {position_size} {self.market} at market price of {last_price}")
                if self.console_output:
                    print(f":::::::::> Buying {position_size} {self.market} at market price of {last_price}")
                order = self.exchange.create_market_buy_order(self.market, position_size)
                if self.file_output:
                    self.logger.info(order)
                if self.console_output:
                    print(order)
                self.in_position = True
            else:
                if self.file_output:
                    self.logger.info(":::::::::> Holding already a position in the market, nothing to buy")
                if self.console_output:
                    print(":::::::::> Holding already a position in the market, nothing to buy")

        if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
            if self.file_output:
                self.logger.info("==> Downtrend detected")
            if self.console_output:
                print("==> Downtrend detected")
            if self.in_position:
                balance = self.exchange.fetch_balance()
                position_size = balance[self.market]['free']
                if self.file_output:
                    self.logger.info(f":::::::::> Selling {position_size} {self.market} at market price")
                if self.console_output:
                    print(f":::::::::> Selling {position_size} {self.market} at market price")
                order = self.exchange.create_market_sell_order(self.market, position_size)
                if self.file_output:
                    self.logger.info(order)
                if self.console_output:
                    print(order)
                self.in_position = False
            else:
                if self.file_output:
                    self.logger.info(":::::::::> Do not hold a position in the market, nothing to sell")
                if self.console_output:
                    print(":::::::::> Do not hold a position in the market, nothing to sell")


    @staticmethod
    def atr(data, period):
        data['tr'] = Worker.tr(data)
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
        if self.file_output:
            self.logger.info("####################################################################")
            self.logger.info("#                                                                  #")
            self.logger.info("#                    SUPERTREND TRADING BOT                        #")
            self.logger.info("#                                                                  #")
            self.logger.info("####################################################################")
            self.logger.info("                                                                    ")
            self.logger.info(f"Bot ID: {self.exchange_name + '_' + self.market.replace('/', '_').lower()}")
            self.logger.info(f"Currency: {self.base_currency}")
            self.logger.info(f"Market: {self.market}")
            self.logger.info(f"Exchange: {self.exchange}")
            self.logger.info(f"Position Size: {self.size}")
        if self.console_output:
            print("####################################################################")
            print("#                                                                  #")
            print("#                    SUPERTREND TRADING BOT                        #")
            print("#                                                                  #")
            print("####################################################################")
            print("                                                                    ")
            print(f"Bot ID: {self.exchange_name + '_' + self.market.replace('/', '_').lower()}")        
            print((f"Currency: {self.base_currency}"))
            print(f"Market: {self.market}")
            print(f"Exchange: {self.exchange}")
            print(f"Position Size: {self.size}")

        schedule.every(int(self.polling_interval)).seconds.do(self.work)
        while True:
            schedule.run_pending()
            time.sleep(1)

    
