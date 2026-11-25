"""Persists scores to claimsdb table claims.fraud_score (owned by claims-platform DDL)."""
import json
import logging

log = logging.getLogger(__name__)

INSERT = """
INSERT INTO claims.fraud_score (claim_id, score, decision, indicators, llm_label, model_version, scored_at)
VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
ON CONFLICT (claim_id) DO UPDATE SET score = EXCLUDED.score, decision = EXCLUDED.decision,
  indicators = EXCLUDED.indicators, llm_label = EXCLUDED.llm_label, scored_at = now()
"""


class ScoreStore:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def save(self, result) -> None:
        try:
            import psycopg
            with psycopg.connect(self.dsn) as conn:
                conn.execute(INSERT, (result.claim_id, result.score, result.decision.value,
                                      json.dumps([i.model_dump() for i in result.indicators]),
                                      result.llm_label, result.model_version))
        except Exception as exc:  # scoring must still answer the caller
            log.error("could not persist score for %s: %s", result.claim_id, exc)
