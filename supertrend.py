from threading import Thread
import pandas as pd
import schedule
import warnings
import time

pd.set_option('display.max_rows', None)
warnings.filterwarnings('ignore')

class Worker(Thread):

    def __init__(self, mos, tp, coutput, dflogging, foutput, interval, currency, timeframe, logger, bot_id, ex_name, exchange, market, size):
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
        self.target_take_profit = tp
        self.last_buy_order_price = float(0)
        self.minimum_order_size = mos

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
        if self.in_position and self.last_buy_order_price > float(0):
            target_sell_price = (1 + self.target_take_profit) * self.last_buy_order_price
            actual_market_price = self.last_price()
            
            if target_sell_price >= actual_market_price:
                position_size = self.free_balance()
                
                self.log_info(":::::::::> Target profit reached")
                self.log_info(f":::::::::> Target price: {target_sell_price} | buy price: {self.last_buy_order_price} | actual price: {actual_market_price}")
                self.log_info(f":::::::::> Selling {position_size} {self.market} at market price")
                # TODO change this to OCO order
                order = self.exchange.create_market_sell_order(self.market, position_size)
                self.last_buy_order_price = float(0)
                self.in_position = False

        if self.dataframe_logging:
            self.log_info(df.tail(3))

        last_row_index = len(df.index) - 1
        previous_row_index = last_row_index - 1

        if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
            self.log_info("==> Uptrend detected")
            
            if not self.in_position:
                last_price = self.last_price()
                position_size = self.buy_position_size(last_price)
                
                if position_size < self.minimum_order_size:
                    self.log_warning(f"Order size less than the expected minimum of {self.minimum_order_size} {self.base_currency}")
                    
                self.log_info(f":::::::::> Buying {position_size} {self.market} at market price of {last_price}")
                order = {}
            
                try:
                    order = self.exchange.create_market_buy_order(self.market, position_size)
                except Exception as e:
                    self.log_exception(e)
                    #send_email, telegram or whatsapp message
                else:
                    self.last_buy_order_price = float(order['cost'])
                    self.in_position = True

                    self.log_info(order)

            else:
                self.log_info(":::::::::> Holding already a position in the market, nothing to buy")

        if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
            self.log_info("==> Downtrend detected")
            
            if self.in_position:
                position_size = self.free_balance()
                self.log_info(f":::::::::> Selling {position_size} {self.market} at market price")
                order = {}

                try:
                    order = self.exchange.create_market_sell_order(self.market, position_size)
                except Exception as e:
                    self.log_exception(e)
                    #send_email, telegram or whatsapp message
                else:   
                    self.last_buy_order_price = float(0)
                    self.in_position = False
                    
                    self.log_info(order)
                
            else:
                self.log_info(":::::::::> Do not hold a position in the market, nothing to sell")

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

    def last_price(self):
        ticker = self.exchange.fetch_ticker(self.market)
        return float(ticker['info']['lastPrice'])

    def free_balance(self):
        balance = self.exchange.fetch_balance()
        return balance[self.base_currency]['free']
    
    def log_info(self, message):
        if self.file_output:
            self.logger.info(message)
        if self.console_output:
            print(message)

    def log_warning(self, message):
        if self.file_output:
            self.logger.warning(message)
        if self.console_output:
            print(message)

    def log_exception(self, exception):
        if self.file_output:
            self.logger.exception(exception)
        if self.console_output:
            print(exception)
    
    def run(self):
        self.log_info("####################################################################")
        self.log_info("#                                                                  #")
        self.log_info("#         MULTITHREADING SUPERTREND CRYPTO TRADER (MSCT)           #")
        self.log_info("#                                                                  #")
        self.log_info("####################################################################")
        self.log_info("                                                                    ")
        self.log_info(f"Bot ID: {self.exchange_name + '_' + self.market.replace('/', '_').lower()}")
        self.log_info(f"Currency: {self.base_currency}")
        self.log_info(f"Market: {self.market}")
        self.log_info(f"Exchange: {self.exchange}")
        self.log_info(f"Position: {self.size}")

        schedule.every(int(self.polling_interval)).seconds.do(self.work)
        while True:
            schedule.run_pending()
            time.sleep(1)