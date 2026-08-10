# Jarvis Trading Assistant

A modular Streamlit trading research dashboard combining:
- Quantitative technical analysis
- Optional FinBERT financial-news sentiment
- Swiss Ephemeris celestial analytics
- Ensemble confidence scoring
- ATR-based risk management
- Paper-trading execution scaffold

> The project starts in PAPER mode. It does not send live broker orders. Technical, sentiment and celestial signals are research heuristics and must be backtested and paper-traded before any live use.

## Repository structure

```text
Jarvis-Trading-Assistant/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── config.yaml
├── README.md
├── core/
│   ├── __init__.py
│   ├── aggregator.py
│   ├── risk_manager.py
│   └── paper_execution.py
├── modules/
│   ├── __init__.py
│   ├── technical_engine.py
│   ├── sentiment_engine.py
│   └── astro_engine.py
├── data/.gitkeep
├── logs/.gitkeep
└── tests/
    ├── __init__.py
    └── test_engines.py
```

## Local setup

Python 3.11 is recommended.

```bash
git clone YOUR_REPOSITORY_URL
cd Jarvis-Trading-Assistant
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## GitHub

```bash
git add .
git commit -m "Initial Jarvis Trading Assistant"
git push
```

## Streamlit Cloud

Create a Streamlit app from this GitHub repository and select `app.py` as the main file. Put secrets only in Streamlit Secrets; never commit `.env`.

## Production roadmap

Before live trading, add:
1. Official broker websocket market data
2. Current broker authentication/instrument mapping
3. Persistent order/position database
4. Idempotent order handling and reconciliation
5. Daily loss limit and kill switch
6. Slippage/commission model
7. Backtesting + walk-forward validation
8. Extensive paper trading
9. Independently verified SBC/Ashtakavarga rules
10. Broker adapter only after validating the current official API documentation
