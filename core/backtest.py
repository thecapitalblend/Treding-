import numpy as np
from core.decision import signal_history


def backtest(df, atr_stop_mult=1.25, target_mult=1.5, max_hold_bars=40):
    """Walk-forward simulation of BUY CALL / BUY PUT signal transitions.
    Entry = close at the signal bar. Exit = whichever of stop-loss / target1
    is hit first within max_hold_bars, else exit at max_hold_bars close.
    Returns win rate, avg R-multiple, and trade count. This is a simple
    bar-close backtest (no intrabar fill precision, no slippage/costs)."""
    raw_signals, _, transitions = signal_history(df)
    trades = []
    idx_list = list(df.index)

    for entry_time, sig, _score in transitions:
        i = idx_list.index(entry_time)
        if i + 1 >= len(df):
            continue
        entry = float(df.iloc[i].Close)
        atr = float(df.iloc[i].ATR) if np.isfinite(df.iloc[i].ATR) else None
        if not atr or atr <= 0:
            continue
        if sig == "BUY CALL":
            stop, target = entry - atr_stop_mult * atr, entry + target_mult * atr
        else:
            stop, target = entry + atr_stop_mult * atr, entry - target_mult * atr

        outcome, exit_price = None, None
        for j in range(i + 1, min(i + 1 + max_hold_bars, len(df))):
            hi, lo = float(df.iloc[j].High), float(df.iloc[j].Low)
            if sig == "BUY CALL":
                if lo <= stop:
                    outcome, exit_price = "LOSS", stop; break
                if hi >= target:
                    outcome, exit_price = "WIN", target; break
            else:
                if hi >= stop:
                    outcome, exit_price = "LOSS", stop; break
                if lo <= target:
                    outcome, exit_price = "WIN", target; break
        if outcome is None:
            j = min(i + max_hold_bars, len(df) - 1)
            exit_price = float(df.iloc[j].Close)
            moved_favorably = (exit_price > entry) if sig == "BUY CALL" else (exit_price < entry)
            outcome = "WIN" if moved_favorably else "LOSS"

        risk = abs(entry - stop)
        r_multiple = (exit_price - entry) / risk if sig == "BUY CALL" else (entry - exit_price) / risk
        trades.append({"time": entry_time, "signal": sig, "entry": entry, "exit": exit_price,
                        "outcome": outcome, "r_multiple": r_multiple})

    if not trades:
        return {"available": False, "message": "No signal transitions in this data window to backtest."}

    wins = [t for t in trades if t["outcome"] == "WIN"]
    win_rate = len(wins) / len(trades) * 100
    avg_r = float(np.mean([t["r_multiple"] for t in trades]))
    return {"available": True, "trades": trades, "trade_count": len(trades),
            "win_rate": win_rate, "avg_r_multiple": avg_r}
