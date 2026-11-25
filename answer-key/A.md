# Answer key A: policy-admin, Oracle ledger, vendored Sentinel SDK, generated policy client

Scope: `services/policy-admin/`, `data/oracle/`, `vendor/sentinel-exchange-sdk/`, `generated/policy-client-ts/`,
`contracts/policy-admin.openapi.yaml`, `contracts/sentinel-claims-exchange.wsdl`, `contracts/sentinel-claims-exchange.xsd`.
Paths below are relative to the estate root. `PA` = `services/policy-admin/src/main/java/com/corvane/policy/`.

Trust signal = expected Ask status (`answered` / `not_known` / `refused`) and the trust level the cited items should
carry (verified, inferred, contradicted, unevidenced, known_unknown, not_in_scope).

## Questions

| ID | Question | Q type | Dim | Expected answer | Evidence | Trust signal |
|---|---|---|---|---|---|---|
| A01 | What happens, step by step, when a quote is bound into a policy? | Q1 | D01, D04 | `PolicyController.bind` (`POST /v1/policies/{quoteId}/bind`) → `PolicyService.bind`: loads the quote, refuses it if referred or expired (`QuoteNotBindableException`, HTTP 409), numbers the policy as line code + 9 digits (`PolicyNumbers.format`), `Policy.bind` sets expiry to 1 year minus 1 day, saves, then `LedgerClient.postPremium` calls Oracle `LEDGER.PKG_POLICY_LEDGER.post_premium`, then `PolicyEventPublisher.policyBound` publishes `policies.bound.v1` keyed by policy number. | `PA/api/PolicyController.java`, `PA/service/PolicyService.java`, `PA/ledger/LedgerClient.java`, `PA/events/PolicyEventPublisher.java`, `data/oracle/PKG_POLICY_LEDGER.pkb` | answered; verified |
| A02 | Which premium engine does policy-admin use in production, and which in dev and test? | Q3 | D17, D15 | Production uses the **mainframe** (`application-prod.yml` `policy.premium-engine: mainframe`: CICS program PRMCALC0 via CTG server CORVCTG1). Dev and test use **java** (`JavaRatingService`). The base `application.yml` default is `java`. `PremiumEngineRouter` picks the engine; an unknown value fails fast. | `services/policy-admin/src/main/resources/application*.yml`, `PA/service/PremiumEngineRouter.java`, `services/policy-admin/README.md` | answered; verified |
| A03 | Is production quote pricing still done on the mainframe? (rewording of A02) | Q10 | D17 | Same as A02: yes, prod prices through PRMCALC0 on the mainframe; the Java port runs only in dev and test. The answer must agree with A02. | as A02 | answered; verified; consistent with A02 |
| A04 | How is the compulsory excess calculated, and is it the same everywhere it's implemented? | Q11 | D11 | policy-admin `RatingService.applyExcess`: compulsory **250** + voluntary, rounded HALF_UP to whole pounds. It is duplicated with drift: COBOL `PRMCALC` paragraph `3000-APPLY-EXCESS` still uses **200**, and claims-service `ClaimSettlementCalculator.applyExcess` uses 250 but rounds DOWN. The Javadoc and README name the duplication (POL-977). The 2026 motor policy wording (PDF, Section 4.2) promises customers **£250**, so the COBOL 200 is the drift. | `PA/service/RatingService.java`; `mainframe/cobol/PRMCALC.cbl`; `services/claims-service/.../ClaimSettlementCalculator.java`; `docs/product/wordings/motor-policy-wording-2026.pdf` | answered; **contradicted** across sources (must surface the drift, not pick one silently) |
| A05 | (Standard recipe) What business rules (D11) has the SOCK discovered for rating? | Q13 | D11 | On the standard recipe, stage 07 runs D01 and D04 only, so D11 is **held_by_policy**. Ask should say the dimension was not discovered. It may still quote rule lines it can cite from code, but it must not present a D11 surface as discovered. On the wide recipe: excess (A04), IPT 12% / 20% for TRV and GDG, per-line referral rules and minimum premiums. | `registry` recipe behaviour; `PA/service/RatingService.java`, `PA/rating/*RatingRules.java` | standard: held_by_policy / known_unknown for D11; wide: answered, verified + contradicted (excess) |
| A06 | Is a PolicyHolder in policy-admin the same thing as a PARTY in the Oracle ledger? | Q4 | D08, D09 | Yes. The same real-world entity, joined on `party_ref` / `PARTY_REF`. It is also the COBOL `INSURED` (POLREC), the portal `Customer` and the claims `claim_party` policyholder row. LEDGER.PARTY holds only the name, not NI number or date of birth. | `PA/domain/PolicyHolder.java` (Javadoc), `data/oracle/01_ledger_tables.sql` (COMMENT), `data/oracle/README.md`, `services/policy-admin/src/main/resources/db/changelog/changes/001-policy.yaml` | answered; verified for the documented statement, inferred for the stage-09 merge |
| A07 | Where is the `Policy` class defined and what does it represent? | Q4 | D08 | There are two: `com.corvane.policy.domain.Policy` (policy-admin) is an **insurance policy**; `com.corvane.claims.security.Policy` (claims-service) is an **access-control policy**. They must not be merged. | `PA/domain/Policy.java` (Javadoc names the homonym), claims-service security package | answered; verified; two separate entities |
| A08 | Which version of jackson-databind does policy-admin use? | Q6 | D21, D12 | **2.17.1** (pom property `jackson.version`). The estate SBOM lists 2.13.4, which is stale. | `services/policy-admin/pom.xml`; `sbom/corvane.cdx.json` | answered; verified (pom) + contradicted (SBOM) |
| A09 | In version 1.x of the Sentinel Exchange SDK, what was the prior-claims search method called, and what is it called now? | Q12 | D02, D21 | 1.x: `SentinelClient.searchClaims(SearchRequest)` returning `ClaimSearchResponse` (`getHits()`). Since 2.0.0 (2025-09-15): `searchPriorClaims(SearchRequest)` returning `SearchResult` (public field `matches`, new `riskBand`); default lookback changed from 3 to 5 years. Vendored version is 2.0.3. | `vendor/sentinel-exchange-sdk/CHANGELOG.md`, `vendor/sentinel-exchange-sdk/src/main/java/com/sentinelexchange/sdk/SentinelClient.java` | answered from the CHANGELOG, or the vendored code flagged not_in_scope; never invented |
| A10 | Does policy-admin send renewal invitations to customers? | Q7 | D06, D04 | **No.** `RenewalService.priceDueRenewals` runs at 06:00 Mon–Fri (Europe/London), finds BOUND policies expiring within 30 days, re-prices them and marks them RENEWAL_DUE, but sending is a TODO (POL-1184). It publishes nothing and sends no email. | `PA/service/RenewalService.java`, `services/policy-admin/README.md` | answered; verified |
| A11 | What was the loss ratio of the Motor book in 2025? | Q8 | — | Not in the estate. There are no claims-cost or earned-premium figures for 2025. | — | **not_known** |
| A12 | Why does policy-admin call the Sentinel Claims Exchange when it prices a quote? | Q9 | D03 | False premise. policy-admin never calls Sentinel. The vendored SDK is used only by claims-service `SentinelExchangeAdapter` during FNOL. Quoting uses the premium engine and the postcode lookup only. | `PA/service/QuoteService.java`, `vendor/sentinel-exchange-sdk/README.md` | answered with the premise corrected; or not_known; never a made-up reason |
| A13 | What would break if `LEDGER.PARTY.PARTY_REF` were renamed? | Q5 | D09, D10 | `PKG_POLICY_LEDGER.party_id_for` (the lookup and its insert), the view `V_POLICY_BALANCE` (selects `p.PARTY_REF`), the unique constraint `UQ_PARTY_REF`, and the link to policy-admin: `LedgerClient` passes `P_PARTY_REF` from `policy_holder.party_ref`. | `data/oracle/PKG_POLICY_LEDGER.pkb`, `data/oracle/02_ledger_views.sql`, `data/oracle/01_ledger_tables.sql`, `PA/ledger/LedgerClient.java` | answered; inferred (impact analysis) with verified citations |
| A14 | How does policy-admin talk to the mainframe? | Q2 | D03, D07 | A CICS Transaction Gateway ECI call (`MainframePremiumAdapter`) to CTG server **CORVCTG1**, program **PRMCALC0**, with a 200-byte EBCDIC (cp037) COMMAREA in the PRMCOMM layout. The premium comes back at offset 100. Timeout 4,000 ms (2,500 ms in prod), behind the `ctg` circuit breaker. | `PA/service/MainframePremiumAdapter.java`, `services/policy-admin/src/main/resources/application.yml`, `application-prod.yml` | answered; verified |
| A15 | Where is the policy holder's national insurance number stored, and does any API return it? | Q15 | D12, D13 | Column `policy_holder.national_id` in policy-admin's Postgres database `policydb` (marked PII). It is not stored in LEDGER.PARTY. `PolicyView` (the API response) never includes it; logs use `maskedNationalId()`. On the claims side the DDL has `claims.claim_party.national_id`, but the live catalogue export (2026-11-14) shows `ni_number` and `ssn` instead (hotfix CHG-90117). | `services/policy-admin/src/main/resources/db/changelog/changes/001-policy.yaml`, `PA/domain/PolicyHolder.java`, `PA/api/dto/PolicyView.java`, `data/oracle/01_ledger_tables.sql` | answered; verified |

