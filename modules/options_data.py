import requests
import yfinance as yf

NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_HOME_URL = "https://www.nseindia.com/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JarvisTradingAssistant/3.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
}


def get_india_vix():
    try:
        df = yf.download("^INDIAVIX", period="5d", interval="1d", progress=False, threads=False, auto_adjust=False)
        if df is None or df.empty:
            return {"available": False, "message": "No India VIX data returned."}
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] for c in df.columns]
        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2]) if len(df) > 1 else last
        return {"available": True, "vix": last, "change_pct": (last - prev) / prev * 100 if prev else 0.0}
    except Exception as e:
        return {"available": False, "message": f"India VIX error: {e}"}


def get_option_chain_summary():
    """PCR, total OI, and Max Pain strike from NSE's public option-chain API.
    NSE requires a warmed-up session (cookies from the homepage) before the
    API call succeeds, and may still rate-limit or block server IPs."""
    try:
        s = requests.Session()
        s.headers.update(HEADERS)
        s.get(NSE_HOME_URL, timeout=10)  # warm up cookies
        r = s.get(NSE_OPTION_CHAIN_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        records = data.get("records", {}).get("data", [])
        if not records:
            return {"available": False, "message": "NSE option chain returned no records."}

        total_ce_oi = sum(row.get("CE", {}).get("openInterest", 0) for row in records if "CE" in row)
        total_pe_oi = sum(row.get("PE", {}).get("openInterest", 0) for row in records if "PE" in row)
        pcr = (total_pe_oi / total_ce_oi) if total_ce_oi else None

        strikes = sorted({row["strikePrice"] for row in records})
        pain = {}
        for expiry_strike in strikes:
            total_loss = 0.0
            for row in records:
                strike = row["strikePrice"]
                ce_oi = row.get("CE", {}).get("openInterest", 0)
                pe_oi = row.get("PE", {}).get("openInterest", 0)
                if expiry_strike > strike:
                    total_loss += (expiry_strike - strike) * ce_oi
                if expiry_strike < strike:
                    total_loss += (strike - expiry_strike) * pe_oi
            pain[expiry_strike] = total_loss
        max_pain_strike = min(pain, key=pain.get) if pain else None

        underlying = data.get("records", {}).get("underlyingValue")
        return {"available": True, "pcr": pcr, "total_ce_oi": total_ce_oi, "total_pe_oi": total_pe_oi,
                "max_pain": max_pain_strike, "underlying": underlying}
    except Exception as e:
        return {"available": False, "message": f"NSE option chain fetch failed (NSE often blocks server IPs/needs a browser session): {e}"}
