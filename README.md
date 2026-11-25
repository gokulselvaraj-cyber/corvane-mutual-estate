# Corvane Mutual insurance platform

Corvane Mutual sells personal and commercial insurance in the UK and the US across 12 product lines:
Motor (MTR), Home buildings (HOM), Home contents (CNT), Travel (TRV), Pet (PET), Landlord (LLD), Marine cargo (MAR),
Commercial property (CPR), Public liability (PLB), Professional indemnity (PIN), Cyber (CYB) and Gadget (GDG).

## Systems

| Folder | What it is |
|---|---|
| `services/policy-admin` | Quotes, rating, policies (Java monolith) |
| `services/claims-service` | First notice of loss, triage, approval, settlement (Java) |
| `services/fraud-scoring` | Fraud rules and LLM triage (Python) |
| `services/payments-gateway` | Claim payouts through ClearRiver Bank (Go) |
| `services/notifications` | Email and SMS (Node) |
| `services/broker-commissions` | Monthly broker commission (.NET) |
| `services/warehouse-loader` | Loads the nightly billing file into the warehouse (Python, Airflow) |
| `mobile/adjuster-app` | Field adjuster Android app (Kotlin) |
| `web/customer-portal` | Customer website (React) |
| `mainframe/` | Premium billing batch and the CICS claims inquiry (COBOL, JCL) |
| `data/` | Claims database (PostgreSQL), policy ledger (Oracle), reference data |
| `contracts/` | OpenAPI, AsyncAPI, Avro, protobuf, WSDL and GraphQL contracts |
| `infra/`, `ops/` | GCP Terraform, Kubernetes, Helm, Ansible, monitoring, runbooks |
| `docs/` | ADRs, architecture, product and help pages |

`vendor/` and `generated/` are third-party and generated code. `retired/` is no longer deployed.

## Running locally

`docker compose up` starts Postgres, Kafka and the services. Set `CLAIMS_DB_PASSWORD`, `LEDGER_DB_PASSWORD`,
`AI_GATEWAY_TOKEN` and `CLEARRIVER_API_KEY` in your shell first.
