from datetime import date
from decimal import Decimal

from corvane_loader.billrec import parse, zoned

REC = "MTR000123456MTR20261102" + "00000045120" + "00000541{" + "GBPUK" + " " * 16


def test_record_is_64_bytes():
    assert len(REC) == 64


def test_parse_fields():
    r = parse(REC)
    assert r.policy_no == "MTR000123456"
    assert r.line_code == "MTR"
    assert r.bill_date == date(2026, 11, 2)
    assert r.premium_amt == Decimal("451.20")
    assert r.ipt_amt == Decimal("54.10")
    assert r.currency == "GBP" and r.region == "UK"


def test_negative_overpunch_is_a_refund():
    assert zoned("0000001234}") == Decimal("-123.40")
