"""Builder E: writes ops/ and governance files at the estate root. Run: python3 -I e_ops_gov.py <estate_root>"""
import json, os, sys

ROOT = sys.argv[1]


def W(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p) or ROOT, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


# ---------------------------------------------------------------- ops/runbooks
W("ops/runbooks/payout-failures.md", """
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
""")
W("ops/runbooks/prmnight-failure.md", """
# Runbook: nightly premium billing (PRMNIGHT) failed or late

**Alert:** `BillingFileNotLanded`. **Owner:** team-mainframe, with team-data-platform for the load.

Chain: PRMNIGHT 01:30 Europe/London (Mon–Sat) → STEP010 PRMEXTR → STEP020 PRMCALC → STEP030 PRMBILL writes
`CORV.PRM.BILLING.DAILY` → STEP040 SFTP to `/landing/billing/` → Airflow DAG `premium_billing_load` at 04:00 →
`dw.premium_billing`.

| Failed step | Usual cause | Action |
|---|---|---|
| STEP010 | VSAM `CORV.POLMAST` enqueued by online CICS | Wait for CICS close at 01:15, then restart from STEP010 |
| STEP020 | Rate table not loaded (RATELOAD) | Run RATELOAD, restart from STEP020 |
| STEP030 | B37 space abend | Increase SPACE on BILLOUT and restart |
| STEP040 | SFTP host `landing-01` unreachable | Check the Ansible-managed host; rerun STEP040 only |

If the file lands after 04:00, trigger the DAG by hand: `airflow dags trigger premium_billing_load`.
Never rerun STEP030 without STEP020: the file would carry yesterday's premiums.
""")
W("ops/runbooks/kafka-lag.md", """
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
""")
W("ops/runbooks/claims-api-errors.md", """
# Runbook: claims API errors

**Alert:** `ClaimsApiErrorRateHigh`. **SLO:** 99.5% over 28 days (`infra/observability/slo-claims-api.yaml`).

1. Check downstream calls first: policy-admin (`POLICY_ADMIN_URL`), fraud-scoring and the Sentinel exchange.
2. In the **test** environment, a 5xx storm on FNOL usually means policy-admin cannot be reached; check the URL in the
   overlay.
3. If fraud-scoring is slow, turn off `fraud.llm-triage.enabled` in the `corvane-env` ConfigMap; claims then score on
   rules only.
""")
W("ops/runbooks/fraud-scoring.md", """
# Runbook: fraud scoring slow or LLM triage down

**Alert:** `FraudScoringSlow`. **Owner:** team-fraud-analytics.

fraud-scoring (`POST /v1/score`) combines per-line rules with an optional LLM triage call to the AI gateway
(`https://ai-gateway.corvane.internal/v1/chat`). Claims with a score of **0.72 or more** are referred to the fraud team
(`REFER_THRESHOLD` in `services/fraud-scoring/corvane_fraud/settings.py`).

1. Check the AI gateway status. If it is slow or failing, turn LLM triage off: set `fraud.llm-triage.enabled` to
   `"false"` in the `corvane-env` ConfigMap of the environment and restart fraud-scoring. Scoring continues on rules
   only, and claims-service is not affected.
2. If scoring itself fails, claims-service treats the claim as "refer" so nothing is auto-approved without a score.
3. Turn LLM triage back on once the gateway p95 is under 2 s for 30 minutes.
""")
W("ops/schedules/batch-schedule.yaml", """
# Batch calendar. Mainframe jobs run under the CA-7 scheduler; the rest under Airflow or Kubernetes CronJobs.
timezone: Europe/London
jobs:
  - name: PRMNIGHT
    system: mainframe
    cron: "30 1 * * 1-6"        # 01:30 Monday to Saturday
    owner: team-mainframe
    output: CORV.PRM.BILLING.DAILY
  - name: CLMDAILY
    system: mainframe
    cron: "0 23 * * *"
    owner: team-mainframe
  - name: PRMMONTH
    system: mainframe
    cron: "0 3 1 * *"
    owner: team-mainframe
  - name: premium_billing_load
    system: airflow
    cron: "0 4 * * 1-6"         # after PRMNIGHT lands
    owner: team-data-platform
    depends_on: PRMNIGHT
  - name: purge_expired_claims
    system: postgres-cron
    cron: "0 2 * * 0"
    owner: team-claims-platform
    calls: claims.purge_expired_claims()
  - name: monthly_commission_statements
    system: kubernetes-cronjob
    cron: "0 6 2 * *"
    owner: team-distribution
""")
W("ops/logs/payments-gateway-2026-11-12.log", """
2026-11-12T08:14:03.112Z INFO  consumer started group=payments-approved topic=claims.approved.v1 partitions=6
2026-11-12T08:14:09.873Z INFO  payout requested claim=CLM-2026-0418811 amount=1840.00 currency=GBP key=pay-0418811-1
2026-11-12T08:14:10.402Z INFO  payout accepted clearriver_ref=CRB-77A1F2 claim=CLM-2026-0418811
2026-11-12T08:31:44.019Z WARN  clearriver timeout after 5000ms attempt=1 claim=CLM-2026-0418902
2026-11-12T08:31:49.511Z WARN  clearriver timeout after 5000ms attempt=2 claim=CLM-2026-0418902
2026-11-12T08:31:55.020Z WARN  clearriver timeout after 5000ms attempt=3 claim=CLM-2026-0418902
2026-11-12T08:31:55.021Z ERROR payout failed claim=CLM-2026-0418902 reason=retries_exhausted
2026-11-12T08:32:40.700Z ERROR circuit open name=clearriver failures=5 open_for=60s
2026-11-12T08:33:41.002Z INFO  circuit half-open name=clearriver
2026-11-12T08:33:41.650Z INFO  payout accepted clearriver_ref=CRB-77A20C claim=CLM-2026-0418902
2026-11-12T08:33:41.700Z INFO  published payments.settled.v1 claim=CLM-2026-0418902
""")
W("ops/logs/prmnight-2026-11-14.log", """
CORV.PRMNIGHT  JOB04417  01:30:00  STARTED
STEP010 PRMEXTR  RC=0000  RECORDS READ=  418,220  SELECTED= 13,904  01:41:17
STEP020 PRMCALC  RC=0004  WARNING: 12 POLICIES WITH NO RATE ROW, DEFAULTED   02:09:52
STEP030 PRMBILL  RC=0000  RECORDS WRITTEN= 13,904  02:14:06
STEP040 SFTPPUT  RC=0000  /landing/billing/PRM.BILLING.D261114  02:15:31
CORV.PRMNIGHT  JOB04417  02:15:31  ENDED  MAXCC=0004
""")
W("ops/logs/claims-service-test-2026-11-15.log", """
2026-11-15T10:02:11.118Z INFO  Started ClaimsServiceApplication in 14.2 seconds (profile=test)
2026-11-15T10:05:40.551Z ERROR PolicyAdminClient getPolicy failed policy=CVM-HOM-0031177 url=http://policy-admin:8081/v1/policies/CVM-HOM-0031177 error=Connection refused
2026-11-15T10:05:40.553Z WARN  POST /v1/claims returned 503 (policy lookup unavailable)
2026-11-15T10:06:02.900Z ERROR PolicyAdminClient getPolicy failed policy=CVM-MTR-0012345 url=http://policy-admin:8081/v1/policies/CVM-MTR-0012345 error=Connection refused
""")

