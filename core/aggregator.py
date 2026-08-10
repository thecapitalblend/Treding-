class MasterAggregator:
    def calculate(self, technical, sentiment, celestial):
        t = float(technical.get("score", 0))
        s = float(sentiment.get("score", 0)) * 100
        c = float(celestial.get("score", 0))
        confidence = max(-100, min(100, 0.65*t + 0.25*s + 0.10*c))
        signal = "BUY" if confidence >= 55 else "SELL" if confidence <= -55 else "HOLD"
        return {
            "confidence": confidence,
            "signal": signal,
            "components": {"technical": t, "sentiment": s, "celestial": c},
            "reason": f"Technical {t:+.0f}, sentiment {s:+.0f}, celestial {c:+.0f}."
        }
