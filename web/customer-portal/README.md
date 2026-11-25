# Customer portal

React 18 + TypeScript single-page app for Corvane Mutual customers.

| Area | Route | Backend |
|---|---|---|
| Get a quote | `/quote/:line` | policy-admin `POST /v1/quotes` |
| View my policy | `/policies/:policyNumber` | policy-admin `GET /v1/policies/{policyNumber}` |
| Report a claim (FNOL) | `/claims/new` | claims-service `POST /v1/claims/drafts`, `POST /v1/claims/drafts/{id}/photos`, `POST /v1/claims` |

The FNOL wizard has five steps: PolicyLookup, IncidentDetails, DamageAndPhotos, Review, Submit.

Postcode lookup uses `https://postcode.lookup.example/v1` (external).

Owned by the Digital team (`@corvane/digital`). Built and deployed by `.github/workflows/portal.yml`.

`dist/` holds the last production bundle checked in for the CDN cache-warm job. It is generated output; do not edit.