# ---------------------------------------------------------------- governance
W("CODEOWNERS", """
# Default reviewers. Later rules win.
*                                   @corvane/platform-architecture

/services/policy-admin/             @corvane/policy-core
/services/claims-service/           @corvane/claims-platform
/services/fraud-scoring/            @corvane/fraud-analytics
/services/notifications/            @corvane/digital
/services/broker-commissions/       @corvane/distribution
/services/warehouse-loader/         @corvane/data-platform
/mobile/adjuster-app/               @corvane/digital
/web/customer-portal/               @corvane/digital
/mainframe/                         @corvane/mainframe-billing
/data/postgres/                     @corvane/claims-platform
/data/oracle/                       @corvane/policy-core
/contracts/                         @corvane/platform-architecture
/infra/                             @corvane/platform-ops
/ops/                               @corvane/platform-ops
/docs/                              @corvane/platform-architecture
/vendor/                            @corvane/platform-architecture
""")
W("LICENSE", """
Copyright (c) 2019-2026 Corvane Mutual Insurance Society Limited. All rights reserved.

Proprietary and confidential. This source code is the property of Corvane Mutual and may not be copied, modified or
distributed without written permission. Third-party components under vendor/ keep their own licences.
""")
W("README.md", """
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
""")

W("catalog-info.yaml", """
apiVersion: backstage.io/v1alpha1
kind: Domain
metadata:
  name: insurance
  description: Corvane Mutual general insurance
spec:
  owner: platform-architecture
---
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: corvane-insurance-platform
  description: Quotes, policies, claims, payouts and billing
spec:
  owner: platform-architecture
  domain: insurance
---
apiVersion: backstage.io/v1alpha1
kind: Group
metadata:
  name: team-fnol
  description: First notice of loss squad (claims intake), formed 2026-04 from claims-platform
spec:
  type: team
  parent: claims
  children: []
---
apiVersion: backstage.io/v1alpha1
kind: Group
metadata:
  name: team-payments
spec:
  type: team
  children: []
---
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: claimsdb
  description: PostgreSQL claims database (europe-west2)
spec:
  type: database
  owner: team-claims-platform
  system: corvane-insurance-platform
---
apiVersion: backstage.io/v1alpha1
kind: Resource
metadata:
  name: corvane-claims-docs-dr
  description: DR copy of claim documents (us-east1)
spec:
  type: storage-bucket
  owner: team-platform-ops
  system: corvane-insurance-platform
""")

