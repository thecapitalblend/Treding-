from __future__ import annotations
import numpy as np
import pandas as pd

class TechnicalAnalyzer:
    """EMA, MACD, RSI and ATR engine."""

    def __init__(self, ema_fast=12, ema_slow=26, rsi_length=14, atr_length=14):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_length = rsi_length
        self.atr_length = atr_length

    @staticmethod
    def _rsi(close, length):
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
        avg_loss = loss.ewm(alpha=1/length, adjust=False, min_periods=length).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(df, length):
        prev_close = df["close"].shift(1)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1/length, adjust=False, min_periods=length).mean()

    def generate_features(self, df):
        data = df.copy()
        data.columns = [str(c).lower() for c in data.columns]
        required = {"open", "high", "low", "close"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing OHLC columns: {sorted(missing)}")

        data["ema_fast"] = data["close"].ewm(span=self.ema_fast, adjust=False).mean()
        data["ema_slow"] = data["close"].ewm(span=self.ema_slow, adjust=False).mean()

        ema12 = data["close"].ewm(span=12, adjust=False).mean()
        ema26 = data["close"].ewm(span=26, adjust=False).mean()
        data["macd"] = ema12 - ema26
        data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
        data["macd_hist"] = data["macd"] - data["macd_signal"]
        data["rsi"] = self._rsi(data["close"], self.rsi_length)
        data["atr"] = self._atr(data, self.atr_length)
        return data

    def evaluate(self, data):
        if len(data) < max(self.ema_slow, self.rsi_length, self.atr_length) + 2:
            return {"score": 0.0, "signal": "WAIT", "reason": "Not enough candles"}

        latest, previous = data.iloc[-1], data.iloc[-2]
        if pd.isna(latest["rsi"]) or pd.isna(latest["atr"]):
            return {"score": 0.0, "signal": "WAIT", "reason": "Indicators warming up"}

        score, reasons = 0.0, []

        if latest["ema_fast"] > latest["ema_slow"]:
            score += 25; reasons.append("EMA trend bullish")
        else:
            score -= 25; reasons.append("EMA trend bearish")

        if latest["macd"] > latest["macd_signal"]:
            score += 25; reasons.append("MACD bullish")
        else:
            score -= 25; reasons.append("MACD bearish")

        if 50 <= latest["rsi"] < 70:
            score += 20; reasons.append("RSI supports bullish momentum")
        elif 30 < latest["rsi"] < 50:
            score -= 20; reasons.append("RSI supports bearish momentum")
        elif latest["rsi"] >= 70:
            score -= 10; reasons.append("RSI overbought")
        else:
            score += 10; reasons.append("RSI recovery zone")

        bullish_cross = latest["ema_fast"] > latest["ema_slow"] and previous["ema_fast"] <= previous["ema_slow"]
        bearish_cross = latest["ema_fast"] < latest["ema_slow"] and previous["ema_fast"] >= previous["ema_slow"]

        if bullish_cross:
            score += 20; reasons.append("Fresh bullish EMA cross")
        elif bearish_cross:
            score -= 20; reasons.append("Fresh bearish EMA cross")

        signal = "BUY" if score >= 50 else "SELL" if score <= -50 else "HOLD"
        return {
            "score": float(np.clip(score, -100, 100)),
            "signal": signal,
            "reason": "; ".join(reasons),
            "rsi": float(latest["rsi"]),
            "atr": float(latest["atr"]),
            "ema_fast": float(latest["ema_fast"]),
            "ema_slow": float(latest["ema_slow"]),
            "macd": float(latest["macd"]),
            "macd_signal": float(latest["macd_signal"])
        }
