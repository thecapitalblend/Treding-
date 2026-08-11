import pandas as pd
import yfinance as yf

def load_market_data(symbol,period,interval):
    df=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False,threads=False)
    if df is None or df.empty: raise RuntimeError(f'No data returned for {symbol}.')
    if isinstance(df.columns,pd.MultiIndex): df.columns=[c[0] for c in df.columns]
    required=['Open','High','Low','Close','Volume']; missing=[c for c in required if c not in df.columns]
    if missing: raise RuntimeError(f'Missing columns: {missing}')
    return df[required].dropna(subset=['Open','High','Low','Close'])
