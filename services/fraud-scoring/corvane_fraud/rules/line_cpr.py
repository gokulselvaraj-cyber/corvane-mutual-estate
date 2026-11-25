"""Commercial property (CPR) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: fire shortly after turnover fell sharply.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "CPR"
HIGH_RISK_CAUSES = ('BUSINESS_INTERRUPTION', 'THEFT_COMMERCIAL')
LARGE_LOSS_GBP = 12000
EARLY_WINDOW_DAYS = 21


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="CPR_CAUSE", weight=0.09, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="CPR_LARGE_LOSS", weight=0.13, detail="above 12000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="CPR_EARLY", weight=0.19, detail="fire shortly after turnover fell sharply"))
    if attrs.get("sprinklers") in (True, "yes") or (isinstance(attrs.get("sprinklers"), (int, float)) and attrs["sprinklers"] >= 2):
        out.append(Indicator(code="CPR_SPRINKLERS", weight=0.22, detail="sprinklers at or above 2"))
    if attrs.get("alarm_grade") in (False, "no", 0):
        out.append(Indicator(code="CPR_NO_ALARM_GRADE", weight=0.15, detail="alarm grade missing"))
    if attrs.get("turnover_drop_pct") == "unknown":
        out.append(Indicator(code="CPR_TURNOVER_DROP_PCT_UNKNOWN", weight=0.27, detail="turnover drop pct not given"))
    return out
