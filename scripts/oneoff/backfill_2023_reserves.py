"""ONE-OFF (run once on 2024-01-14 by claims-platform, ticket CLM-2210). Do not schedule.

Backfills claims.claim_reserve for 2023 claims migrated from claims-v1, which stored reserves in a
free-text column. Uses the 2023 reserve factors, NOT the current ones in claims-service.
"""
import re
import sys

import psycopg

FACTORS_2023 = {"MTR": 1.10, "HOM": 1.25, "TRV": 1.00, "PET": 1.05}
AMOUNT = re.compile(r"(\d+(?:\.\d{1,2})?)")


def main(dsn: str) -> None:
    with psycopg.connect(dsn) as conn:
        rows = conn.execute("""SELECT claim_id, line_code, legacy_reserve_text FROM claims.claim
                               WHERE EXTRACT(YEAR FROM reported_at) = 2023 AND legacy_reserve_text IS NOT NULL""").fetchall()
        for claim_id, line, text in rows:
            m = AMOUNT.search(text or "")
            if not m:
                continue
            amount = round(float(m.group(1)) * FACTORS_2023.get(line, 1.0), 2)
            conn.execute("""INSERT INTO claims.claim_reserve (claim_id, reserve_type, amount, currency, set_by, set_at)
                            VALUES (%s, 'INDEMNITY', %s, 'GBP', 'backfill-2023', now())
                            ON CONFLICT DO NOTHING""", (claim_id, amount))
        print(f"backfilled {len(rows)} reserves")


if __name__ == "__main__":
    main(sys.argv[1])
