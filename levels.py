def support_resistance(df,lookback=80):
    x=df.tail(min(lookback,len(df))); return {'support':float(x.Low.rolling(10,min_periods=1).min().iloc[-1]),'resistance':float(x.High.rolling(10,min_periods=1).max().iloc[-1])}
