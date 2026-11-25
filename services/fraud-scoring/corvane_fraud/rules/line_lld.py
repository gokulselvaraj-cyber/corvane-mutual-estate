"""Landlord (LLD) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: loss of rent claimed with no tenancy agreement.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "LLD"
HIGH_RISK_CAUSES = ('MALICIOUS_DAMAGE_TENANT', 'STORM')
LARGE_LOSS_GBP = 12000
EARLY_WINDOW_DAYS = 60


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="LLD_CAUSE", weight=0.08, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="LLD_LARGE_LOSS", weight=0.15, detail="above 12000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="LLD_EARLY", weight=0.22, detail="loss of rent claimed with no tenancy agreement"))
    if attrs.get("inventory_check") in (True, "yes") or (isinstance(attrs.get("inventory_check"), (int, float)) and attrs["inventory_check"] >= 30):
        out.append(Indicator(code="LLD_INVENTORY_CHECK", weight=0.08, detail="inventory check at or above 30"))
    if attrs.get("tenancy_months") in (False, "no", 0):
        out.append(Indicator(code="LLD_NO_TENANCY_MONTHS", weight=0.24, detail="tenancy months missing"))
    if attrs.get("agent_managed") == "unknown":
        out.append(Indicator(code="LLD_AGENT_MANAGED_UNKNOWN", weight=0.15, detail="agent managed not given"))
    return out
