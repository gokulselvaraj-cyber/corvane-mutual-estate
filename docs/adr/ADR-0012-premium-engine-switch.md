# ADR-0012: Premium engine switch

- **Status:** Accepted
- **Date:** 2025-09-01
- **Deciders:** Platform architecture board

## Decision

policy-admin rates premiums either with the mainframe (CICS program PRMCALC0 via CTG) or with the new Java rating engine. The switch is the setting `policy.premium-engine` (`mainframe` or `java`). Dev and test run `java`; prod stays on `mainframe` until parallel-run results match for 3 consecutive months.

## Consequences

Rating rules exist twice during the migration. The excess rules are known to differ slightly; see the parallel-run report.