## Planted traps in part A

| Trap | Path | What a correct SOCK does |
|---|---|---|
| R2 excess: 250 + voluntary, HALF_UP (copies: COBOL 200, claims rounds DOWN) | `PA/service/RatingService.java` | Reports the drift (D11, stage 08) |
| D17 seam: `policy.premium-engine` java/mainframe; dev=java, test=java, prod=mainframe | `PA/service/PremiumEngineRouter.java`, `services/policy-admin/src/main/resources/application-{dev,test,prod}.yml` | Finds the dynamic dispatch and the per-environment value |
| Homonym `com.corvane.policy.domain.Policy` vs claims `security.Policy` | `PA/domain/Policy.java` | Keeps two entities (stage 09) |
| Synonyms PolicyHolder = PARTY = INSURED = Customer = claim_party | `PA/domain/PolicyHolder.java`, `data/oracle/01_ledger_tables.sql`, `001-policy.yaml` | Merges into one entity (stage 09) |
| D06: `RenewalService` prices but never sends (TODO POL-1184) | `PA/service/RenewalService.java` | Flags an incomplete flow |
| D06 / unclaimed format: `LEDGER_ARCHIVE.pls`, not deployed since 2022 | `data/oracle/LEDGER_ARCHIVE.pls` | Counted at stage 02, not parsed; not reported as live |
| Scope trap: vendored third-party SDK | `vendor/sentinel-exchange-sdk/` | Scoped out of Corvane's own code (stage 07, not_in_scope) |
| Scope trap: generated client ("DO NOT EDIT") | `generated/policy-client-ts/` | Recognised as generated |
| Versions: SDK CHANGELOG 1.4 → 2.0 rename | `vendor/sentinel-exchange-sdk/CHANGELOG.md` | Answers Q12 for the right version |
| SBOM conflict: pom jackson-databind 2.17.1 (SBOM 2.13.4) | `services/policy-admin/pom.xml` | Reports the mismatch (D21) |
| PII: `national_id`, `date_of_birth`, address in `policy_holder` | `001-policy.yaml`, `PA/domain/PolicyHolder.java` | D12 footprint |
| Secrets only as `${ENV}` placeholders (DB, CTG, postcode key) | `services/policy-admin/src/main/resources/application.yml` | Pass the stage-01 secret scan |
| External boundary: postcode lookup, Sentinel SOAP endpoint, CTG | `PA/service/PostcodeLookupClient.java`, `contracts/sentinel-claims-exchange.wsdl` | Ends marked outside the boundary |
| Roles CUSTOMER, ADJUSTER, CLAIMS_MANAGER, BROKER via JWT `roles` claim; issuer `https://login.corvane.internal` | `PA/config/SecurityConfig.java`, controllers | D13 |
| Port 8080 everywhere (the claims test overlay's 8081 is builder E's X1 bug) | `services/policy-admin/src/main/resources/application.yml`, `Dockerfile` | Lets Ask spot the X1 bug |
| D20: well tested (RatingService, router, PolicyService, numbers, CTG COMMAREA, all 12 lines); JaCoCo 80% gate | `services/policy-admin/src/test/...`, `pom.xml` | Quality evidence |
| Append-only ledger postings (delete refused by trigger) | `data/oracle/03_ledger_triggers.sql` | D11 / D13 rule |

