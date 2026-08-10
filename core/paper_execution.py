from pathlib import Path
import json

class PaperExecutionEngine:
    def __init__(self, path="logs/paper_trades.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, trade):
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trade, default=str) + "\n")
