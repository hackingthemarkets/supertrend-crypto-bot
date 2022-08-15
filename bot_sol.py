import ccxt
import config
import supertrend_bot

account = ccxt.binance({
    "apiKey": config.API_BINANCE,
    "secret": config.SECRET_BINANCE,
})

bot_matic = supertrend_bot.SupertrendBot(
                account=account,
                coinpair='SOL/USDT',
                trade_log_path='log/trade_log_bot_sol.txt',
                length = 7, multiplier = 4.5,
                is_in_position=True, 
                position=1.05, 
                lot=50,
                timeframe='15m',
                timeframe_in_minutes=15)

# print('\n', bot_matic.get_supertrend_data().tail(100), '\n')
bot_matic.run_forever()