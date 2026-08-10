class SentimentEngine:
    def __init__(self, enabled=False):
        self.analyzer=None
        if enabled:
            try:
                from transformers import pipeline
                self.analyzer=pipeline("sentiment-analysis",model="ProsusAI/finbert")
            except Exception: self.analyzer=None

    def market_score(self, headlines):
        if not headlines or not self.analyzer:
            return {"score":0.0,"label":"NEUTRAL / NO NEWS"}
        vals=[]
        for text in headlines:
            try:
                r=self.analyzer(text,truncation=True)[0]
                v=float(r["score"])
                vals.append(v if r["label"].lower()=="positive" else -v if r["label"].lower()=="negative" else 0)
            except Exception: vals.append(0)
        score=sum(vals)/len(vals)
        return {"score":score,"label":"POSITIVE" if score>.15 else "NEGATIVE" if score<-.15 else "NEUTRAL"}
