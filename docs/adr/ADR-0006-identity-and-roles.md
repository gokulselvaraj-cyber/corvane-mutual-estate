# ADR-0006: Identity and roles

- **Status:** Accepted
- **Date:** 2022-01-17
- **Deciders:** Platform architecture board

## Decision

All services accept JWTs issued by `https://login.corvane.internal`. Roles: CUSTOMER, ADJUSTER, CLAIMS_MANAGER, BROKER. Every API endpoint requires an authenticated caller.

## Consequences

Service-to-service calls relay the caller's token. Exceptions need a new ADR.
