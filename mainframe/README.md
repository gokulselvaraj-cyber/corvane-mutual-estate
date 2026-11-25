# CORVMF: Corvane mainframe (billing and claims inquiry)

z/OS batch and CICS. Owned by team-mainframe (`@corvane/mainframe-billing`).

## Batch

| Job | When (Europe/London) | Steps |
|---|---|---|
| `PRMNIGHT` | 01:30 Mon–Sat | STEP010 `PRMEXTR` → STEP020 `PRMCALC` → STEP030 `PRMBILL` → STEP040 SFTP to `/landing/billing/` |
| `CLMDAILY` | 22:00 daily | STEP005 `CLMFEED` (Postgres changes into CLMMAST) → STEP010 backup `CORV.CLMMAST` → STEP020 `CLMHIST` (source is EBCDIC, see `ebcdic/`) |
| `PRMMONTH` | 1st working day, 06:00 | Monthly IPT summary for finance |

`PRMCALC` calls the rating program for the policy's line dynamically (`RAT` + line code + `01`), then
`PRMRULES` (the underwriting rule table), applies the excess, and calls `IPTCALC`.
The billing file (`BILLREC`, 64 bytes) is loaded by the data platform's Airflow DAG `premium_billing_load`.

## Online (CICS region CORVCICP)

| Transaction | Program | Purpose |
|---|---|---|
| `CLMI` | `CLMINQ0` | Claims inquiry, read-only. Being replaced by `GET /v1/claims/{id}/summary`. |
| `PRMC` (CTG mirror) | `PRMCALC0` | Premium calculation for policy-admin, through CTG server `CORVCTG1`. Prod only. |
| `PRMQ` | `PRMQ000` | Branch phone quote. Source lost in 2016; only the load module exists. |

## Not run

`CLMPURGE` (6-year claims purge) has not been scheduled since the 2024 claims migration.
