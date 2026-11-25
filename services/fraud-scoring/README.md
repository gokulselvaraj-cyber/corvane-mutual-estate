# fraud-scoring

Scores a newly registered claim for fraud risk. Called synchronously by claims-service
(`FraudScoringClient.score` → `POST /v1/score`, plain HTTP/JSON) during first notice of loss, and also
consumes `claims.registered.v1` to re-score claims asynchronously once photos and documents arrive.

## How a score is made
1. `rules/` — one module per product line (MTR, HOM, …) adds weighted indicators.
2. `bureau` signal — prior claims count passed in by claims-service (from Sentinel Claims Exchange).
3. Optional LLM triage — when `fraud.llm-triage.enabled` is true the claim narrative **and injury notes**
   are sent to the AI gateway with `prompts/fraud-triage.txt`; the model's label nudges the score.

Score ≥ `REFER_THRESHOLD` (see `corvane_fraud/settings.py`) → `REFER` (route to the counter-fraud team).
Score ≥ `DECLINE_THRESHOLD` → `HOLD` (payment blocked until a manager reviews).

## Run locally
    uvicorn corvane_fraud.app:app --port 8090

Owner: Fraud Analytics (team-fraud-analytics). Runbook: ops/runbooks/fraud-scoring.md