## Names other builders rely on
- CTG server `CORVCTG1`, CICS program `PRMCALC0`, COMMAREA layout `PRMCOMM` (LINE-CODE X(3), POSTCODE X(8), HOLDER-AGE 9(3),
  SUM-INSURED 9(9)V99, VOL-EXCESS 9(5)V99, PRIOR-CLAIMS 9(2); response at offset 100: BASE-PREMIUM 9(9)V99, REFER-FLAG X,
  REFER-REASON X(60)). Builder D's PRMCOMM copybook should match.
- Generated rating classes claim to port mainframe programs `RAT<code>01` (e.g. RATMTR01), which match builder D's generator.
- `PolicyBoundEvent` fields for `contracts/avro/PolicyBound.avsc` (builder B): policyNumber, lineCode, partyRef, brokerCode,
  annualPremium, iptAmount, currency, inceptionDate, premiumEngine.

## Addendum: data added in place on 2026-11-18

These files were added to the same estate folder (no new version) from `stage-validation/expected-estate/corvane-data-gaps.json`; the full change log is `corvane-data-changes.json` next to it. Answers above that change are already edited in place; the rows below are new.
| ID | Question | Q | Dim | Expected answer | Evidence | Expected trust signal |
|---|---|---|---|---|---|---|
| A16 | What is in the LEDGER.PAYMENT table, and is it the same as claims.payment? | Q4 | D08, D09 | `LEDGER.PAYMENT` holds **premium collected** from the policyholder (PAYMENT_ID, POLICY_ACCOUNT_ID → `LEDGER.POLICY_ACCOUNT.ACCOUNT_ID`, AMOUNT, METHOD DD or CARD, COLLECTED_ON). It is **not** `claims.payment` in claimsdb, which is a claim payout to a payee. Same name and kind, different store and meaning: they must stay two nodes | `data/oracle/01_ledger_tables.sql` (appended at the end); `data/postgres/001_claims_schema.sql` | answered; verified; two entities (homonym kept apart) |

| Trap | Plan code | Where |
|---|---|---|
| Same-name, same-kind homonym across stores: `LEDGER.PAYMENT` (premium collected) vs `claims.payment` (payout) (G15) | X15, stage 09/10 | `data/oracle/01_ledger_tables.sql` (end of file); `data/postgres/001_claims_schema.sql` |
| Documentary side of R2: the motor policy wording PDF says compulsory £250 (G13) | R2, D11, F10 | `docs/product/wordings/motor-policy-wording-2026.pdf` |
