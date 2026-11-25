"""Gadget (GDG) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: device claimed lost within weeks of a policy upgrade.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "GDG"
HIGH_RISK_CAUSES = ('ACCIDENTAL_DAMAGE', 'LIQUID_DAMAGE')
LARGE_LOSS_GBP = 4000
EARLY_WINDOW_DAYS = 45


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="GDG_CAUSE", weight=0.13, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="GDG_LARGE_LOSS", weight=0.13, detail="above 4000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="GDG_EARLY", weight=0.18, detail="device claimed lost within weeks of a policy upgrade"))
    if attrs.get("bought_second_hand") in (True, "yes") or (isinstance(attrs.get("bought_second_hand"), (int, float)) and attrs["bought_second_hand"] >= 3):
        out.append(Indicator(code="GDG_BOUGHT_SECOND_HAND", weight=0.24, detail="bought second hand at or above 3"))
    if attrs.get("proof_of_purchase") in (False, "no", 0):
        out.append(Indicator(code="GDG_NO_PROOF_OF_PURCHASE", weight=0.29, detail="proof of purchase missing"))
    if attrs.get("device_age_months") == "unknown":
        out.append(Indicator(code="GDG_DEVICE_AGE_MONTHS_UNKNOWN", weight=0.09, detail="device age months not given"))
    return out
