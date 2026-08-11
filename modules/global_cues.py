import yfinance as yf

GLOBAL_TICKERS = {
    "Dow Futures": "YM=F",
    "Crude Oil (WTI)": "CL=F",
    "USD/INR": "INR=X",
}


def get_global_cues():
    out = {}
    for label, tkr in GLOBAL_TICKERS.items():
        try:
            df = yf.download(tkr, period="5d", interval="1d", progress=False, threads=False, auto_adjust=False)
            if df is None or df.empty:
                out[label] = {"available": False}
                continue
            if hasattr(df.columns, "levels"):
                df.columns = [c[0] for c in df.columns]
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else last
            out[label] = {"available": True, "price": last, "change_pct": (last - prev) / prev * 100 if prev else 0.0}
        except Exception as e:
            out[label] = {"available": False, "message": str(e)}
    return out
