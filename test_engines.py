import numpy as np
import pandas as pd
from modules.technical_engine import TechnicalAnalyzer
from modules.sentiment_engine import SentimentEngine
from core.risk_manager import RiskManager

def sample_data(n=100):
    close = np.linspace(100,120,n)
    return pd.DataFrame({
        "open":close-.5, "high":close+1, "low":close-1,
        "close":close, "volume":np.full(n,1000)
    })

def test_technical_features():
    out = TechnicalAnalyzer().generate_features(sample_data())
    for col in ["ema_fast","macd","rsi","atr"]:
        assert col in out.columns

def test_sentiment_fallback():
    assert SentimentEngine(False).analyze_headline("Strong bullish growth") > 0

def test_risk_manager():
    result = RiskManager(100000).calculate(100,2,"BUY")
    assert result["quantity"] > 0
    assert result["stop"] < 100
