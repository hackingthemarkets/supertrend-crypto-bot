import ccxt
import config
import supertrend_bot

account = ccxt.binance({
    "apiKey": config.API_BINANCE,
    "secret": config.SECRET_BINANCE,
})

bot_matic = supertrend_bot.SupertrendBot(
                account=account,
                coinpair='MATIC/USDT',
                trade_log_path='log/trade_log_bot_matic.txt',
                length = 4, multiplier = 19,
                is_in_position=True, 
                position=53.8, 
                lot=50,
                timeframe='15m',
                timeframe_in_minutes=15)


bot_matic.run_forever()