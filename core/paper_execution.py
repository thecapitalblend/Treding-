from datetime import datetime, timezone
class PaperExecutionEngine:
    def __init__(self): self.orders = []
    def place_order(self, symbol, side, quantity, price):
        order = {"timestamp": datetime.now(timezone.utc).isoformat(),
                 "symbol": symbol, "side": side, "quantity": quantity,
                 "price": price, "mode": "PAPER"}
        self.orders.append(order)
        return order
