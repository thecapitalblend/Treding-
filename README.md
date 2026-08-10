# Jarvis Trading Assistant V2

Streamlit research dashboard combining:

- Technical analysis: EMA, MACD, RSI, ATR, VWAP, ADX/DMI, volume
- News sentiment with optional FinBERT
- Swiss Ephemeris celestial calculations
- Experimental SBC/Vedha/Ashtakavarga research fields
- Master ensemble confidence
- BUY CALL / BUY PUT / HOLD / SELL-EXIT research actions
- ATR-based paper risk levels
- Paper trade journal

## GitHub structure

Upload the files exactly like this:

Jarvis-Trading-Assistant/
├── app.py
├── config.yaml
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── aggregator.py
│   ├── paper_execution.py
│   └── risk_manager.py
├── modules/
│   ├── __init__.py
│   ├── astro_engine.py
│   ├── sentiment_engine.py
│   └── technical_engine.py
├── data/
└── logs/

## Important

This version is PAPER MODE. It does not connect to Dhan/Fyers and does not send real orders.

FinBERT downloads model files on first activation and can be resource intensive on Streamlit Cloud. Keep it OFF until the base dashboard is stable.

Celestial/SBC/astrology signals are experimental and should not be treated as scientifically validated predictors or guaranteed trading signals.

## Streamlit

Set the main file to `app.py` and reboot/redeploy after committing changes.
