from datetime import datetime, timezone
import uuid

class PaperExecutionEngine:
    """Safe simulator. No broker order is sent."""

    def __init__(self):
        self.orders = []

    def place_order(self, symbol, side, quantity, price):
        order = {
            "order_id":str(uuid.uuid4()),
            "timestamp":datetime.now(timezone.utc).isoformat(),
            "symbol":symbol,
            "side":side,
            "quantity":int(quantity),
            "price":float(price),
            "status":"PAPER_FILLED"
        }
        self.orders.append(order)
        return order
