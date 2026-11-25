# ADR-0003: Kafka for cross-service events

- **Status:** Accepted
- **Date:** 2020-11-03
- **Deciders:** Platform architecture board

## Decision

Services publish domain events to Kafka (Confluent Cloud): policies.bound.v1, claims.registered.v1, claims.approved.v1, payments.settled.v1 and claims.closed.v1. Schemas are Avro, registered per topic.

## Consequences

Consumers are decoupled from producers. Every consumer must be idempotent.
