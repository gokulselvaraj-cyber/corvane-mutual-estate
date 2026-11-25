"""Motor (MTR) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: whiplash claimed after a low-speed impact.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "MTR"
HIGH_RISK_CAUSES = ('COLLISION_SINGLE', 'FIRE_VEHICLE')
LARGE_LOSS_GBP = 60000
EARLY_WINDOW_DAYS = 60


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="MTR_CAUSE", weight=0.16, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="MTR_LARGE_LOSS", weight=0.24, detail="above 60000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="MTR_EARLY", weight=0.23, detail="whiplash claimed after a low-speed impact"))
    if attrs.get("third_party_count") in (True, "yes") or (isinstance(attrs.get("third_party_count"), (int, float)) and attrs["third_party_count"] >= 2):
        out.append(Indicator(code="MTR_THIRD_PARTY_COUNT", weight=0.18, detail="third party count at or above 2"))
    if attrs.get("garaged") in (False, "no", 0):
        out.append(Indicator(code="MTR_NO_GARAGED", weight=0.22, detail="garaged missing"))
    if attrs.get("dashcam_footage") == "unknown":
        out.append(Indicator(code="MTR_DASHCAM_FOOTAGE_UNKNOWN", weight=0.24, detail="dashcam footage not given"))
    return out
