"""One check per product line: a high-risk cause above the large-loss amount raises line indicators."""
from decimal import Decimal

import pytest

from corvane_fraud.rules import registry

CASES = [
    ("MTR", "COLLISION_SINGLE", 60000),
    ("HOM", "FIRE", 12000),
    ("CNT", "FIRE", 2500),
    ("TRV", "BAGGAGE_LOSS", 60000),
    ("PET", "ILLNESS", 1500),
    ("LLD", "MALICIOUS_DAMAGE_TENANT", 12000),
    ("MAR", "HANDLING_DAMAGE", 12000),
    ("CPR", "BUSINESS_INTERRUPTION", 12000),
    ("PLB", "PRODUCT_INJURY", 25000),
    ("PIN", "DEFAMATION", 2500),
    ("CYB", "DDOS", 25000),
    ("GDG", "ACCIDENTAL_DAMAGE", 4000),
]


@pytest.mark.parametrize("line,cause,cap", CASES)
def test_line_indicators(make_request, line, cause, cap):
    req = make_request(line_code=line, loss_cause=cause, claimed_amount=Decimal(cap + 1))
    codes = {i.code for i in registry.for_line(line).evaluate(req)}
    assert f"{line}_CAUSE" in codes and f"{line}_LARGE_LOSS" in codes


def test_every_line_has_a_module():
    for line in registry.LINES:
        assert hasattr(registry.for_line(line), "evaluate")
