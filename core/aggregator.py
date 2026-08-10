class MasterAggregator:
    """Weighted ensemble of technical, sentiment and celestial research signals."""

    def decide(self, technical_score, sentiment_score, celestial_score, atr=0.0, regime="NORMAL"):
        # Technical is the primary signal. Sentiment/celestial are confirmation layers.
        tech = max(-100.0, min(100.0, float(technical_score)))
        sent = max(-1.0, min(1.0, float(sentiment_score))) * 100.0
        cel = max(-100.0, min(100.0, float(celestial_score)))

        if regime == "HIGH_VOL":
            weights = (0.45, 0.40, 0.15)
        elif regime == "LOW_VOL":
            weights = (0.65, 0.25, 0.10)
        else:
            weights = (0.55, 0.30, 0.15)

        confidence = tech * weights[0] + sent * weights[1] + cel * weights[2]
        confidence = max(-100.0, min(100.0, confidence))

        if confidence >= 60:
            signal = "BUY"
        elif confidence <= -60:
            signal = "SELL"
        else:
            signal = "HOLD"

        reason = (
            f"weights T/S/C={weights[0]:.2f}/{weights[1]:.2f}/{weights[2]:.2f}; "
            f"components={tech:.0f}/{sent:.0f}/{cel:.0f}"
        )
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "regime": regime,
        }
