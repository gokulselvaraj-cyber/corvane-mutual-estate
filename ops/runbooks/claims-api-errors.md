# Runbook: claims API errors

**Alert:** `ClaimsApiErrorRateHigh`. **SLO:** 99.5% over 28 days (`infra/observability/slo-claims-api.yaml`).

1. Check downstream calls first: policy-admin (`POLICY_ADMIN_URL`), fraud-scoring and the Sentinel exchange.
2. In the **test** environment, a 5xx storm on FNOL usually means policy-admin cannot be reached; check the URL in the
   overlay.
3. If fraud-scoring is slow, turn off `fraud.llm-triage.enabled` in the `corvane-env` ConfigMap; claims then score on
   rules only.
