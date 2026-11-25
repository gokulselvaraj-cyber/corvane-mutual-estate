# Runbook: claim payouts failing

**Alert:** `PayoutFailures` or `PaymentsGatewayDown`. **Owner:** team-payments. **Severity:** page.

payments-gateway consumes `claims.approved.v1`, calls the ClearRiver Bank Payouts API
(`https://api.clearriver-bank.example/payouts/v2`) and writes `claims.payment`. Each call has a 5 s timeout and
3 retries; after 5 consecutive failures the circuit breaker opens for 60 s.

1. Check the ClearRiver status page and our egress NAT (`corvane-egress-prod`).
2. `kubectl -n corvane-prod get pods -l app=payments-gateway`. **Prod runs one replica**, so a crash-looping pod
   stops all payouts. Scale to 2 as a stop-gap: `kubectl scale deploy/payments-gateway --replicas=2`.
3. Payouts are idempotent on `claims.payment.idempotency_key`, so replaying `claims.approved.v1` from the last
   committed offset is safe.
4. If ClearRiver is down for more than 2 hours, tell the claims operations lead: customers are promised payment within
   3 working days.