sbom = {
    "bomFormat": "CycloneDX", "specVersion": "1.5", "version": 7,
    "metadata": {"timestamp": "2025-06-30T09:00:00Z",
                 "component": {"type": "application", "name": "corvane-insurance-platform", "version": "2025.06"},
                 "tools": [{"vendor": "CycloneDX", "name": "cyclonedx-maven-plugin", "version": "2.7.9"}]},
    "components": [
        {"type": "library", "group": "com.fasterxml.jackson.core", "name": "jackson-databind", "version": "2.13.4",
         "purl": "pkg:maven/com.fasterxml.jackson.core/jackson-databind@2.13.4", "licenses": [{"license": {"id": "Apache-2.0"}}]},
        {"type": "library", "group": "org.springframework.boot", "name": "spring-boot", "version": "3.1.5",
         "purl": "pkg:maven/org.springframework.boot/spring-boot@3.1.5", "licenses": [{"license": {"id": "Apache-2.0"}}]},
        {"type": "library", "group": "io.github.resilience4j", "name": "resilience4j-circuitbreaker", "version": "2.1.0",
         "purl": "pkg:maven/io.github.resilience4j/resilience4j-circuitbreaker@2.1.0", "licenses": [{"license": {"id": "Apache-2.0"}}]},
        {"type": "library", "group": "com.sentinelexchange", "name": "sentinel-exchange-sdk", "version": "1.4.2",
         "purl": "pkg:maven/com.sentinelexchange/sentinel-exchange-sdk@1.4.2", "licenses": [{"license": {"name": "Sentinel Member Licence"}}]},
        {"type": "library", "name": "fastapi", "version": "0.103.2", "purl": "pkg:pypi/fastapi@0.103.2", "licenses": [{"license": {"id": "MIT"}}]},
        {"type": "library", "name": "react", "version": "18.2.0", "purl": "pkg:npm/react@18.2.0", "licenses": [{"license": {"id": "MIT"}}]},
        {"type": "library", "name": "github.com/sony/gobreaker", "version": "0.5.0", "purl": "pkg:golang/github.com/sony/gobreaker@0.5.0", "licenses": [{"license": {"id": "MIT"}}]},
        {"type": "library", "name": "Confluent.Kafka", "version": "2.3.0", "purl": "pkg:nuget/Confluent.Kafka@2.3.0", "licenses": [{"license": {"id": "Apache-2.0"}}]},
    ],
}
W("sbom/corvane.cdx.json", json.dumps(sbom, indent=2) + "\n")

