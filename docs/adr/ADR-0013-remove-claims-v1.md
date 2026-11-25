# ADR-0013: Remove the retired claims-v1 application

Status: Accepted, 16 Nov 2026

## Context
`retired/claims-v1` was the servlet-era claims app, switched off in 2023 (see ADR-0002). Its code still answered
questions about a 1,000 GBP auto-approve limit and a 150 GBP excess, which confused new joiners and tooling.

## Decision
Delete `retired/claims-v1` and the one-off script `scripts/oneoff/backfill_2023_reserves.py`. History stays in git.

## Consequences
- The prod auto-approve limit is now 4,000 GBP (`application-prod.yml`), lowered from 5,000 after the Q3 2026 leakage
  review. `docs/product/claims-handling.md` was updated to match.
- The mainframe compulsory excess is raised from 200 to 250 GBP (CR-4471), so PRMCALC now agrees with
  policy-admin `RatingService`. claims-service still rounds down.
- payments-gateway gets an owner in CODEOWNERS (@corvane/payments) and runs 2 replicas in prod.
