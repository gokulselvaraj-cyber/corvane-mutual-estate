"""Fixed-width layout of the mainframe BILLREC copybook (mainframe/copybooks/BILLREC.cpy).

    05 POLICY-NO     PIC X(12).          positions  1-12
    05 LINE-CODE     PIC X(3).           positions 13-15
    05 BILL-DATE     PIC 9(8).           positions 16-23   (CCYYMMDD)
    05 PREMIUM-AMT   PIC S9(9)V99.       positions 24-34   (zoned decimal, sign overpunched in last byte)
    05 IPT-AMT       PIC S9(7)V99.       positions 35-43
    05 CURRENCY      PIC X(3).           positions 44-46
    05 REGION        PIC X(2).           positions 47-48
    05 FILLER        PIC X(16).          positions 49-64

The file arrives ASCII (the SFTP step in JCL PRMNIGHT STEP040 converts from EBCDIC).
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

RECORD_LENGTH = 64

# (name, start, length) with 0-based start
FIELDS = (
    ("policy_no", 0, 12),
    ("line_code", 12, 3),
    ("bill_date", 15, 8),
    ("premium_amt", 23, 11),
    ("ipt_amt", 34, 9),
    ("currency", 43, 3),
    ("region", 46, 2),
)

# Zoned-decimal overpunch: last character carries the sign.
_POS = {"{": "0", "A": "1", "B": "2", "C": "3", "D": "4", "E": "5", "F": "6", "G": "7", "H": "8", "I": "9"}
_NEG = {"}": "0", "J": "1", "K": "2", "L": "3", "M": "4", "N": "5", "O": "6", "P": "7", "Q": "8", "R": "9"}


def zoned(text: str, scale: int = 2) -> Decimal:
    last = text[-1]
    sign = 1
    if last in _POS:
        text = text[:-1] + _POS[last]
    elif last in _NEG:
        text = text[:-1] + _NEG[last]
        sign = -1
    return sign * Decimal(text) / (10 ** scale)


@dataclass(frozen=True)
class BillingRecord:
    policy_no: str
    line_code: str
    bill_date: date
    premium_amt: Decimal
    ipt_amt: Decimal
    currency: str
    region: str


def parse(line: str) -> BillingRecord:
    line = line.rstrip("\r\n").ljust(RECORD_LENGTH)
    raw = {name: line[start:start + length] for name, start, length in FIELDS}
    d = raw["bill_date"]
    return BillingRecord(
        policy_no=raw["policy_no"].strip(),
        line_code=raw["line_code"],
        bill_date=date(int(d[0:4]), int(d[4:6]), int(d[6:8])),
        premium_amt=zoned(raw["premium_amt"]),
        ipt_amt=zoned(raw["ipt_amt"]),
        currency=raw["currency"],
        region=raw["region"],
    )
