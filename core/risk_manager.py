class RiskManager:
    def __init__(self, sl_atr=1.5, tp1_atr=1.5, tp2_atr=3.0):
        self.sl_atr = sl_atr
        self.tp1_atr = tp1_atr
        self.tp2_atr = tp2_atr

    def calculate(self, entry, atr, side):
        entry = float(entry)
        atr = max(float(atr), 0.0)

        if side == "BUY":
            return {
                "entry": entry,
                "sl": entry - atr * self.sl_atr,
                "tp1": entry + atr * self.tp1_atr,
                "tp2": entry + atr * self.tp2_atr,
            }
        if side == "SELL":
            return {
                "entry": entry,
                "sl": entry + atr * self.sl_atr,
                "tp1": entry - atr * self.tp1_atr,
                "tp2": entry - atr * self.tp2_atr,
            }
        return {"entry": entry, "sl": entry, "tp1": entry, "tp2": entry}
