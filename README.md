# Jarvis Trading Assistant

Research dashboard combining:
- Quantitative technical analysis
- Market-news sentiment
- Swiss Ephemeris celestial calculations
- Ensemble decision scoring
- ATR-based paper risk levels

## Streamlit

Main entry point:

```bash
streamlit run app.py
```

## GitHub structure

```text
app.py
config.yaml
requirements.txt
core/
  __init__.py
  aggregator.py
  paper_execution.py
  risk_manager.py
modules/
  __init__.py
  technical_engine.py
  sentiment_engine.py
  astro_engine.py
logs/
```

## Important

The application is deliberately PAPER MODE. No broker credentials or real orders are included.

Celestial/Sarvatobhadra-style outputs are experimental research features and are not scientifically validated predictors of market prices.

FinBERT is optional because first-time model loading can be slow and memory intensive on Streamlit Cloud. Enable it from the sidebar after the base application is stable.

Never commit broker API keys, TOTP secrets, access tokens, or passwords to GitHub.
