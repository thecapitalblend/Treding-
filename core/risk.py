def position_size(capital, risk_pct, entry, stop, lot_size=75):
    """ATR/stop-based position sizing.
    capital: total trading capital (INR)
    risk_pct: % of capital willing to risk on this one trade (e.g. 1.0 for 1%)
    entry, stop: price levels from the decision engine
    lot_size: NIFTY lot size (check current NSE lot size -- it changes periodically)
    Returns max lots/quantity so that a stop-loss hit loses at most risk_pct of capital.
    """
    risk_amount = capital * (risk_pct / 100.0)
    per_unit_risk = abs(entry - stop)
    if per_unit_risk <= 0:
        return {"available": False, "message": "Entry and stop are equal -- cannot size position."}
    max_qty = risk_amount / per_unit_risk
    max_lots = int(max_qty // lot_size)
    actual_qty = max_lots * lot_size
    actual_risk = actual_qty * per_unit_risk
    return {
        "available": True,
        "risk_amount": risk_amount,
        "per_unit_risk": per_unit_risk,
        "max_lots": max_lots,
        "actual_qty": actual_qty,
        "actual_risk": actual_risk,
        "warning": None if max_lots > 0 else "Risk amount too small for even 1 lot at this stop distance -- reduce risk_pct is not the fix here, this trade's stop is too wide for your capital.",
    }
