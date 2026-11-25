# payments-gateway

Consumes `claims.approved.v1`, pays the claimant through the ClearRiver Bank Payouts API v2, records the
payment in `claims.payment` and publishes `payments.settled.v1` (claims-service marks the claim PAID).

* Outbound call: 5 s timeout, up to 3 retries with exponential back-off, circuit breaker (opens after
  5 consecutive failures, half-open after 60 s).
* Idempotency: the claim id + approval sequence is the `idempotency_key`; ClearRiver dedupes on the
  `Idempotency-Key` header and we keep a unique index on `claims.payment.idempotency_key`.
* No automated tests yet (PAY-77). Owner: team-payments.
