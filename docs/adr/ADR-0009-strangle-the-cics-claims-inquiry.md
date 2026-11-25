# ADR-0009: Strangle the CICS claims inquiry

- **Status:** Accepted
- **Date:** 2024-02-26
- **Deciders:** Platform architecture board

## Decision

The 3270 claims inquiry (transaction CLMI, program CLMINQ0, map CLMINQM) is replaced step by step by `GET /v1/claims/{id}/summary` in claims-service. Call-centre screens move first; CLMI is switched off when its daily use falls below 50 calls.

## Consequences

Both paths read the same claim data until CLMI is retired. CLMI is still in use (about 1,900 calls a day in Oct 2026).
