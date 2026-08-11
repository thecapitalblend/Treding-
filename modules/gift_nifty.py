import os,yfinance as yf

def load_gift_nifty():
    symbols=[os.getenv('GIFT_NIFTY_SYMBOL','NIFTY_GIFT'),'GIFTNIFTY']
    for s in symbols:
        try:
            h=yf.Ticker(s).history(period='5d',interval='5m',auto_adjust=False)
            if h is not None and not h.empty:
                c=float(h.Close.dropna().iloc[-1]); first=float(h.Close.dropna().iloc[0]); return {'available':True,'price':c,'change_pct':(c-first)/first*100 if first else 0,'source':f'Yahoo/yfinance symbol: {s}'}
        except Exception: pass
    return {'available':False,'message':'GIFT Nifty feed is not exposed by the configured Yahoo/yfinance symbols. Set GIFT_NIFTY_SYMBOL to a symbol supported by your provider; no value is fabricated.'}
