# claims-service

Corvane Mutual claims handling: first notice of loss (FNOL), triage, approval, payout hand-off and the REST
replacement for the CICS claims inquiry (transaction CLMI).

| Endpoint | Purpose | Roles |
|---|---|---|
| `POST /v1/claims` | Register a claim (FNOL, journey J1) | CUSTOMER, ADJUSTER |
| `POST /v1/claims/drafts` | Start a draft claim from the portal wizard | CUSTOMER |
| `POST /v1/claims/drafts/{id}/photos` | Attach damage photos to a draft | CUSTOMER |
| `PUT /v1/claims/{id}/approve` | Approve a referred claim (journey J2) | ADJUSTER, CLAIMS_MANAGER |
| `GET /v1/claims/{id}/summary` | Claim summary, replaces CICS CLMI / CLMINQ0 | ADJUSTER, CUSTOMER |
| `GET /v1/claims/export` | CSV export for the MI team | see SecurityConfig |

Listens on port 8080. Talks to policy-admin (`GET /v1/policies/{policyNumber}`), fraud-scoring (`POST /v1/score`,
plain HTTP JSON), the Sentinel Claims Exchange (through the vendored SDK) and Kafka.

Topics produced: `claims.registered.v1`, `claims.approved.v1`, `claims.closed.v1`.
Topics consumed: `payments.settled.v1`.

Auto-approve limit: see `claims.triage.auto-approve-limit` per environment. Do not hard-code it in new code.
