class MasterAggregator:
    def decide(self, technical, sentiment_score, celestial):
        tech = float(max(-100, min(100, technical.get("score", 0))))
        sent = float(max(-1, min(1, sentiment_score))) * 100
        cel = float(max(-100, min(100, celestial.get("score", 0))))
        regime = technical.get("regime", "NORMAL")

        if regime == "HIGH_VOL":
            weights = (0.50, 0.35, 0.15)
        elif regime == "LOW_VOL":
            weights = (0.65, 0.25, 0.10)
        else:
            weights = (0.60, 0.25, 0.15)

        confidence = tech*weights[0] + sent*weights[1] + cel*weights[2]
        confidence = float(max(-100, min(100, confidence)))

        bull_confluence = tech >= 55 and sent >= -20 and cel >= -20
        bear_confluence = tech <= -55 and sent <= 20 and cel <= 20

        if bull_confluence and confidence >= 50:
            action = "BUY CALL"
        elif bear_confluence and confidence <= -50:
            action = "BUY PUT"
        elif confidence <= -70 or sent <= -90:
            action = "SELL / EXIT"
        else:
            action = "HOLD"

        reason = (
            f"T/S/C={tech:+.0f}/{sent:+.0f}/{cel:+.0f}; "
            f"weights={weights[0]:.2f}/{weights[1]:.2f}/{weights[2]:.2f}"
        )
        return {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "regime": regime,
            "weights": weights,
        }
