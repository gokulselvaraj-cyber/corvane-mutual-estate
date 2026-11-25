"""Home buildings (HOM) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: damage reported after a long unoccupied period.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "HOM"
HIGH_RISK_CAUSES = ('FIRE', 'SUBSIDENCE')
LARGE_LOSS_GBP = 12000
EARLY_WINDOW_DAYS = 14


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="HOM_CAUSE", weight=0.15, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="HOM_LARGE_LOSS", weight=0.14, detail="above 12000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="HOM_EARLY", weight=0.14, detail="damage reported after a long unoccupied period"))
    if attrs.get("property_age_years") in (True, "yes") or (isinstance(attrs.get("property_age_years"), (int, float)) and attrs["property_age_years"] >= 10):
        out.append(Indicator(code="HOM_PROPERTY_AGE_YEARS", weight=0.15, detail="property age years at or above 10"))
    if attrs.get("unoccupied_days") in (False, "no", 0):
        out.append(Indicator(code="HOM_NO_UNOCCUPIED_DAYS", weight=0.21, detail="unoccupied days missing"))
    if attrs.get("roof_type") == "unknown":
        out.append(Indicator(code="HOM_ROOF_TYPE_UNKNOWN", weight=0.25, detail="roof type not given"))
    return out
