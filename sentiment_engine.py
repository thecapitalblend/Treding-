from __future__ import annotations
import re
import numpy as np

class SentimentEngine:
    """Optional FinBERT engine with transparent keyword fallback."""

    def __init__(self, enabled=False):
        self.analyzer = None
        if enabled:
            try:
                from transformers import pipeline
                self.analyzer = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert",
                    truncation=True
                )
            except Exception:
                self.analyzer = None

    def analyze_headline(self, text):
        text = (text or "").strip()
        if not text:
            return 0.0

        if self.analyzer:
            try:
                result = self.analyzer(text)[0]
                label, score = result["label"].lower(), float(result["score"])
                return score if label == "positive" else -score if label == "negative" else 0.0
            except Exception:
                pass

        positive = {"bullish","surge","rally","growth","profit","beats","strong","upgrade","positive","inflow","record"}
        negative = {"bearish","crash","fall","loss","miss","weak","downgrade","negative","outflow","risk","panic"}
        words = set(re.findall(r"[a-zA-Z]+", text.lower()))
        p, n = len(words & positive), len(words & negative)
        if p == n:
            return 0.0
        return max(-1.0, min(1.0, (p-n)/max(3, p+n)))

    def aggregate(self, headlines):
        headlines = [h for h in headlines if str(h).strip()]
        if not headlines:
            return 0.0
        scores = [self.analyze_headline(h) for h in headlines]
        weights = np.exp(np.linspace(-1, 0, len(scores)))
        return float(np.average(scores, weights=weights))
