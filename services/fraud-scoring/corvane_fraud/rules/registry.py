"""Maps a product line code to its rule module (generated modules live next to this file)."""
import importlib

LINES = ("MTR", "HOM", "CNT", "TRV", "PET", "LLD", "MAR", "CPR", "PLB", "PIN", "CYB", "GDG")


def for_line(code: str):
    if code not in LINES:
        raise ValueError(f"unknown product line {code}")
    return importlib.import_module(f"corvane_fraud.rules.line_{code.lower()}")
