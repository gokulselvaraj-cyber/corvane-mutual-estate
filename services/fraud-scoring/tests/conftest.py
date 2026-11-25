from datetime import date
from decimal import Decimal

import pytest

from corvane_fraud.models import Claimant, ScoreRequest


@pytest.fixture
def make_request():
    def _make(**kw):
        base = dict(claim_id="CLM-2026-000123", policy_number="MTR-00012345", line_code="MTR",
                    loss_date=date(2026, 5, 20), reported_date=date(2026, 5, 21),
                    policy_start_date=date(2025, 6, 1), claimed_amount=Decimal("1840.55"),
                    loss_cause="COLLISION_THIRD_PARTY", narrative="Rear-ended at lights.",
                    claimant=Claimant(full_name="Test Person", postcode="ZZ1 1ZZ"))
        base.update(kw)
        return ScoreRequest(**base)
    return _make
