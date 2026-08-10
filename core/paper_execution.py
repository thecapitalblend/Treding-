from pathlib import Path
from datetime import datetime, timezone
import csv

class PaperExecutionEngine:
    def __init__(self, path="logs/paper_trades.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, decision, levels, symbol):
        new_file = not self.path.exists()
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["timestamp_utc","symbol","signal","confidence","entry","sl","tp1","tp2"])
            writer.writerow([
                datetime.now(timezone.utc).isoformat(),
                symbol,
                decision["signal"],
                round(decision["confidence"], 2),
                round(levels["entry"], 2),
                round(levels["sl"], 2),
                round(levels["tp1"], 2),
                round(levels["tp2"], 2),
            ])
