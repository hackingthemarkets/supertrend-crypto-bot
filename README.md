# supertrend-bot

Supertrend bot using python (pandas and ccxt)

## Demo Video and Instructions:
* https://www.youtube.com/watch?v=1PEyddA1y5E


## Notes
- Exchange requires >1 second to update its prices. So if you request prices milisecond right after the candle closes, you WILL NOT get the latest price candle (latest price row).