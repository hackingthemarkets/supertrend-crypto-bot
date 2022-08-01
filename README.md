# supertrend-bot

Supertrend bot using python (pandas and ccxt)

## Demo Video and Instructions:
* https://www.youtube.com/watch?v=1PEyddA1y5E


## Notes in implemetation
- Filled position is different from calculated position (e.g. position = lot / price). It's safer to update position from exected order's returned result. Good for trade log and avoid selling more than what you actually bought.
- Exchange requires >1 second or much more to update its prices. So if you request prices miliseconds right after the candle closes, you WILL NOT get the latest price candle (latest price row). [Read more here.](https://docs.ccxt.com/en/latest/manual.html#notes-on-latency)