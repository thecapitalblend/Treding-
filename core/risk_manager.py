class RiskManager:
    @staticmethod
    def levels(price, atr, side, sl_mult=1.2, t1_mult=1.5, t2_mult=2.5):
        atr = max(float(atr), 1e-9)
        price = float(price)
        if side == "LONG":
            return price, price - sl_mult*atr, price + t1_mult*atr, price + t2_mult*atr
        if side == "SHORT":
            return price, price + sl_mult*atr, price - t1_mult*atr, price - t2_mult*atr
        return price, price, price, price
