# Corvane Mutual Insurance: test estate (TD-19)

A fictional UK and US insurer, built to test MSOCK end to end on msock-dev. It is dataset **TD-19** in
`../SOCK-TEST-DATA-PLAN.md`, and also covers the upload-safe parts of TD-01, TD-05, TD-08, TD-15a, TD-15b and TD-16.
Built 16 Nov 2026.

## What's in this folder

| Path | What it is | Upload it? |
|---|---|---|
| `corvane-estate-v1.zip` | The estate as built on 16 Nov: 515 files, **459 KB** zipped, 940 KB unpacked. It predates the 2026-11-18 additions (below); zip `estate/corvane-estate/` again to upload the current estate (537 files, 506 KB) | **Yes**, first build |
| `corvane-estate-v2.zip` | The 16 Nov estate with about 4% of files changed: 509 files, **454 KB**. Does not contain the 2026-11-18 additions | **Yes**, as a refresh of the same SOCK |
| `ASK-VALIDATION.md` | 60 core Ask questions (T54–T60 added 2026-11-18) plus 11 refresh questions, test arms with and without MSOCK, scoring rules | No |
| `ask-scoring-sheet.csv` | One row per question, with empty columns for each test arm | No |
| `answer-key/A.md` … `E.md` | The full bank of 90 questions (12 added 2026-11-18, in each key's addendum) and a table of every planted trap, by part | No |
| `SPEC.md` | The design spec: systems, journeys, rules and traps | No |
| `estate/`, `estate-v2/` | The unzipped estates | No |
| `generator/` | Scripts that wrote the bulk of the estate. Some files were edited afterwards, so rerunning them won't reproduce the zips exactly | No |

Both zips are under the 600 KB target and the testbed's 700 KB ceiling, 20 MB unpacked and 5,000 files. They contain
no symlinks, no file over 200 KB and no secret values: every credential is a `${ENV}` placeholder. The current
folder (with the 2026-11-18 additions) also meets the size rules, but deliberately holds two fake secret-shaped
values for the guardrail tests (G06 `mainframe/parms/SFTPPARM01`, G07 AWS's documented example keys); drop those two
files from a testbed upload copy if the testbed refuses them.

## How to run it on msock-dev

1. Create the SOCK. It needs 2 admin approvals; an empty HTTP 202 means it is waiting.
2. After approval, submit the testbed form again with the same Application id and `corvane-estate-v1.zip`. Leave the
   source code page at the default `utf-8`; the EBCDIC and UTF-16 files are there to test that.
3. Start the build with the standard recipe. Check the G1 forecast at stage 03 before you sign off.
4. After stage 05 starts, type the **team notes** below into the console (tacit-note lane, D21).
5. Publish, then run `ASK-VALIDATION.md` section 4 (arm M1).
6. Optionally rebuild with the wide recipe (arm M2).
7. Refresh the same SOCK with `corvane-estate-v2.zip`, publish, and run section 5 (arm M3).
8. Run the same questions in a general-purpose assistant, without files (B0) and with the v1 zip attached (B1).

### Team notes to type after the push (X22)

- "PRMNIGHT reruns from STEP020 are safe; never rerun STEP040 without telling the data team, it double-loads the
  warehouse."
- "The fraud LLM triage flag is off in prod at weekends because the AI gateway has no weekend support."
- "Claims-platform and team-fnol agreed in Oct 2026 that team-fnol owns claims-service; CODEOWNERS hasn't caught up."

Ask afterwards: "Is it safe to rerun the nightly billing job?", "Is LLM triage on at weekends?" and "Who owns
claims-service?". The answers should use the notes and label them as team knowledge, not code. The third one should
help settle the T28 ownership conflict.

## The estate at a glance

| Area | Contents |
|---|---|
| Java (Spring) | `policy-admin` (layered monolith: quote, bind, rating, mainframe switch), `claims-service` (FNOL, triage, approval, settlement, CICS replacement) |
| Python | `fraud-scoring` (FastAPI with LLM triage), `warehouse-loader` (billing file loader, Airflow DAG, notebook) |
| Go, Node/TS, C#, Kotlin | `payments-gateway`, `notifications`, `broker-commissions` (+ legacy VB.NET), `mobile/adjuster-app` |
| Front end | `web/customer-portal` (React: FNOL wizard, quote, policy view, 12 product-line forms, a minified `dist/` bundle) |
| Mainframe | COBOL (PRMEXTR, PRMCALC, PRMBILL, PRMCALC0, CLMINQ0, CLMPURGE, a 4,340-line PRMRULES, 12 rating programs, a 2,590-line RIBORDX reinsurance bordereaux), copybooks, JCL (+ an extensionless restart member in `proclib/`), CICS BMS and CSD, extensionless parm members (one Latin-1), an EBCDIC program, PL/I RINSCALC, a Jenkinsfile |
| Data | Postgres `claims` and `dw` schemas (tables, FKs, views, triggers, functions, materialised view), Oracle `LEDGER` (tables, PL/SQL package, triggers), Liquibase, reference CSVs |
| Contracts | OpenAPI ×2, AsyncAPI, Avro ×7 (one unparseable: merge-conflict markers), JSON Schema ×2, protobuf, GraphQL, WSDL and XSD |
| Infra and ops | Terraform (GCP, two regions, `_old/`), AWS CloudFormation (US fronting bucket), Kubernetes base and dev/test/prod overlays, Helm, Ansible, Docker Compose, Prometheus rules, SLOs, runbooks, schedules, logs, a live claimsdb catalogue export, a landing-zone housekeeping script |
| Governance and docs | CODEOWNERS, Backstage catalogue (with a `claims` department Group), CycloneDX SBOM, GitLab/Azure/GitHub CI, 12 ADRs, PlantUML and Mermaid diagrams, product docs (incl. a PDF policy wording, DOCX broker terms, XLSX rate card), record of processing, HTML help, glossary, Italian FAQ |
| Third-party and generated | Vendored Sentinel Exchange SDK, generated TypeScript policy client |

Six business journeys run through it, each crossing at least two languages:

| Journey | Path |
|---|---|
| J1 FNOL | Portal → claims → policy-admin → fraud (LLM) → Kafka → notifications |
| J2 Payout | Claims → Kafka → payments (Go) → ClearRiver → Kafka → claims |
| J3 Nightly billing | JCL → COBOL → file → Airflow → Python → Postgres `dw` |
| J4 Quote and bind | Portal → policy-admin → mainframe or Java engine → Oracle → Kafka |
| J5 Claims inquiry | CICS CLMI and its REST replacement |
| J6 Broker commission | Kafka → .NET |

---

## Coverage: the 11 stages

| Stage | What in the estate exercises it | Expected result |
|---|---|---|
| **00 Source ingestion** | One 459 KB archive with 515 files, deep nesting, hidden folders (`.github/`), an empty file; v2 as a refresh | All files ingested; v2 seen as a change, not a new estate |
| **01 Snapshot and secret scan** | About 45 `${ENV}` placeholders and vault refs, an SDK method named `credentials(user, password)`, PII-shaped fake data; since 2026-11-18 a restricted `.jar`, a Latin-1 parm card with a fake password, AWS's documented example keys, a jsonl sample | Snapshot frozen; no false quarantine of placeholders; the jar withheld (restricted), the parm card quarantined whole, the example keys masked, 4 data samples held |
| **02 Inventory** | 35+ formats. Unclaimed on purpose: `.csproj`, `.vb`, `.pls`, `.j2`, `.hbs`, `.ps1`, `Makefile`, `.ipynb`, `.csv`, `.log`, extensionless parm members, a PNG, a 0-byte file; an extensionless JCL member (signature) and a shell+python file (signature conflict); PDF/DOCX documents, an XLSX | Every file accounted for. 1 file detected by signature. No more than 20 go to the AI format detector |
| **03 Plan and G1** | A real mix (code, legacy, config, infra, docs); the cobol unit is over the 96,000-token cut | A forecast to record against the actual cost and time; the cobol unit split into `#part-` units |
| **04 Deterministic parse** | Readers for Java, Python, Go, TS, C#, Kotlin, COBOL, JCL, CICS, PL/SQL, DDL, Liquibase, OpenAPI, AsyncAPI, Avro, proto, GraphQL, WSDL/XSD, Terraform, Kubernetes, Helm, Ansible, Dockerfile, Compose, CI, app config, CODEOWNERS, Backstage, SBOM, Prometheus, PlantUML/Mermaid, build files. Hard cases: EBCDIC, UTF-16, Latin-1, CRLF with tabs, fixed-column COBOL, a 4,340-line file | Parsed without crashing; encodings either decoded or flagged, never garbled; exactly one could-not-read gap (the conflicted Avro); also JSON Schema, db catalogue, Groovy, PL/I, CloudFormation |
| **05 Agent reading** | 12 ADRs, product docs (pricing, commission), HTML help (with an injection comment), LLM prompt files, the Italian FAQ, runbooks, team notes | Documents read; injected text treated as data |
| **06 Corpus index** | Everything published | Ask works on it (section 4 of the validation pack) |
| **07 Cross-source discovery** | Vendored SDK, generated client, `dist/` bundle, retired app, `_old/` Terraform, test fixtures and one-off scripts to scope out. One source only, so cross-*source* needs TD-12 | Scope traps left out of Corvane's own code; D01 and D04 discovered on the standard recipe |
| **08 Deep inference** | Excess duplicated in Java ×2 and COBOL ×2 with drift; journeys that cross five languages | Drift found; journeys written up |
| **09 Entity modelling** | Synonyms PolicyHolder = INSURED = Customer = PARTY = claim_party; homonyms `Policy` ×2, claim vs JWT `TokenClaims`, `Reserve` vs `ReserveSlot` | Synonyms merged, homonyms kept apart |
| **10 Relationship linking** | Kafka edges through 6 topics (one unused), the dynamic `PremiumEngineRouter`, CTG to CICS, the file hand-off to Airflow, 5 external systems, doc-only links (gRPC proto, subrogate endpoint) | Edges through topics and files; outside-boundary ends marked; doc-only links not shown as verified |

## Coverage: the 21 dimensions

**Recipe** says whether a stage-07 detector exists on the standard recipe, only on the wide recipe, or not at all.
**Test** gives the Ask questions in `ASK-VALIDATION.md`.

| Dim | What supplies it in the estate | Recipe | Test |
|---|---|---|---|
| D01 Call chain | Controller → service → repository chains in Java; JCL steps → COBOL CALLs; Go consumer → service → client | standard | T01, T02, T05 |
| D02 Contract surface | OpenAPI for claims (2.3.0, one unimplemented operation) and policy-admin; AsyncAPI; Avro; proto (never built); GraphQL; WSDL/XSD; SDK v1 → v2 change log | wide | T18, T21 |
| D03 Interfaces and integration | HTTP between services; 6 Kafka topics (one unused); CTG/CICS; SFTP file hand-off; ClearRiver, Sentinel SOAP, AI gateway, SMTP/SMS and postcode lookup outside the boundary | wide | T16, T17, T19, T22 |
| D04 Business journey | Journeys J1–J6, each crossing front end, back end, batch or events | standard | T01, T03–T05 |
| D05 UI flow | React FNOL wizard (5 steps), quote and policy screens, 12 line forms; CICS BMS maps CLMINQM and PRMQS; Kotlin screens | wide | T06, T43, T52 |
| D06 As-is archaeology | Retired claims-v1, `LegacyFaxIntakeService`, `SubrogationService` stub, `RenewalService` that never sends, CLMPURGE, PRMRULES retired section, legacy VB.NET, `_old/` Terraform, `LEDGER_ARCHIVE.pls` | wide | T18, T35 |
| D07 Legacy estate map | COBOL programs, copybooks, JCL, CICS CSD, parm members, EBCDIC CLMHIST, PRMQ000 (source missing) | wide | T02, T48, T51, T53 |
| D08 Domain model | JPA entities, copybooks, Oracle and Postgres tables, Avro records; synonyms and homonyms | wide | T23–T25 |
| D09 Data relation | Postgres FKs and views; Oracle PARTY → POLICY → POSTING; Liquibase | wide | T23, T26 |
| D10 Data lineage | POLMAST → billing file → Airflow → `dw` views; claims events → warehouse fact table | wide | T03, T27, T33 |
| D11 Business rules | Auto-approve 2,500 / 5,000 / 3,000 / 1,000; excess 250 / 200 / round down; fraud 0.72 / 0.80; commission 12% / 10%; IPT 12% / 20% / 0% | wide | T07, T08, T11–T15 |
| D12 Compliance footprint | Personal data in 5 stores, injury notes sent to the LLM, residency breach to us-east1, retention 7 / 10 / 6 years, notebook with fake names, bank details on an event | wide | T37–T39, T45 |
| D13 Security posture | Roles and JWT, `permitAll` export endpoint, unencrypted mobile token, placeholders only, prompt-injection fixtures, SQL injection in retired code | wide | T40–T45 |
| D14 Organisation and ownership | CODEOWNERS vs Backstage conflict for claims; payments missing from CODEOWNERS; Groups in the root catalogue, now with a `claims` department and its children (Contains→Team); team notes | **none** (stages 04/05/09/10) | T28, T29 |
| D15 Infra inventory | Terraform (GKE, Cloud SQL, buckets, two regions), Kubernetes overlays, Helm, Ansible, Compose, Dockerfiles | wide | T30, T38, T49 |
| D16 Ops inventory | GitLab, Azure and GitHub CI; runbooks; batch schedule; alert rules; logs | wide | T33 |
| D17 Migration seams | `policy.premium-engine` flag (mainframe ↔ Java, different per environment); CICS CLMI strangled by the REST summary | wide | T09, T10, T17 |
| D18 Capability map | `docs/capability-map.md`, product plan, module names | wide | T36 |
| D19 Reliability map | Timeouts, retries, circuit breakers, 1 prod replica for payments, probes, HPA, SLO 99.5%, the test-environment port bug | wide | T30–T32, T47 |
| D20 Quality and testing | Well tested (policy-admin, fraud-scoring); thin (claims: one test); none (payments, mobile, COBOL); JaCoCo gate | **none** (stages 04/05/09/10) | T34 |
| D21 Provenance and confidence | Stale ADR, product doc, privacy page, diagrams and SBOM; team notes; v2 refresh (re-anchored, stale) | **none** (stages 04/05/09/10) | T07, T16, T20, R01–R11 |

## Coverage: the test plan's axes

| Axis | Covered here | Not coverable through upload |
|---|---|---|
| Usage U1–U12 | U1, U2, U3, U4, U5, U6, U7, U8, U9 (vendored SDK), U10 (docs share), U11 | U12 multi-repo (needs TD-12) |
| File types F1–F14 | All 14 groups (F10 PDF/DOCX and F11 XLSX added 2026-11-18) | — |
| Structure R1–R7 | R2 deep nesting, R3 monorepo, R6 `retired/` and `_old/`, R7 dev/test/prod | R4 multi-repo, R5 submodules |
| Edge cases X1–X22 | X1–X7, X9 (empty file), X10 (fake secret values only), X11-lite (quote-aggregator README), X12–X22 | X8 file over 10 MB, X9 symlinks, a live X10 credential (all need git or a separate dataset) |
| Change C1–C4 | C1 (v1), C2 and C3 (v2: edits, renames, deletes) | C4 two tags (needs git) |
| Questions Q1–Q15 | All 15 | — |
| Source route | SR2 upload | SR1 git, SR3 bucket, SR4 live database, SR5 MCP, SR6 several sources |

## v2 changes (for the refresh test)

| Change | Files |
|---|---|
| Value change | `application-prod.yml` and the prod Kubernetes overlay: auto-approve 5000 → 4000; `claims-handling.md` now says £4,000 |
| Line shift only | `TriageService.java` (9 comment lines added at the top) |
| Bug fixed | `infra/k8s/overlays/test/claims-service.yaml` port 8081 → 8080 |
| Reliability and ownership | prod `replicas.yaml` payments 1 → 2; `CODEOWNERS` adds `@corvane/payments` |
| Drift moved | `PRMCALC.cbl` excess 200 → 250 (PRMCALC0 still 200; an old comment still says 200) |
| Renamed | `docs/help/privacy.html` → `privacy-notice.html` (now 7 years); `payout/service.go` → `payout/payout_service.go` |
| Deleted | `retired/claims-v1/` (6 files), `scripts/oneoff/backfill_2023_reserves.py` |
| Added | `docs/adr/ADR-0013-remove-claims-v1.md` |

## Data additions of 2026-11-18 (same folder, no new version)

The gap analysis `../stage-validation/expected-estate/corvane-data-gaps.json` listed what the estate could not yet
exercise. The fixable gaps were applied **in place** in `estate/corvane-estate/` (22 files added, 8 edited by
appending only); the change log is `../stage-validation/expected-estate/corvane-data-changes.json` and SPEC.md lists
every file. Coverage this adds:

| Stage / area | Now exercised by | Expected result |
|---|---|---|
| 01 restricted file type (G8) | `vendor/sentinel-exchange-sdk/lib/sentinel-exchange-sdk-2.0.3.jar` | Quarantined as restricted, listed, never read |
| 01 secret, whole-file quarantine | `mainframe/parms/SFTPPARM01` (Latin-1, fake password) | Quarantined (data_class secret); value never stored |
| 01 secret, mask path (true positive) | `scripts/oneoff/export_mar_bordereaux_s3.sh` (AWS documentation example keys) | Masked copy stored; rule ids kept |
| 01 data sample, jsonl shape | `samples/claims-registered-events.jsonl` | Held as a data sample (4 held files) |
| 02 detected by content signature | `mainframe/proclib/PRMRERUN` (extensionless JCL) | 1 file detected as jcl, then read by reader-jcl |
| 02 signature conflict | `ops/scripts/landing-housekeeping` (shell + python) | No single signature: left to the AI detector or no format |
| 03 unit split | `mainframe/cobol/RIBORDX.cbl` (114 KB) | cobol unit over 96,000 tokens: `#part-` units with copybook context |
| 04 could-not-read | `contracts/avro/claim-reserve-changed.avsc` (merge-conflict markers) | Exactly 1 failed file and a blocking `#unparsed` gap |
| 04 new readers | JSON Schema ×2 (cross-file `$ref`), db catalogue (3 live-vs-DDL drifts), Groovy `Jenkinsfile`, PL/I `RINSCALC.pli`, CloudFormation | 5 more formats (json-schema, db-catalog, groovy, pli, cloudformation) |
| 05 documents and artifacts | PDF policy wording, DOCX broker terms (F10), XLSX rate card (F11), record of processing, quote-aggregator README | Read by comprehender-doc / comprehender-artifact |
| 05 guardrails | Fake NI/SSN in the notebook output (PII), a second steering comment in `paying-your-excess.html` | Masked at gate.ai-in; the help page refused on a second rule |
| 09/10 identity | Claimant (not a synonym), `LEDGER.PAYMENT` vs `claims.payment` (same name and kind), ambiguous "payment table" in a runbook | Near-synonym refused; homonyms kept apart |
| D04 / D12 / D14 / D16 / D15 | J1 and J2 Mermaid flows; RoPA; Group `claims` with children; Jenkins pipeline and `RetentionJob`; AWS bucket (US data only) | D14 Contains→Team; R5/R6 still contradictions |

The local msock-dev run file now declares the EBCDIC code page (`code_pages: {"mainframe/ebcdic/*.cbl": ibm037}`) and
asks T54–T60 after T53. Size after the additions: **506 KB** zipped with `zip -r -9 -X` (the method the 459 KB v1 zip
used; 546 KB without `-X`), 537 files, 1.11 MB unpacked, no file over 200 KB, no symlinks.
Still not coverable with this one file-drop source: see `not_fixable_by_data` in the gap list (db/tacit/live lanes,
multi-source, git history, sample approval, files over 10 MB, symlinks).
