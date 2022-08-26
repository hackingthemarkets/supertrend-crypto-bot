# supertrend-bot

Supertrend bot using python (pandas and ccxt)

Code modified from: https://www.youtube.com/watch?v=1PEyddA1y5E

## Instruction

Class SupertrendBot (`supertrend.py`) is mainly used to run bot. Quickly read through the `__init__` of this class to learn how to initiate an object (an individual bot).  

An example of a bot is `bot_matic.py`.

## Notes in implemetation
- Filled position is different from calculated position (e.g. position = lot / price). It's safer to update position from exected order's returned result. Good for trade log and avoid getting error for selling more than what you actually bought.
- Exchange requires >1 second or much more to update its prices. So if you request prices miliseconds right after the candle closes, you WILL NOT get the latest price candle (latest price row). [Read more here.](https://docs.ccxt.com/en/latest/manual.html#notes-on-latency)
- Choosing the optimal configuration when trading on small timeframe (e.g. 15m) require large historical data. Because 1000 data points of 15m timeframe only covers ~10 days, which is very bias (specifically, what if it's downtrend during that period)



# Roadmap

Week 1 (04/07)
- Write buy/sell logic: Create TP mechanism for Supertrend - Done
- Check the math after TP and trendChange - Done. TP at 1:1 cut a part of the profit while most of which is achieved in very long trend. Additionally, such long trends are not many. Thus, less profit in the end.
- Back-test Supertrend, observe results with different config as well (length, multiplier (maybe 1->5)) - Done

Week 2 (18/7):
- Use ccxt to forward-test / Create class as an account 
- Forward testing (with variable 'balance'?)

Week 3 (25/7):
- Use test API ByBit for forward testing, compare result after 2 weeks with shorten past data of the same length.

Week 4 (1/8/2022):
- Use real API Binance with little money (Current Profit/Loss: +6.5)
- Use larger historical data to find optimal configuration:
    - https://docs.coinapi.io/#limits
    - 📍 Split bull/bear data
    - Choose best config from overall, test on bull/bear
- Plot chart for further insights: https://dygraphs.com/ + JS

In queue:
- ALGO: Write buy/sell logic: Set order when RSI escaped overbought>75/oversold<25 (threshold) zone, TP/SL: half if move x amount (if touch TP, set SL to entry), half if touch the opposite threshold
- ALGO: Use deep learning (e.g., LSTM) 
- To execute real order, use official API from Exchange
- Set up alarm (for every execution?)


## Others
- Price API: https://messari.io/api/docs
- TA-Lib (Python): https://mrjbq7.github.io/ta-lib/
- Toi di code dao: https://www.youtube.com/watch?v=WlO4lkvyLvI
- Indicator: https://github.com/thanhnguyennguyen/trading-indicator 
- Visualisation: https://github.com/yongghongg/stock-screener/blob/main/supertrend_demo_medium.ipynb / https://medium.datadriveninvestor.com/the-supertrend-implementing-screening-backtesting-in-python-70e8f88f383d

## Mics bookmarks for CAB420
- https://towardsdatascience.com/how-to-get-started-building-a-stock-cryptocurrency-forex-trading-program-2abbf0a4729f
- https://thecitadelpub.com/elons-lethal-mistake-predicting-the-stock-price-of-tesla-with-twitter-and-machine-learning-5e89282ce75f
- https://medium.datadriveninvestor.com/get-up-to-date-financial-ratios-p-e-p-b-and-more-of-stocks-using-python-4b53dd82908f
- https://www.youtube.com/watch?v=xfzGZB4HhEE
- https://www.youtube.com/watch?v=z9wt01WW9go&list=WL&index=100
- https://towardsdatascience.com/machine-learning-for-day-trading-27c08274df54
- https://www.mdpi.com/2673-2688/2/4/30/htm

## Notes
- 1000 datapoints of 5m time-frame cover 3.6 days => $12
- 1000 datapoints of 15m ............... 10 days => $16
- 1000 datapoints of 1h  ............... 40 days => $36
- 1000 datapoints of 4h  ............... 160 days (5.3 months) => $75
