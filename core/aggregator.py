from __future__ import annotations

import math
from datetime import datetime, timezone
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from modules.technical_engine import TechnicalEngine
from modules.sentiment_engine import SentimentEngine
from modules.astro_engine import CelestialEngine


class MasterAggregator:
    def __init__(self):
        self.tech_engine = TechnicalEngine()
        self.sent_engine = SentimentEngine()
        self.astro_engine = CelestialEngine()

    @staticmethod
    def fetch_market_data(symbol: str, interval: str = "15m") -> pd.DataFrame:
        # Yahoo intraday limits: use a compatible period automatically.
        period_map = {"5m": "1mo", "15m": "1mo", "30m": "1mo", "1h": "3mo"}
        period = period_map.get(interval, "1mo")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False, actions=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume"
        })
        needed = ["open", "high", "low", "close", "volume"]
        df = df[[c for c in needed if c in df.columns]].copy()
        for c in needed:
            if c not in df:
                df[c] = 0.0
        df = df.dropna(subset=["open", "high", "low", "close"])
        if getattr(df.index, "tz", None) is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        return df.sort_index()

    def analyze(self, df, symbol, news_query, enable_finbert=False):
        tech_df = self.tech_engine.calculate(df.copy())
        tech = self.tech_engine.summary(tech_df)
        sentiment = self.sent_engine.analyze(news_query, enable_finbert=enable_finbert)
        celestial = self.astro_engine.calculate(datetime.now(timezone.utc))

        # Missing/neutral celestial and news are deliberately neutral, not bearish.
        technical_score = float(tech["score"])
        sentiment_score = float(sentiment["score"])
        celestial_score = float(celestial["score"])

        composite = (
            0.65 * (technical_score / 100.0)
            + 0.25 * (sentiment_score / 100.0)
            + 0.10 * (celestial_score / 100.0)
        )
        confidence = float(np.clip(composite * 100.0, -100, 100))

        # Require technical confirmation for an actionable signal.
        if technical_score >= 35 and confidence >= 30:
            signal = "BUY CALL"
        elif technical_score <= -35 and confidence <= -30:
            signal = "BUY PUT"
        else:
            signal = "HOLD"

        price = float(tech_df["close"].iloc[-1])
        atr = float(tech["atr"]) if np.isfinite(tech["atr"]) and tech["atr"] > 0 else max(price * 0.003, 1.0)
        direction = "CALL / LONG" if signal == "BUY CALL" else ("PUT / SHORT" if signal == "BUY PUT" else "WAIT")

        if signal == "BUY CALL":
            entry = price
            sl = price - 1.2 * atr
            t1 = price + 1.5 * atr
            t2 = price + 2.5 * atr
        elif signal == "BUY PUT":
            entry = price
            sl = price + 1.2 * atr
            t1 = price - 1.5 * atr
            t2 = price - 2.5 * atr
        else:
            entry = price
            sl = price
            t1 = price
            t2 = price

        return {
            "price": price,
            "technical": tech,
            "sentiment": sentiment,
            "celestial": celestial,
            "decision": {
                "signal": signal,
                "confidence": confidence,
                "technical_score": technical_score,
                "sentiment_score": sentiment_score,
                "celestial_score": celestial_score,
                "bull_probability": float(np.clip(50 + confidence / 2, 0, 100)),
                "bear_probability": float(np.clip(50 - confidence / 2, 0, 100)),
            },
            "levels": {
                "direction": direction,
                "entry": entry,
                "stop_loss": sl,
                "target1": t1,
                "target2": t2,
            },
        }
