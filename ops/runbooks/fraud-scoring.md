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
