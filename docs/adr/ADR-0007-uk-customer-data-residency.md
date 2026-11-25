# ADR-0007: UK customer data residency

- **Status:** Accepted
- **Date:** 2022-06-30
- **Deciders:** Platform architecture board

## Decision

**UK customer data stays in europe-west2 (London).** This covers databases, backups, documents and logs that contain personal data of UK customers. US business data may be stored in us-east1.

## Consequences

Disaster recovery for UK data must use a second zone in europe-west2, not another region. Any copy of UK personal data outside europe-west2 needs a data protection impact assessment and DPO sign-off.
