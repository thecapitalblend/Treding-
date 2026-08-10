import numpy as np
import pandas as pd

class TechnicalAnalyzer:
    def __init__(self, df): self.df = df.copy()

    def ema(self, s, n): return s.ewm(span=n, adjust=False).mean()

    def rsi(self, s, n=14):
        d=s.diff()
        gain=d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
        loss=(-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
        rs=gain/loss.replace(0,np.nan)
        return 100-(100/(1+rs))

    def atr(self, df, n=14):
        p=df["close"].shift(1)
        tr=pd.concat([df["high"]-df["low"],(df["high"]-p).abs(),(df["low"]-p).abs()],axis=1).max(axis=1)
        return tr.ewm(alpha=1/n, adjust=False).mean()

    def generate_features(self):
        self.df["ema_fast"]=self.ema(self.df["close"],12)
        self.df["ema_slow"]=self.ema(self.df["close"],26)
        self.df["macd"]=self.df["ema_fast"]-self.df["ema_slow"]
        self.df["macd_signal"]=self.df["macd"].ewm(span=9,adjust=False).mean()
        self.df["rsi"]=self.rsi(self.df["close"])
        self.df["atr"]=self.atr(self.df)
        typical=(self.df["high"]+self.df["low"]+self.df["close"])/3
        vol=self.df["volume"].replace(0,np.nan)
        self.df["vwap"]=(typical*vol).cumsum()/vol.cumsum()
        self.df["adx"]=0.0
        return self.df

    def evaluate(self):
        x=self.df.iloc[-1]; p=self.df.iloc[-2]
        score=0
        score += 25 if x.ema_fast>x.ema_slow else -25
        score += 20 if x.macd>x.macd_signal else -20
        score += 15 if x.close>x.vwap else -15
        score += 10 if x.rsi>50 else -10
        if x.ema_fast>x.ema_slow and p.ema_fast<=p.ema_slow: score+=10
        if x.ema_fast<x.ema_slow and p.ema_fast>=p.ema_slow: score-=10
        trend="BULLISH" if score>=25 else "BEARISH" if score<=-25 else "NEUTRAL"
        return {"score":float(score),"trend":trend,"rsi":float(x.rsi),
                "macd":float(x.macd),"adx":float(x.adx),"atr":float(x.atr),
                "vwap":float(x.vwap)}
