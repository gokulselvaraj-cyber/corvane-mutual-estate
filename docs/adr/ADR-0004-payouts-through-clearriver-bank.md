# ADR-0004: Payouts through ClearRiver Bank

- **Status:** Accepted
- **Date:** 2021-05-20
- **Deciders:** Platform architecture board

## Decision

Claim payouts go through the ClearRiver Bank Payouts API v2 from a dedicated Go service, payments-gateway. Calls use a 5 second timeout, 3 retries and a circuit breaker.

## Consequences

Payouts are isolated from claims-service. A second payout provider is out of scope for now.
