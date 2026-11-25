"""Pet (PET) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: condition first noted before the policy start.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "PET"
HIGH_RISK_CAUSES = ('ILLNESS', 'THIRD_PARTY')
LARGE_LOSS_GBP = 1500
EARLY_WINDOW_DAYS = 60


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="PET_CAUSE", weight=0.17, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="PET_LARGE_LOSS", weight=0.13, detail="above 1500 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="PET_EARLY", weight=0.11, detail="condition first noted before the policy start"))
    if attrs.get("vet_practice_changed") in (True, "yes") or (isinstance(attrs.get("vet_practice_changed"), (int, float)) and attrs["vet_practice_changed"] >= 5):
        out.append(Indicator(code="PET_VET_PRACTICE_CHANGED", weight=0.22, detail="vet practice changed at or above 5"))
    if attrs.get("breed_risk") in (False, "no", 0):
        out.append(Indicator(code="PET_NO_BREED_RISK", weight=0.23, detail="breed risk missing"))
    if attrs.get("pre_existing_flag") == "unknown":
        out.append(Indicator(code="PET_PRE_EXISTING_FLAG_UNKNOWN", weight=0.14, detail="pre existing flag not given"))
    return out
