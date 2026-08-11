from core.data import load_market_data
from core.indicators import add_indicators

HIGHER_TF = {"1m": ("5m", "1mo"), "5m": ("15m", "1mo"), "15m": ("1h", "3mo"),
             "30m": ("1h", "3mo"), "1h": ("1d", "1y"), "1d": ("1wk", "2y")}


def _trend_of(df):
    r = df.iloc[-1]
    if r.Close > r.EMA20 > r.EMA50:
        return "BULLISH"
    if r.Close < r.EMA20 < r.EMA50:
        return "BEARISH"
    return "NEUTRAL"


def mtf_confirmation(symbol, base_interval, base_trend):
    """Check the base-timeframe trend against a higher timeframe's trend.
    Returns aligned=True only when both agree and neither is NEUTRAL."""
    higher_interval, period = HIGHER_TF.get(base_interval, ("1d", "1y"))
    try:
        htf_df = add_indicators(load_market_data(symbol, period, higher_interval))
        if htf_df.empty or len(htf_df) < 55:
            return {"available": False, "message": f"Not enough {higher_interval} history for MTF confirmation."}
        htf_trend = _trend_of(htf_df)
        aligned = (base_trend == htf_trend) and base_trend != "NEUTRAL"
        return {"available": True, "higher_interval": higher_interval,
                "higher_trend": htf_trend, "base_trend": base_trend, "aligned": aligned}
    except Exception as e:
        return {"available": False, "message": f"MTF confirmation error: {e}"}
