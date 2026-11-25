# Runbook: nightly premium billing (PRMNIGHT) failed or late

**Alert:** `BillingFileNotLanded`. **Owner:** team-mainframe, with team-data-platform for the load.

Chain: PRMNIGHT 01:30 Europe/London (Mon–Sat) → STEP010 PRMEXTR → STEP020 PRMCALC → STEP030 PRMBILL writes
`CORV.PRM.BILLING.DAILY` → STEP040 SFTP to `/landing/billing/` → Airflow DAG `premium_billing_load` at 04:00 →
`dw.premium_billing`.

| Failed step | Usual cause | Action |
|---|---|---|
| STEP010 | VSAM `CORV.POLMAST` enqueued by online CICS | Wait for CICS close at 01:15, then restart from STEP010 |
| STEP020 | Rate table not loaded (RATELOAD) | Run RATELOAD, restart from STEP020 |
| STEP030 | B37 space abend | Increase SPACE on BILLOUT and restart |
| STEP040 | SFTP host `landing-01` unreachable | Check the Ansible-managed host; rerun STEP040 only |

If the file lands after 04:00, trigger the DAG by hand: `airflow dags trigger premium_billing_load`.
Never rerun STEP030 without STEP020: the file would carry yesterday's premiums.
