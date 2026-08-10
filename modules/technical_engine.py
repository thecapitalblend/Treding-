import numpy as np
import pandas as pd

class TechnicalAnalyzer:
    def __init__(self, df):
        self.df = df.copy()

    @staticmethod
    def _ema(s, n):
        return s.ewm(span=n, adjust=False).mean()

    def generate_features(self):
        d = self.df
        d["ema_fast"] = self._ema(d["close"], 12)
        d["ema_slow"] = self._ema(d["close"], 26)

        d["macd"] = d["ema_fast"] - d["ema_slow"]
        d["macd_signal"] = d["macd"].ewm(span=9, adjust=False).mean()

        delta = d["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        d["rsi"] = (100 - (100 / (1 + rs))).fillna(50)

        prev_close = d["close"].shift(1)
        tr = pd.concat([
            d["high"] - d["low"],
            (d["high"] - prev_close).abs(),
            (d["low"] - prev_close).abs()
        ], axis=1).max(axis=1)
        d["atr"] = tr.ewm(alpha=1/14, adjust=False).mean()

        typical = (d["high"] + d["low"] + d["close"]) / 3
        if d["volume"].fillna(0).sum() > 0:
            session_key = pd.Series(d.index.date, index=d.index)
            pv = typical * d["volume"].fillna(0)
            d["vwap"] = pv.groupby(session_key).cumsum() / d["volume"].fillna(0).groupby(session_key).cumsum().replace(0, np.nan)
        else:
            # For index feeds with unreliable volume, use cumulative typical-price mean.
            d["vwap"] = typical.expanding().mean()

        up = d["high"].diff()
        down = -d["low"].diff()
        plus_dm = up.where((up > down) & (up > 0), 0.0)
        minus_dm = down.where((down > up) & (down > 0), 0.0)
        atr = d["atr"].replace(0, np.nan)
        plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        d["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()

        d.replace([np.inf, -np.inf], np.nan, inplace=True)
        return d

    def evaluate_signals(self):
        d = self.df
        if len(d) < 30:
            return {"score": 0, "trend": "NEUTRAL", "regime": "NORMAL"}

        x = d.iloc[-1]
        score = 0.0

        if x["ema_fast"] > x["ema_slow"]:
            score += 25
        else:
            score -= 25

        if x["macd"] > x["macd_signal"]:
            score += 20
        else:
            score -= 20

        if 50 < x["rsi"] < 70:
            score += 15
        elif 30 < x["rsi"] <= 50:
            score -= 5
        elif x["rsi"] >= 70:
            score -= 5
        elif x["rsi"] <= 30:
            score += 5

        if pd.notna(x["vwap"]):
            if x["close"] > x["vwap"]:
                score += 15
            else:
                score -= 15

        if pd.notna(x["adx"]) and x["adx"] >= 20:
            score += 10 if x["ema_fast"] > x["ema_slow"] else -10

        score = max(-100, min(100, score))
        trend = "BULLISH" if score >= 30 else "BEARISH" if score <= -30 else "NEUTRAL"

        atr_pct = float(x["atr"] / x["close"] * 100) if x["close"] else 0
        regime = "HIGH_VOL" if atr_pct >= 1.0 else "LOW_VOL" if atr_pct <= 0.25 else "NORMAL"

        return {"score": score, "trend": trend, "regime": regime}
