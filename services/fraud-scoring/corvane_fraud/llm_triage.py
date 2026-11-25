"""LLM triage through Corvane's AI gateway.

Sends the claim narrative AND the injury notes to the gateway with prompts/fraud-triage.txt.
DPIA-2025-031 covered the narrative only; injury notes (special-category health data) were added in
v1.7 to improve whiplash detection and have not been re-assessed. Names and national IDs are NOT masked
before the call; see the TODO in build_prompt.
"""
from __future__ import annotations

import pathlib

import httpx

from .models import ScoreRequest
from .settings import LLM_MAX_CHARS, settings

LABELS = ("low", "medium", "high")


def load_prompt(name: str = "fraud-triage.txt") -> str:
    return (pathlib.Path(settings.prompt_dir) / name).read_text(encoding="utf-8")


def build_prompt(req: ScoreRequest, template: str) -> str:
    # TODO(FRAUD-412): mask claimant name and national id before sending (agreed with DPO, not yet done)
    text = template.format(
        claim_id=req.claim_id,
        line_code=req.line_code,
        loss_cause=req.loss_cause,
        loss_date=req.loss_date.isoformat(),
        reported_date=req.reported_date.isoformat(),
        claimed_amount=f"{req.claimed_amount} {req.currency}",
        claimant_name=req.claimant.full_name,
        claimant_postcode=req.claimant.postcode or "unknown",
        narrative=req.narrative,
        injury_notes=req.injury_notes or "none",
        prior_claims=req.prior_claims_3y,
    )
    return text[:LLM_MAX_CHARS]


class LlmTriageClient:
    def __init__(self, http: httpx.AsyncClient | None = None):
        self.http = http or httpx.AsyncClient(timeout=settings.ai_timeout_s)
        self.template = load_prompt()

    async def triage(self, req: ScoreRequest) -> str | None:
        prompt = build_prompt(req, self.template)
        resp = await self.http.post(
            settings.ai_gateway_url,
            headers={"Authorization": f"Bearer {settings.ai_gateway_token}", "X-Corvane-Purpose": "fraud-triage"},
            json={"model": settings.ai_model, "temperature": 0,
                  "messages": [{"role": "user", "content": prompt}], "max_tokens": 20},
        )
        resp.raise_for_status()
        label = resp.json()["choices"][0]["message"]["content"].strip().lower()
        return label if label in LABELS else None
