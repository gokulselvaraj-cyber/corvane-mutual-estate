"""Home contents (CNT) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: high-value items with no receipts and no forced entry.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "CNT"
HIGH_RISK_CAUSES = ('FIRE', 'LOSS_AWAY')
LARGE_LOSS_GBP = 2500
EARLY_WINDOW_DAYS = 45


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="CNT_CAUSE", weight=0.17, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="CNT_LARGE_LOSS", weight=0.21, detail="above 2500 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="CNT_EARLY", weight=0.23, detail="high-value items with no receipts and no forced entry"))
    if attrs.get("receipts_provided") in (True, "yes") or (isinstance(attrs.get("receipts_provided"), (int, float)) and attrs["receipts_provided"] >= 2):
        out.append(Indicator(code="CNT_RECEIPTS_PROVIDED", weight=0.09, detail="receipts provided at or above 2"))
    if attrs.get("single_item_max") in (False, "no", 0):
        out.append(Indicator(code="CNT_NO_SINGLE_ITEM_MAX", weight=0.07, detail="single item max missing"))
    if attrs.get("police_reference") == "unknown":
        out.append(Indicator(code="CNT_POLICE_REFERENCE_UNKNOWN", weight=0.16, detail="police reference not given"))
    return out
