import re
import numpy as np
import requests
from bs4 import BeautifulSoup

class SentimentEngine:
    def __init__(self, enable_finbert=False):
        self.enabled = bool(enable_finbert)
        self.analyzer = None
        if self.enabled:
            try:
                from transformers import pipeline
                self.analyzer = pipeline("sentiment-analysis", model="ProsusAI/finbert")
            except Exception:
                self.analyzer = None
                self.enabled = False

    def fetch_headlines(self, query):
        url = "https://news.google.com/rss/search"
        try:
            r = requests.get(url, params={"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
                             timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "xml")
            return [i.title.get_text(strip=True) for i in soup.find_all("item")[:15] if i.title]
        except Exception:
            return []

    def analyze_headline(self, text):
        if self.analyzer is not None:
            try:
                result = self.analyzer(text[:1000])[0]
                label, score = result["label"].lower(), float(result["score"])
                return score if label == "positive" else -score if label == "negative" else 0.0
            except Exception:
                pass

        # Conservative keyword fallback; this is not a replacement for FinBERT.
        pos = ["gain", "surge", "rally", "growth", "profit", "bullish", "upgrade", "strong"]
        neg = ["fall", "drop", "crash", "loss", "bearish", "downgrade", "weak", "inflation"]
        t = text.lower()
        p = sum(t.count(w) for w in pos)
        n = sum(t.count(w) for w in neg)
        return max(-1, min(1, (p - n) / 3))

    def aggregate_market_sentiment(self, query):
        headlines = self.fetch_headlines(query)
        if not headlines:
            return 0.0, []

        scores = [self.analyze_headline(h) for h in headlines]
        weights = np.exp(np.linspace(-1, 0, len(scores)))
        score = float(np.average(scores, weights=weights))
        return max(-1.0, min(1.0, score)), headlines

    def status(self, score, headlines):
        if not headlines:
            return "NEUTRAL / NO NEWS"
        if score >= 0.25:
            return "POSITIVE"
        if score <= -0.25:
            return "NEGATIVE"
        return "NEUTRAL"
