# policy-admin

Layered Spring Boot monolith (controller → service → domain → repository) that owns the policy lifecycle for all
twelve Corvane product lines: **quote → rate → bind → renew**.

| Concern | Where |
|---|---|
| REST API | `api/QuoteController`, `api/PolicyController` (contract: `contracts/policy-admin.openapi.yaml`) |
| Rating | `service/RatingService` + per-line `rating/<Line>RatingRules` |
| Premium engine switch | `service/PremiumEngineRouter` reads `policy.premium-engine` (`java` or `mainframe`) |
| Ledger | `ledger/LedgerClient` calls Oracle `LEDGER.PKG_POLICY_LEDGER.post_premium` |
| Events | `events/PolicyEventPublisher` publishes `policies.bound.v1` |

## Premium engine (migration seam)
Until the mainframe rating engine (CICS program `PRMCALC0` behind CTG server `CORVCTG1`) is retired, production
keeps `policy.premium-engine: mainframe`. Dev and test run the Java port (`JavaRatingService`). See ADR-0009.

## Running locally
`docker compose up policy-admin` from the estate root, or `mvn spring-boot:run -Dspring-boot.run.profiles=dev`.
The service listens on **8080** in every environment.

## Renewals
`RenewalService` finds policies due in the next 30 days and prices them. Sending the renewal invitations is still
TODO (POL-1184); nothing is emailed yet.
