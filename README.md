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
