import math

class RiskManager:
    def __init__(self, account_size, risk_per_trade_pct=1.0, atr_stop_multiplier=1.5, max_quantity=1000):
        self.account_size = account_size
        self.risk_per_trade_pct = risk_per_trade_pct
        self.atr_stop_multiplier = atr_stop_multiplier
        self.max_quantity = max_quantity

    def calculate(self, entry, atr, side):
        if entry <= 0 or atr <= 0:
            return {"quantity":0, "stop":None, "risk_amount":0}
        risk_amount = self.account_size * self.risk_per_trade_pct / 100
        stop_distance = atr * self.atr_stop_multiplier
        quantity = min(self.max_quantity, max(1, math.floor(risk_amount / stop_distance)))
        stop = entry - stop_distance if side.upper() == "BUY" else entry + stop_distance
        return {
            "quantity":quantity,
            "stop":round(stop,2),
            "risk_amount":round(risk_amount,2),
            "stop_distance":round(stop_distance,2)
        }
