import numpy as np
import pandas as pd

class TechnicalEngine:
    @staticmethod
    def _ema(s, n):
        return s.ewm(span=n, adjust=False, min_periods=n).mean()

    @staticmethod
    def _rsi(s, n=14):
        d = s.diff()
        up = d.clip(lower=0)
        dn = -d.clip(upper=0)
        au = up.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
        ad = dn.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
        rs = au / ad.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def _atr(df, n=14):
        prev = df["close"].shift(1)
        tr = pd.concat([
            df["high"] - df["low"],
            (df["high"] - prev).abs(),
            (df["low"] - prev).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1/n, adjust=False, min_periods=n).mean()

    @staticmethod
    def _adx(df, n=14):
        high, low, close = df["high"], df["low"], df["close"]
        up = high.diff()
        dn = -low.diff()
        plus_dm = up.where((up > dn) & (up > 0), 0.0)
        minus_dm = dn.where((dn > up) & (dn > 0), 0.0)
        prev = close.shift(1)
        tr = pd.concat([
            high-low, (high-prev).abs(), (low-prev).abs()
        ], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
        plus_di = 100 * plus_dm.ewm(alpha=1/n, adjust=False, min_periods=n).mean() / atr.replace(0, np.nan)
        minus_di = 100 * minus_dm.ewm(alpha=1/n, adjust=False, min_periods=n).mean() / atr.replace(0, np.nan)
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1/n, adjust=False, min_periods=n).mean()
        return adx, plus_di, minus_di

    def calculate(self, df):
        df = df.copy()
        df["ema_fast"] = self._ema(df["close"], 12)
        df["ema_slow"] = self._ema(df["close"], 26)
        df["rsi"] = self._rsi(df["close"])
        df["atr"] = self._atr(df)
        df["macd"] = df["ema_fast"] - df["ema_slow"]
        df["macd_signal"] = self._ema(df["macd"], 9)

        adx, dip, dim = self._adx(df)
        df["adx"], df["di_plus"], df["di_minus"] = adx, dip, dim

        pv = ((df["high"] + df["low"] + df["close"]) / 3) * df["volume"].fillna(0)
        vol = df["volume"].fillna(0)
        if vol.sum() > 0:
            df["vwap"] = pv.cumsum() / vol.cumsum().replace(0, np.nan)
        else:
            df["vwap"] = df["close"].rolling(20, min_periods=1).mean()

        return df

    def summary(self, df):
        r = df.iloc[-1]
        price = float(r["close"])
        score = 0.0

        # Trend / VWAP
        if np.isfinite(r["ema_fast"]) and np.isfinite(r["ema_slow"]):
            score += 20 if r["ema_fast"] > r["ema_slow"] else -20
        if np.isfinite(r["vwap"]):
            score += 15 if price > r["vwap"] else -15

        # RSI
        if r["rsi"] >= 55: score += 15
        elif r["rsi"] <= 45: score -= 15

        # MACD
        if r["macd"] > r["macd_signal"]: score += 15
        else: score -= 15

        # DMI + ADX
        if r["adx"] >= 20:
            if r["di_plus"] > r["di_minus"]: score += 20
            else: score -= 20

        score = float(np.clip(score, -100, 100))
        trend = "BULLISH" if score >= 25 else ("BEARISH" if score <= -25 else "NEUTRAL")

        def val(x, default=0.0):
            try:
                x = float(x)
                return x if np.isfinite(x) else default
            except Exception:
                return default

        return {
            "score": score,
            "trend": trend,
            "rsi": val(r["rsi"], 50),
            "macd": val(r["macd"]),
            "atr": val(r["atr"]),
            "vwap": val(r["vwap"]),
            "adx": val(r["adx"]),
            "di_plus": val(r["di_plus"]),
            "di_minus": val(r["di_minus"]),
            "ema_fast": val(r["ema_fast"]),
            "ema_slow": val(r["ema_slow"]),
        }
