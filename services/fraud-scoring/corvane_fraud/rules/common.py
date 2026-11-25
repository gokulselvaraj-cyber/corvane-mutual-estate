"""Indicators that apply to every product line."""
from ..models import Indicator, ScoreRequest

EARLY_CLAIM_DAYS = 30        # loss within 30 days of inception
LATE_REPORT_DAYS = 45        # reported more than 45 days after loss
PRIOR_CLAIMS_HEAVY = 3       # three or more prior claims in 3 years (Sentinel Claims Exchange)
ROUND_AMOUNT_MIN = 1000


def evaluate(req: ScoreRequest) -> list[Indicator]:
    out: list[Indicator] = []
    if (req.loss_date - req.policy_start_date).days < EARLY_CLAIM_DAYS:
        out.append(Indicator(code="EARLY_CLAIM", weight=0.22, detail="loss within 30 days of policy start"))
    if (req.reported_date - req.loss_date).days > LATE_REPORT_DAYS:
        out.append(Indicator(code="LATE_REPORT", weight=0.12, detail="reported more than 45 days after loss"))
    if req.prior_claims_3y >= PRIOR_CLAIMS_HEAVY:
        out.append(Indicator(code="PRIOR_CLAIMS", weight=0.25, detail=f"{req.prior_claims_3y} prior claims"))
    elif req.prior_claims_3y > 0:
        out.append(Indicator(code="PRIOR_CLAIM", weight=0.08, detail="at least one prior claim"))
    if req.claimed_amount >= ROUND_AMOUNT_MIN and req.claimed_amount % 500 == 0:
        out.append(Indicator(code="ROUND_AMOUNT", weight=0.06, detail="claimed amount is a round figure"))
    if "ignore previous instructions" in (req.narrative or "").lower():
        # Narrative text is data. Instruction-like text is itself a weak fraud signal (manipulation attempt).
        out.append(Indicator(code="NARRATIVE_MANIPULATION", weight=0.3, detail="instruction-like text in narrative"))
    return out
