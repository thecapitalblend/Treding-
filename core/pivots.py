import yfinance as yf


def get_pivots(symbol="^NSEI"):
    """Classic + Camarilla pivot points from the previous completed trading day."""
    try:
        daily = yf.download(symbol, period="10d", interval="1d", progress=False, threads=False, auto_adjust=False)
        if daily is None or daily.empty or len(daily) < 2:
            return {"available": False, "message": "Not enough daily history for pivot calculation."}
        if hasattr(daily.columns, "levels"):
            daily.columns = [c[0] for c in daily.columns]
        prev = daily.iloc[-2]  # last fully completed day
        H, L, C = float(prev["High"]), float(prev["Low"]), float(prev["Close"])
        P = (H + L + C) / 3
        classic = {
            "pivot": P,
            "r1": 2 * P - L, "r2": P + (H - L), "r3": H + 2 * (P - L),
            "s1": 2 * P - H, "s2": P - (H - L), "s3": L - 2 * (H - P),
        }
        rng = H - L
        camarilla = {
            "r4": C + rng * 1.1 / 2, "r3": C + rng * 1.1 / 4,
            "r2": C + rng * 1.1 / 6, "r1": C + rng * 1.1 / 12,
            "s1": C - rng * 1.1 / 12, "s2": C - rng * 1.1 / 6,
            "s3": C - rng * 1.1 / 4, "s4": C - rng * 1.1 / 2,
        }
        return {"available": True, "prev_high": H, "prev_low": L, "prev_close": C,
                "classic": classic, "camarilla": camarilla}
    except Exception as e:
        return {"available": False, "message": f"Pivot calculation error: {e}"}
