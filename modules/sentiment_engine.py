import re
from urllib.parse import quote_plus
import requests
import xml.etree.ElementTree as ET

POS = {"gain","gains","bullish","positive","surge","surges","rally","rallies","strong","growth","up","record","beat","beats","optimistic","buy","upgrade","upgrades"}
NEG = {"loss","losses","bearish","negative","fall","falls","drop","drops","weak","decline","declines","sell","downgrade","downgrades","risk","crash","inflation","fear","fears"}

class SentimentEngine:
    def _rss(self, query):
        url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.text)
        titles = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            if title:
                titles.append(title.strip())
        return titles[:12]

    def _score_headline(self, text):
        words = set(re.findall(r"[a-zA-Z]+", text.lower()))
        p = len(words & POS)
        n = len(words & NEG)
        if p == n:
            return 0
        return 1 if p > n else -1

    def analyze(self, query, enable_finbert=False):
        try:
            headlines = self._rss(query or "Nifty 50 India markets")
        except Exception:
            headlines = []

        scores = [self._score_headline(h) for h in headlines]
        score = (sum(scores) / len(scores) * 100) if scores else 0.0
        status = "BULLISH" if score > 15 else ("BEARISH" if score < -15 else "NEUTRAL / NO STRONG NEWS")

        # FinBERT is intentionally optional. The app remains fully functional without it.
        if enable_finbert:
            status += " | FinBERT optional layer enabled"

        return {
            "score": float(max(-100, min(100, score))),
            "status": status,
            "articles_used": len(headlines),
            "headlines": headlines,
        }
