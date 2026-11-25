"""Combines rule indicators, bureau history and the optional LLM label into one score."""
from __future__ import annotations

import logging

from . import settings as cfg
from .models import Decision, Indicator, ScoreRequest, ScoreResponse
from .rules import common, registry

log = logging.getLogger(__name__)

MODEL_VERSION = "fraud-rules-2026.02+llm"

LLM_LABEL_WEIGHTS = {"low": -0.5, "medium": 0.4, "high": 1.0}


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def decide(score: float) -> Decision:
    if score >= cfg.DECLINE_THRESHOLD:
        return Decision.HOLD
    if score >= cfg.REFER_THRESHOLD:
        return Decision.REFER
    return Decision.CLEAR


class ScoringEngine:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def score(self, req: ScoreRequest) -> ScoreResponse:
        indicators: list[Indicator] = []
        indicators += common.evaluate(req)
        line_rules = registry.for_line(req.line_code)
        indicators += line_rules.evaluate(req)

        raw = sum(i.weight for i in indicators)
        score = clamp(raw)

        label = None
        if self.llm_client is not None and cfg.settings.llm_triage_enabled:
            try:
                label = await self.llm_client.triage(req)
            except Exception as exc:  # the LLM is advisory: a failure never blocks a claim
                log.warning("llm triage failed for claim %s: %s", req.claim_id, exc)
            if label in LLM_LABEL_WEIGHTS:
                delta = cfg.LLM_WEIGHT * LLM_LABEL_WEIGHTS[label]
                score = clamp(score + delta)
                indicators.append(Indicator(code="LLM_TRIAGE", weight=round(delta, 3), detail=f"label={label}"))

        decision = decide(score)
        log.info("claim %s scored %.3f -> %s (%d indicators)", req.claim_id, score, decision.value, len(indicators))
        return ScoreResponse(claim_id=req.claim_id, score=round(score, 4), decision=decision,
                             indicators=indicators, llm_label=label, model_version=MODEL_VERSION)
