"""Angel One SmartAPI connector -- live NIFTY 50 LTP + candle data.

SETUP (one time):
  1. Create an app at https://smartapi.angelone.in -> get API Key.
  2. Enable TOTP: https://smartapi.angelbroking.com/enable-totp
     (scan the QR with Google Authenticator / any TOTP app, and also save
     the raw QR "secret" string -- that secret is what goes in
     ANGELONE_TOTP_SECRET below, NOT the 6-digit code itself.)
  3. Set these environment variables before running streamlit (never hardcode
     them in code or commit them):
       ANGELONE_API_KEY
       ANGELONE_CLIENT_CODE
       ANGELONE_PIN            (your trading PIN/password)
       ANGELONE_TOTP_SECRET    (the base32 secret from step 2)
  4. pip install smartapi-python pyotp websocket-client

This module never stores credentials in code or in files -- it only reads
them from the environment at runtime.
"""

import os
from datetime import datetime, timedelta

try:
    from SmartApi import SmartConnect
    import pyotp
    OK = True
except Exception:
    OK = False

# Well-known Angel One instrument token for the NSE NIFTY 50 index.
# Verify against the latest scrip master if it ever stops matching:
# https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json
NIFTY50_TOKEN = "99926000"
NIFTY50_SYMBOL = "Nifty 50"
NIFTY50_EXCHANGE = "NSE"

_session = {"client": None, "feed_token": None, "logged_in_at": None}


def _creds_present():
    return all(os.environ.get(k) for k in
               ("ANGELONE_API_KEY", "ANGELONE_CLIENT_CODE", "ANGELONE_PIN", "ANGELONE_TOTP_SECRET"))


def login():
    """Log in (or reuse an existing session for up to 6 hours) and return
    {'available': bool, 'message'?: str}."""
    if not OK:
        return {"available": False, "message": "smartapi-python / pyotp not installed. Run: pip install smartapi-python pyotp websocket-client"}
    if not _creds_present():
        return {"available": False, "message": "Angel One credentials not set. Export ANGELONE_API_KEY, ANGELONE_CLIENT_CODE, ANGELONE_PIN, ANGELONE_TOTP_SECRET as environment variables."}

    if _session["client"] and _session["logged_in_at"] and \
       datetime.now() - _session["logged_in_at"] < timedelta(hours=6):
        return {"available": True}

    try:
        api_key = os.environ["ANGELONE_API_KEY"]
        client_code = os.environ["ANGELONE_CLIENT_CODE"]
        pin = os.environ["ANGELONE_PIN"]
        totp_secret = os.environ["ANGELONE_TOTP_SECRET"]

        totp = pyotp.TOTP(totp_secret).now()
        client = SmartConnect(api_key)
        data = client.generateSession(client_code, pin, totp)
        if not data.get("status"):
            return {"available": False, "message": f"Angel One login failed: {data.get('message', data)}"}

        feed_token = client.getfeedToken()
        _session["client"] = client
        _session["feed_token"] = feed_token
        _session["logged_in_at"] = datetime.now()
        return {"available": True}
    except Exception as e:
        return {"available": False, "message": f"Angel One login error: {e}"}


def get_nifty_ltp():
    """Return live NIFTY 50 LTP quote, or an error dict."""
    status = login()
    if not status["available"]:
        return status
    try:
        client = _session["client"]
        r = client.ltpData(NIFTY50_EXCHANGE, NIFTY50_SYMBOL, NIFTY50_TOKEN)
        if not r.get("status"):
            return {"available": False, "message": f"LTP fetch failed: {r.get('message', r)}"}
        d = r["data"]
        return {
            "available": True,
            "price": float(d["ltp"]),
            "open": float(d.get("open", 0) or 0),
            "high": float(d.get("high", 0) or 0),
            "low": float(d.get("low", 0) or 0),
            "close": float(d.get("close", 0) or 0),
            "source": "Angel One SmartAPI (live)",
        }
    except Exception as e:
        return {"available": False, "message": f"Angel One LTP error: {e}"}


def get_nifty_candles(interval="FIVE_MINUTE", days=5):
    """Return recent NIFTY 50 candles via Angel One historical API.
    interval: ONE_MINUTE, THREE_MINUTE, FIVE_MINUTE, TEN_MINUTE, FIFTEEN_MINUTE,
              THIRTY_MINUTE, ONE_HOUR, ONE_DAY
    """
    status = login()
    if not status["available"]:
        return status
    try:
        client = _session["client"]
        to_dt = datetime.now()
        from_dt = to_dt - timedelta(days=days)
        params = {
            "exchange": NIFTY50_EXCHANGE,
            "symboltoken": NIFTY50_TOKEN,
            "interval": interval,
            "fromdate": from_dt.strftime("%Y-%m-%d %H:%M"),
            "todate": to_dt.strftime("%Y-%m-%d %H:%M"),
        }
        r = client.getCandleData(params)
        if not r.get("status"):
            return {"available": False, "message": f"Candle fetch failed: {r.get('message', r)}"}
        rows = r["data"]  # each row: [timestamp, open, high, low, close, volume]
        return {"available": True, "candles": rows}
    except Exception as e:
        return {"available": False, "message": f"Angel One candle error: {e}"}
