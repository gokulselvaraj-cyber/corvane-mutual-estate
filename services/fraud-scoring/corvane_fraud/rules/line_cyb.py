"""Cyber (CYB) fraud indicators.

Typical pattern the counter-fraud team asked us to catch: MFA declared at inception but absent at the time of loss.
Weights reviewed by Fraud Analytics; generated from the rules catalogue (fraud-rules-2026.02).
"""
from ..models import Indicator, ScoreRequest

LINE = "CYB"
HIGH_RISK_CAUSES = ('DDOS', 'RANSOMWARE')
LARGE_LOSS_GBP = 25000
EARLY_WINDOW_DAYS = 14


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    attrs = req.attributes or {}
    if req.loss_cause in HIGH_RISK_CAUSES:
        out.append(Indicator(code="CYB_CAUSE", weight=0.12, detail=f"high-risk cause {req.loss_cause}"))
    if req.claimed_amount > LARGE_LOSS_GBP:
        out.append(Indicator(code="CYB_LARGE_LOSS", weight=0.14, detail="above 25000 GBP"))
    if (req.loss_date - req.policy_start_date).days < EARLY_WINDOW_DAYS:
        out.append(Indicator(code="CYB_EARLY", weight=0.28, detail="MFA declared at inception but absent at the time of loss"))
    if attrs.get("records_affected") in (True, "yes") or (isinstance(attrs.get("records_affected"), (int, float)) and attrs["records_affected"] >= 10):
        out.append(Indicator(code="CYB_RECORDS_AFFECTED", weight=0.11, detail="records affected at or above 10"))
    if attrs.get("patch_age_days") in (False, "no", 0):
        out.append(Indicator(code="CYB_NO_PATCH_AGE_DAYS", weight=0.18, detail="patch age days missing"))
    if attrs.get("mfa_enabled") == "unknown":
        out.append(Indicator(code="CYB_MFA_ENABLED_UNKNOWN", weight=0.28, detail="mfa enabled not given"))
    return out
