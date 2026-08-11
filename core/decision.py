def build_decision(df,levels):
    r=df.iloc[-1]; price=float(r.Close); score=0
    if price>r.EMA20>r.EMA50: score+=30
    elif price<r.EMA20<r.EMA50: score-=30
    if r.RSI>55: score+=15
    elif r.RSI<45: score-=15
    if r.MACD>r.MACD_SIGNAL: score+=15
    else: score-=15
    if r.DI_PLUS>r.DI_MINUS and r.ADX>=20: score+=20
    elif r.DI_MINUS>r.DI_PLUS and r.ADX>=20: score-=20
    if price>r.VWAP: score+=10
    elif price<r.VWAP: score-=10
    trend='BULLISH' if score>=25 else 'BEARISH' if score<=-25 else 'NEUTRAL'; signal='BUY CALL' if score>=45 else 'BUY PUT' if score<=-45 else 'HOLD'; atr=float(r.ATR) if r.ATR==r.ATR else 0
    if signal=='BUY CALL': stop=price-1.25*atr; t1=price+1.5*atr; t2=price+2.5*atr
    elif signal=='BUY PUT': stop=price+1.25*atr; t1=price-1.5*atr; t2=price-2.5*atr
    else: stop=t1=t2=price
    return {'signal':signal,'trend':trend,'technical_score':score,'context_score':0,'celestial_score':0,'confidence':min(100,abs(score)),'entry':price,'stop':stop,'target1':t1,'target2':t2}
