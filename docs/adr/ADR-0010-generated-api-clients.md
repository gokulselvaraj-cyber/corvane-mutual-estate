# ADR-0010: Generated API clients

- **Status:** Accepted
- **Date:** 2024-07-08
- **Deciders:** Platform architecture board

## Decision

Clients for policy-admin are generated from contracts/policy-admin.openapi.yaml with openapi-generator into generated/policy-client-ts. Generated code is never edited by hand.

## Consequences

The portal still uses hand-written wrappers; moving it to the generated client is planned.
