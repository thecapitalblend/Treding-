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
        d["ema20"] = self._ema(d["close"], 20)
        d["ema50"] = self._ema(d["close"], 50)

        d["macd"] = d["ema_fast"] - d["ema_slow"]
        d["macd_signal"] = d["macd"].ewm(span=9, adjust=False).mean()
        d["macd_hist"] = d["macd"] - d["macd_signal"]

        delta = d["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        d["rsi"] = (100 - 100 / (1 + rs)).fillna(50)

        prev_close = d["close"].shift(1)
        tr = pd.concat([
            d["high"] - d["low"],
            (d["high"] - prev_close).abs(),
            (d["low"] - prev_close).abs()
        ], axis=1).max(axis=1)
        d["atr"] = tr.ewm(alpha=1/14, adjust=False).mean()

        typical = (d["high"] + d["low"] + d["close"]) / 3
        volume = d["volume"].fillna(0)
        if float(volume.sum()) > 0:
            dates = pd.Series(d.index.date, index=d.index)
            pv = typical * volume
            den = volume.groupby(dates).cumsum().replace(0, np.nan)
            d["vwap"] = pv.groupby(dates).cumsum() / den
        else:
            d["vwap"] = typical.expanding().mean()

        up = d["high"].diff()
        down = -d["low"].diff()
        plus_dm = up.where((up > down) & (up > 0), 0.0)
        minus_dm = down.where((down > up) & (down > 0), 0.0)
        atr = d["atr"].replace(0, np.nan)
        d["di_plus"] = 100 * plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        d["di_minus"] = 100 * minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr
        dx = 100 * (d["di_plus"] - d["di_minus"]).abs() / (d["di_plus"] + d["di_minus"]).replace(0, np.nan)
        d["adx"] = dx.ewm(alpha=1/14, adjust=False).mean()

        d["volume_sma20"] = volume.rolling(20).mean()
        d["volume_ratio"] = volume / d["volume_sma20"].replace(0, np.nan)

        d.replace([np.inf, -np.inf], np.nan, inplace=True)
        return d

    def evaluate_signals(self):
        d = self.df
        if len(d) < 30:
            return {"score": 0, "trend": "NEUTRAL", "regime": "NORMAL",
                    "bull_conditions": [], "bear_conditions": []}

        x = d.iloc[-1]
        p = d.iloc[-2]
        score = 0.0
        bull, bear = [], []

        if x.ema_fast > x.ema_slow:
            score += 20; bull.append("EMA12>EMA26")
        else:
            score -= 20; bear.append("EMA12<EMA26")

        if x.ema20 > x.ema50:
            score += 10; bull.append("EMA20>EMA50")
        else:
            score -= 10; bear.append("EMA20<EMA50")

        if x.macd > x.macd_signal:
            score += 15; bull.append("MACD bullish")
        else:
            score -= 15; bear.append("MACD bearish")

        if 50 <= x.rsi < 68:
            score += 10; bull.append("RSI bullish zone")
        elif 32 < x.rsi < 50:
            score -= 5; bear.append("RSI weak")
        elif x.rsi >= 70:
            score -= 5; bear.append("RSI overbought")
        elif x.rsi <= 30:
            score += 5; bull.append("RSI oversold")

        if pd.notna(x.vwap):
            if x.close > x.vwap:
                score += 15; bull.append("Price>VWAP")
            else:
                score -= 15; bear.append("Price<VWAP")

        if pd.notna(x.adx) and x.adx >= 20:
            if x.di_plus > x.di_minus:
                score += 10; bull.append("DMI bullish")
            else:
                score -= 10; bear.append("DMI bearish")

        if pd.notna(x.volume_ratio) and x.volume_ratio >= 1.2:
            score += 5 if x.close >= p.close else -5

        score = float(max(-100, min(100, score)))
        trend = "BULLISH" if score >= 30 else "BEARISH" if score <= -30 else "NEUTRAL"

        atr_pct = float(x.atr / x.close * 100) if x.close else 0
        regime = "HIGH_VOL" if atr_pct >= 1.0 else "LOW_VOL" if atr_pct <= 0.25 else "NORMAL"

        cross_up = x.ema_fast > x.ema_slow and p.ema_fast <= p.ema_slow
        cross_down = x.ema_fast < x.ema_slow and p.ema_fast >= p.ema_slow

        return {
            "score": score,
            "trend": trend,
            "regime": regime,
            "bull_conditions": bull,
            "bear_conditions": bear,
            "ema_cross_up": bool(cross_up),
            "ema_cross_down": bool(cross_down),
        }
