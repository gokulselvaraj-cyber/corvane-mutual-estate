"""Consumes claims.registered.v1 and re-scores claims once documents are attached.

Event schema: contracts/avro/ClaimRegistered.avsc. The synchronous FNOL score is the one that drives
triage; this async re-score only raises a REFER if the score has crossed the threshold since.
"""
import asyncio
import json
import logging
from datetime import date
from decimal import Decimal

from .engine import ScoringEngine
from .llm_triage import LlmTriageClient
from .models import Claimant, ScoreRequest
from .settings import settings

log = logging.getLogger(__name__)


def to_request(evt: dict) -> ScoreRequest:
    return ScoreRequest(
        claim_id=evt["claimId"], policy_number=evt["policyNumber"], line_code=evt["lineCode"],
        loss_date=date.fromisoformat(evt["lossDate"]), reported_date=date.fromisoformat(evt["reportedDate"]),
        policy_start_date=date.fromisoformat(evt.get("policyStartDate", evt["lossDate"])),
        claimed_amount=Decimal(str(evt["claimedAmount"])), currency=evt.get("currency", "GBP"),
        loss_cause=evt["lossCause"], narrative=evt.get("narrative", ""), injury_notes=evt.get("injuryNotes"),
        prior_claims_3y=evt.get("priorClaims3y", 0),
        claimant=Claimant(full_name=evt["claimantName"], postcode=evt.get("postcode")),
    )


def run() -> None:
    from confluent_kafka import Consumer
    c = Consumer({"bootstrap.servers": settings.kafka_bootstrap, "group.id": settings.consumer_group,
                  "enable.auto.commit": False, "auto.offset.reset": "earliest"})
    c.subscribe([settings.registered_topic])
    eng = ScoringEngine(LlmTriageClient() if settings.llm_triage_enabled else None)
    while True:
        msg = c.poll(1.0)
        if msg is None or msg.error():
            continue
        evt = json.loads(msg.value())
        res = asyncio.run(eng.score(to_request(evt)))
        log.info("re-scored %s: %s", res.claim_id, res.decision.value)
        c.commit(msg)


if __name__ == "__main__":
    run()
