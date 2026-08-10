from dataclasses import dataclass

@dataclass
class Decision:
    confidence: float
    action: str
    technical: float
    sentiment: float
    celestial: float
    regime: str
    explanation: str

class MasterAggregator:
    def __init__(self, technical_weight=.55, sentiment_weight=.25, celestial_weight=.20,
                 buy_threshold=60, sell_threshold=-60, risk_off_threshold=-85):
        self.base = {"technical":technical_weight, "sentiment":sentiment_weight, "celestial":celestial_weight}
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.risk_off_threshold = risk_off_threshold

    def detect_regime(self, atr, price, news_abs):
        atr_pct = atr / price * 100 if price else 0
        if news_abs >= .75: return "NEWS_SHOCK"
        if atr_pct >= 1.5: return "HIGH_VOLATILITY"
        if atr_pct <= .4: return "LOW_VOLATILITY"
        return "NORMAL"

    def decide(self, technical_score, sentiment_score, celestial_score, atr, price):
        regime = self.detect_regime(atr, price, abs(sentiment_score))
        w = self.base.copy()
        if regime == "NEWS_SHOCK":
            w = {"technical":.25,"sentiment":.60,"celestial":.15}
        elif regime == "HIGH_VOLATILITY":
            w = {"technical":.40,"sentiment":.35,"celestial":.25}
        elif regime == "LOW_VOLATILITY":
            w = {"technical":.65,"sentiment":.20,"celestial":.15}

        score = technical_score*w["technical"] + sentiment_score*100*w["sentiment"] + celestial_score*w["celestial"]
        score = max(-100, min(100, score))

        if score <= self.risk_off_threshold: action = "RISK-OFF / EXIT"
        elif score >= self.buy_threshold: action = "BUY"
        elif score <= self.sell_threshold: action = "SELL"
        else: action = "HOLD"

        return Decision(
            float(score), action, technical_score, sentiment_score, celestial_score, regime,
            f"Regime={regime}; weights T/S/C={w['technical']:.2f}/{w['sentiment']:.2f}/{w['celestial']:.2f}"
        )