W(".gitlab-ci.yml", """
stages: [test, build, deploy]

variables:
  REGISTRY: europe-west2-docker.pkg.dev/corvane-platform/apps

.java: &java
  image: maven:3.9-eclipse-temurin-17
  cache: {paths: [.m2/repository]}

policy-admin:test:
  <<: *java
  stage: test
  script: [cd services/policy-admin, mvn -B verify]
  rules: [{changes: [services/policy-admin/**/*]}]

claims-service:test:
  <<: *java
  stage: test
  script: [cd services/claims-service, mvn -B verify]
  rules: [{changes: [services/claims-service/**/*]}]

fraud-scoring:test:
  stage: test
  image: python:3.11
  script: [cd services/fraud-scoring, pip install -r requirements.txt, pytest -q]

warehouse-loader:test:
  stage: test
  image: python:3.11
  script: [cd services/warehouse-loader, pip install -r requirements.txt, pytest -q]

payments-gateway:build:
  stage: build
  image: golang:1.22
  script: [cd services/payments-gateway, go build ./...]   # no tests exist for this service

notifications:test:
  stage: test
  image: node:20
  script: [cd services/notifications, npm ci, npm test]

images:
  stage: build
  image: gcr.io/kaniko-project/executor:debug
  parallel:
    matrix:
      - SERVICE: [policy-admin, claims-service, fraud-scoring, payments-gateway, notifications, warehouse-loader]
  script:
    - /kaniko/executor --context services/$SERVICE --destination $REGISTRY/$SERVICE:$CI_COMMIT_SHORT_SHA

deploy:prod:
  stage: deploy
  image: google/cloud-sdk:489.0.0
  when: manual
  environment: production
  script:
    - kubectl kustomize infra/k8s/overlays/prod | sed "s/\\${IMAGE_TAG}/$CI_COMMIT_SHORT_SHA/" | kubectl apply -f -
  rules: [{if: '$CI_COMMIT_BRANCH == "main"'}]
""")
W("azure-pipelines.yml", """
# broker-commissions is built in Azure DevOps (distribution team's tenant) and pushed to the shared registry.
trigger:
  branches: {include: [main]}
  paths: {include: [services/broker-commissions/*]}

pool: {vmImage: ubuntu-22.04}

steps:
- task: UseDotNet@2
  inputs: {packageType: sdk, version: 8.0.x}
- script: dotnet test services/broker-commissions/Corvane.Commissions.Tests --configuration Release
  displayName: Unit tests
- script: |
    docker build -t europe-west2-docker.pkg.dev/corvane-platform/apps/broker-commissions:$(Build.BuildId) services/broker-commissions
  displayName: Image
""")
W(".github/workflows/portal.yml", """
name: customer-portal
on:
  push:
    branches: [main]
    paths: ["web/customer-portal/**"]
jobs:
  build:
    runs-on: ubuntu-24.04
    defaults: {run: {working-directory: web/customer-portal}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: {node-version: 20}
      - run: npm install
      - run: npm test
      - run: npm run build
      - name: Upload to CDN bucket
        run: gsutil -m rsync -r dist gs://corvane-portal-static
        env:
          GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_DEPLOY_KEY_PATH }}
""")
print("ops and governance written")
