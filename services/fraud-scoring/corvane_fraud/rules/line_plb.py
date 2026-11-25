"""Public liability (PLB) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: claimant represented before the incident was reported to us.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "PLB"
HIGH_RISK_CAUSES = ('PRODUCT_INJURY', 'SLIP_TRIP')
LARGE_LOSS_GBP = 25000
EARLY_WINDOW_DAYS = 45


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="PLB_CAUSE", weight=0.19, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="PLB_LARGE_LOSS", weight=0.23, detail="above 25000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="PLB_EARLY", weight=0.23, detail="claimant represented before the incident was reported to us"))
    if attrs.get("cctv_available") in (True, "yes") or (isinstance(attrs.get("cctv_available"), (int, float)) and attrs["cctv_available"] >= 2):
        out.append(Indicator(code="PLB_CCTV_AVAILABLE", weight=0.09, detail="cctv available at or above 2"))
    if attrs.get("claimant_solicitor_first") in (False, "no", 0):
        out.append(Indicator(code="PLB_NO_CLAIMANT_SOLICITOR_FIRST", weight=0.12, detail="claimant solicitor first missing"))
    if attrs.get("witnesses") == "unknown":
        out.append(Indicator(code="PLB_WITNESSES_UNKNOWN", weight=0.16, detail="witnesses not given"))
    return out
