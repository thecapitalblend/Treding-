
import os, re, requests
import yfinance as yf

NSEIX_URL = "https://www.nseix.com/"


def _from_env_symbol():
    """If the user has set GIFT_NIFTY_SYMBOL, try it via yfinance first."""
    sym = os.environ.get("GIFT_NIFTY_SYMBOL")
    if not sym:
        return None
    try:
        df = yf.download(sym, period="1d", interval="5m", progress=False, threads=False)
        if df is None or df.empty:
            return None
        last = df.iloc[-1]
        prev = df.iloc[0]
        price = float(last["Close"])
        change = price - float(prev["Close"])
        change_pct = (change / float(prev["Close"]) * 100) if prev["Close"] else 0.0
        return {"available": True, "price": price, "change": change, "change_pct": change_pct,
                "source": f"Yahoo Finance ({sym})", "url": f"https://finance.yahoo.com/quote/{sym}"}
    except Exception:
        return None


def load_gift_nifty():
    env_result = _from_env_symbol()
    if env_result:
        return env_result
    try:
        r = requests.get(NSEIX_URL, timeout=12, headers={"User-Agent": "Mozilla/5.0 JarvisTradingAssistant/3.0"})
        r.raise_for_status()
        html = r.text
        # NSE IX currently exposes the near-month GIFT NIFTY future on its public page.
        patterns = [
            r"Near month GIFT NIFTY Future.*?([0-9]{2,3},?[0-9]{3}(?:\.[0-9]+)?).*?([+-]?[0-9]+(?:\.[0-9]+)?)\s*\(([-+]?[0-9]+(?:\.[0-9]+)?)%\)",
            r"GIFT NIFTY.*?([0-9]{2,3},?[0-9]{3}(?:\.[0-9]+)?).*?([+-]?[0-9]+(?:\.[0-9]+)?)\s*\(([-+]?[0-9]+(?:\.[0-9]+)?)%\)"
        ]
        for pat in patterns:
            m = re.search(pat, html, re.I | re.S)
            if m:
                return {"available": True, "price": float(m.group(1).replace(",", "")),
                        "change": float(m.group(2)), "change_pct": float(m.group(3)),
                        "source": "NSE International Exchange (NSE IX)", "url": NSEIX_URL}
        return {"available": False, "message": "NSE IX did not expose a parsable live GIFT NIFTY value right now.",
                "source": "NSE International Exchange (NSE IX)", "url": NSEIX_URL}
    except Exception as e:
        return {"available": False, "message": f"NSE IX GIFT Nifty feed error: {e}",
                "source": "NSE International Exchange (NSE IX)", "url": NSEIX_URL}
