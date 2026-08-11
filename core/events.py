from datetime import datetime, timedelta

# NSE moved NIFTY 50 weekly expiry from Thursday to Tuesday effective
# 1 Sept 2025 (SEBI circular). Monthly expiry = last Tuesday of the month.
# This does NOT account for exchange holidays shifting expiry to the
# previous trading day -- add known holidays to HOLIDAYS below if needed.
HOLIDAYS = set()  # e.g. {"2026-08-15", "2026-10-02"}

WEEKLY_EXPIRY_WEEKDAY = 1  # Monday=0 ... Tuesday=1


def _is_last_weekday_of_month(d, weekday):
    nxt = d + timedelta(days=7)
    return d.weekday() == weekday and nxt.month != d.month


def expiry_flag(now=None):
    now = now or datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    is_weekly = now.weekday() == WEEKLY_EXPIRY_WEEKDAY
    is_monthly = _is_last_weekday_of_month(now, WEEKLY_EXPIRY_WEEKDAY)
    is_holiday = today_str in HOLIDAYS

    if is_holiday:
        return {"expiry_today": False, "note": "Marked as an exchange holiday in the local HOLIDAYS list -- expiry likely shifted to the previous trading day. Verify against the official NSE circular."}
    if is_monthly:
        return {"expiry_today": True, "note": "Monthly NIFTY expiry (last Tuesday) -- expect elevated volatility and less reliable intraday signals."}
    if is_weekly:
        return {"expiry_today": True, "note": "Weekly NIFTY expiry (Tuesday) -- expect elevated volatility and less reliable intraday signals."}
    return {"expiry_today": False, "note": "Not an expiry day."}
