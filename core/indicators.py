import numpy as np
import pandas as pd

def add_indicators(df):
    x=df.copy(); c,h,l,v=x.Close,x.High,x.Low,x.Volume
    x['EMA20']=c.ewm(span=20,adjust=False).mean(); x['EMA50']=c.ewm(span=50,adjust=False).mean(); x['SMA200']=c.rolling(200,min_periods=50).mean()
    d=c.diff(); gain=d.clip(lower=0).rolling(14).mean(); loss=(-d.clip(upper=0)).rolling(14).mean(); rs=gain/loss.replace(0,np.nan); x['RSI']=(100-100/(1+rs)).fillna(50)
    e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean(); x['MACD']=e12-e26; x['MACD_SIGNAL']=x.MACD.ewm(span=9,adjust=False).mean()
    pc=c.shift(1); tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()],axis=1).max(axis=1); x['ATR']=tr.rolling(14).mean()
    typical=(h+l+c)/3; dates=pd.Series(x.index.date,index=x.index); pv=typical*v.fillna(0); x['VWAP']=pv.groupby(dates).cumsum()/v.fillna(0).groupby(dates).cumsum().replace(0,np.nan)
    up=h.diff(); down=-l.diff(); pdm=np.where((up>down)&(up>0),up,0.0); mdm=np.where((down>up)&(down>0),down,0.0); atr=x.ATR
    x['DI_PLUS']=100*pd.Series(pdm,index=x.index).rolling(14).mean()/atr.replace(0,np.nan); x['DI_MINUS']=100*pd.Series(mdm,index=x.index).rolling(14).mean()/atr.replace(0,np.nan); dx=100*(x.DI_PLUS-x.DI_MINUS).abs()/(x.DI_PLUS+x.DI_MINUS).replace(0,np.nan); x['ADX']=dx.rolling(14).mean()
    return x
