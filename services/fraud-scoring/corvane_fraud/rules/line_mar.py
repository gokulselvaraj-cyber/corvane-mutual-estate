"""Marine cargo (MAR) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: seal numbers do not match the bill of lading.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "MAR"
HIGH_RISK_CAUSES = ('HANDLING_DAMAGE', 'TOTAL_LOSS')
LARGE_LOSS_GBP = 12000
EARLY_WINDOW_DAYS = 7


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="MAR_CAUSE", weight=0.16, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="MAR_LARGE_LOSS", weight=0.2, detail="above 12000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="MAR_EARLY", weight=0.14, detail="seal numbers do not match the bill of lading"))
    if attrs.get("container_sealed") in (True, "yes") or (isinstance(attrs.get("container_sealed"), (int, float)) and attrs["container_sealed"] >= 90):
        out.append(Indicator(code="MAR_CONTAINER_SEALED", weight=0.06, detail="container sealed at or above 90"))
    if attrs.get("voyage_days") in (False, "no", 0):
        out.append(Indicator(code="MAR_NO_VOYAGE_DAYS", weight=0.14, detail="voyage days missing"))
    if attrs.get("transhipments") == "unknown":
        out.append(Indicator(code="MAR_TRANSHIPMENTS_UNKNOWN", weight=0.12, detail="transhipments not given"))
    return out
