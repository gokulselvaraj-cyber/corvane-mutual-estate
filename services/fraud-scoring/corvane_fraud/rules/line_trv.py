"""Travel (TRV) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: trip cancelled shortly after the policy was bought.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "TRV"
HIGH_RISK_CAUSES = ('BAGGAGE_LOSS', 'PERSONAL_MONEY')
LARGE_LOSS_GBP = 60000
EARLY_WINDOW_DAYS = 60


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="TRV_CAUSE", weight=0.16, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="TRV_LARGE_LOSS", weight=0.14, detail="above 60000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="TRV_EARLY", weight=0.2, detail="trip cancelled shortly after the policy was bought"))
    if attrs.get("medical_provider_known") in (True, "yes") or (isinstance(attrs.get("medical_provider_known"), (int, float)) and attrs["medical_provider_known"] >= 30):
        out.append(Indicator(code="TRV_MEDICAL_PROVIDER_KNOWN", weight=0.27, detail="medical provider known at or above 30"))
    if attrs.get("days_abroad") in (False, "no", 0):
        out.append(Indicator(code="TRV_NO_DAYS_ABROAD", weight=0.08, detail="days abroad missing"))
    if attrs.get("destination_risk") == "unknown":
        out.append(Indicator(code="TRV_DESTINATION_RISK_UNKNOWN", weight=0.15, detail="destination risk not given"))
    return out
