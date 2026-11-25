# Runbook: Kafka consumer lag

**Alert:** `ConsumerLagHigh`.

| Consumer group | Topic | Service |
|---|---|---|
| notifications-claims | claims.registered.v1 | notifications |
| fraud-async | claims.registered.v1 | fraud-scoring |
| payments-approved | claims.approved.v1 | payments-gateway |
| claims-payments | payments.settled.v1 | claims-service |
| commissions-bound | policies.bound.v1 | broker-commissions |
| notifications-policies | policies.bound.v1 | notifications |
| warehouse-closed | claims.closed.v1 | warehouse-loader |

Scale the consumer, check for a poison message in the logs, and skip it only with the owning team's agreement.
