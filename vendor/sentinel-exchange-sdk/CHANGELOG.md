# Changelog — Sentinel Claims Exchange Java SDK

## 2.0.3 (2026-03-02)
- Fix: `SoapTransport` now honours `maxRetries` on HTTP 503 only, not on SOAP faults.

## 2.0.0 (2025-09-15) — breaking
- **Renamed** `SentinelClient.searchClaims(SearchRequest)` to `searchPriorClaims(SearchRequest)`.
- **Renamed** result type `ClaimSearchResponse` to `SearchResult`; `getHits()` replaced by the public field `matches`.
- New `riskBand` (A–E) on `SearchResult`; `hasUndisclosedClaims()` is true for bands D and E.
- `lookbackYears` default changed from 3 to 5.
- Minimum Java version is now 17.

## 1.4.2 (2024-11-20)
- `searchClaims` accepts `vehicleRegistration` for motor searches.

## 1.4.0 (2024-06-01)
- Added `registerClaim` and `updateClaimStatus`.
- Credentials moved from a properties file to `Builder.credentials(user, password)`.
