"""Professional indemnity (PIN) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: claim follows a fee dispute with the same client.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "PIN"
HIGH_RISK_CAUSES = ('DEFAMATION', 'LOSS_OF_DOCUMENTS')
LARGE_LOSS_GBP = 2500
EARLY_WINDOW_DAYS = 14


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="PIN_CAUSE", weight=0.11, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="PIN_LARGE_LOSS", weight=0.16, detail="above 2500 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="PIN_EARLY", weight=0.23, detail="claim follows a fee dispute with the same client"))
    if attrs.get("prior_notifications") in (True, "yes") or (isinstance(attrs.get("prior_notifications"), (int, float)) and attrs["prior_notifications"] >= 5):
        out.append(Indicator(code="PIN_PRIOR_NOTIFICATIONS", weight=0.25, detail="prior notifications at or above 5"))
    if attrs.get("years_qualified") in (False, "no", 0):
        out.append(Indicator(code="PIN_NO_YEARS_QUALIFIED", weight=0.23, detail="years qualified missing"))
    if attrs.get("profession") == "unknown":
        out.append(Indicator(code="PIN_PROFESSION_UNKNOWN", weight=0.15, detail="profession not given"))
    return out
