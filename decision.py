
import numpy as np

def score_row(r):
    score = 0.0
    price = float(r.Close)
    if price > r.EMA20 > r.EMA50: score += 30
    elif price < r.EMA20 < r.EMA50: score -= 30
    if r.RSI >= 55: score += 15
    elif r.RSI <= 45: score -= 15
    if r.MACD > r.MACD_SIGNAL: score += 15
    else: score -= 15
    if r.DI_PLUS > r.DI_MINUS and r.ADX >= 20: score += 20
    elif r.DI_MINUS > r.DI_PLUS and r.ADX >= 20: score -= 20
    if np.isfinite(r.VWAP):
        if price > r.VWAP: score += 10
        elif price < r.VWAP: score -= 10
    return float(score)

def build_decision(df, levels, context_score=0.0, celestial_score=0.0):
    r = df.iloc[-1]
    tech = score_row(r)
    signal = "BUY CALL" if tech >= 45 else "BUY PUT" if tech <= -45 else "HOLD"
    trend = "BULLISH" if tech >= 25 else "BEARISH" if tech <= -25 else "NEUTRAL"
    atr = float(r.ATR) if np.isfinite(r.ATR) else 0.0
    price = float(r.Close)
    if signal == "BUY CALL":
        stop, t1, t2 = price-1.25*atr, price+1.5*atr, price+2.5*atr
    elif signal == "BUY PUT":
        stop, t1, t2 = price+1.25*atr, price-1.5*atr, price-2.5*atr
    else:
        stop=t1=t2=price
    confidence=min(100.0, abs(tech)+abs(context_score)*0.5+abs(celestial_score)*0.5)
    return {"signal":signal,"trend":trend,"technical_score":tech,
            "context_score":float(context_score),"celestial_score":float(celestial_score),
            "confidence":confidence,"entry":price,"stop":stop,"target1":t1,"target2":t2}

def signal_history(df):
    scores=df.apply(score_row,axis=1)
    raw=scores.apply(lambda s:"BUY CALL" if s>=45 else "BUY PUT" if s<=-45 else "HOLD")
    counts=raw.value_counts().to_dict()
    transitions=[]
    prev="HOLD"
    for idx,sig in raw.items():
        if sig in ("BUY CALL","BUY PUT") and sig!=prev:
            transitions.append((idx,sig,float(scores.loc[idx])))
        prev=sig
    return raw,counts,transitions
