# Sentinel Claims Exchange Java SDK 2.0.3 — VENDORED COPY, DO NOT EDIT

Third-party SDK from Sentinel Exchange Ltd for the industry claims-history bureau (SOAP,
`https://soap.sentinel-exchange.example/ClaimsExchange`). Vendored into the Corvane estate because the vendor does not
publish to a Maven repository. Licence: see LICENSE.txt (proprietary, redistribution not permitted).

Used by claims-service `SentinelExchangeAdapter` only. Upgrade by replacing this folder with the vendor's release zip.

```java
SentinelClient client = SentinelClient.builder()
    .endpoint(SentinelClient.DEFAULT_ENDPOINT)
    .memberId("CORV01")
    .credentials(user, password)
    .timeout(Duration.ofSeconds(4))
    .maxRetries(1)
    .build();
SearchResult r = client.searchPriorClaims(new SearchRequest().withMember("CORV01"));
```
