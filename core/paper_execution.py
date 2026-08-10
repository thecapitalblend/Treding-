from pathlib import Path
import pandas as pd

class PaperExecutionEngine:
    def __init__(self, path="data/paper_journal.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, row: dict):
        df = self.read()
        new = pd.DataFrame([row])
        out = pd.concat([df, new], ignore_index=True)
        out.to_csv(self.path, index=False)

    def read(self):
        if self.path.exists():
            try:
                return pd.read_csv(self.path)
            except Exception:
                pass
        return pd.DataFrame()
