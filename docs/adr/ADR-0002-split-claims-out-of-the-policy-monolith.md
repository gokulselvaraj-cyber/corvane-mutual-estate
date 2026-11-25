# ADR-0002: Split claims out of the policy monolith

- **Status:** Accepted
- **Date:** 2020-09-14
- **Deciders:** Platform architecture board

## Decision

Claims handling moves from policy-admin into its own Spring Boot service, claims-service, with its own PostgreSQL database `claimsdb`. policy-admin stays a layered monolith for quotes, rating and policies.

## Consequences

Claims can scale and release independently. claims-service reads policies over REST (`GET /v1/policies/{policyNumber}`) and never touches the Oracle ledger directly.
