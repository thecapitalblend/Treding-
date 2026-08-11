# Jarvis Trading Assistant v2

TradingView-style NIFTY chart layer with real OHLC candlesticks, EMA 20/50, SMA 200, VWAP, volume, support/resistance, RSI, MACD, ATR, ADX/DI, paper-mode decision engine, Sidereal Lahiri planetary positions, and a configurable GIFT Nifty connector.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GIFT Nifty

Yahoo/yfinance does not guarantee a universal GIFT Nifty symbol. The app tries `NIFTY_GIFT` and `GIFTNIFTY`. If your provider uses another symbol, set `GIFT_NIFTY_SYMBOL` in the environment. The app never invents a price.

For true exchange-grade real-time data, replace the market-data modules with a broker/exchange feed. Yahoo/yfinance is a research-data source, not an execution-grade feed.

Astrology uses Swiss Ephemeris + Lahiri sidereal mode for astronomical positions. It is an experimental/non-scientifically-validated decision layer, not a guaranteed market predictor.

The app is PAPER MODE and sends no broker orders.

## Angel One live data (optional)

To get real live NIFTY 50 LTP instead of yfinance's ~15-20 min delayed data:

1. Create an app at https://smartapi.angelone.in and get an API Key.
2. Enable TOTP at https://smartapi.angelbroking.com/enable-totp and save the
   TOTP secret (not the 6-digit code).
3. Set environment variables before launching (never commit these):
   ```bash
   export ANGELONE_API_KEY="..."
   export ANGELONE_CLIENT_CODE="..."
   export ANGELONE_PIN="..."
   export ANGELONE_TOTP_SECRET="..."
   ```
4. `pip install -r requirements.txt` (now includes smartapi-python, pyotp, websocket-client)
5. Run the app as usual. When symbol is NIFTY 50, the Price metric will show
   "Price (Angel One LIVE)" if login succeeds, otherwise it silently falls
   back to the delayed yfinance price and shows the reason in the sidebar.

This only fetches LTP/quote data via REST -- it never places orders (the app
remains PAPER MODE). Historical candles still come from yfinance; swap in
`core/broker_angelone.py::get_nifty_candles` if you want Angel One's own
candle history instead.
