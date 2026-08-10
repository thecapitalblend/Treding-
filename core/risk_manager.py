class RiskManager:
    def calculate(self, price, atr, direction):
        price = float(price)
        atr = max(float(atr), price * 0.001)
        if direction == "BUY":
            sl, t1, t2 = price-1.5*atr, price+1.5*atr, price+3*atr
        elif direction == "SELL":
            sl, t1, t2 = price+1.5*atr, price-1.5*atr, price-3*atr
        else:
            sl = t1 = t2 = price
        return {"entry": price, "stop_loss": sl, "target1": t1, "target2": t2}
