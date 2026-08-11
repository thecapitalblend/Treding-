import requests
import yfinance as yf

try:
    from nsepython import nse_optionchain_scrapper
    NSEPYTHON_OK = True
except Exception:
    NSEPYTHON_OK = False

NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
NSE_HOME_URL = "https://www.nseindia.com/"
NSE_OC_PAGE_URL = "https://www.nseindia.com/option-chain"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/option-chain",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
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


def _summarize(records, underlying):
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
    return {"available": True, "pcr": pcr, "total_ce_oi": total_ce_oi, "total_pe_oi": total_pe_oi,
            "max_pain": max_pain_strike, "underlying": underlying}


def _fetch_via_requests():
    s = requests.Session()
    s.headers.update(HEADERS)
    # NSE needs a "warm" session: hit the homepage, then the option-chain
    # page itself (sets additional cookies), before the JSON API will
    # respond instead of 401/403/404.
    s.get(NSE_HOME_URL, timeout=10)
    s.get(NSE_OC_PAGE_URL, timeout=10)
    r = s.get(NSE_OPTION_CHAIN_URL, timeout=10, headers={**HEADERS, "Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    records = data.get("records", {}).get("data", [])
    if not records:
        raise RuntimeError("NSE option chain returned no records.")
    return _summarize(records, data.get("records", {}).get("underlyingValue"))


def _fetch_via_nsepython():
    data = nse_optionchain_scrapper("NIFTY")
    records = data.get("records", {}).get("data", [])
    if not records:
        raise RuntimeError("nsepython returned no records.")
    return _summarize(records, data.get("records", {}).get("underlyingValue"))


def get_option_chain_summary():
    """PCR, total OI, and Max Pain strike for NIFTY. Tries a direct
    requests-based fetch first (with a proper browser-like warm-up), then
    falls back to the nsepython library if installed. NSE still blocks many
    cloud/server IPs outright regardless of headers -- if both fail, this
    is most likely an IP-level block, not a code bug."""
    try:
        return _fetch_via_requests()
    except Exception as e1:
        if NSEPYTHON_OK:
            try:
                return _fetch_via_nsepython()
            except Exception as e2:
                return {"available": False, "message": f"Direct fetch failed ({e1}); nsepython fallback also failed ({e2})."}
        return {"available": False, "message": f"NSE option chain fetch failed: {e1}. Install nsepython for a fallback: pip install nsepython"}
