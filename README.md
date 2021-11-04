# Multithreading Supertrend Crypto Trader (MSCT)

## Get Started
Following steps must be completed to get the MSCT up und running:

1. Make a copy of the `settings.example.conf` and rename the copy to `settings.conf`
```shell
cp settings.example.conf settings.conf
```

2. Requesting API key and secret from your crypto exchange. Following steps show how to aquire a binance API Key and secret for testnet (sandbox mode).

    - Go to `https://testnet.binance.vision` and login using your Github account
    - Then, click on `Generate HMAC_SHA256 Key` 

3. Set your api key in the coresponding section of `settings.conf``
```conf
[binance]
...
ApiKeySandbox = your-binance-testnet-api-key
ApiSecretSandbox = your-binance-testnet-api-secret
```

4. Run `pip3 install -r requirements.txt` from the project root to install the required packages

5. Adjust oder variable in `settings.conf` according to your needs (optional)

6. Run `python3 bot.py` to start MSCT

## Other useful infos
On the sandbox mode only following pairs are available

### Binance
- BNB/BUSD
- BTC/BUSD
- ETH/BUSD
- LTC/BUSD
- TRX/BUSD
- XRP/BUSD
- BNB/USDT
- BTC/USDT
- ETH/USDT
- LTC/USDT
- TRX/USDT
- XRP/USDT
- BNB/BTC
- ETH/BTC
- LTC/BTC
- TRX/BTC
- XRP/BTC
- LTC/BNB
- TRX/BNB
- XRP/BNB

## Open tasks
- Parametrize the stategy (supertrend, momentum etc.) so that they can be executed for each market

## Special Note
Special Thanks to Part Time Lary from sharing his knowledge. Don't hesistate to support him.

* https://buymeacoffee.com/parttimelarry
* https://youtube.com/parttimelarry
* https://www.youtube.com/watch?v=1PEyddA1y5E
