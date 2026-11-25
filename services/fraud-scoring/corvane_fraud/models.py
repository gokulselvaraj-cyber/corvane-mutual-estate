"""Request and response models for POST /v1/score."""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Decision(str, Enum):
    CLEAR = "CLEAR"
    REFER = "REFER"
    HOLD = "HOLD"


class Claimant(BaseModel):
    full_name: str
    date_of_birth: Optional[date] = None
    postcode: Optional[str] = None
    national_id: Optional[str] = Field(None, description="NI number (UK) or SSN (US); never logged")


class ScoreRequest(BaseModel):
    claim_id: str
    policy_number: str
    line_code: str = Field(..., pattern="^(MTR|HOM|CNT|TRV|PET|LLD|MAR|CPR|PLB|PIN|CYB|GDG)$")
    loss_date: date
    reported_date: date
    policy_start_date: date
    claimed_amount: Decimal
    currency: str = "GBP"
    loss_cause: str
    narrative: str = ""
    injury_notes: Optional[str] = None
    prior_claims_3y: int = 0
    claimant: Claimant
    attributes: dict = Field(default_factory=dict)


class Indicator(BaseModel):
    code: str
    weight: float
    detail: str


class ScoreResponse(BaseModel):
    claim_id: str
    score: float
    decision: Decision
    indicators: list[Indicator]
    llm_label: Optional[str] = None
    model_version: str
